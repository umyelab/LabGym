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
from pathlib import Path

import matplotlib as mpl
import pandas as pd
import torch
import wx

from LabGym.analyzebehaviors import AnalyzeAnimal
from LabGym.analyzebehaviorsdetector import AnalyzeAnimalDetector
from LabGym.tools import plot_evnets
from ..utils import WX_VIDEO_WILDCARD, WX_IMAGE_WILDCARD, LabGymWindow

the_absolute_current_path = str(Path(__file__).resolve().parent.parent.parent)


class ColorPicker(wx.Dialog):
    def __init__(self, parent, title, name_and_color):
        super(ColorPicker, self).__init__(parent=None, title=title, size=(200, 200))

        self.name_and_color = name_and_color
        name = self.name_and_color[0]
        hex_color = self.name_and_color[1][1].lstrip("#")
        color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        boxsizer = wx.BoxSizer(wx.VERTICAL)

        self.color_picker = wx.ColourPickerCtrl(self, colour=color)

        button = wx.Button(self, wx.ID_OK, label="Apply")

        boxsizer.Add(0, 10, 0)
        boxsizer.Add(self.color_picker, 0, wx.ALL | wx.CENTER, 10)
        boxsizer.Add(button, 0, wx.ALL | wx.CENTER, 10)
        boxsizer.Add(0, 10, 0)

        self.SetSizer(boxsizer)


class AnalyzeBehaviors(LabGymWindow):
    def __init__(self):
        super().__init__(title="Analyze Behaviors", size=(1000, 600))
        self.behavior_mode = 0
        self.use_detector = False
        self.detector_path = None
        self.path_to_detector = None
        self.detector_batch = 1
        self.detection_threshold = 0
        self.animal_kinds = []
        self.background_path = (
            None  # if not None, will load background images from path
        )
        self.model_path = None  # the parent path of the Categorizers
        self.path_to_categorizer = None
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
        self.behaviornames_and_colors = {}
        self.dim_tconv = 8
        self.dim_conv = 8
        self.channel = 1
        self.length = 15
        self.animal_vs_bg = 0  # 0: animals birghter than the background; 1: animals darker than the background; 2: hard to tell
        self.stable_illumination = True
        self.animation_analyzer = True
        self.animal_to_include = []
        self.behavior_to_include = ["all"]  # behaviors for annotation and analyze
        self.parameter_to_analyze = []
        self.include_bodyparts = False
        self.std = 0
        self.uncertain = 0
        self.show_legend = True
        self.background_free = True
        self.normalize_distance = True  # whether to normalize the distance (in pixel) to the animal contour area
        self.social_distance = 0
        self.specific_behaviors = {}
        self.correct_ID = False

        self.dispaly_window()

    def dispaly_window(self):
        self.text_selectcategorizer = self.module_text(
            "Default: no behavior classification, just track animals and quantify motion kinematcis."
        )
        self.add_module(
            button_label="Select a Categorizer for\nbehavior classification",
            button_handler=self.select_categorizer,
            tool_tip="The fps of the videos to analyze should match that of the selected Categorizer. Uncertain level determines the threshold for the Categorizer to output an ‘NA’ for behavioral classification. See Extended Guide for details.",
            text=self.text_selectcategorizer,
        )

        self.text_inputvideos = self.module_text("None.")
        self.add_module(
            button_label="Select the video(s) / image(s)\nfor behavior analysis",
            button_handler=self.select_videos,
            tool_tip='Select one or more videos / images for a behavior analysis batch. If analyzing videos, one analysis batch will yield one raster plot showing the behavior events of all the animals in all selected videos. For "Static images" mode, each annotated images will be in this folder. See Extended Guide for details.',
            text=self.text_inputvideos,
        )

        self.text_outputfolder = self.module_text("None.")
        self.add_module(
            button_label="Select a folder to store\nthe analysis results",
            button_handler=self.select_outpath,
            tool_tip='If analyzing videos, will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video and stores the detailed analysis results for this video. For "Static images" mode, all results will be in this folder. See Extended Guide for details.',
            text=self.text_outputfolder,
        )

        self.text_detection = self.module_text(
            "Default: Background subtraction-based method."
        )
        self.add_module(
            button_label="Specify the method to\ndetect animals or objects",
            button_handler=self.select_method,
            tool_tip="Background subtraction-based method is accurate and fast but requires static background and stable illumination in videos; Detectors-based method is accurate and versatile in any recording settings but is slow. See Extended Guide for details.",
            text=self.text_detection,
        )

        self.text_startanalyze = self.module_text(
            "Default: at the beginning of the video(s)."
        )
        self.add_module(
            button_label="Specify when the analysis\nshould begin (unit: second)",
            button_handler=self.specify_timing,
            tool_tip='Enter a beginning time point for all videos in one analysis batch or use "Decode from filenames" to let LabGym decode the different beginning time for different videos. See Extended Guide for details.',
            text=self.text_startanalyze,
        )

        self.text_duration = self.module_text(
            "Default: from the specified start time to the end of a video"
        )
        self.add_module(
            button_label="Specify the analysis duration\n(unit: second)",
            button_handler=self.input_duration,
            tool_tip="The duration is the same for all the videos in a same analysis batch.",
            text=self.text_duration,
        )

        self.text_animalnumber = self.module_text("Default: 1.")
        self.add_module(
            button_label="Specify the number of animals\nin a video",
            button_handler=self.specify_animalnumber,
            tool_tip='Enter a number for all videos in one analysis batch or use "Decode from filenames" to let LabGym decode the different animal number for different videos. See Extended Guide for details.',
            text=self.text_animalnumber,
        )

        self.text_selectbehaviors = self.module_text(
            "Default: No Categorizer selected, no behavior selected."
        )
        self.add_module(
            button_label="Select the behaviors for\nannotations and plots",
            button_handler=self.select_behaviors,
            tool_tip="The behavior categories are determined by the selected Categorizer. Select which behaviors to show in the annotated videos / images and the raster plot (only for videos). See Extended Guide for details.",
            text=self.text_selectbehaviors,
        )

        self.text_selectparameters = self.module_text("Default: None.")
        self.add_module(
            button_label="Select the quantitative measurements\nfor each behavior",
            button_handler=self.select_parameters,
            tool_tip='If select "not to normalize distances", all distances will be output in pixels. If select "normalize distances", all distances will be normalized to the animal size. See Extended Guide for details.',
            text=self.text_selectparameters,
        )

        self.add_submit_button(
            label="Start to analyze the behaviors",
            handler=self.analyze_behaviors,
            tool_tip='If analyzing videos, will output a raster plot for all behavior events in all videos, an annotated video copy for each video, various spreadsheets storing quantification results for each selected behavior parameter. For "Static images" mode, will output annotated image copies and spreadsheet storing behavior count and probability.',
        )

        self.display_window()

    def select_categorizer(self, event):
        if self.model_path is None:
            self.model_path = os.path.join(the_absolute_current_path, "models")

        categorizers = [
            i
            for i in os.listdir(self.model_path)
            if os.path.isdir(os.path.join(self.model_path, i))
        ]
        if "__pycache__" in categorizers:
            categorizers.remove("__pycache__")
        if "__init__" in categorizers:
            categorizers.remove("__init__")
        if "__init__.py" in categorizers:
            categorizers.remove("__init__.py")
        categorizers.sort()
        if (
            "No behavior classification, just track animals and quantify motion kinematics"
            not in categorizers
        ):
            categorizers.append(
                "No behavior classification, just track animals and quantify motion kinematics"
            )
        if "Choose a new directory of the Categorizer" not in categorizers:
            categorizers.append("Choose a new directory of the Categorizer")

        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Categorizer for behavior classification",
            caption="Select a Categorizer",
            choices=categorizers,
        )

        if dialog.ShowModal() == wx.ID_OK:
            categorizer = dialog.GetStringSelection()
            if categorizer == "Choose a new directory of the Categorizer":
                dialog1 = wx.DirDialog(
                    self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.path_to_categorizer = dialog1.GetPaths()
                dialog1.Destroy()
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Enter the Categorizer's uncertainty level (0~100%)",
                    "If probability difference between\n1st- and 2nd-likely behaviors\nis less than uncertainty,\nclassfication outputs an 'NA'. Enter 0 if don't know how to set.",
                    "Uncertainty level",
                    0,
                    0,
                    100,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    uncertain = dialog1.GetValue()
                    self.uncertain = uncertain / 100
                dialog1.Destroy()
                self.text_selectcategorizer.SetLabel(
                    "The path to the Categorizer is: "
                    + self.path_to_categorizer
                    + " with uncertainty of "
                    + str(uncertain)
                    + "%."
                )
            elif (
                categorizer
                == "No behavior classification, just track animals and quantify motion kinematics"
            ):
                self.path_to_categorizer = None
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Specify a time window used for measuring\nmotion kinematics of the tracked animals",
                    "Enter the number of\nframes (minimum=3):",
                    "Time window for calculating kinematics",
                    15,
                    1,
                    100000000000000,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.length = int(dialog1.GetValue())
                    if self.length < 3:
                        self.length = 3
                dialog1.Destroy()
                self.text_selectcategorizer.SetLabel(
                    "No behavior classification; the time window to measure kinematics of tracked animals is: "
                    + str(self.length)
                    + " frames."
                )
                self.text_selectbehaviors.SetLabel(
                    "No behavior classification. Just track animals and quantify motion kinematics."
                )
            else:
                self.path_to_categorizer = os.path.join(self.model_path, categorizer)
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Enter the Categorizer's uncertainty level (0~100%)",
                    "If probability difference between\n1st- and 2nd-likely behaviors\nis less than uncertainty,\nclassfication outputs an 'NA'.",
                    "Uncertainty level",
                    0,
                    0,
                    100,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    uncertain = dialog1.GetValue()
                    self.uncertain = uncertain / 100
                    self.text_selectcategorizer.SetLabel(
                        "Categorizer: "
                        + categorizer
                        + " with uncertainty of "
                        + str(uncertain)
                        + "%."
                    )
            self.text_selectbehaviors.SetLabel(
                "All the behaviors in the selected Categorizer with default colors."
            )

            if self.path_to_categorizer is not None:
                parameters = pd.read_csv(
                    os.path.join(self.path_to_categorizer, "model_parameters.txt")
                )
                complete_colors = list(mpl.colors.cnames.values())
                colors = []
                for c in complete_colors:
                    colors.append(["#ffffff", c])
                self.behaviornames_and_colors = {}

                for behavior_name in list(parameters["classnames"]):
                    index = list(parameters["classnames"]).index(behavior_name)
                    if index < len(colors):
                        self.behaviornames_and_colors[behavior_name] = colors[index]
                    else:
                        self.behaviornames_and_colors[behavior_name] = [
                            "#ffffff",
                            "#ffffff",
                        ]

                if "dim_conv" in parameters:
                    self.dim_conv = int(parameters["dim_conv"][0])
                if "dim_tconv" in parameters:
                    self.dim_tconv = int(parameters["dim_tconv"][0])
                self.channel = int(parameters["channel"][0])
                self.length = int(parameters["time_step"][0])
                if self.length < 3:
                    self.length = 3
                categorizer_type = int(parameters["network"][0])
                if categorizer_type == 2:
                    self.animation_analyzer = True
                else:
                    self.animation_analyzer = False
                if int(parameters["inner_code"][0]) == 0:
                    self.include_bodyparts = True
                else:
                    self.include_bodyparts = False
                self.std = int(parameters["std"][0])
                if int(parameters["background_free"][0]) == 0:
                    self.background_free = True
                else:
                    self.background_free = False
                if "behavior_kind" in parameters:
                    self.behavior_mode = int(parameters["behavior_kind"][0])
                else:
                    self.behavior_mode = 0
                if self.behavior_mode == 2:
                    self.social_distance = int(parameters["social_distance"][0])
                    if self.social_distance == 0:
                        self.social_distance = float("inf")
                    self.text_detection.SetLabel(
                        "Only Detector-based detection method is available for the selected Categorizer."
                    )
                if self.behavior_mode == 3:
                    self.text_detection.SetLabel(
                        "Only Detector-based detection method is available for the selected Categorizer."
                    )
                    self.text_startanalyze.SetLabel(
                        'No need to specify this since the selected behavior mode is "Static images".'
                    )
                    self.text_duration.SetLabel(
                        'No need to specify this since the selected behavior mode is "Static images".'
                    )
                    self.text_animalnumber.SetLabel(
                        'No need to specify this since the selected behavior mode is "Static images".'
                    )
                    self.text_selectparameters.SetLabel(
                        'No need to specify this since the selected behavior mode is "Static images".'
                    )

        dialog.Destroy()

    def select_videos(self, event):
        if self.behavior_mode == 3:
            wildcard = WX_IMAGE_WILDCARD
        else:
            wildcard = WX_VIDEO_WILDCARD

        dialog = wx.FileDialog(
            self, "Select video(s) / image(s)", "", "", wildcard, style=wx.FD_MULTIPLE
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_videos = dialog.GetPaths()
            self.path_to_videos.sort()
            path = os.path.dirname(self.path_to_videos[0])
            dialog1 = wx.MessageDialog(
                self,
                'Proportional resize the video frames / images? Reducing frame / image size\nis highly recommended. But select "No" if dont know what it is.',
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
                "Results will be in: " + self.result_path + "."
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
                    the_absolute_current_path, "detectors"
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
                            message="Specify which animals/objects involved in analysis",
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

                if self.behavior_mode < 3:
                    if torch.cuda.is_available():
                        dialog1 = wx.NumberEntryDialog(
                            self,
                            "Enter the batch size for faster processing",
                            "GPU is available in this device for Detectors.\nYou may use batch processing for faster speed.",
                            "Batch size",
                            0,
                            0,
                            500,
                        )
                        if dialog1.ShowModal() == wx.ID_OK:
                            self.detector_batch = int(dialog1.GetValue())
                        else:
                            self.detector_batch = 1
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
                message="Specify beginning time of analysis",
                caption="Beginning time of analysis",
                choices=methods,
            )
            if dialog.ShowModal() == wx.ID_OK:
                method = dialog.GetStringSelection()
                if method == "Automatic (for light on and off)":
                    self.autofind_t = True
                    self.decode_t = False
                    self.text_startanalyze.SetLabel(
                        "Automatically find the onset of the 1st time when light on / off as the beginning time."
                    )
                elif method == 'Decode from filenames: "_bt_"':
                    self.autofind_t = False
                    self.decode_t = True
                    self.text_startanalyze.SetLabel(
                        'Decode the beginning time from the filenames: the "t" immediately after the letter "b"" in "_bt_".'
                    )
                else:
                    self.autofind_t = False
                    self.decode_t = False
                    dialog2 = wx.NumberEntryDialog(
                        self,
                        "Enter the beginning time of analysis",
                        "The unit is second:",
                        "Beginning time of analysis",
                        0,
                        0,
                        100000000000000,
                    )
                    if dialog2.ShowModal() == wx.ID_OK:
                        self.t = float(dialog2.GetValue())
                        if self.t < 0:
                            self.t = 0
                        self.text_startanalyze.SetLabel(
                            "Analysis will begin at the: " + str(self.t) + " second."
                        )
                    dialog2.Destroy()
            dialog.Destroy()

    def input_duration(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            dialog = wx.NumberEntryDialog(
                self,
                "Enter the duration of the analysis",
                "The unit is second:",
                "Analysis duration",
                0,
                0,
                100000000000000,
            )
            if dialog.ShowModal() == wx.ID_OK:
                self.duration = int(dialog.GetValue())
                if self.duration != 0:
                    self.text_duration.SetLabel(
                        "The analysis duration is " + str(self.duration) + " seconds."
                    )
                else:
                    self.text_duration.SetLabel(
                        "The analysis duration is from the specified beginning time to the end of a video."
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

    def select_behaviors(self, event):
        if self.path_to_categorizer is None:
            wx.MessageBox(
                "No Categorizer selected! The behavior names are listed in the Categorizer.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            if len(self.animal_kinds) > 1:
                dialog = wx.MultiChoiceDialog(
                    self,
                    message="Specify which animals/objects to annotate",
                    caption="Animal/Object to annotate",
                    choices=self.animal_kinds,
                )
                if dialog.ShowModal() == wx.ID_OK:
                    self.animal_to_include = [
                        self.animal_kinds[i] for i in dialog.GetSelections()
                    ]
                else:
                    self.animal_to_include = self.animal_kinds
                dialog.Destroy()
            else:
                self.animal_to_include = self.animal_kinds

            dialog = wx.MultiChoiceDialog(
                self,
                message="Select behaviors",
                caption="Behaviors to annotate",
                choices=list(self.behaviornames_and_colors.keys()),
            )
            if dialog.ShowModal() == wx.ID_OK:
                self.behavior_to_include = [
                    list(self.behaviornames_and_colors.keys())[i]
                    for i in dialog.GetSelections()
                ]
            else:
                self.behavior_to_include = list(self.behaviornames_and_colors.keys())
            dialog.Destroy()

            if len(self.behavior_to_include) == 0:
                self.behavior_to_include = list(self.behaviornames_and_colors.keys())
            if self.behavior_to_include[0] == "all":
                self.behavior_to_include = list(self.behaviornames_and_colors.keys())

            if self.behavior_mode == 2:
                dialog = wx.MessageDialog(
                    self,
                    "Specify individual-specific behaviors? e.g., sex-specific behaviors only occur in a specific sex and\ncan be used to maintain the correct ID of this individual during the entire analysis.",
                    "Individual-specific behaviors?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if dialog.ShowModal() == wx.ID_YES:
                    for animal_name in self.animal_kinds:
                        dialog1 = wx.MultiChoiceDialog(
                            self,
                            message="Select individual-specific behaviors for "
                            + str(animal_name),
                            caption="Individual-specific behaviors for "
                            + str(animal_name),
                            choices=self.behavior_to_include,
                        )
                        if dialog1.ShowModal() == wx.ID_OK:
                            self.specific_behaviors[animal_name] = {}
                            self.correct_ID = True
                            specific_behaviors = [
                                self.behavior_to_include[i]
                                for i in dialog1.GetSelections()
                            ]
                            for specific_behavior in specific_behaviors:
                                self.specific_behaviors[animal_name][
                                    specific_behavior
                                ] = None
                        dialog1.Destroy()
                else:
                    self.correct_ID = False
                dialog.Destroy()

            complete_colors = list(mpl.colors.cnames.values())
            colors = []
            for c in complete_colors:
                colors.append(["#ffffff", c])

            dialog = wx.MessageDialog(
                self,
                "Specify the color to represent\nthe behaviors in annotations and plots?",
                "Specify colors for behaviors?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog.ShowModal() == wx.ID_YES:
                names_colors = {}
                n = 0
                while n < len(self.behavior_to_include):
                    dialog2 = ColorPicker(
                        self,
                        "Color for " + self.behavior_to_include[n],
                        [self.behavior_to_include[n], colors[n]],
                    )
                    if dialog2.ShowModal() == wx.ID_OK:
                        (r, b, g, _) = dialog2.color_picker.GetColour()
                        new_color = "#%02x%02x%02x" % (r, b, g)
                        self.behaviornames_and_colors[self.behavior_to_include[n]] = [
                            "#ffffff",
                            new_color,
                        ]
                        names_colors[self.behavior_to_include[n]] = new_color
                    else:
                        if n < len(colors):
                            names_colors[self.behavior_to_include[n]] = colors[n][1]
                            self.behaviornames_and_colors[
                                self.behavior_to_include[n]
                            ] = colors[n]
                    dialog2.Destroy()
                    n += 1
                if self.correct_ID is True:
                    self.text_selectbehaviors.SetLabel(
                        "Selected: "
                        + str(list(names_colors.keys()))
                        + ". Specific behaviors: "
                        + str(self.specific_behaviors)
                        + "."
                    )
                else:
                    self.text_selectbehaviors.SetLabel(
                        "Selected: " + str(list(names_colors.keys())) + "."
                    )
            else:
                for color in colors:
                    index = colors.index(color)
                    if index < len(self.behavior_to_include):
                        behavior_name = list(self.behaviornames_and_colors.keys())[
                            index
                        ]
                        self.behaviornames_and_colors[behavior_name] = color
                if self.correct_ID is True:
                    self.text_selectbehaviors.SetLabel(
                        "Selected: "
                        + str(self.behavior_to_include)
                        + " with default colors. Specific behaviors:"
                        + str(self.specific_behaviors)
                        + "."
                    )
                else:
                    self.text_selectbehaviors.SetLabel(
                        "Selected: "
                        + str(self.behavior_to_include)
                        + " with default colors."
                    )
            dialog.Destroy()

            if self.behavior_mode != 3:
                dialog = wx.MessageDialog(
                    self,
                    "Show legend of behavior names in the annotated video?",
                    "Legend in video?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if dialog.ShowModal() == wx.ID_YES:
                    self.show_legend = True
                else:
                    self.show_legend = False
                dialog.Destroy()

    def select_parameters(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            if self.path_to_categorizer is None:
                parameters = [
                    "3 areal parameters",
                    "3 length parameters",
                    "4 locomotion parameters",
                ]
            else:
                if self.behavior_mode == 1:
                    parameters = ["count", "duration", "latency"]
                else:
                    parameters = [
                        "count",
                        "duration",
                        "latency",
                        "3 areal parameters",
                        "3 length parameters",
                        "4 locomotion parameters",
                    ]

            dialog = wx.MultiChoiceDialog(
                self,
                message="Select quantitative measurements",
                caption="Quantitative measurements",
                choices=parameters,
            )
            if dialog.ShowModal() == wx.ID_OK:
                self.parameter_to_analyze = [
                    parameters[i] for i in dialog.GetSelections()
                ]
            else:
                self.parameter_to_analyze = []
            dialog.Destroy()

            if len(self.parameter_to_analyze) <= 0:
                self.parameter_to_analyze = []
                self.normalize_distance = False
                self.text_selectparameters.SetLabel("NO parameter selected.")
            else:
                if "4 locomotion parameters" in self.parameter_to_analyze:
                    dialog = wx.MessageDialog(
                        self,
                        "Normalize the distances by the size of an animal? If no, all distances will be output in pixels.",
                        "Normalize the distances?",
                        wx.YES_NO | wx.ICON_QUESTION,
                    )
                    if dialog.ShowModal() == wx.ID_YES:
                        self.normalize_distance = True
                        self.text_selectparameters.SetLabel(
                            "Selected: "
                            + str(self.parameter_to_analyze)
                            + "; with normalization of distance."
                        )
                    else:
                        self.normalize_distance = False
                        self.text_selectparameters.SetLabel(
                            "Selected: "
                            + str(self.parameter_to_analyze)
                            + "; NO normalization of distance."
                        )
                    dialog.Destroy()
                else:
                    self.normalize_distance = False
                    self.text_selectparameters.SetLabel(
                        "Selected: " + str(self.parameter_to_analyze) + "."
                    )

    def analyze_behaviors(self, event):
        if self.path_to_videos is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / result folder.", "Error", wx.OK | wx.ICON_ERROR
            )

        else:
            if self.behavior_mode >= 3:
                if self.path_to_categorizer is None or self.path_to_detector is None:
                    wx.MessageBox(
                        "You need to select a Categorizer / Detector.",
                        "Error",
                        wx.OK | wx.ICON_ERROR,
                    )
                else:
                    AAD = AnalyzeAnimalDetector()
                    AAD.analyze_images_individuals(
                        self.path_to_detector,
                        self.path_to_videos,
                        self.result_path,
                        self.animal_kinds,
                        path_to_categorizer=self.path_to_categorizer,
                        generate=False,
                        animal_to_include=self.animal_to_include,
                        behavior_to_include=self.behavior_to_include,
                        names_and_colors=self.behaviornames_and_colors,
                        imagewidth=self.framewidth,
                        dim_conv=self.dim_conv,
                        channel=self.channel,
                        detection_threshold=self.detection_threshold,
                        uncertain=self.uncertain,
                        background_free=self.background_free,
                        social_distance=0,
                    )

            else:
                all_events = {}
                event_data = {}
                all_lengths = []

                if self.use_detector is True:
                    for animal_name in self.animal_kinds:
                        all_events[animal_name] = {}
                    if len(self.animal_to_include) == 0:
                        self.animal_to_include = self.animal_kinds

                if self.path_to_categorizer is None:
                    self.behavior_to_include = []
                else:
                    if self.behavior_to_include[0] == "all":
                        self.behavior_to_include = list(
                            self.behaviornames_and_colors.keys()
                        )

                for i in self.path_to_videos:
                    filename = os.path.splitext(os.path.basename(i))[0].split("_")
                    if self.decode_animalnumber is True:
                        if self.use_detector is True:
                            self.animal_number = {}
                            number = [
                                x[1:] for x in filename if len(x) > 1 and x[0] == "n"
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

                    if self.path_to_categorizer is None:
                        self.behavior_mode = 0
                        categorize_behavior = False
                    else:
                        categorize_behavior = True

                    if self.use_detector is False:
                        AA = AnalyzeAnimal()
                        AA.prepare_analysis(
                            i,
                            self.result_path,
                            self.animal_number,
                            delta=self.delta,
                            names_and_colors=self.behaviornames_and_colors,
                            framewidth=self.framewidth,
                            stable_illumination=self.stable_illumination,
                            dim_tconv=self.dim_tconv,
                            dim_conv=self.dim_conv,
                            channel=self.channel,
                            include_bodyparts=self.include_bodyparts,
                            std=self.std,
                            categorize_behavior=categorize_behavior,
                            animation_analyzer=self.animation_analyzer,
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
                            AA.acquire_information(background_free=self.background_free)
                            AA.craft_data()
                            interact_all = False
                        else:
                            AA.acquire_information_interact_basic(
                                background_free=self.background_free
                            )
                            interact_all = True
                        if self.path_to_categorizer is not None:
                            AA.categorize_behaviors(
                                self.path_to_categorizer, uncertain=self.uncertain
                            )
                        AA.annotate_video(
                            self.behavior_to_include,
                            show_legend=self.show_legend,
                            interact_all=interact_all,
                        )
                        AA.export_results(
                            normalize_distance=self.normalize_distance,
                            parameter_to_analyze=self.parameter_to_analyze,
                        )

                        if self.path_to_categorizer is not None:
                            for n in AA.event_probability:
                                all_events[len(all_events)] = AA.event_probability[n]
                                all_lengths.append(len(AA.event_probability[n]))

                    else:
                        AAD = AnalyzeAnimalDetector()
                        AAD.prepare_analysis(
                            self.path_to_detector,
                            i,
                            self.result_path,
                            self.animal_number,
                            self.animal_kinds,
                            self.behavior_mode,
                            names_and_colors=self.behaviornames_and_colors,
                            framewidth=self.framewidth,
                            dim_tconv=self.dim_tconv,
                            dim_conv=self.dim_conv,
                            channel=self.channel,
                            include_bodyparts=self.include_bodyparts,
                            std=self.std,
                            categorize_behavior=categorize_behavior,
                            animation_analyzer=self.animation_analyzer,
                            t=self.t,
                            duration=self.duration,
                            length=self.length,
                            social_distance=self.social_distance,
                        )
                        AAD.acquire_information(
                            batch_size=self.detector_batch,
                            background_free=self.background_free,
                        )
                        if self.behavior_mode != 1:
                            AAD.craft_data()
                        if self.path_to_categorizer is not None:
                            AAD.categorize_behaviors(
                                self.path_to_categorizer, uncertain=self.uncertain
                            )
                        if self.correct_ID is True:
                            AAD.correct_identity(self.specific_behaviors)
                        AAD.annotate_video(
                            self.animal_to_include,
                            self.behavior_to_include,
                            show_legend=self.show_legend,
                        )
                        AAD.export_results(
                            normalize_distance=self.normalize_distance,
                            parameter_to_analyze=self.parameter_to_analyze,
                        )

                        if self.path_to_categorizer is not None:
                            for animal_name in self.animal_kinds:
                                for n in AAD.event_probability[animal_name]:
                                    all_events[animal_name][
                                        len(all_events[animal_name])
                                    ] = AAD.event_probability[animal_name][n]
                                    all_lengths.append(
                                        len(AAD.event_probability[animal_name][n])
                                    )

                if self.path_to_categorizer is not None:
                    if self.use_detector is False:
                        for n in all_events:
                            event_data[len(event_data)] = all_events[n][
                                : min(all_lengths)
                            ]
                        time_points = AA.all_time[: min(all_lengths)]
                        all_events_df = pd.DataFrame(event_data, index=time_points)
                        all_events_df.to_excel(
                            os.path.join(self.result_path, "all_events.xlsx"),
                            float_format="%.2f",
                            index_label="time/ID",
                        )
                        plot_evnets(
                            self.result_path,
                            event_data,
                            time_points,
                            self.behaviornames_and_colors,
                            self.behavior_to_include,
                            width=0,
                            height=0,
                        )
                        folders = [
                            i
                            for i in os.listdir(self.result_path)
                            if os.path.isdir(os.path.join(self.result_path, i))
                        ]
                        folders.sort()
                        for behavior_name in self.behaviornames_and_colors:
                            all_summary = []
                            for folder in folders:
                                individual_summary = os.path.join(
                                    self.result_path,
                                    folder,
                                    behavior_name,
                                    "all_summary.xlsx",
                                )
                                if os.path.exists(individual_summary) is True:
                                    all_summary.append(
                                        pd.read_excel(individual_summary)
                                    )
                            if len(all_summary) >= 1:
                                all_summary = pd.concat(all_summary, ignore_index=True)
                                all_summary.to_excel(
                                    os.path.join(
                                        self.result_path,
                                        behavior_name + "_summary.xlsx",
                                    ),
                                    float_format="%.2f",
                                    index_label="ID/parameter",
                                )

                    else:
                        for animal_name in self.animal_to_include:
                            for n in all_events[animal_name]:
                                event_data[len(event_data)] = all_events[animal_name][
                                    n
                                ][: min(all_lengths)]
                            event_data[len(event_data)] = [["NA", -1]] * min(
                                all_lengths
                            )
                        del event_data[len(event_data) - 1]
                        time_points = AAD.all_time[: min(all_lengths)]
                        all_events_df = pd.DataFrame(event_data, index=time_points)
                        all_events_df.to_excel(
                            os.path.join(self.result_path, "all_events.xlsx"),
                            float_format="%.2f",
                            index_label="time/ID",
                        )
                        plot_evnets(
                            self.result_path,
                            event_data,
                            time_points,
                            self.behaviornames_and_colors,
                            self.behavior_to_include,
                            width=0,
                            height=0,
                        )
                        folders = [
                            i
                            for i in os.listdir(self.result_path)
                            if os.path.isdir(os.path.join(self.result_path, i))
                        ]
                        folders.sort()
                        for animal_name in self.animal_kinds:
                            for behavior_name in self.behaviornames_and_colors:
                                all_summary = []
                                for folder in folders:
                                    individual_summary = os.path.join(
                                        self.result_path,
                                        folder,
                                        behavior_name,
                                        animal_name + "_all_summary.xlsx",
                                    )
                                    if os.path.exists(individual_summary) is True:
                                        all_summary.append(
                                            pd.read_excel(individual_summary)
                                        )
                                if len(all_summary) >= 1:
                                    all_summary = pd.concat(
                                        all_summary, ignore_index=True
                                    )
                                    all_summary.to_excel(
                                        os.path.join(
                                            self.result_path,
                                            animal_name
                                            + "_"
                                            + behavior_name
                                            + "_summary.xlsx",
                                        ),
                                        float_format="%.2f",
                                        index_label="ID/parameter",
                                    )
