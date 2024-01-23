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


import shutil
import os
from pathlib import Path

import wx

from LabGym.categorizers import Categorizers
from LabGym.gui.utils import BehaviorMode, LabGymWindow


the_absolute_current_path = str(Path(__file__).resolve().parent.parent)


class TrainCategorizers(LabGymWindow):
    """Train a Categorizer model using sorted behavior examples.

    Attributes:
        file_path: The location of the sorted behavior examples.
        new_path: The location of the renamed, labeled examples.
        behavior_mode: The behavior mode.
        using_animation_analyzer: Whether or not to use animations in training
            the categorizer.
        level_tconv: ???
        level_conv: ???
        dim_tconv: ???
        dim_conv: ???
        channel: The number of channels in ???
        length: The number of frames in a single behavior example.
        aug_methods: A list of augmentation methods to use while training.
        augvalid: Whether or not to use augmentation for validation data.
        data_path: The path to all prepared training examples.
        model_path: The location of the available categorizers.
        path_to_categorizer: The path to the newly created categorizer.
        out_path: The folder in which to store training reports.
        include_bodyparts: Whether or not to include body parts.
        std: ???
        resize: Whether or not to resize the animation frames and pattern
            images before data augmentation.
        background_free: ???
        social_distance: The social distance when detecting interactive
            behaviors. (Units are ???)
    """

    def __init__(self):
        super().__init__(title="Train Categorizers", size=(1200, 550))
        self.file_path = None
        self.new_path = None
        self.behavior_mode = BehaviorMode.NON_INTERACTIVE
        self.using_animation_analyzer = True
        self.level_tconv = 2
        self.level_conv = 2
        self.dim_tconv = 32
        self.dim_conv = 32
        self.channel = 1
        self.length = 15
        self.aug_methods = []
        self.augvalid = True
        self.data_path = None
        self.model_path = os.path.join(the_absolute_current_path, "models")
        self.path_to_categorizer = os.path.join(
            the_absolute_current_path, "models", "New_model"
        )
        self.out_path = None
        self.include_bodyparts = False
        self.std = 0
        self.resize = None
        self.background_free = True
        self.social_distance = 0

        self.text_inputexamples = self.module_text("None.")
        self.add_module(
            "Select the folder that stores\nthe sorted behavior examples",
            self.select_filepath,
            "This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders will be read by LabGym as the behavior names.",
            self.text_inputexamples,
        )

        self.text_renameexample = self.module_text("None.")
        self.add_module(
            "Select a new folder to store\nall the prepared behavior examples",
            self.select_outpath,
            "This folder will store all the prepared behavior examples and can be directly used for training. Preparing behavior examples is copying all examples into this folder and renaming them to put behavior name labels to their file names.",
            self.text_renameexample,
        )

        self.add_submit_button(
            "Start to prepare the training examples",
            self.rename_files,
            "All prepared behavior examples will be stored in the same folder and ready to be input for training.",
        )

        self.text_categorizertype = self.module_text(
            "Default: Categorizer (Animation Analyzer LV2 + Pattern Recognizer LV2). Behavior mode: Non-interact (identify behavior for each individual)."
        )
        self.add_module(
            "Specify the type / complexity of\nthe Categorizer to train",
            self.specify_categorizer,
            "Categorizer with both Animation Analyzer and Pattern Recognizer is slower but a little more accurate than that with Pattern Recognizer only. Higher complexity level means deeper and more complex network architecture. See Extended Guide for details.",
            self.text_categorizertype,
        )

        self.text_categorizershape = self.module_text(
            "Default: (width,height,channel) is (32,32,1) / (32,32,3)."
        )
        self.add_module(
            "Specify the input shape for\nAnimation Analyzer / Pattern Recognizer",
            self.set_categorizer,
            "The input frame / image size should be an even integer and larger than 8. The larger size, the wider of network architecture. Use large size only when there are detailed features in frames / images that are important for identifying behaviors. See Extended Guide for details.",
            self.text_categorizershape,
        )

        self.text_length = self.module_text("Default: 15.")
        self.add_module(
            "Specify the number of frames for\nan animation / pattern image",
            self.input_timesteps,
            'The duration (how many frames) of a behavior example. This info can be found in the filenames of the generated behavior examples, "_lenXX_" where "XX" is the number you need to enter here.',
            self.text_length,
        )

        self.text_trainingfolder = self.module_text("None.")
        self.add_module(
            "Select the folder that stores\nall the prepared training examples",
            self.select_datapath,
            'The folder that stores all the prepared behavior examples. If body parts are included, the STD value can be found in the filenames of the generated behavior examples with "_stdXX_" where "XX" is the number you need to enter here.',
            self.text_trainingfolder,
        )

        self.text_augmentation = self.module_text("None.")
        self.add_module(
            "Specify the methods to\naugment training examples",
            self.specify_augmentation,
            'Randomly change or add noise into the training examples to increase their amount and diversity, which can benefit the training. If the amount of examples less than 1,000 before augmentation, choose "Also augment the validation data". See Extended Guide for details.',
            self.text_augmentation,
        )

        self.text_report = self.module_text("None.")
        self.add_module(
            "Select a folder to\nexport training reports",
            self.select_reportpath,
            "This is the folder to store the reports of training history and metrics. It is optional.",
            self.text_report,
        )

        self.add_submit_button(
            "Train the Categorizer",
            self.train_categorizer,
            "Need to name the Categorizer to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.",
        )

        self.display_window()

    def select_filepath(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.file_path = dialog.GetPath()
            self.text_inputexamples.SetLabel(
                "Path to sorted behavior examples: " + self.file_path + "."
            )
        dialog.Destroy()

    def select_outpath(self, event):
        dialog = wx.DirDialog(
            self, "Select a new directory", "", style=wx.DD_DEFAULT_STYLE
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.new_path = dialog.GetPath()
            self.text_renameexample.SetLabel(
                "Will copy and rename the examples to: " + self.new_path + "."
            )
        dialog.Destroy()

        dialog = wx.MessageDialog(
            self,
            'Reducing frame / image size can speed up training\nSelect "No" if dont know what it is.',
            "Resize the frames / images?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            dialog1 = wx.NumberEntryDialog(
                self,
                "Enter the desired width dimension",
                "No smaller than the\ndesired input dimension of the Categorizer:",
                "Frame / image dimension",
                32,
                1,
                300,
            )
            if dialog1.ShowModal() == wx.ID_OK:
                self.resize = int(dialog1.GetValue())
            if self.resize < 16:
                self.resize = 16
            self.text_renameexample.SetLabel(
                "Will copy, rename, and resize (to "
                + str(self.resize)
                + ") the examples to: "
                + self.new_path
                + "."
            )
            dialog1.Destroy()
        else:
            self.resize = None
        dialog.Destroy()

    def rename_files(self, event):
        if self.file_path is None or self.new_path is None:
            wx.MessageBox(
                "Please select a folder that stores the sorted examples /\na new folder to store prepared training examples!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        else:
            CA = Categorizers()
            CA.rename_label(self.file_path, self.new_path, resize=self.resize)

    def specify_categorizer(self, event):
        behavior_modes = [
            "Non-interact (identify behavior for each individual)",
            "Interact basic (identify behavior for the interactive pair / group)",
            "Interact advanced (identify behavior for both each individual and each interactive pair / group)",
            "Static images (non-interactive): behaviors of each individual in static images(each image contains one animal / object)",
        ]
        dialog = wx.SingleChoiceDialog(
            self,
            message="Specify the mode of behavior for the Categorizer to identify",
            caption="Behavior mode",
            choices=behavior_modes,
        )
        if dialog.ShowModal() == wx.ID_OK:
            behavior_mode = dialog.GetStringSelection()
            if behavior_mode == "Non-interact (identify behavior for each individual)":
                self.behavior_mode = 0
            elif (
                behavior_mode
                == "Interact basic (identify behavior for the interactive pair / group)"
            ):
                self.behavior_mode = 1
            elif (
                behavior_mode
                == "Interact advanced (identify behavior for both each individual and each interactive pair / group)"
            ):
                self.behavior_mode = 2
                self.channel = 3
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Interactions happen within the social distance.",
                    "How many folds of the animals's diameter\nis the social distance (0=inf):",
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
            else:
                self.behavior_mode = 3
                self.text_length.SetLabel(
                    'No need to specify this since the selected behavior mode is "Static images".'
                )
        dialog.Destroy()

        if self.behavior_mode >= 3:
            categorizer_types = [
                "Categorizer (Pattern Recognizer only) (faster / a little less accurate)"
            ]
        else:
            categorizer_types = [
                "Categorizer (Animation Analyzer + Pattern Recognizer)",
                "Categorizer (Pattern Recognizer only) (faster / a little less accurate)",
            ]
        dialog = wx.SingleChoiceDialog(
            self,
            message="Select the Categorizer type",
            caption="Categorizer types",
            choices=categorizer_types,
        )
        if dialog.ShowModal() == wx.ID_OK:
            categorizer_tp = dialog.GetStringSelection()
            if (
                categorizer_tp
                == "Categorizer (Pattern Recognizer only) (faster / a little less accurate)"
            ):
                self.using_animation_analyzer = False
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Complexity level from 1 to 7\nhigher level = deeper network",
                    "Enter a number (1~7)",
                    "Pattern Recognizer level",
                    2,
                    1,
                    7,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.level_conv = int(dialog1.GetValue())
                dialog1.Destroy()
                level = self.level_conv
            else:
                self.using_animation_analyzer = True
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Complexity level from 1 to 7\nhigher level = deeper network",
                    "Enter a number (1~7)",
                    "Animation Analyzer level",
                    2,
                    1,
                    7,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.level_tconv = int(dialog1.GetValue())
                dialog1.Destroy()
                dialog1 = wx.NumberEntryDialog(
                    self,
                    "Complexity level from 1 to 7\nhigher level = deeper network",
                    "Enter a number (1~7)",
                    "Pattern Recognizer level",
                    2,
                    1,
                    7,
                )
                if dialog1.ShowModal() == wx.ID_OK:
                    self.level_conv = int(dialog1.GetValue())
                dialog1.Destroy()
                level = [self.level_tconv, self.level_conv]
        else:
            categorizer_tp = ""
            level = ""
        dialog.Destroy()

        if behavior_mode == 0:
            self.text_categorizertype.SetLabel(
                categorizer_tp
                + " (LV "
                + str(level)
                + ") to identify behaviors of each non-interactive individual."
            )
        elif behavior_mode == 1:
            self.text_categorizertype.SetLabel(
                categorizer_tp
                + " (LV "
                + str(level)
                + ") to identify behaviors of the interactive group."
            )
        elif behavior_mode == 2:
            self.text_categorizertype.SetLabel(
                categorizer_tp
                + " (LV "
                + str(level)
                + ") to identify behaviors of the interactive individuals and groups. Social distance: "
                + str(self.social_distance)
                + " folds of the animal diameter."
            )
        else:
            self.text_categorizertype.SetLabel(
                categorizer_tp
                + " (LV "
                + str(level)
                + ") to identify behaviors of each non-interactive individual in static images."
            )

    def set_categorizer(self, event):
        if self.using_animation_analyzer is True:
            dialog = wx.NumberEntryDialog(
                self,
                "Input dimension of Animation Analyzer\nlarger dimension = wider network",
                "Enter a number:",
                "Animation Analyzer input",
                32,
                1,
                300,
            )
            if dialog.ShowModal() == wx.ID_OK:
                self.dim_tconv = int(dialog.GetValue())
            dialog.Destroy()
            if self.behavior_mode == 2:
                self.channel = 3
            else:
                dialog = wx.MessageDialog(
                    self,
                    'Grayscale input of Animation Analyzer?\nSelect "Yes" if the color of animals is behavior irrelevant.',
                    "Grayscale Animation Analyzer?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if dialog.ShowModal() == wx.ID_YES:
                    self.channel = 1
                else:
                    self.channel = 3
                dialog.Destroy()

        dialog = wx.NumberEntryDialog(
            self,
            "Input dimension of Pattern Recognizer\nlarger dimension = wider network",
            "Enter a number:",
            "Input the dimension",
            32,
            1,
            300,
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.dim_conv = int(dialog.GetValue())
            if self.behavior_mode >= 3:
                dialog1 = wx.MessageDialog(
                    self,
                    'Grayscale input?\nSelect "Yes" if the color of animals is behavior irrelevant.',
                    "Grayscale inputs?",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if dialog1.ShowModal() == wx.ID_YES:
                    self.channel = 1
                else:
                    self.channel = 3
                dialog.Destroy()
        dialog.Destroy()

        shape_tconv = (
            "("
            + str(self.dim_tconv)
            + ","
            + str(self.dim_tconv)
            + ","
            + str(self.channel)
            + ")"
        )
        if self.behavior_mode >= 3:
            shape_conv = (
                "("
                + str(self.dim_conv)
                + ","
                + str(self.dim_conv)
                + ","
                + str(self.channel)
                + ")"
            )
        else:
            shape_conv = (
                "(" + str(self.dim_conv) + "," + str(self.dim_conv) + "," + "3)"
            )
        if self.using_animation_analyzer is False:
            self.text_categorizershape.SetLabel(
                "Input shapes: Pattern Recognizer" + shape_conv + "."
            )
        else:
            self.text_categorizershape.SetLabel(
                "Input shapes: Animation Analyzer"
                + shape_tconv
                + "; Pattern Recognizer"
                + shape_conv
                + "."
            )

    def input_timesteps(self, event):
        if self.behavior_mode >= 3:
            wx.MessageBox(
                'No need to specify this since the selected behavior mode is "Static images".',
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

        else:
            dialog = wx.NumberEntryDialog(
                self,
                "The number of frames of\na behavior example",
                "Enter a number (minimum=3):",
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
                    "The duration of a behavior example is :" + str(self.length) + "."
                )
            dialog.Destroy()

    def select_datapath(self, event):
        dialog = wx.MessageDialog(
            self,
            "Are the animations (in any) in\ntraining examples background free?",
            "Background-free animations?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            self.background_free = True
        else:
            self.background_free = False
        dialog.Destroy()

        if self.behavior_mode >= 3:
            self.include_bodyparts = False
        else:
            dialog = wx.MessageDialog(
                self,
                "Do the pattern images in training examples\ninclude body parts?",
                "Body parts in pattern images?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog.ShowModal() == wx.ID_YES:
                self.include_bodyparts = True
                dialog2 = wx.NumberEntryDialog(
                    self,
                    "Should match the STD of the pattern images in training examples.",
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

        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.data_path = dialog.GetPath()
            if self.include_bodyparts is True:
                if self.background_free is True:
                    self.text_trainingfolder.SetLabel(
                        "Animations w/o background, pattern images w/ bodyparts ("
                        + str(self.std)
                        + ") in: "
                        + self.data_path
                        + "."
                    )
                else:
                    self.text_trainingfolder.SetLabel(
                        "Animations w/ background, pattern images w/ bodyparts ("
                        + str(self.std)
                        + ") in: "
                        + self.data_path
                        + "."
                    )
            else:
                if self.background_free is True:
                    self.text_trainingfolder.SetLabel(
                        "Animations w/o background, pattern images w/o bodyparts in: "
                        + self.data_path
                        + "."
                    )
                else:
                    self.text_trainingfolder.SetLabel(
                        "Animations w/ background, pattern images w/o bodyparts in: "
                        + self.data_path
                        + "."
                    )
        dialog.Destroy()

    def specify_augmentation(self, event):
        dialog = wx.MessageDialog(
            self,
            'Use default augmentation methods?\nSelect "Yes" if dont know how to specify.',
            "Use default augmentation?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            selected = "default"
            self.aug_methods = ["default"]
        else:
            aug_methods = [
                "random rotation",
                "horizontal flipping",
                "vertical flipping",
                "random brightening",
                "random dimming",
                "random shearing",
                "random rescaling",
                "random deletion",
            ]
            selected = ""
            dialog1 = wx.MultiChoiceDialog(
                self,
                message="Data augmentation methods",
                caption="Augmentation methods",
                choices=aug_methods,
            )
            if dialog1.ShowModal() == wx.ID_OK:
                self.aug_methods = [aug_methods[i] for i in dialog1.GetSelections()]
                for i in dialog1.GetSelections():
                    if selected == "":
                        selected = selected + aug_methods[i]
                    else:
                        selected = selected + "," + aug_methods[i]
            else:
                self.aug_methods = []
            dialog1.Destroy()
        if len(self.aug_methods) <= 0:
            selected = "none"
        else:
            if self.aug_methods[0] == "default":
                self.aug_methods = [
                    "random rotation",
                    "horizontal flipping",
                    "vertical flipping",
                    "random brightening",
                    "random dimming",
                ]
        dialog.Destroy()

        dialog = wx.MessageDialog(
            self,
            'Also augment the validation data?\nSelect "No" if dont know what it is.',
            "Augment validation data?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            self.augvalid = True
            self.text_augmentation.SetLabel(
                "Augment both training and validation examples with: " + selected + "."
            )
        else:
            self.augvalid = False
            self.text_augmentation.SetLabel(
                "Augment training examples with: " + selected + "."
            )
        dialog.Destroy()

    def select_reportpath(self, event):
        dialog = wx.MessageDialog(
            self,
            "Export the training reports?",
            "Export training reports?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            dialog2 = wx.DirDialog(
                self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
            )
            if dialog2.ShowModal() == wx.ID_OK:
                self.out_path = dialog2.GetPath()
                self.text_report.SetLabel(
                    "Training reports will be in: " + self.out_path + "."
                )
            dialog2.Destroy()
        else:
            self.out_path = None
        dialog.Destroy()

    def train_categorizer(self, event):
        if self.data_path is None:
            wx.MessageBox(
                "No path to training examples.", "Error", wx.OK | wx.ICON_ERROR
            )

        else:
            do_nothing = False

            stop = False
            while stop is False:
                dialog = wx.TextEntryDialog(
                    self,
                    "Enter a name for the Categorizer to train",
                    "Categorizer name",
                )
                if dialog.ShowModal() == wx.ID_OK:
                    if dialog.GetValue() != "":
                        self.path_to_categorizer = os.path.join(
                            self.model_path, dialog.GetValue()
                        )
                        if not os.path.isdir(self.path_to_categorizer):
                            os.makedirs(self.path_to_categorizer)
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
                if self.using_animation_analyzer is False:
                    CA = Categorizers()
                    if self.behavior_mode >= 3:
                        self.length = self.std = 0
                        self.include_bodyparts = False
                    else:
                        self.channel = 3
                    CA.train_pattern_recognizer(
                        self.data_path,
                        self.path_to_categorizer,
                        self.out_path,
                        dim=self.dim_conv,
                        channel=self.channel,
                        time_step=self.length,
                        level=self.level_conv,
                        aug_methods=self.aug_methods,
                        augvalid=self.augvalid,
                        include_bodyparts=self.include_bodyparts,
                        std=self.std,
                        background_free=self.background_free,
                        behavior_mode=self.behavior_mode,
                        social_distance=self.social_distance,
                    )
                else:
                    if self.behavior_mode == 2:
                        self.channel = 3
                    CA = Categorizers()
                    CA.train_combnet(
                        self.data_path,
                        self.path_to_categorizer,
                        self.out_path,
                        dim_tconv=self.dim_tconv,
                        dim_conv=self.dim_conv,
                        channel=self.channel,
                        time_step=self.length,
                        level_tconv=self.level_tconv,
                        level_conv=self.level_conv,
                        aug_methods=self.aug_methods,
                        augvalid=self.augvalid,
                        include_bodyparts=self.include_bodyparts,
                        std=self.std,
                        background_free=self.background_free,
                        behavior_mode=self.behavior_mode,
                        social_distance=self.social_distance,
                    )


class TestCategorizers(wx.Frame):
    def __init__(self):
        super(TestCategorizers, self).__init__(
            parent=None, title="Test Categorizers", size=(1000, 240)
        )
        self.file_path = None  # the file path storing ground-truth examples
        self.model_path = os.path.join(the_absolute_current_path, "models")
        self.path_to_categorizer = None
        self.out_path = None  # for storing testing reports

        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        module_selectcategorizer = wx.BoxSizer(wx.HORIZONTAL)
        button_selectcategorizer = wx.Button(
            panel, label="Select a Categorizer\nto test", size=(300, 40)
        )
        button_selectcategorizer.Bind(wx.EVT_BUTTON, self.select_categorizer)
        wx.Button.SetToolTip(
            button_selectcategorizer,
            "The behavioral names in ground-truth dataset should exactly match those in the selected Categorizer.",
        )
        self.text_selectcategorizer = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_selectcategorizer.Add(
            button_selectcategorizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectcategorizer.Add(
            self.text_selectcategorizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(0, 10, 0)
        boxsizer.Add(module_selectcategorizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_inputexamples = wx.BoxSizer(wx.HORIZONTAL)
        button_inputexamples = wx.Button(
            panel,
            label="Select the folder that stores\nthe ground-truth behavior examples",
            size=(300, 40),
        )
        button_inputexamples.Bind(wx.EVT_BUTTON, self.select_filepath)
        wx.Button.SetToolTip(
            button_inputexamples,
            "This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders are the ground-truth behavior names, which should match those in the selected Categorizer.",
        )
        self.text_inputexamples = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_inputexamples.Add(
            button_inputexamples, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_inputexamples.Add(
            self.text_inputexamples, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_inputexamples, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_report = wx.BoxSizer(wx.HORIZONTAL)
        button_report = wx.Button(
            panel, label="Select a folder to\nexport testing reports", size=(300, 40)
        )
        button_report.Bind(wx.EVT_BUTTON, self.select_reportpath)
        wx.Button.SetToolTip(
            button_report,
            "This is the folder to store the reports of testing results and metrics. It is optional.",
        )
        self.text_report = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_report.Add(button_report, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module_report.Add(self.text_report, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(module_report, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        testanddelete = wx.BoxSizer(wx.HORIZONTAL)
        button_test = wx.Button(panel, label="Test the Categorizer", size=(300, 40))
        button_test.Bind(wx.EVT_BUTTON, self.test_categorizer)
        wx.Button.SetToolTip(
            button_test,
            "Test the selected Categorizer on the ground-truth behavior examples",
        )
        button_delete = wx.Button(panel, label="Delete a Categorizer", size=(300, 40))
        button_delete.Bind(wx.EVT_BUTTON, self.remove_categorizer)
        wx.Button.SetToolTip(
            button_delete,
            "Permanently delete a Categorizer. The deletion CANNOT be restored.",
        )
        testanddelete.Add(button_test, 0, wx.RIGHT, 50)
        testanddelete.Add(button_delete, 0, wx.LEFT, 50)
        boxsizer.Add(0, 5, 0)
        boxsizer.Add(testanddelete, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        boxsizer.Add(0, 10, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def select_categorizer(self, event):
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
        if "Choose a new directory of the Categorizer" not in categorizers:
            categorizers.append("Choose a new directory of the Categorizer")

        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Categorizer to test",
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
                else:
                    self.path_to_categorizer = None
                dialog1.Destroy()
                self.text_selectcategorizer.SetLabel(
                    "The path to the Categorizer to test is: "
                    + self.path_to_categorizer
                    + "."
                )
            else:
                self.path_to_categorizer = os.path.join(self.model_path, categorizer)
                self.text_selectcategorizer.SetLabel(
                    "Categorizer to test: " + categorizer + "."
                )

        dialog.Destroy()

    def select_filepath(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.file_path = dialog.GetPath()
            self.text_inputexamples.SetLabel(
                "Path to ground-truth behavior examples: " + self.file_path + "."
            )
        dialog.Destroy()

    def select_reportpath(self, event):
        dialog = wx.MessageDialog(
            self,
            "Export the testing reports?",
            "Export testing reports?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            dialog1 = wx.DirDialog(
                self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE
            )
            if dialog1.ShowModal() == wx.ID_OK:
                self.out_path = dialog1.GetPath()
                self.text_report.SetLabel(
                    "Testing reports will be in: " + self.out_path + "."
                )
            dialog1.Destroy()
        else:
            self.out_path = None
        dialog.Destroy()

    def test_categorizer(self, event):
        if self.file_path is None or self.path_to_categorizer is None:
            wx.MessageBox(
                "No Categorizer selected / path to ground-truth behavior examples.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        else:
            CA = Categorizers()
            CA.test_categorizer(
                self.file_path, self.path_to_categorizer, result_path=self.out_path
            )

    def remove_categorizer(self, event):
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

        dialog = wx.SingleChoiceDialog(
            self,
            message="Select a Categorizer to delete",
            caption="Delete a Categorizer",
            choices=categorizers,
        )
        if dialog.ShowModal() == wx.ID_OK:
            categorizer = dialog.GetStringSelection()
            dialog1 = wx.MessageDialog(
                self,
                "Delete " + str(categorizer) + "?",
                "CANNOT be restored!",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog1.ShowModal() == wx.ID_YES:
                shutil.rmtree(os.path.join(self.model_path, categorizer))
            dialog1.Destroy()
        dialog.Destroy()
