"""
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext. 

For license issues, please contact:

Dr. Bing Ye
Life Sciences Institute
University of Michigan
210 Washtenaw Avenue, Room 5403
Ann Arbor, MI 48109-2216
USA

Email: bingye@umich.edu
"""


import os

import wx

from LabGym.analyzebehaviorsdetector import (
    delete_detector,
    get_animal_names,
    get_annotation_class_names,
    test_detector,
    train_detector,
    get_detector_names,
)
from LabGym.tools import extract_frames
from LabGym.gui.utils import WX_VIDEO_WILDCARD, LabGymWindow


class GenerateImageExamples(LabGymWindow):
    """Generate image examples to use to train a Detector."""

    def __init__(self):
        """Open the Generate Image Example frame."""
        super().__init__(title="Generate Image Examples", size=(1000, 330))
        self.path_to_videos = None
        self.result_path = None
        self.framewidth = None
        self.t = 0
        self.duration = 0
        self.skip_redundant = 1000

        self.text_inputvideos = self.module_text("None.")
        self.add_module(
            "Select the video(s) to generate\nimage examples",
            self.select_videos,
            "Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.",
            self.text_inputvideos,
        )

        self.text_outputfolder = self.module_text("None.")
        self.add_module(
            "Select a folder to store the\ngenerated image examples",
            self.select_outpath,
            "The generated image examples (extracted frames) will be stored in this folder.",
            self.text_outputfolder,
        )

        self.text_startgenerate = self.module_text(
            "Default: at the beginning of the video(s)."
        )
        self.add_module(
            "Specify when generating image examples\nshould begin (unit: second)",
            self.specify_timing,
            "Enter a beginning time point for all videos",
            self.text_startgenerate,
        )

        self.text_duration = self.module_text(
            "Default: from the specified beginning time to the end of a video."
        )
        self.add_module(
            "Specify how long generating examples\nshould last (unit: second)",
            self.input_duration,
            "This duration will be used for all the videos.",
            self.text_duration,
        )

        self.text_skipredundant = self.module_text(
            "Default: generate an image example every 1000 frames."
        )
        self.add_module(
            "Specify how many frames to skip when\ngenerating two consecutive images",
            self.specify_redundant,
            "To increase the efficiency of training a Detector, you need to make the training images as diverse (look different) as possible. You can do this by setting an interval between the two consecutively extracted images.",
            self.text_skipredundant,
        )

        self.add_submit_button(
            label="Start to generate image examples",
            handler=self.generate_images,
            tool_tip="Press the button to start generating image examples.",
        )

        self.display_window()

    def select_videos(self, event):
        """Open dialogs to select videos to generate images from."""
        video_select_dialog = wx.FileDialog(
            self, "Select video(s)", "", "", WX_VIDEO_WILDCARD, style=wx.FD_MULTIPLE
        )
        if video_select_dialog.ShowModal() != wx.ID_OK:
            video_select_dialog.Destroy()
            return

        self.path_to_videos = video_select_dialog.GetPaths()
        video_select_dialog.Destroy()

        path = os.path.dirname(self.path_to_videos[0])
        resize_dialog = wx.MessageDialog(
            self,
            'Proportional resize the video frames?\nSelect "No" if dont know what it is.',
            "(Optional) resize the frames?",
            wx.YES_NO | wx.ICON_QUESTION,
        )

        if resize_dialog.ShowModal() != wx.ID_YES:
            self.framewidth = None
            self.text_inputvideos.SetLabel(
                f"Selected {len(self.path_to_videos)} video(s) in: {path} (original framesize)."
            )
            resize_dialog.Destroy()
            return

        resize_dialog.Destroy()

        frame_width_dialog = wx.NumberEntryDialog(
            self,
            "Enter the desired frame width",
            "The unit is pixel:",
            "Desired frame width",
            480,
            1,
            10000,
        )

        if frame_width_dialog.ShowModal() != wx.ID_OK:
            self.framewidth = None
            self.text_inputvideos.SetLabel(
                f"Selected {len(self.path_to_videos)} video(s) in: {path} (original framesize)."
            )
            frame_width_dialog.Destroy()
            return

        self.framewidth = max(int(frame_width_dialog.GetValue()), 10)
        self.text_inputvideos.SetLabel(
            f"Selected {len(self.path_to_videos)} video(s) in: {path} (proportionally resize framewidth to {self.framewidth})."
        )
        frame_width_dialog.Destroy()

    def select_outpath(self, event):
        """Select directory to store image examples."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                f"Generate image examples in: {self.result_path}."
            )
        dialog.Destroy()

    def specify_timing(self, event):
        """Choose time point to start generating image examples."""
        dialog = wx.NumberEntryDialog(
            parent=self,
            message="Enter beginning time to generate examples",
            prompt="The unit is second:",
            caption="Beginning time to generate examples",
            value=0,
            min=0,
            max=100000000000000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.t = max(float(dialog.GetValue()), 0)
            self.text_startgenerate.SetLabel(
                f"Start to generate image examples at the: {str(self.t)} second."
            )
        dialog.Destroy()

    def input_duration(self, event):
        """Choose duration to generate video examples."""
        dialog = wx.NumberEntryDialog(
            parent=self,
            message="Enter the duration for generating examples",
            prompt="The unit is second:",
            caption="Duration for generating examples",
            value=0,
            min=0,
            max=100000000000000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.duration = int(dialog.GetValue())
            self.text_duration.SetLabel(
                f"The generation of image examples lasts for {self.duration} seconds."
            )
        dialog.Destroy()

    def specify_redundant(self, event):
        """Select number of frames to skip per example."""
        dialog = wx.NumberEntryDialog(
            self,
            "How many frames to skip?",
            "Enter a number:",
            "Interval for generating examples",
            15,
            0,
            100000000000000,
        )
        self.skip_redundant = (
            int(dialog.GetValue()) if dialog.ShowModal() == wx.ID_OK else 1000
        )
        self.text_skipredundant.SetLabel(
            f"Generate an image example every {self.skip_redundant} frames."
        )
        dialog.Destroy()

    def generate_images(self, event):
        """Confirm image example generation."""
        if self.path_to_videos is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / output folder selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        dialog = wx.MessageDialog(
            self,
            "Start to generate image examples?",
            "Start to generate examples?",
            wx.YES_NO | wx.ICON_QUESTION,
        )

        if dialog.ShowModal() == wx.ID_YES:
            print("Generating image examples...")
            for i in self.path_to_videos:
                extract_frames(
                    i,
                    self.result_path,
                    framewidth=self.framewidth,
                    start_t=self.t,
                    duration=self.duration,
                    skip_redundant=self.skip_redundant,
                )
            print("Image example generation completed!")
        dialog.Destroy()


class TrainDetectors(LabGymWindow):
    """Train Detectors using labeled image examples."""

    def __init__(self):
        super().__init__(title="Train Detectors", size=(1000, 280))
        self.path_to_trainingimages = None
        self.path_to_annotation = None
        self.inference_size = 320
        self.iteration_num = 200

        self.text_selectimages = self.module_text("None.")
        self.add_module(
            button_label="Select the folder containing\nall the training images",
            button_handler=self.select_images,
            tool_tip="The folder that stores all the training images.",
            text=self.text_selectimages,
        )

        self.text_selectannotation = self.module_text("None.")
        self.add_module(
            button_label="Select the *.json\nannotation file",
            button_handler=self.select_annotation,
            tool_tip="The .json file that stores the annotation for the training images. Make sure it is in “COCO instance segmentation” format.",
            text=self.text_selectannotation,
        )

        self.text_inferencingsize = self.module_text("Default: 480.")
        self.add_module(
            button_label="Specify the inferencing framesize\nfor the Detector to train",
            button_handler=self.input_inferencingsize,
            tool_tip="This number should be divisible by 32. It determines the speed-accuracy trade-off of Detector performance. Larger size means higher accuracy but slower speed. See Extended Guide for details.",
            text=self.text_inferencingsize,
        )

        self.text_iterations = self.module_text("Default: 200.")
        self.add_module(
            button_label="Specify the iteration number\nfor the Detector training",
            button_handler=self.input_iterations,
            tool_tip='More training iterations typically yield higher accuracy but take longer. A number between 200 ~ 2000 is good for most scenarios. For "Interactive advanced" mode, more iterations (>2000) may be needed. You may also increase the diversity and amount of training images for higher accuracy.',
            text=self.text_iterations,
        )

        self.add_submit_button(
            label="Train the Detector",
            handler=self.train_detector,
            tool_tip="You need to name the Detector to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.",
        )

        self.display_window()

    def select_images(self, event):
        """Select labeled images."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_trainingimages = dialog.GetPath()
            self.text_selectimages.SetLabel(
                f"Path to training images: {self.path_to_trainingimages}."
            )
        dialog.Destroy()

    def select_annotation(self, event):
        """Select COCO annotation file for images."""
        dialog = wx.FileDialog(
            self,
            "Select the annotation file (.json)",
            "",
            wildcard="Annotation File (*.json)|*.json",
            style=wx.FD_OPEN,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_annotation = dialog.GetPath()
            class_names = get_annotation_class_names(self.path_to_annotation)
            self.text_selectannotation.SetLabel(
                f"Animal/object categories in annotation file: {class_names}."
            )
        dialog.Destroy()

    @property
    def inference_size(self) -> int:
        """The inferencing frame size for the Detector."""
        return self._inference_size

    @inference_size.setter
    def inference_size(self, inference_size: int):
        """Set the inferencing frame size.

        Args:
            inference_size: The new inferencing frame size.

        Raises:
            ValueError: The frame size is not a multiple of 32.
        """
        if inference_size % 32 != 0:
            raise ValueError(f"{inference_size} is not a multiple of 32.")
        self._inference_size = inference_size

    def input_inferencingsize(self, event):
        """Enter inferencing frame size for the Detector."""
        dialog = wx.NumberEntryDialog(
            self,
            "Input the inferencing frame size\nof the Detector to train",
            "Enter a number:",
            "Divisible by 32",
            value=self.inference_size,
            min=32,
            max=2048,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        try:
            self.inference_size = int(dialog.GetValue())
            self.text_inferencingsize.SetLabel(
                "Inferencing frame size: " + str(self.inference_size) + "."
            )
        except ValueError as err:
            wx.MessageBox(
                str(err),
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        dialog.Destroy()

    def input_iterations(self, event):
        """Set the number of iterations for Detector training."""
        dialog = wx.NumberEntryDialog(
            self,
            "Input the iteration number\nfor the Detector training",
            "Enter a number:",
            "Iterations",
            value=self.iteration_num,
            min=1,
            max=10000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.iteration_num = int(dialog.GetValue())
            self.text_iterations.SetLabel(
                f"Training iteration number: {self.iteration_num}."
            )
        dialog.Destroy()

    def train_detector(self, event):
        """Train a Detector with the given parameters."""
        if self.path_to_trainingimages is None or self.path_to_annotation is None:
            wx.MessageBox(
                "No training images / annotation file selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        while True:
            dialog = wx.TextEntryDialog(
                self, "Enter a name for the Detector to train", "Detector name"
            )
            if dialog.ShowModal() != wx.ID_OK:
                break

            if dialog.GetValue().strip() == "":
                wx.MessageBox(
                    "Please enter a name.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                continue

            detector_name = dialog.GetValue()
            if detector_name in get_detector_names():
                wx.MessageBox(
                    f"The Detector {dialog.GetValue()} already exists!",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                continue

            train_detector(
                self.path_to_annotation,
                self.path_to_trainingimages,
                detector_name,
                self.iteration_num,
                self.inference_size,
            )
            break


class TestDetectors(LabGymWindow):
    """Test Detectors using labeled image examples."""

    def __init__(self):
        super().__init__(title="Test Detectors", size=(1000, 280))
        self.path_to_testingimages = None
        self.path_to_annotation = None
        self.detector_name = None
        self.results_folder = None

        self.text_selectdetector = self.module_text("None.")
        self.add_module(
            "Select a Detector\nto test",
            self.select_detector,
            "The object / animal names in the ground-truth testing image dataset should match those in the selected Detector.",
            self.text_selectdetector,
        )

        self.text_selectimages = self.module_text("None.")
        self.add_module(
            "Select the folder containing\nall the testing images",
            self.select_images,
            "The folder that stores all the testing images.",
            self.text_selectimages,
        )

        self.text_selectannotation = self.module_text("None.")
        self.add_module(
            "Select the *.json\nannotation file",
            self.select_annotation,
            "The .json file that stores the annotation for the testing images. Make sure it is in “COCO instance segmentation” format.",
            self.text_selectannotation,
        )

        self.text_select_results_folder = self.module_text("None.")
        self.add_module(
            "Select the folder to\nstore testing results",
            self.select_results_folder,
            "The folder will stores the testing results.",
            self.text_select_results_folder,
        )

        testanddelete = wx.BoxSizer(wx.HORIZONTAL)
        button_test = wx.Button(self.panel, label="Test the Detector", size=(300, 40))
        button_test.Bind(wx.EVT_BUTTON, self.test_detector)
        wx.Button.SetToolTip(
            button_test,
            "Test the selected Detector on the annotated, ground-truth testing images.",
        )
        button_delete = wx.Button(self.panel, label="Delete a Detector", size=(300, 40))
        button_delete.Bind(wx.EVT_BUTTON, self.delete_detector)
        wx.Button.SetToolTip(
            button_delete,
            "Permanently delete a Detector. The deletion CANNOT be restored.",
        )
        testanddelete.Add(button_test, 0, wx.RIGHT, 5)
        testanddelete.Add(button_delete, 0, wx.LEFT, 5)
        self.boxsizer.Add(0, self.MODULE_TOP_MARGIN, 0)
        self.boxsizer.Add(
            testanddelete, 0, wx.RIGHT | wx.ALIGN_RIGHT, self.BOTTOM_MARGIN * 2
        )
        self.boxsizer.Add(0, self.BOTTOM_MARGIN, 0)

        self.display_window()

    def select_detector(self, event):
        """Select a detector to test."""
        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Detector to test",
            caption="Test a Detector",
            choices=get_detector_names(),
        )

        if dialog.ShowModal() == wx.ID_OK:
            self.detector_name = dialog.GetStringSelection()
            self.text_selectdetector.SetLabel(
                f"Selected: {self.detector_name} (animals/objects: {get_animal_names(self.detector_name)})."
            )
        dialog.Destroy()

    def select_images(self, event):
        """Select annotated testing images."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_testingimages = dialog.GetPath()
            self.text_selectimages.SetLabel(
                f"Path to testing images: {self.path_to_testingimages}."
            )
        dialog.Destroy()

    def select_annotation(self, event):
        """Select COCO annotation file."""
        dialog = wx.FileDialog(
            self,
            "Select the annotation file (.json)",
            "",
            wildcard="Annotation File (*.json)|*.json",
            style=wx.FD_OPEN,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_annotation = dialog.GetPath()
            class_names = get_annotation_class_names(self.path_to_annotation)
            self.text_selectannotation.SetLabel(
                f"Animal/object categories in annotation file: {class_names}."
            )
        dialog.Destroy()

    def select_results_folder(self, event):
        """Select folder to store testing results."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.results_folder = dialog.GetPath()
            self.text_select_results_folder.SetLabel(
                f"Testing results stored in: {self.results_folder}."
            )
        dialog.Destroy()

    def test_detector(self, event):
        """Test the selected detector."""
        if (
            self.detector_name is None
            or self.path_to_testingimages is None
            or self.path_to_annotation is None
            or self.results_folder is None
        ):
            wx.MessageBox(
                "No Detector / training images / annotation file / output path selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        else:
            test_detector(
                self.path_to_annotation,
                self.path_to_testingimages,
                self.detector_name,
                self.results_folder,
            )

    def delete_detector(self, event):
        """Delete a Detector."""
        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Detector to delete",
            caption="Delete a Detector",
            choices=get_detector_names().sort(),
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        detector = dialog.GetStringSelection()
        confirm = wx.MessageDialog(
            self,
            f"Delete {detector}?",
            "CANNOT be restored!",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if confirm.ShowModal() == wx.ID_YES:
            delete_detector(detector)
        confirm.Destroy()
