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

import cv2
import numpy as np
import wx

from ..utils import LabGymWindow
from ...analyzebehaviors import AnalyzeAnimal
from ...analyzebehaviorsdetector import AnalyzeAnimalDetector
from ...tools import AnimalVsBg


THE_ABSOLUTE_CURRENT_PATH = str(Path(__file__).resolve().parent.parent)


class BehaviorMode:
    NON_INTERACTIVE = 0
    INTERACT_BASIC = 1
    INTERACT_ADVANCED = 2
    STATIC_IMAGES = 3


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
        if self.behavior_mode >= 3:
            wildcard = "Image files(*.jpg;*.jpeg;*.png;*.tiff;*.bmp)|*.jpg;*.JPG;*.jpeg;*.JPEG;*.png;*.PNG;*.tiff;*.TIFF;*.bmp;*.BMP"
        else:
            wildcard = "Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov"

        dialog = wx.FileDialog(
            self, "Select video(s) / image(s)", "", "", wildcard, style=wx.FD_MULTIPLE
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_videos = dialog.GetPaths()
            self.path_to_videos.sort()
            path = os.path.dirname(self.path_to_videos[0])
            dialog1 = wx.MessageDialog(
                self,
                'Proportional resize the video frames / images?\nSelect "No" if dont know what it is.',
                "(Optional) resize the frames / images?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog1.ShowModal() == wx.ID_YES:
                dialog2 = wx.NumberEntryDialog(
                    self,
                    "Enter the desired frame / image width",
                    "The unit is pixel:",
                    "Desired frame / image width",
                    480,
                    1,
                    10000,
                )
                if dialog2.ShowModal() == wx.ID_OK:
                    self.framewidth = int(dialog2.GetValue())
                    if self.framewidth < 10:
                        self.framewidth = 10
                    self.text_inputvideos.SetLabel(
                        "Selected "
                        + str(len(self.path_to_videos))
                        + " file(s) in: "
                        + path
                        + " (proportionally resize frame / image width to "
                        + str(self.framewidth)
                        + ")."
                    )
                else:
                    self.framewidth = None
                    self.text_inputvideos.SetLabel(
                        "Selected "
                        + str(len(self.path_to_videos))
                        + " file(s) in: "
                        + path
                        + " (original frame / image size)."
                    )
                dialog2.Destroy()
            else:
                self.framewidth = None
                self.text_inputvideos.SetLabel(
                    "Selected "
                    + str(len(self.path_to_videos))
                    + " file(s) in: "
                    + path
                    + " (original frame / image size)."
                )
            dialog1.Destroy()

        dialog.Destroy()

    def select_outpath(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                "Generate behavior examples in: " + self.result_path + "."
            )
        dialog.Destroy()

    def select_method(self, event):
        if self.behavior_mode <= 1:
            methods = [
                "Subtract background (fast but requires static background & stable illumination)",
                "Use trained Detectors (versatile but slow)",
            ]
        else:
            methods = ["Use trained Detectors (versatile but slow)"]

        dialog = wx.SingleChoiceDialog(
            self,
            message="How to detect the animals?",
            caption="Detection methods",
            choices=methods,
        )
        if dialog.ShowModal() == wx.ID_OK:
            method = dialog.GetStringSelection()

            if (
                method
                == "Subtract background (fast but requires static background & stable illumination)"
            ):
                self.use_detector = False

                contrasts = [
                    "Animal brighter than background",
                    "Animal darker than background",
                    "Hard to tell",
                ]
                dialog1 = wx.SingleChoiceDialog(
                    self,
                    message="Select the scenario that fits your videos best",
                    caption="Which fits best?",
                    choices=contrasts,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    contrast = dialog1.GetStringSelection()
                    if contrast == "Animal brighter than background":
                        self.animal_vs_bg = 0
                    elif contrast == "Animal darker than background":
                        self.animal_vs_bg = 1
                    else:
                        self.animal_vs_bg = 2
                    dialog2 = wx.MessageDialog(
                        self,
                        'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
                        "(Optional) load existing background?",
                        wx.YES_NO | wx.ICON_QUESTION,
                    )
                    if dialog2.ShowModal() == wx.ID_YES:
                        dialog3 = wx.DirDialog(
                            self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
                        )
                        if dialog3.ShowModal() == wx.ID_OK:
                            self.background_path = dialog3.GetPath()
                        dialog3.Destroy()
                    else:
                        self.background_path = None
                        if self.animal_vs_bg != 2:
                            dialog3 = wx.MessageDialog(
                                self,
                                'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
                                "(Optional) unstable illumination?",
                                wx.YES_NO | wx.ICON_QUESTION,
                            )
                            if dialog3.ShowModal() == wx.ID_YES:
                                self.stable_illumination = False
                            else:
                                self.stable_illumination = True
                            dialog3.Destroy()
                    dialog2.Destroy()
                    if self.background_path is None:
                        ex_methods = [
                            "Use the entire duration (default but NOT recommended)",
                            'Decode from filenames: "_xst_" and "_xet_"',
                            "Enter two time points",
                        ]
                        dialog2 = wx.SingleChoiceDialog(
                            self,
                            message="Specify the time window for background extraction",
                            caption="Time window for background extraction",
                            choices=ex_methods,
                        )
                        if dialog2.ShowModal() == wx.ID_OK:
                            ex_method = dialog2.GetStringSelection()
                            if (
                                ex_method
                                == "Use the entire duration (default but NOT recommended)"
                            ):
                                self.decode_extraction = False
                                if self.animal_vs_bg == 0:
                                    self.text_detection.SetLabel(
                                        "Background subtraction: animal brighter, using the entire duration."
                                    )
                                elif self.animal_vs_bg == 1:
                                    self.text_detection.SetLabel(
                                        "Background subtraction: animal darker, using the entire duration."
                                    )
                                else:
                                    self.text_detection.SetLabel(
                                        "Background subtraction: animal partially brighter/darker, using the entire duration."
                                    )
                            elif (
                                ex_method
                                == 'Decode from filenames: "_xst_" and "_xet_"'
                            ):
                                self.decode_extraction = True
                                if self.animal_vs_bg == 0:
                                    self.text_detection.SetLabel(
                                        'Background subtraction: animal brighter, using time window decoded from filenames "_xst_" and "_xet_".'
                                    )
                                elif self.animal_vs_bg == 1:
                                    self.text_detection.SetLabel(
                                        'Background subtraction: animal darker, using time window decoded from filenames "_xst_" and "_xet_".'
                                    )
                                else:
                                    self.text_detection.SetLabel(
                                        'Background subtraction: animal partially brighter/darker, using time window decoded from filenames "_xst_" and "_xet_".'
                                    )
                            else:
                                self.decode_extraction = False
                                dialog3 = wx.NumberEntryDialog(
                                    self,
                                    "Enter the start time",
                                    "The unit is second:",
                                    "Start time for background extraction",
                                    0,
                                    0,
                                    100000000000000,
                                )
                                if dialog3.ShowModal() == wx.ID_OK:
                                    self.ex_start = int(dialog3.GetValue())
                                dialog3.Destroy()
                                dialog3 = wx.NumberEntryDialog(
                                    self,
                                    "Enter the end time",
                                    "The unit is second:",
                                    "End time for background extraction",
                                    0,
                                    0,
                                    100000000000000,
                                )
                                if dialog3.ShowModal() == wx.ID_OK:
                                    self.ex_end = int(dialog3.GetValue())
                                    if self.ex_end == 0:
                                        self.ex_end = None
                                dialog3.Destroy()
                                if self.animal_vs_bg == 0:
                                    if self.ex_end is None:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal brighter, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to the end."
                                        )
                                    else:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal brighter, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to "
                                            + str(self.ex_end)
                                            + "."
                                        )
                                elif self.animal_vs_bg == 1:
                                    if self.ex_end is None:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal darker, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to the end."
                                        )
                                    else:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal darker, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to "
                                            + str(self.ex_end)
                                            + "."
                                        )
                                else:
                                    if self.ex_end is None:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal partially brighter/darker, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to the end."
                                        )
                                    else:
                                        self.text_detection.SetLabel(
                                            "Background subtraction: animal partially brighter/darker, using time window (in seconds) from "
                                            + str(self.ex_start)
                                            + " to "
                                            + str(self.ex_end)
                                            + "."
                                        )
                        dialog2.Destroy()
                dialog1.Destroy()

            else:
                self.use_detector = True
                self.animal_number = {}
                self.detector_path = os.path.join(
                    THE_ABSOLUTE_CURRENT_PATH, "detectors"
                )

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
                if "Choose a new directory of the Detector" not in detectors:
                    detectors.append("Choose a new directory of the Detector")

                dialog1 = wx.SingleChoiceDialog(
                    self,
                    message="Select a Detector for animal detection",
                    caption="Select a Detector",
                    choices=detectors,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    detector = dialog1.GetStringSelection()
                    if detector == "Choose a new directory of the Detector":
                        dialog2 = wx.DirDialog(
                            self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
                        )
                        if dialog2.ShowModal() == wx.ID_OK:
                            self.path_to_detector = dialog2.GetPaths()
                        dialog2.Destroy()
                    else:
                        self.path_to_detector = os.path.join(
                            self.detector_path, detector
                        )
                    with open(
                        os.path.join(self.path_to_detector, "model_parameters.txt")
                    ) as f:
                        model_parameters = f.read()
                    animal_names = json.loads(model_parameters)["animal_names"]
                    if len(animal_names) > 1:
                        dialog2 = wx.MultiChoiceDialog(
                            self,
                            message="Specify which animals/objects involved in behavior examples",
                            caption="Animal/Object kind",
                            choices=animal_names,
                        )
                        if dialog2.ShowModal() == wx.ID_OK:
                            self.animal_kinds = [
                                animal_names[i] for i in dialog2.GetSelections()
                            ]
                        else:
                            self.animal_kinds = animal_names
                        dialog2.Destroy()
                    else:
                        self.animal_kinds = animal_names
                    if self.behavior_mode >= 3:
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
                            "Detector: "
                            + detector
                            + " (detection threshold: "
                            + str(detection_threshold)
                            + "%); The animals/objects: "
                            + str(self.animal_kinds)
                            + "."
                        )
                        dialog2.Destroy()
                    else:
                        for animal_name in self.animal_kinds:
                            self.animal_number[animal_name] = 1
                        self.text_animalnumber.SetLabel(
                            "The number of "
                            + str(self.animal_kinds)
                            + " is: "
                            + str(list(self.animal_number.values()))
                            + "."
                        )
                        self.text_detection.SetLabel(
                            "Detector: "
                            + detector
                            + "; "
                            + "The animals/objects: "
                            + str(self.animal_kinds)
                            + "."
                        )
                dialog1.Destroy()

        dialog.Destroy()

    def specify_timing(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
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

            if self.delta == 1.2 and self.use_detector is False:
                methods = [
                    "Automatic (for light on and off)",
                    'Decode from filenames: "_bt_"',
                    "Enter a time point",
                ]
            else:
                methods = ['Decode from filenames: "_bt_"', "Enter a time point"]

            dialog = wx.SingleChoiceDialog(
                self,
                message="Specify beginning time to generate behavior examples",
                caption="Beginning time for generator",
                choices=methods,
            )
            if dialog.ShowModal() == wx.ID_OK:
                method = dialog.GetStringSelection()
                if method == "Automatic (for light on and off)":
                    self.autofind_t = True
                    self.decode_t = False
                    self.text_startgenerate.SetLabel(
                        "Automatically find the onset of the 1st time when light on / off as the beginning time."
                    )
                elif method == 'Decode from filenames: "_bt_"':
                    self.autofind_t = False
                    self.decode_t = True
                    self.text_startgenerate.SetLabel(
                        'Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".'
                    )
                else:
                    self.autofind_t = False
                    self.decode_t = False
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
                        self.t = float(dialog2.GetValue())
                        if self.t < 0:
                            self.t = 0
                        self.text_startgenerate.SetLabel(
                            "Start to generate behavior examples at the: "
                            + str(self.t)
                            + " second."
                        )
                    dialog2.Destroy()
            dialog.Destroy()

    def input_duration(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                "No need to specify this since the selected behavior mode is 'Static images'.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
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
                        "The generation of behavior examples lasts for "
                        + str(self.duration)
                        + " seconds."
                    )
                else:
                    self.text_duration.SetLabel(
                        "The generation of behavior examples lasts for the entire duration of a video."
                    )
            dialog.Destroy()

    def specify_animalnumber(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            methods = ['Decode from filenames: "_nn_"', "Enter the number of animals"]

            dialog = wx.SingleChoiceDialog(
                self,
                message="Specify the number of animals in a video",
                caption="The number of animals in a video",
                choices=methods,
            )
            if dialog.ShowModal() == wx.ID_OK:
                method = dialog.GetStringSelection()
                if method == "Enter the number of animals":
                    self.decode_animalnumber = False
                    if self.use_detector is True:
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
                                self.animal_number[animal_name] = int(
                                    dialog1.GetValue()
                                )
                            else:
                                self.animal_number[animal_name] = 1
                            dialog1.Destroy()
                        self.text_animalnumber.SetLabel(
                            "The number of "
                            + str(self.animal_kinds)
                            + " is: "
                            + str(list(self.animal_number.values()))
                            + "."
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
                            "The total number of animals in a video is "
                            + str(self.animal_number)
                            + "."
                        )
                        dialog1.Destroy()
                else:
                    self.decode_animalnumber = True
                    self.text_animalnumber.SetLabel(
                        'Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.'
                    )
            dialog.Destroy()

    def input_length(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
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
                self.length = int(dialog.GetValue())
                if self.length < 3:
                    self.length = 3
                self.text_length.SetLabel(
                    "The duration of a behavior example is: "
                    + str(self.length)
                    + " frames."
                )
            dialog.Destroy()

    def specify_redundant(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
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
                    "Generate a pair of example every "
                    + str(self.skip_redundant)
                    + " frames."
                )
            else:
                self.skip_redundant = 1
                self.text_skipredundant.SetLabel(
                    "Generate a pair of example at every frame."
                )
            dialog.Destroy()

    def generate_data(self, event):
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
                'Include background in animations? Select "No"\nif background is behavior irrelevant.',
                "Including background?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog.ShowModal() == wx.ID_YES:
                self.background_free = False
            else:
                self.background_free = True
            dialog.Destroy()

            if self.behavior_mode >= 3:
                if self.path_to_detector is None:
                    wx.MessageBox(
                        "You need to select a Detector.", "Error", wx.OK | wx.ICON_ERROR
                    )
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

            else:
                dialog = wx.MessageDialog(
                    self,
                    'Include body parts in pattern images?\nSelect "No" if limb movement is neglectable.',
                    "Including body parts?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
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
                else:
                    self.include_bodyparts = False
                dialog.Destroy()

                dialog = wx.MessageDialog(
                    self,
                    "Start to generate behavior examples?",
                    "Start to generate examples?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if dialog.ShowModal() == wx.ID_YES:
                    do_nothing = False
                else:
                    do_nothing = True
                dialog.Destroy()

                if do_nothing is False:
                    for i in self.path_to_videos:
                        filename = os.path.splitext(os.path.basename(i))[0].split("_")
                        if self.decode_animalnumber is True:
                            if self.use_detector is True:
                                self.animal_number = {}
                                number = [
                                    x[1:]
                                    for x in filename
                                    if len(x) > 1 and x[0] == "n"
                                ]
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
                                i,
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
                            if self.behavior_mode == 0:
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
                                i,
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
                            if self.behavior_mode == 0:
                                AAD.generate_data(
                                    background_free=self.background_free,
                                    skip_redundant=self.skip_redundant,
                                )
                            elif self.behavior_mode == 1:
                                AAD.generate_data_interact_basic(
                                    background_free=self.background_free,
                                    skip_redundant=self.skip_redundant,
                                )
                            else:
                                AAD.generate_data_interact_advance(
                                    background_free=self.background_free,
                                    skip_redundant=self.skip_redundant,
                                )


class SortBehaviorExamples(wx.Frame):
    def __init__(self):
        super(SortBehaviorExamples, self).__init__(
            parent=None, title="Sort Behavior Examples", size=(1000, 240)
        )
        self.input_path = None
        self.result_path = None
        self.keys_behaviors = {}
        self.keys_behaviorpaths = {}

        self.display_window()

    def display_window(self):
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        module_inputfolder = wx.BoxSizer(wx.HORIZONTAL)
        button_inputfolder = wx.Button(
            panel,
            label="Select the folder that stores\nunsorted behavior examples",
            size=(300, 40),
        )
        button_inputfolder.Bind(wx.EVT_BUTTON, self.input_folder)
        wx.Button.SetToolTip(
            button_inputfolder,
            'Select a folder that stores the behavior examples generated by "Generate Behavior Examples" functional unit. All examples in this folder should be in pairs (animation + pattern image).',
        )
        self.text_inputfolder = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_inputfolder.Add(
            button_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_inputfolder.Add(
            self.text_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(0, 10, 0)
        boxsizer.Add(module_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_outputfolder = wx.BoxSizer(wx.HORIZONTAL)
        button_outputfolder = wx.Button(
            panel,
            label="Select the folder to store\nthe sorted behavior examples",
            size=(300, 40),
        )
        button_outputfolder.Bind(wx.EVT_BUTTON, self.output_folder)
        wx.Button.SetToolTip(
            button_outputfolder,
            "A subfolder will be created for each behavior type under the behavior name.",
        )
        self.text_outputfolder = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_outputfolder.Add(
            button_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_outputfolder.Add(
            self.text_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_keynames = wx.BoxSizer(wx.HORIZONTAL)
        button_keynames = wx.Button(
            panel,
            label="Enter a single character shortcut key and\nthe corresponding behavior name",
            size=(300, 40),
        )
        button_keynames.Bind(wx.EVT_BUTTON, self.input_keys)
        wx.Button.SetToolTip(
            button_keynames,
            'Format: "shortcutkey-behaviorname". "o", "p", "q", and "u" are reserved for "Previous", "Next", "Quit", and "Undo". When hit a shortcut key, the behavior example pair will be moved to the folder named after the corresponding behavior name.',
        )
        self.text_keynames = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_keynames.Add(button_keynames, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module_keynames.Add(self.text_keynames, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(module_keynames, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        button_sort = wx.Button(panel, label="Sort behavior examples", size=(300, 40))
        button_sort.Bind(wx.EVT_BUTTON, self.sort_behaviors)
        wx.Button.SetToolTip(
            button_sort,
            "You will see each example pair in the screen one by one and can use shortcut keys to sort them into folders of the behavior types.",
        )
        boxsizer.Add(0, 5, 0)
        boxsizer.Add(button_sort, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        boxsizer.Add(0, 10, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def input_folder(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.input_path = dialog.GetPath()
            self.text_inputfolder.SetLabel(
                "Unsorted behavior examples are in: " + self.input_path + "."
            )
        dialog.Destroy()

    def output_folder(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                "Sorted behavior examples will be in: " + self.result_path + "."
            )
        dialog.Destroy()

    def input_keys(self, event):
        keynamepairs = ""
        stop = False

        while stop is False:
            dialog = wx.TextEntryDialog(
                self,
                'Enter key-behaviorname pairs separated by ",".',
                "Format: key1-name1,key2-name2,...",
                value=keynamepairs,
            )
            if dialog.ShowModal() == wx.ID_OK:
                keynamepairs = dialog.GetValue()
                try:
                    for pair in keynamepairs.split(","):
                        key = pair.split("-")[0]
                        name = pair.split("-")[1]
                        if len(key) > 1:
                            wx.MessageBox(
                                "Key must be a single character.",
                                "Error",
                                wx.OK | wx.ICON_ERROR,
                            )
                            break
                        if key in ["O", "o", "P", "p", "U", "u", "Q", "q"]:
                            wx.MessageBox(
                                "The " + key + " is reserved. Please use another key.",
                                "Error",
                                wx.OK | wx.ICON_ERROR,
                            )
                            break
                        else:
                            self.keys_behaviors[key] = name
                    self.text_keynames.SetLabel(
                        "The key-behaviorname pairs: " + keynamepairs + "."
                    )
                    stop = True
                except:
                    wx.MessageBox(
                        "Please follow the correct format: key1-name1,key2-name2,....",
                        "Error",
                        wx.OK | wx.ICON_ERROR,
                    )
            else:
                stop = True
        dialog.Destroy()

    def sort_behaviors(self, event):
        if (
            self.input_path is None
            or self.result_path is None
            or len(self.keys_behaviors.items()) == 0
        ):
            wx.MessageBox(
                "No input / output folder or shortcut key - behavior name pair specified.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
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

                if len(animations) > 0 and index < len(animations):
                    example_name = animations[index].split(".")[0]
                    pattern_image = cv2.resize(
                        cv2.imread(
                            os.path.join(self.input_path, example_name + ".jpg")
                        ),
                        (600, 600),
                        interpolation=cv2.INTER_AREA,
                    )

                    if only_image is False:
                        frame_count = example_name.split("_len")[0].split("_")[-1]
                        animation = cv2.VideoCapture(
                            os.path.join(self.input_path, example_name + ".avi")
                        )
                        fps = round(animation.get(cv2.CAP_PROP_FPS))

                    while True:
                        if only_image is False:
                            ret, frame = animation.read()
                            if not ret:
                                animation.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                continue
                            frame = cv2.resize(
                                frame, (600, 600), interpolation=cv2.INTER_AREA
                            )
                            combined = np.hstack((frame, pattern_image))
                            cv2.putText(
                                combined,
                                "frame count: " + frame_count,
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
                            if len(actions) > 0:
                                last = actions.pop()
                                shortcutkey = last[0]
                                example_name = last[1]
                                if only_image is False:
                                    shutil.move(
                                        os.path.join(
                                            self.keys_behaviorpaths[shortcutkey],
                                            example_name + ".avi",
                                        ),
                                        os.path.join(
                                            self.input_path, example_name + ".avi"
                                        ),
                                    )
                                shutil.move(
                                    os.path.join(
                                        self.keys_behaviorpaths[shortcutkey],
                                        example_name + ".jpg",
                                    ),
                                    os.path.join(
                                        self.input_path, example_name + ".jpg"
                                    ),
                                )
                                break
                            else:
                                wx.MessageBox(
                                    "Nothing to undo.", "Error", wx.OK | wx.ICON_ERROR
                                )
                                continue

                        if key == ord("p"):
                            index += 1
                            break

                        if key == ord("o"):
                            if index >= 1:
                                index -= 1
                            break

                        if key == ord("q"):
                            stop = True
                            break

                    if only_image is False:
                        animation.release()

                else:
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

            cv2.destroyAllWindows()
