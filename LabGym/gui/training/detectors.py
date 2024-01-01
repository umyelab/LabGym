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


import json
import os
import shutil
from pathlib import Path
from typing import Callable

import wx

from ...analyzebehaviorsdetector import test_detector, train_detector
from ...tools import extract_frames, wx_video_wildcard


detector_path = str(Path(__file__).resolve().parent.parent / "detectors")


class GenerateImageExamples(wx.Frame):
    """Generate image examples to use to train a Detector."""

    def __init__(self):
        """Open the Generate Image Example frame."""
        super().__init__(parent=None, title="Generate Image Examples", size=(1000, 330))
        self.path_to_videos = None
        self.result_path = None
        self.framewidth = None
        self.t = 0
        self.duration = 0
        self.skip_redundant = 1000

        self.panel = wx.Panel(self)
        self.boxsizer = wx.BoxSizer(wx.VERTICAL)

        self.text_inputvideos = wx.StaticText(
            self.panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        self.add_module(
            "Select the video(s) to generate\nimage examples",
            self.select_videos,
            "Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.",
            self.text_inputvideos,
        )

        self.text_outputfolder = wx.StaticText(
            self.panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        self.add_module(
            "Select a folder to store the\ngenerated image examples",
            self.select_outpath,
            "The generated image examples (extracted frames) will be stored in this folder.",
            self.text_outputfolder,
        )

        self.text_startgenerate = wx.StaticText(
            self.panel,
            label="Default: at the beginning of the video(s).",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        self.add_module(
            "Specify when generating image examples\nshould begin (unit: second)",
            self.specify_timing,
            "Enter a beginning time point for all videos",
            self.text_startgenerate,
        )

        self.text_duration = wx.StaticText(
            self.panel,
            label="Default: from the specified beginning time to the end of a video.",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        self.add_module(
            "Specify how long generating examples\nshould last (unit: second)",
            self.input_duration,
            "This duration will be used for all the videos.",
            self.text_duration,
        )

        self.text_skipredundant = wx.StaticText(
            self.panel,
            label="Default: generate an image example every 1000 frames.",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        self.add_module(
            "Specify how many frames to skip when\ngenerating two consecutive images",
            self.specify_redundant,
            "To increase the efficiency of training a Detector, you need to make the training images as diverse (look different) as possible. You can do this by setting an interval between the two consecutively extracted images.",
            self.text_skipredundant,
        )

        generate = wx.BoxSizer(wx.HORIZONTAL)
        button_generate = wx.Button(
            self.panel, label="Start to generate image examples", size=(300, 40)
        )
        button_generate.Bind(wx.EVT_BUTTON, self.generate_images)
        wx.Button.SetToolTip(
            button_generate, "Press the button to start generating image examples."
        )
        generate.Add(button_generate, 0, wx.LEFT, 50)
        self.boxsizer.Add(0, 5, 0)
        self.boxsizer.Add(generate, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        self.boxsizer.Add(0, 10, 0)

        self.panel.SetSizer(self.boxsizer)

        self.Centre()
        self.Show(True)

    def add_module(
        self,
        button_label: str,
        button_handler: Callable,
        tool_tip: str,
        text: wx.StaticText,
    ):
        """
        Adds a button and text box to the main sizer.

        Args:
            button_label: The button label.
            button_handler: The function to handle the button press.
            tooltip: The text displayed when the user hovers over the button.
            text: The wx.StaticText to be displayed next to the button.
        """
        module = wx.BoxSizer(wx.HORIZONTAL)
        button = wx.Button(self.panel, label=button_label, size=(300, 40))
        button.Bind(wx.EVT_BUTTON, button_handler)
        wx.Button.SetToolTip(button, tool_tip)
        module.Add(button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module.Add(text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        self.boxsizer.Add(0, 10, 0)
        self.boxsizer.Add(module, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

    def select_videos(self, event):
        """Open dialogs to select videos to generate images from."""
        video_select_dialog = wx.FileDialog(
            self, "Select video(s)", "", "", wx_video_wildcard(), style=wx.FD_MULTIPLE
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
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                "Generate image examples in: " + self.result_path + "."
            )
        dialog.Destroy()

    def specify_timing(self, event):
        dialog = wx.NumberEntryDialog(
            self,
            "Enter beginning time to generate examples",
            "The unit is second:",
            "Beginning time to generate examples",
            0,
            0,
            100000000000000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.t = float(dialog.GetValue())
            if self.t < 0:
                self.t = 0
            self.text_startgenerate.SetLabel(
                "Start to generate image examples at the: " + str(self.t) + " second."
            )
        dialog.Destroy()

    def input_duration(self, event):
        dialog = wx.NumberEntryDialog(
            self,
            "Enter the duration for generating examples",
            "The unit is second:",
            "Duration for generating examples",
            0,
            0,
            100000000000000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.duration = int(dialog.GetValue())
            if self.duration != 0:
                self.text_duration.SetLabel(
                    "The generation of image examples lasts for "
                    + str(self.duration)
                    + " seconds."
                )
        dialog.Destroy()

    def specify_redundant(self, event):
        dialog = wx.NumberEntryDialog(
            self,
            "How many frames to skip?",
            "Enter a number:",
            "Interval for generating examples",
            15,
            0,
            100000000000000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.skip_redundant = int(dialog.GetValue())
            self.text_skipredundant.SetLabel(
                "Generate an image example every "
                + str(self.skip_redundant)
                + " frames."
            )
        else:
            self.skip_redundant = 1000
            self.text_skipredundant.SetLabel(
                "Generate an image example every 10000 frames."
            )
        dialog.Destroy()

    def generate_images(self, event):
        if self.path_to_videos is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / output folder selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            do_nothing = True

            dialog = wx.MessageDialog(
                self,
                "Start to generate image examples?",
                "Start to generate examples?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog.ShowModal() == wx.ID_YES:
                do_nothing = False
            else:
                do_nothing = True
            dialog.Destroy()

            if do_nothing is False:
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


class TrainDetectors(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Train Detectors", size=(1000, 280))
        self.path_to_trainingimages = None
        self.path_to_annotation = None
        self.inference_size = 320
        self.iteration_num = 200
        self.detector_path = detector_path
        self.path_to_detector = None

        self.dispaly_window()

    def dispaly_window(self):
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        module_selectimages = wx.BoxSizer(wx.HORIZONTAL)
        button_selectimages = wx.Button(
            panel,
            label="Select the folder containing\nall the training images",
            size=(300, 40),
        )
        button_selectimages.Bind(wx.EVT_BUTTON, self.select_images)
        wx.Button.SetToolTip(
            button_selectimages, "The folder that stores all the training images."
        )
        self.text_selectimages = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectimages.Add(
            button_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectimages.Add(
            self.text_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(0, 10, 0)
        boxsizer.Add(module_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_selectannotation = wx.BoxSizer(wx.HORIZONTAL)
        button_selectannotation = wx.Button(
            panel, label="Select the *.json\nannotation file", size=(300, 40)
        )
        button_selectannotation.Bind(wx.EVT_BUTTON, self.select_annotation)
        wx.Button.SetToolTip(
            button_selectannotation,
            "The .json file that stores the annotation for the training images. Make sure it is in “COCO instance segmentation” format.",
        )
        self.text_selectannotation = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectannotation.Add(
            button_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectannotation.Add(
            self.text_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_inferencingsize = wx.BoxSizer(wx.HORIZONTAL)
        button_inferencingsize = wx.Button(
            panel,
            label="Specify the inferencing framesize\nfor the Detector to train",
            size=(300, 40),
        )
        button_inferencingsize.Bind(wx.EVT_BUTTON, self.input_inferencingsize)
        wx.Button.SetToolTip(
            button_inferencingsize,
            "This number should be divisible by 32. It determines the speed-accuracy trade-off of Detector performance. Larger size means higher accuracy but slower speed. See Extended Guide for details.",
        )
        self.text_inferencingsize = wx.StaticText(
            panel, label="Default: 480.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_inferencingsize.Add(
            button_inferencingsize, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_inferencingsize.Add(
            self.text_inferencingsize, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_inferencingsize, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_iterations = wx.BoxSizer(wx.HORIZONTAL)
        button_iterations = wx.Button(
            panel,
            label="Specify the iteration number\nfor the Detector training",
            size=(300, 40),
        )
        button_iterations.Bind(wx.EVT_BUTTON, self.input_iterations)
        wx.Button.SetToolTip(
            button_iterations,
            'More training iterations typically yield higher accuracy but take longer. A number between 200 ~ 2000 is good for most scenarios. For "Interactive advanced" mode, more iterations (>2000) may be needed. You may also increase the diversity and amount of training images for higher accuracy.',
        )
        self.text_iterations = wx.StaticText(
            panel, label="Default: 200.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_iterations.Add(button_iterations, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module_iterations.Add(
            self.text_iterations, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_iterations, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        button_train = wx.Button(panel, label="Train the Detector", size=(300, 40))
        button_train.Bind(wx.EVT_BUTTON, self.train_detector)
        wx.Button.SetToolTip(
            button_train,
            "You need to name the Detector to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.",
        )
        boxsizer.Add(0, 5, 0)
        boxsizer.Add(button_train, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        boxsizer.Add(0, 10, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def select_images(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_trainingimages = dialog.GetPath()
            self.text_selectimages.SetLabel(
                "Path to training images: " + self.path_to_trainingimages + "."
            )
        dialog.Destroy()

    def select_annotation(self, event):
        wildcard = "Annotation File (*.json)|*.json"
        dialog = wx.FileDialog(
            self,
            "Select the annotation file (.json)",
            "",
            wildcard=wildcard,
            style=wx.FD_OPEN,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_annotation = dialog.GetPath()
            f = open(self.path_to_annotation)
            info = json.load(f)
            classnames = []
            for i in info["categories"]:
                if i["id"] > 0:
                    classnames.append(i["name"])
            self.text_selectannotation.SetLabel(
                "Animal/object categories in annotation file: " + str(classnames) + "."
            )
        dialog.Destroy()

    def input_inferencingsize(self, event):
        dialog = wx.NumberEntryDialog(
            self,
            "Input the inferencing frame size\nof the Detector to train",
            "Enter a number:",
            "Divisible by 32",
            480,
            1,
            2048,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.inference_size = int(dialog.GetValue())
            self.text_inferencingsize.SetLabel(
                "Inferencing frame size: " + str(self.inference_size) + "."
            )
        dialog.Destroy()

    def input_iterations(self, event):
        dialog = wx.NumberEntryDialog(
            self,
            "Input the iteration number\nfor the Detector training",
            "Enter a number:",
            "Iterations",
            200,
            1,
            10000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.iteration_num = int(dialog.GetValue())
            self.text_iterations.SetLabel(
                "Training iteration number: " + str(self.iteration_num) + "."
            )
        dialog.Destroy()

    def train_detector(self, event):
        if self.path_to_trainingimages is None or self.path_to_annotation is None:
            wx.MessageBox(
                "No training images / annotation file selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            do_nothing = False

            stop = False
            while stop is False:
                dialog = wx.TextEntryDialog(
                    self, "Enter a name for the Detector to train", "Detector name"
                )
                if dialog.ShowModal() == wx.ID_OK:
                    if dialog.GetValue() != "":
                        self.path_to_detector = os.path.join(
                            self.detector_path, dialog.GetValue()
                        )
                        if not os.path.isdir(self.path_to_detector):
                            stop = True
                        else:
                            wx.MessageBox(
                                "The name already exists.",
                                "Error",
                                wx.OK | wx.ICON_ERROR,
                            )
                else:
                    do_nothing = True
                    stop = True
                dialog.Destroy()

            if do_nothing is False:
                train_detector(
                    self.path_to_annotation,
                    self.path_to_trainingimages,
                    self.path_to_detector,
                    self.iteration_num,
                    self.inference_size,
                )


class TestDetectors(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Test Detectors", size=(1000, 280))
        self.path_to_testingimages = None
        self.path_to_annotation = None
        self.detector_path = detector_path
        self.path_to_detector = None
        self.output_path = None

        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        module_selectdetector = wx.BoxSizer(wx.HORIZONTAL)
        button_selectdetector = wx.Button(
            panel, label="Select a Detector\nto test", size=(300, 40)
        )
        button_selectdetector.Bind(wx.EVT_BUTTON, self.select_detector)
        wx.Button.SetToolTip(
            button_selectdetector,
            "The object / animal names in the ground-truth testing image dataset should match those in the selected Detector.",
        )
        self.text_selectdetector = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectdetector.Add(
            button_selectdetector, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectdetector.Add(
            self.text_selectdetector, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(0, 10, 0)
        boxsizer.Add(module_selectdetector, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_selectimages = wx.BoxSizer(wx.HORIZONTAL)
        button_selectimages = wx.Button(
            panel,
            label="Select the folder containing\nall the testing images",
            size=(300, 40),
        )
        button_selectimages.Bind(wx.EVT_BUTTON, self.select_images)
        wx.Button.SetToolTip(
            button_selectimages, "The folder that stores all the testing images."
        )
        self.text_selectimages = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectimages.Add(
            button_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectimages.Add(
            self.text_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_selectimages, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_selectannotation = wx.BoxSizer(wx.HORIZONTAL)
        button_selectannotation = wx.Button(
            panel, label="Select the *.json\nannotation file", size=(300, 40)
        )
        button_selectannotation.Bind(wx.EVT_BUTTON, self.select_annotation)
        wx.Button.SetToolTip(
            button_selectannotation,
            "The .json file that stores the annotation for the testing images. Make sure it is in “COCO instance segmentation” format.",
        )
        self.text_selectannotation = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectannotation.Add(
            button_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectannotation.Add(
            self.text_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_selectannotation, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_selectoutpath = wx.BoxSizer(wx.HORIZONTAL)
        button_selectoutpath = wx.Button(
            panel, label="Select the folder to\nstore testing results", size=(300, 40)
        )
        button_selectoutpath.Bind(wx.EVT_BUTTON, self.select_outpath)
        wx.Button.SetToolTip(
            button_selectoutpath, "The folder will stores the testing results."
        )
        self.text_selectoutpath = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectoutpath.Add(
            button_selectoutpath, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectoutpath.Add(
            self.text_selectoutpath, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_selectoutpath, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        testanddelete = wx.BoxSizer(wx.HORIZONTAL)
        button_test = wx.Button(panel, label="Test the Detector", size=(300, 40))
        button_test.Bind(wx.EVT_BUTTON, self.test_detector)
        wx.Button.SetToolTip(
            button_test,
            "Test the selected Detector on the annotated, ground-truth testing images.",
        )
        button_delete = wx.Button(panel, label="Delete a Detector", size=(300, 40))
        button_delete.Bind(wx.EVT_BUTTON, self.remove_detector)
        wx.Button.SetToolTip(
            button_delete,
            "Permanently delete a Detector. The deletion CANNOT be restored.",
        )
        testanddelete.Add(button_test, 0, wx.RIGHT, 50)
        testanddelete.Add(button_delete, 0, wx.LEFT, 50)
        boxsizer.Add(0, 5, 0)
        boxsizer.Add(testanddelete, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        boxsizer.Add(0, 10, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def select_detector(self, event):
        detectors = [
            i
            for i in os.listdir(self.detector_path)
            if os.path.isdir(os.path.join(self.detector_path, i))
        ]
        if "__pycache__" in detectors:
            detectors.remove("__pycache__")
        if "__init__" in detectors:
            detectors.remove("__init__")
        if "__init__.py" in detectors:
            detectors.remove("__init__.py")
        detectors.sort()

        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Detector to test",
            caption="Test a Detector",
            choices=detectors,
        )
        if dialog.ShowModal() == wx.ID_OK:
            detector = dialog.GetStringSelection()
            self.path_to_detector = os.path.join(self.detector_path, detector)
            animalmapping = os.path.join(self.path_to_detector, "model_parameters.txt")
            with open(animalmapping) as f:
                model_parameters = f.read()
            animal_names = json.loads(model_parameters)["animal_names"]
            self.text_selectdetector.SetLabel(
                "Selected: "
                + str(detector)
                + " (animals / objects: "
                + str(animal_names)
                + ")."
            )
        dialog.Destroy()

    def select_images(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_testingimages = dialog.GetPath()
            self.text_selectimages.SetLabel(
                "Path to testing images: " + self.path_to_testingimages + "."
            )
        dialog.Destroy()

    def select_annotation(self, event):
        wildcard = "Annotation File (*.json)|*.json"
        dialog = wx.FileDialog(
            self,
            "Select the annotation file (.json)",
            "",
            wildcard=wildcard,
            style=wx.FD_OPEN,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_annotation = dialog.GetPath()
            f = open(self.path_to_annotation)
            info = json.load(f)
            classnames = []
            for i in info["categories"]:
                if i["id"] > 0:
                    classnames.append(i["name"])
            self.text_selectannotation.SetLabel(
                "Animal/object categories in annotation file: " + str(classnames) + "."
            )
        dialog.Destroy()

    def select_outpath(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.output_path = dialog.GetPath()
            self.text_selectoutpath.SetLabel(
                "Path to testing images: " + self.output_path + "."
            )
        dialog.Destroy()

    def test_detector(self, event):
        if (
            self.path_to_detector is None
            or self.path_to_testingimages is None
            or self.path_to_annotation is None
            or self.output_path is None
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
                self.path_to_detector,
                self.output_path,
            )

    def remove_detector(self, event):
        detectors = [
            i
            for i in os.listdir(self.detector_path)
            if os.path.isdir(os.path.join(self.detector_path, i))
        ]
        if "__pycache__" in detectors:
            detectors.remove("__pycache__")
        if "__init__" in detectors:
            detectors.remove("__init__")
        if "__init__.py" in detectors:
            detectors.remove("__init__.py")
        detectors.sort()

        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Detector to delete",
            caption="Delete a Detector",
            choices=detectors,
        )
        if dialog.ShowModal() == wx.ID_OK:
            detector = dialog.GetStringSelection()
            dialog1 = wx.MessageDialog(
                self,
                "Delete " + str(detector) + "?",
                "CANNOT be restored!",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog1.ShowModal() == wx.ID_YES:
                shutil.rmtree(os.path.join(self.detector_path, detector))
            dialog1.Destroy()
        dialog.Destroy()
