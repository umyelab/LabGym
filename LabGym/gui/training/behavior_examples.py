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
import shutil
from pathlib import Path

import cv2
import numpy as np
import wx

from LabGym.tools import AnimalVsBg
from LabGym.analyzebehaviors import AnalyzeAnimal
from LabGym.analyzebehaviorsdetector import (
    AnalyzeAnimalDetector,
    get_animal_names,
    get_detector_names,
)
from LabGym.gui.utils import (
    WX_IMAGE_WILDCARD,
    WX_VIDEO_WILDCARD,
    LabGymWindow,
    BehaviorMode,
)


THE_ABSOLUTE_CURRENT_PATH = str(Path(__file__).resolve().parent.parent)


class GenerateBehaviorExamples(LabGymWindow):
    """Generate behavior examples for the user to sort."""

    def __init__(self):
        super().__init__(title="Generate Behavior Examples", size=(1000, 530))
        self.behavior_mode = BehaviorMode.NON_INTERACTIVE
        self.use_detector = False
        self.detector_path = None
        self.path_to_detector = None
        self.detection_threshold = 0
        self.animal_kinds = []
        self.background_path = None
        self.path_to_videos = None
        self.result_path = None
        self.framewidth = None
        self.delta = 10000
        self.decode_animalnumber = False
        self.animal_number = None
        self.autofind_t = False
        self.decode_t = False
        self.t = 0
        self.duration = 0
        self.decode_extraction = False
        self.ex_start = 0
        self.ex_end = None
        self.animal_vs_bg = AnimalVsBg.ANIMAL_LIGHTER
        self.stable_illumination = True
        self.length = 15
        self.skip_redundant = 1
        self.include_bodyparts = False
        self.std = 0
        self.background_free = True
        self.social_distance = 0

        self.text_specifymode = self.module_text(
            "Default: Non-interactive: behaviors of each individuals (each example contains one animal / object)"
        )
        self.add_module(
            "Specify the mode of behavior\nexamples to generate",
            self.specify_mode,
            '"Non-interactive" is for behaviors of each individual; "Interactive basic" is for interactive behaviors of all animals but not distinguishing each individual; "Interactive advanced" is slower in analysis than "basic" but distinguishes individuals during close body contact. "Static images" is for analyzing images not videos. See Extended Guide for details.',
            self.text_specifymode,
        )

        self.text_inputvideos = self.module_text("None.")
        self.add_module(
            "Select the video(s) / image(s) to\ngenerate behavior examples",
            self.select_videos,
            "Select one or more videos / images. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) or image formats (jpg, jpeg, png, tiff, bmp) are supported except wmv format.",
            self.text_inputvideos,
        )

        self.text_outputfolder = self.module_text("None.")
        self.add_module(
            "Select a folder to store the\ngenerated behavior examples",
            self.select_outpath,
            'Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video and stores the generated behavior examples. For "Static images" mode, all generated behavior examples will be in this folder.',
            self.text_outputfolder,
        )

        self.text_detection = self.module_text(
            "Default: Background subtraction-based method."
        )
        self.add_module(
            "Specify the method to\ndetect animals or objects",
            self.select_method,
            "Background subtraction-based method is accurate and fast but needs static background and stable illumination in videos; Detectors-based method is accurate and versatile in any recording settings but is slow. See Extended Guide for details.",
            self.text_detection,
        )

        self.text_startgenerate = self.module_text(
            "Default: at the beginning of the video(s)."
        )
        self.add_module(
            "Specify when generating behavior examples\nshould begin (unit: second)",
            self.specify_timing,
            'Enter a beginning time point for all videos or use "Decode from filenames" to let LabGym decode the different beginning time for different videos. See Extended Guide for details.',
            self.text_startgenerate,
        )

        self.text_duration = self.module_text(
            "Default: from the specified beginning time to the end of a video."
        )
        self.add_module(
            "Specify how long generating examples\nshould last (unit: second)",
            self.input_duration,
            "The duration is the same for all the videos in one batch.",
            self.text_duration,
        )

        self.text_animalnumber = self.module_text("Default: 1.")
        self.add_module(
            "Specify the number of animals\nin a video",
            self.specify_animalnumber,
            'Enter a number for all videos or use "Decode from filenames" to let LabGym decode the different animal number for different videos. See Extended Guide for details.',
            self.text_animalnumber,
        )

        self.text_length = self.module_text("Default: 15 frames.")
        self.add_module(
            "Specify the number of frames for\nan animation / pattern image",
            self.input_length,
            "The duration (the number of frames, an integer) of each behavior example, which should approximate the length of a behavior episode. This duration needs to be the same across all the behavior examples for training one Categorizer. See Extended Guide for details.",
            self.text_length,
        )

        self.text_skipredundant = self.module_text(
            "Default: no frame to skip (generate a behavior example every frame)."
        )
        self.add_module(
            "Specify how many frames to skip when\ngenerating two consecutive behavior examples",
            self.specify_redundant,
            "If two consecutively generated examples have many overlapping frames, they look similar, which makes training inefficient and sorting laborious. Specifying an interval (skipped frames) between two examples can address this. See Extended Guide for details.",
            self.text_skipredundant,
        )

        self.add_submit_button(
            "Start to generate behavior examples",
            self.generate_data,
            "Need to specify whether to include background and body parts in the generated behavior examples. See Extended Guide for details.",
        )

        self.display_window()

    def specify_mode(self, event):
        """Select a behavior mode to generate examples."""

        # The indices of each behavior mode in this list are mapped to the same
        # constant values used in the BehaviorMode class.
        behavior_modes = [
            "Non-interactive: behaviors of each individual (each example contains one animal / object)",
            "Interactive basic: behaviors of all (each example contains all animals / objects)",
            "Interactive advanced: behaviors of each individual and social groups (each example contains either one or multiple animals / objects)",
            "Static images (non-interactive): behaviors of each individual in static images(each image contains one animal / object)",
        ]
        dialog = wx.SingleChoiceDialog(
            self,
            message="Specify the mode of behavior examples to generate",
            caption="Behavior-example mode",
            choices=behavior_modes,
        )
        if dialog.ShowModal() != wx.ID_OK:
            self.behavior_mode = BehaviorMode.NON_INTERACTIVE
            self.text_specifymode.SetLabel(
                f"Behavior mode: {behavior_modes[self.behavior_mode]}."
            )
            dialog.Destroy()
            return

        self.behavior_mode = dialog.GetSelection()
        dialog.Destroy()

        if self.behavior_mode == BehaviorMode.INTERACT_ADVANCED:
            # Need to set social distance for Interactive Advanced mode
            dialog1 = wx.NumberEntryDialog(
                self,
                "Interactions happen within the social distance.",
                "(See Extended Guide for details)\nHow many folds of square root of the animals area\nis the social distance (0=infinity far):",
                "Social distance (Enter an integer)",
                0,
                0,
                100000000000000,
            )
            if dialog1.ShowModal() == wx.ID_OK:
                self.social_distance = int(dialog1.GetValue())
                if self.social_distance == 0:
                    self.social_distance = float("inf")
            else:
                self.social_distance = float("inf")
            dialog1.Destroy()
            self.text_detection.SetLabel(
                "Only Detector-based detection method is available for the selected behavior mode."
            )
        elif self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            self.text_detection.SetLabel(
                "Only Detector-based detection method is available for the selected behavior mode."
            )
            self.text_startgenerate.SetLabel(
                'No need to specify this since the selected behavior mode is "Static images".'
            )
            self.text_duration.SetLabel(
                'No need to specify this since the selected behavior mode is "Static images".'
            )
            self.text_animalnumber.SetLabel(
                'No need to specify this since the selected behavior mode is "Static images".'
            )
            self.text_length.SetLabel(
                'No need to specify this since the selected behavior mode is "Static images".'
            )
            self.text_skipredundant.SetLabel(
                'No need to specify this since the selected behavior mode is "Static images".'
            )

        label_text = f"Behavior mode: {behavior_modes[self.behavior_mode]}"
        if self.behavior_mode == BehaviorMode.INTERACT_ADVANCED:
            label_text += f" with social distance {self.social_distance}"
        label_text += "."
        self.text_specifymode.SetLabel(label_text)

    def select_videos(self, event):
        """Select videos/images to generate behavior examples from."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wildcard = WX_IMAGE_WILDCARD
        else:
            wildcard = WX_VIDEO_WILDCARD

        dialog = wx.FileDialog(
            self, "Select video(s) / image(s)", "", "", wildcard, style=wx.FD_MULTIPLE
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        self.path_to_videos = dialog.GetPaths()
        self.path_to_videos.sort()
        dialog.Destroy()

        folder = os.path.dirname(self.path_to_videos[0])
        dialog1 = wx.MessageDialog(
            self,
            'Proportional resize the video frames / images?\nSelect "No" if dont know what it is.',
            "(Optional) resize the frames / images?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog1.ShowModal() != wx.ID_YES:
            self.framewidth = None
            self.text_inputvideos.SetLabel(
                f"Selected {len(self.path_to_videos)} file(s) in {folder} (original frame / image size)."
            )
            dialog1.Destroy()
            return

        dialog2 = wx.NumberEntryDialog(
            self,
            "Enter the desired frame / image width",
            "The unit is pixel:",
            "Desired frame / image width",
            480,
            1,
            10000,
        )
        if dialog2.ShowModal() != wx.ID_OK:
            self.framewidth = None
            self.text_inputvideos.SetLabel(
                f"Selected {len(self.path_to_videos)} file(s) in {folder} (original frame / image size)."
            )
            dialog2.Destroy()
            return

        self.framewidth = max(int(dialog2.GetValue()), 10)
        dialog2.Destroy()
        self.text_inputvideos.SetLabel(
            f"Selected {len(self.path_to_videos)} file(s) in {folder} (proportionally resize frame / image width to {self.framewidth})."
        )

    def select_outpath(self, event):
        """Select folder to store behavior examples."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                f"Generate behavior examples in: {self.result_path}."
            )
        dialog.Destroy()

    def _configure_background_subtraction(self):
        """Configure background subtraction-based example generation."""
        self.use_detector = False

        # The indices of these options are mapped to the same values as the
        # constants in the AnimalVsBg class
        contrasts = [
            "Animal brighter than background",
            "Animal darker than background",
            "Hard to tell",
        ]
        dialog = wx.SingleChoiceDialog(
            self,
            message="Select the scenario that fits your videos best",
            caption="Which fits best?",
            choices=contrasts,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        self.animal_vs_bg = dialog.GetSelection()
        label_options = [
            "animal brighter",
            "animal darker",
            "animal partially brighter/darker",
        ]
        label_text = f"Background Subtraction: {label_options[self.animal_vs_bg]}"
        dialog.Destroy()

        dialog2 = wx.MessageDialog(
            self,
            'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
            "(Optional) load existing background?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog2.ShowModal() == wx.ID_YES:
            start_time_dialog = wx.DirDialog(
                self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
            )
            if start_time_dialog.ShowModal() == wx.ID_OK:
                self.background_path = start_time_dialog.GetPath()
            start_time_dialog.Destroy()
        else:
            self.background_path = None
            if self.animal_vs_bg != AnimalVsBg.HARD_TO_TELL:
                start_time_dialog = wx.MessageDialog(
                    self,
                    'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
                    "(Optional) unstable illumination?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                self.stable_illumination = start_time_dialog.ShowModal() != wx.ID_YES
                start_time_dialog.Destroy()
        dialog2.Destroy()

        if self.background_path is not None:
            self.text_detection.SetLabel(label_text)
            return

        extraction_methods = [
            "Use the entire duration (default but NOT recommended)",
            'Decode from filenames: "_xst_" and "_xet_"',
            "Enter two time points",
        ]
        dialog2 = wx.SingleChoiceDialog(
            self,
            message="Specify the time window for background extraction",
            caption="Time window for background extraction",
            choices=extraction_methods,
        )
        if dialog2.ShowModal() != wx.ID_OK:
            self.text_detection.SetLabel(label_text)
            return

        extraction_method = dialog2.GetStringSelection()
        dialog2.Destroy()

        self.decode_extraction = False
        if extraction_method == extraction_methods[0]:
            self.text_detection.SetLabel(f"{label_text}, using the entire duration.")
            return
        elif extraction_method == extraction_methods[1]:
            self.decode_extraction = True
            self.text_detection.SetLabel(
                f"{label_text}, using time window decoded from filenames '_xst_' and '_xet_'."
            )
            return

        # Prompt for extraction time window
        label_text += ", using time window (in seconds) from "
        start_time_dialog = wx.NumberEntryDialog(
            self,
            "Enter the start time",
            "The unit is second:",
            "Start time for background extraction",
            0,
            0,
            100000000000000,
        )
        if start_time_dialog.ShowModal() == wx.ID_OK:
            self.ex_start = int(start_time_dialog.GetValue())
            label_text += f"{self.ex_start} to "
        start_time_dialog.Destroy()

        end_time_dialog = wx.NumberEntryDialog(
            self,
            "Enter the end time",
            "The unit is second:",
            "End time for background extraction",
            0,
            0,
            100000000000000,
        )
        if end_time_dialog.ShowModal() == wx.ID_OK:
            self.ex_end = int(end_time_dialog.GetValue())
            if self.ex_end == 0:
                self.ex_end = None
                label_text += "the end."
            else:
                label_text += f"{self.ex_end}."
        end_time_dialog.Destroy()

        self.text_detection.SetLabel(label_text)

    def _configure_detector(self):
        """Configure Detector-based example generation."""
        self.use_detector = True
        self.animal_number = {}
        self.detector_path = os.path.join(THE_ABSOLUTE_CURRENT_PATH, "detectors")

        detectors = get_detector_names()
        detectors.append("Choose a new directory of the Detector")

        select_detector_dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Detector for animal detection",
            caption="Select a Detector",
            choices=detectors,
        )
        if select_detector_dialog.ShowModal() != wx.ID_OK:
            select_detector_dialog.Destroy()
            return
        else:
            detector = select_detector_dialog.GetStringSelection()
            select_detector_dialog.Destroy()

        if detector == "Choose a new directory of the Detector":
            dialog2 = wx.DirDialog(
                self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
            )
            if dialog2.ShowModal() == wx.ID_OK:
                self.path_to_detector = dialog2.GetPaths()
            dialog2.Destroy()
        else:
            self.path_to_detector = os.path.join(self.detector_path, detector)

        animal_names = get_animal_names(detector)
        if len(animal_names) > 1:
            dialog2 = wx.MultiChoiceDialog(
                self,
                message="Specify which animals/objects involved in behavior examples",
                caption="Animal/Object kind",
                choices=animal_names,
            )
            if dialog2.ShowModal() == wx.ID_OK:
                self.animal_kinds = [animal_names[i] for i in dialog2.GetSelections()]
            else:
                self.animal_kinds = animal_names
            dialog2.Destroy()
        else:
            self.animal_kinds = animal_names

        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            dialog2 = wx.NumberEntryDialog(
                self,
                "Enter the Detector's detection threshold (0~100%)",
                "The higher detection threshold,\nthe higher detection accuracy,\nbut the lower detection sensitivity.\nEnter 0 if don't know how to set.",
                "Detection threshold",
                0,
                0,
                100,
            )
            if dialog2.ShowModal() == wx.ID_OK:
                detection_threshold = dialog2.GetValue()
                self.detection_threshold = detection_threshold / 100
                self.text_detection.SetLabel(
                    f"Detector: {detector} (detection threshold: {detection_threshold}%); The animals/objects: {self.animal_kinds}."
                )
            dialog2.Destroy()
        else:
            for animal_name in self.animal_kinds:
                self.animal_number[animal_name] = 1
            self.text_animalnumber.SetLabel(
                f"The number of {self.animal_kinds} is: {list(self.animal_number.values())}."
            )
            self.text_detection.SetLabel(
                f"Detector: {detector}; The animals/objects: {self.animal_kinds}."
            )

    def select_method(self, event):
        """Select method to generate contours for behavior examples."""
        DETECTOR = "Use trained Detectors (versatile but slow)"
        BACKGROUND_SUBTRACTION = "Subtract background (fast but requires static background & stable illumination)"
        methods = [DETECTOR]
        if self.behavior_mode in [
            BehaviorMode.NON_INTERACTIVE,
            BehaviorMode.INTERACT_BASIC,
        ]:
            methods.append(BACKGROUND_SUBTRACTION)

        dialog = wx.SingleChoiceDialog(
            self,
            message="How to detect the animals?",
            caption="Detection methods",
            choices=methods,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return

        method = dialog.GetStringSelection()
        dialog.Destroy()

        if method == BACKGROUND_SUBTRACTION:
            self._configure_background_subtraction()
        else:
            self._configure_detector()

    def specify_timing(self, event):
        """Specify how to handle lighting changes for optogenetic experiments."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        if self.use_detector is False:
            dialog = wx.MessageDialog(
                self,
                "light on and off in videos?",
                "Illumination shifts?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog.ShowModal() == wx.ID_YES:
                self.delta = 1.2
            else:
                self.delta = 10000
            dialog.Destroy()

        AUTOMATIC = "Automatic (for light on and off)"
        DECODE = 'Decode from filenames: "_bt_"'
        TIME_POINT = "Enter a time point"
        methods = [DECODE, TIME_POINT]
        if self.delta == 1.2 and self.use_detector is False:
            methods.insert(0, AUTOMATIC)

        dialog = wx.SingleChoiceDialog(
            self,
            message="Specify beginning time to generate behavior examples",
            caption="Beginning time for generator",
            choices=methods,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        else:
            method = dialog.GetStringSelection()
            dialog.Destroy()

        self.autofind_t = False
        self.decode_t = False
        if method == AUTOMATIC:
            self.autofind_t = True
            self.text_startgenerate.SetLabel(
                "Automatically find the onset of the 1st time when light on / off as the beginning time."
            )
        elif method == DECODE:
            self.decode_t = True
            self.text_startgenerate.SetLabel(
                'Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".'
            )
        else:
            dialog2 = wx.NumberEntryDialog(
                self,
                "Enter beginning time to generate examples",
                "The unit is second:",
                "Beginning time to generate examples",
                0,
                0,
                100000000000000,
            )
            if dialog2.ShowModal() == wx.ID_OK:
                self.t = max(float(dialog2.GetValue()), 0)
                self.text_startgenerate.SetLabel(
                    f"Start to generate behavior examples at the: {self.t} second."
                )
            dialog2.Destroy()

    def input_duration(self, event):
        """Select duration for generating behavior examples."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wx.MessageBox(
                "No need to specify this since the selected behavior mode is 'Static images'.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

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
                    f"The generation of behavior examples lasts for {self.duration} seconds."
                )
            else:
                self.text_duration.SetLabel(
                    "The generation of behavior examples lasts for the entire duration of a video."
                )
        dialog.Destroy()

    def specify_animalnumber(self, event):
        """Select the number of animals in the video."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        DECODE = 'Decode from filenames: "_nn_"'
        ENTER = "Enter the number of animals"
        methods = [DECODE, ENTER]

        dialog = wx.SingleChoiceDialog(
            self,
            message="Specify the number of animals in a video",
            caption="The number of animals in a video",
            choices=methods,
        )
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        else:
            method = dialog.GetStringSelection()
            dialog.Destroy()

        self.decode_animalnumber = False
        if method == DECODE:
            self.decode_animalnumber = True
            self.text_animalnumber.SetLabel(
                'Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.'
            )
            return

        if self.use_detector:
            self.animal_number = {}
            for animal_name in self.animal_kinds:
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "",
                    "The number of " + str(animal_name) + ": ",
                    str(animal_name) + " number",
                    1,
                    1,
                    100,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.animal_number[animal_name] = int(dialog1.GetValue())
                else:
                    self.animal_number[animal_name] = 1
                dialog1.Destroy()
            self.text_animalnumber.SetLabel(
                f"The number of {self.animal_kinds} is: {list(self.animal_number.values())}."
            )
        else:
            dialog1 = wx.NumberEntryDialog(
                self,
                "",
                "The number of animals:",
                "Animal number",
                1,
                1,
                100,
            )
            if dialog1.ShowModal() == wx.ID_OK:
                self.animal_number = int(dialog1.GetValue())
            else:
                self.animal_number = 1
            self.text_animalnumber.SetLabel(
                f"The total number of animals in a video is {self.animal_number}."
            )
            dialog1.Destroy()

    def input_length(self, event):
        """Enter the number of frames corresponding to a behavior."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        dialog = wx.NumberEntryDialog(
            self,
            "Enter the number of frames\nfor a behavior example",
            "Enter a number\n(minimum=3):",
            "Behavior episode duration",
            15,
            1,
            1000,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.length = max(int(dialog.GetValue()), 3)
            self.text_length.SetLabel(
                f"The duration of a behavior example is: {self.length} frames."
            )
        dialog.Destroy()

    def specify_redundant(self, event):
        """Select the number of frames to skip when generating examples."""
        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

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
                f"Generate a pair of example every {self.skip_redundant} frames."
            )
        else:
            self.skip_redundant = 1
            self.text_skipredundant.SetLabel(
                "Generate a pair of example at every frame."
            )
        dialog.Destroy()

    def generate_data(self, event):
        """Generate behavior examples with the given configuration."""
        if self.path_to_videos is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / output folder selected.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        dialog = wx.MessageDialog(
            self,
            'Include background in animations? Select "No"\nif background is behavior irrelevant.',
            "Including background?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        self.background_free = dialog.ShowModal() != wx.ID_YES
        dialog.Destroy()

        if self.behavior_mode == BehaviorMode.STATIC_IMAGES:
            if self.path_to_detector is None:
                wx.MessageBox(
                    "You need to select a Detector.", "Error", wx.OK | wx.ICON_ERROR
                )
                return
            else:
                AAD = AnalyzeAnimalDetector()
                AAD.analyze_images_individuals(
                    self.path_to_detector,
                    self.path_to_videos,
                    self.result_path,
                    self.animal_kinds,
                    generate=True,
                    imagewidth=self.framewidth,
                    detection_threshold=self.detection_threshold,
                    background_free=self.background_free,
                )
                return

        dialog = wx.MessageDialog(
            self,
            'Include body parts in pattern images?\nSelect "No" if limb movement is neglectable.',
            "Including body parts?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        self.include_bodyparts = False
        if dialog.ShowModal() == wx.ID_YES:
            self.include_bodyparts = True
            dialog2 = wx.NumberEntryDialog(
                self,
                "Leave it as it is if dont know what it is.",
                "Enter a number between 0 and 255:",
                "STD for motionless pixels",
                0,
                0,
                255,
            )
            if dialog2.ShowModal() == wx.ID_OK:
                self.std = int(dialog2.GetValue())
            else:
                self.std = 0
            dialog2.Destroy()
        dialog.Destroy()

        dialog = wx.MessageDialog(
            self,
            "Start to generate behavior examples?",
            "Start to generate examples?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        else:
            dialog.Destroy()

        for video in self.path_to_videos:
            filename = os.path.splitext(os.path.basename(video))[0].split("_")
            if self.decode_animalnumber is True:
                if self.use_detector is True:
                    self.animal_number = {}
                    number = [x[1:] for x in filename if len(x) > 1 and x[0] == "n"]
                    for a, animal_name in enumerate(self.animal_kinds):
                        self.animal_number[animal_name] = int(number[a])
                else:
                    for x in filename:
                        if len(x) > 1:
                            if x[0] == "n":
                                self.animal_number = int(x[1:])
            if self.decode_t is True:
                for x in filename:
                    if len(x) > 1:
                        if x[0] == "b":
                            self.t = float(x[1:])
            if self.decode_extraction is True:
                for x in filename:
                    if len(x) > 2:
                        if x[:2] == "xs":
                            self.ex_start = int(x[2:])
                        if x[:2] == "xe":
                            self.ex_end = int(x[2:])

            if self.animal_number is None:
                if self.use_detector is True:
                    self.animal_number = {}
                    for animal_name in self.animal_kinds:
                        self.animal_number[animal_name] = 1
                else:
                    self.animal_number = 1

            if self.use_detector is False:
                AA = AnalyzeAnimal()
                AA.prepare_analysis(
                    video,
                    self.result_path,
                    self.animal_number,
                    delta=self.delta,
                    framewidth=self.framewidth,
                    stable_illumination=self.stable_illumination,
                    channel=3,
                    include_bodyparts=self.include_bodyparts,
                    std=self.std,
                    categorize_behavior=False,
                    animation_analyzer=False,
                    path_background=self.background_path,
                    autofind_t=self.autofind_t,
                    t=self.t,
                    duration=self.duration,
                    ex_start=self.ex_start,
                    ex_end=self.ex_end,
                    length=self.length,
                    animal_vs_bg=self.animal_vs_bg,
                )
                if self.behavior_mode == BehaviorMode.NON_INTERACTIVE:
                    AA.generate_data(
                        background_free=self.background_free,
                        skip_redundant=self.skip_redundant,
                    )
                else:
                    AA.generate_data_interact_basic(
                        background_free=self.background_free,
                        skip_redundant=self.skip_redundant,
                    )
            else:
                AAD = AnalyzeAnimalDetector()
                AAD.prepare_analysis(
                    self.path_to_detector,
                    video,
                    self.result_path,
                    self.animal_number,
                    self.animal_kinds,
                    self.behavior_mode,
                    framewidth=self.framewidth,
                    channel=3,
                    include_bodyparts=self.include_bodyparts,
                    std=self.std,
                    categorize_behavior=False,
                    animation_analyzer=False,
                    t=self.t,
                    duration=self.duration,
                    length=self.length,
                    social_distance=self.social_distance,
                )
                if self.behavior_mode == BehaviorMode.NON_INTERACTIVE:
                    AAD.generate_data(
                        background_free=self.background_free,
                        skip_redundant=self.skip_redundant,
                    )
                elif self.behavior_mode == BehaviorMode.INTERACT_BASIC:
                    AAD.generate_data_interact_basic(
                        background_free=self.background_free,
                        skip_redundant=self.skip_redundant,
                    )
                else:
                    AAD.generate_data_interact_advance(
                        background_free=self.background_free,
                        skip_redundant=self.skip_redundant,
                    )


class SortBehaviorExamples(LabGymWindow):
    """Sort pattern images and animations."""

    def __init__(self):
        super().__init__(title="Sort Behavior Examples", size=(1000, 240))
        self.input_path = None
        self.result_path = None
        self.keys_behaviors = {}
        self.keys_behaviorpaths = {}

        self.text_inputfolder = self.module_text("None.")
        self.add_module(
            "Select the folder that stores\nunsorted behavior examples",
            self.input_folder,
            'Select a folder that stores the behavior examples generated by "Generate Behavior Examples" functional unit. All examples in this folder should be in pairs (animation + pattern image).',
            self.text_inputfolder,
        )

        self.text_outputfolder = self.module_text("None.")
        self.add_module(
            "Select the folder to store\nthe sorted behavior examples",
            self.output_folder,
            "A subfolder will be created for each behavior type under the behavior name.",
            self.text_outputfolder,
        )

        self.text_keynames = self.module_text("None.")
        self.add_module(
            "Enter a single character shortcut key and\nthe corresponding behavior name",
            self.input_keys,
            'Format: "shortcutkey-behaviorname". "o", "p", "q", and "u" are reserved for "Previous", "Next", "Quit", and "Undo". When hit a shortcut key, the behavior example pair will be moved to the folder named after the corresponding behavior name.',
            self.text_keynames,
        )

        self.add_submit_button(
            "Sort behavior examples",
            self.sort_behaviors,
            "You will see each example pair in the screen one by one and can use shortcut keys to sort them into folders of the behavior types.",
        )

        self.display_window()

    def input_folder(self, event):
        """Select folder with unsorted behavior examples."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.input_path = dialog.GetPath()
            self.text_inputfolder.SetLabel(
                f"Unsorted behavior examples are in: f{self.input_path}."
            )
        dialog.Destroy()

    def output_folder(self, event):
        """Select folder to store sorted behavior examples."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                f"Sorted behavior examples will be in: {self.result_path}."
            )
        dialog.Destroy()

    def parse_key_behavior_pairs(self, key_behavior_pairs: str):
        """Parse a keyboard shortcut behavior string into a dictionary.

        Each key should be associated with a behavior name in the format

            key-behavior, key-behavior, key-behavior...

        where key is a single character corresponding to a key on the keyboard
        and behavior is a string describing the behavior name. The keys 'o',
        'p', 'u', and 'q' (case-insensitive) are reserved for the 'previous',
        'next', 'quit', and 'undo' operations respectively.

        Args:
            key_behavior_pairs: The user-submitted key-behavior pair string.

        Returns:
            None. The shortcuts are stored in the self.keys_behaviors
            attribute.

        Raises:
            ValueError: There was an issue parsing the input string.
        """
        self.keys_behaviors = {}
        RESERVED_KEYS = ["o", "p", "u", "q"]
        for pair in key_behavior_pairs.split(","):
            pair = pair.strip()

            if len(pair.split("-")) != 2:
                raise ValueError(f"Invalid key-behavior pair '{pair}'.")

            key = pair.split("-")[0]
            behavior_name = pair.split("-")[1]

            if len(key) != 1:
                raise ValueError(
                    f"Invalid key '{key}'. Key must be a single character."
                )

            if key.lower() in RESERVED_KEYS:
                raise ValueError(
                    f"Key '{key}' is reserved. Please use a different key."
                )

            self.keys_behaviors[key] = behavior_name

    def input_keys(self, event):
        """Enter keyboard shortcuts to automate sorting."""
        while True:
            dialog = wx.TextEntryDialog(
                self,
                'Enter key-behaviorname pairs separated by ",".',
                "Format: key1-name1,key2-name2,...",
                value="",
            )
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                break
            else:
                key_behavior_pairs = dialog.GetValue()
                dialog.Destroy()

            try:
                self.parse_key_behavior_pairs(key_behavior_pairs)
            except ValueError as err:
                wx.MessageBox(
                    str(err),
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                continue

            self.text_keynames.SetLabel(
                f"The key-behaviorname pairs: {key_behavior_pairs}."
            )
            break

    def sort_behaviors(self, event):
        """Sort behavior examples."""
        if (
            self.input_path is None
            or self.result_path is None
            or not self.keys_behaviors
        ):
            wx.MessageBox(
                "No input / output folder or shortcut key - behavior name pair specified.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        # Create folders to sort behavior examples into
        for key in self.keys_behaviors:
            behavior_path = os.path.join(self.result_path, self.keys_behaviors[key])
            self.keys_behaviorpaths[key] = behavior_path
            os.makedirs(behavior_path, exist_ok=True)

        cv2.namedWindow("Sorting Behavior Examples", cv2.WINDOW_NORMAL)
        actions = []
        index = 0
        stop = False
        moved = False
        only_image = False

        # Check for whether using animations or only pattern images
        check_animations = [
            i for i in os.listdir(self.input_path) if i.endswith(".avi")
        ]
        if len(check_animations) == 0:
            check_images = [
                i for i in os.listdir(self.input_path) if i.endswith(".jpg")
            ]
            if len(check_images) == 0:
                wx.MessageBox("No examples!", "Error", wx.OK | wx.ICON_ERROR)
                stop = True
            else:
                only_image = True

        while stop is False:
            if moved is True:
                moved = False
                if only_image is False:
                    shutil.move(
                        os.path.join(self.input_path, example_name + ".avi"),
                        os.path.join(
                            self.keys_behaviorpaths[shortcutkey],
                            example_name + ".avi",
                        ),
                    )
                shutil.move(
                    os.path.join(self.input_path, example_name + ".jpg"),
                    os.path.join(
                        self.keys_behaviorpaths[shortcutkey], example_name + ".jpg"
                    ),
                )

            # Check for remaining animations/pattern images
            if only_image is False:
                animations = [
                    i for i in os.listdir(self.input_path) if i.endswith(".avi")
                ]
                animations = sorted(
                    animations,
                    key=lambda name: int(name.split("_len")[0].split("_")[-1]),
                )
            else:
                animations = [
                    i for i in os.listdir(self.input_path) if i.endswith(".jpg")
                ]

            if not (0 <= index < len(animations)):
                if len(animations) == 0:
                    wx.MessageBox(
                        "Behavior example sorting completed!",
                        "Completed!",
                        wx.OK | wx.ICON_INFORMATION,
                    )
                    stop = True
                else:
                    wx.MessageBox(
                        "This is the last behavior example!",
                        "To the end.",
                        wx.OK | wx.ICON_INFORMATION,
                    )
                    index = 0
                continue

            # Load the pattern image and animation
            example_name = animations[index].split(".")[0]
            pattern_image = cv2.resize(
                cv2.imread(os.path.join(self.input_path, example_name + ".jpg")),
                (600, 600),
                interpolation=cv2.INTER_AREA,
            )

            if only_image is False:
                frame_count = example_name.split("_len")[0].split("_")[-1]
                animation = cv2.VideoCapture(
                    os.path.join(self.input_path, example_name + ".avi")
                )
                fps = round(animation.get(cv2.CAP_PROP_FPS))
                frame_count = int(animation.get(cv2.CAP_PROP_FRAME_COUNT))

            # This loop is for repeatedly displaying the animation frames
            while True:
                # Create the image preview
                if only_image is False:
                    ret, frame = animation.read()
                    if not ret:
                        animation.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    frame = cv2.resize(frame, (600, 600), interpolation=cv2.INTER_AREA)
                    combined = np.hstack((frame, pattern_image))
                    cv2.putText(
                        combined,
                        f"frame count: {frame_count}",
                        (10, 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                    x_begin = 550
                else:
                    combined = pattern_image
                    x_begin = 5

                # Add keyboard shortcut overlay
                n = 1
                for i in ["o: Prev", "p: Next", "q: Quit", "u: Undo"]:
                    cv2.putText(
                        combined,
                        i,
                        (x_begin, 15 * n),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                    n += 1
                n += 1
                for i in self.keys_behaviors:
                    cv2.putText(
                        combined,
                        i + ": " + self.keys_behaviors[i],
                        (x_begin, 15 * n),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                    n += 1

                cv2.imshow("Sorting Behavior Examples", combined)
                cv2.moveWindow("Sorting Behavior Examples", 50, 0)

                if only_image is False:
                    key = cv2.waitKey(int(1000 / fps)) & 0xFF
                else:
                    key = cv2.waitKey(1) & 0xFF

                for shortcutkey in self.keys_behaviorpaths:
                    if key == ord(shortcutkey):
                        example_name = animations[index].split(".")[0]
                        actions.append([shortcutkey, example_name])
                        moved = True
                        break
                if moved is True:
                    break

                if key == ord("u"):
                    if len(actions) == 0:
                        wx.MessageBox(
                            "Nothing to undo.", "Error", wx.OK | wx.ICON_ERROR
                        )
                        continue

                    shortcutkey, example_name = actions.pop()
                    if only_image is False:
                        shutil.move(
                            os.path.join(
                                self.keys_behaviorpaths[shortcutkey],
                                example_name + ".avi",
                            ),
                            os.path.join(self.input_path, example_name + ".avi"),
                        )
                    shutil.move(
                        os.path.join(
                            self.keys_behaviorpaths[shortcutkey],
                            example_name + ".jpg",
                        ),
                        os.path.join(self.input_path, example_name + ".jpg"),
                    )
                    break

                if key == ord("p"):
                    index += 1
                    break

                if key == ord("o"):
                    if index > 0:
                        index -= 1
                    break

                if key == ord("q"):
                    stop = True
                    break

            if only_image is False:
                animation.release()

        cv2.destroyAllWindows()
