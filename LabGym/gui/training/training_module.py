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

from typing import Callable

import wx
import wx.lib.agw.hyperlink

from .categorizers import (
    TrainCategorizers,
    TestCategorizers,
)
from .detectors import (
    GenerateImageExamples,
    TrainDetectors,
    TestDetectors,
)
from .behavior_examples import GenerateBehaviorExamples, SortBehaviorExamples


class TrainingModule(wx.Frame):
    """Contains functions related to training and testing Detectors and Categorizers."""

    def __init__(self):
        super().__init__(parent=None, title="Training Module", size=(500, 560))
        self.panel = wx.Panel(self)
        self.boxsizer = wx.BoxSizer(wx.VERTICAL)
        self.boxsizer.Add(0, 60, 0)

        self.add_button(
            "Generate Image Examples",
            self.generate_images,
            "Extract frames from videos for annotating animals / objects in them so that they can be used to train a Detector to detect animals / objects of your interest. See Extended Guide for how to select images to annotate.",
        )

        annotate_link = wx.lib.agw.hyperlink.HyperLinkCtrl(
            self.panel,
            0,
            "\nAnnotate images with Roboflow\n",
            URL="https://roboflow.com",
        )
        self.boxsizer.Add(annotate_link, 0, wx.ALIGN_CENTER, 10)
        self.boxsizer.Add(0, 5, 0)

        self.add_button(
            "Train Detectors",
            self.train_detectors,
            "There are two detection methods in LabGym, the Detector-based method is more versatile (useful in any recording conditions and complex interactive behaviors) but slower than the other background subtraction-based method (requires static background and stable illumination in videos).",
        )

        self.add_button(
            "Test Detectors",
            self.test_detectors,
            "Test trained Detectors on the annotated ground-truth image dataset (similar to the image dataset used for training a Detector).",
        )

        self.boxsizer.Add(0, 45, 0)

        self.add_button(
            "Generate Behavior Examples",
            self.generate_behavior_examples,
            "Generate behavior examples for sorting them so that they can be used to teach a Categorizer to recognize behaviors defined by you.",
        )

        self.add_button(
            "Sort Behavior Examples",
            self.sort_behavior_examples,
            "Set shortcut keys for behavior categories to help sorting the behavior examples in an easier way. See Extended Guide for how to select and sort the behavior examples.",
        )

        self.add_button(
            "Train Categorizers",
            self.train_categorizers,
            "Customize a Categorizer and use the sorted behavior examples to train it so that it can recognize the behaviors of your interest during analysis.",
        )

        self.add_button(
            "Test Categorizers",
            self.test_categorizers,
            "Test trained Categorizers on the sorted ground-truth behavior examples (similar to the behavior examples used for training a Categorizer).",
        )

        self.boxsizer.Add(0, 45, 0)
        self.panel.SetSizer(self.boxsizer)
        self.Centre()
        self.Show(True)

    def add_button(
        self, button_label: str, button_handler: Callable, button_tool_tip: str
    ):
        """
        Adds a button to the main sizer.

        Args:
            button_label: The button label.
            button_handler: The function to handle the button press.
            button_tool_tip: The text displayed when the user hovers over the button.
        """
        button = wx.Button(self.panel, label=button_label, size=(300, 40))
        button.Bind(wx.EVT_BUTTON, button_handler)
        wx.Button.SetToolTip(button, button_tool_tip)
        self.boxsizer.Add(button, 0, wx.ALIGN_CENTER, 10)
        self.boxsizer.Add(0, 5, 0)

    def generate_images(self, event):
        GenerateImageExamples()

    def train_detectors(self, event):
        TrainDetectors()

    def test_detectors(self, event):
        TestDetectors()

    def generate_behavior_examples(self, event):
        GenerateBehaviorExamples()

    def sort_behavior_examples(self, event):
        SortBehaviorExamples()

    def train_categorizers(self, event):
        TrainCategorizers()

    def test_categorizers(self, event):
        TestCategorizers()
