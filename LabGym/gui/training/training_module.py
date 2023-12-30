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

import wx
import wx.lib.agw.hyperlink

from .categorizers import (
    GenerateExamples,
    TrainCategorizers,
    TestCategorizers,
)
from .detectors import (
    GenerateImages,
    TrainDetectors,
    TestDetectors,
)
from .sort_behaviors import SortBehaviors


class TrainingModule(wx.Frame):
    """Contains functions related to training and testing Detectors and Categorizers."""

    def __init__(self):
        super().__init__(parent=None, title="Training Module", size=(500, 560))
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        boxsizer.Add(0, 60, 0)

        # Generate images
        generate_images_button = wx.Button(
            panel, label="Generate Image Examples", size=(300, 40)
        )
        generate_images_button.Bind(wx.EVT_BUTTON, self.generate_images)
        wx.Button.SetToolTip(
            generate_images_button,
            "Extract frames from videos for annotating animals / objects in them so that they can be used to train a Detector to detect animals / objects of your interest. See Extended Guide for how to select images to annotate.",
        )
        boxsizer.Add(generate_images_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Annotate images
        annotate_link = wx.lib.agw.hyperlink.HyperLinkCtrl(
            panel, 0, "\nAnnotate images with Roboflow\n", URL="https://roboflow.com"
        )
        boxsizer.Add(annotate_link, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Train detectors
        train_detectors_button = wx.Button(
            panel, label="Train Detectors", size=(300, 40)
        )
        train_detectors_button.Bind(wx.EVT_BUTTON, self.train_detectors)
        wx.Button.SetToolTip(
            train_detectors_button,
            "There are two detection methods in LabGym, the Detector-based method is more versatile (useful in any recording conditions and complex interactive behaviors) but slower than the other background subtraction-based method (requires static background and stable illumination in videos).",
        )
        boxsizer.Add(train_detectors_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Test detectors
        test_detectors_button = wx.Button(panel, label="Test Detectors", size=(300, 40))
        test_detectors_button.Bind(wx.EVT_BUTTON, self.test_detectors)
        wx.Button.SetToolTip(
            test_detectors_button,
            "Test trained Detectors on the annotated ground-truth image dataset (similar to the image dataset used for training a Detector).",
        )
        boxsizer.Add(test_detectors_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 50, 0)

        # Generate behavior examples
        generate_behavior_examples_button = wx.Button(
            panel, label="Generate Behavior Examples", size=(300, 40)
        )
        generate_behavior_examples_button.Bind(
            wx.EVT_BUTTON, self.generate_behavior_examples
        )
        wx.Button.SetToolTip(
            generate_behavior_examples_button,
            "Generate behavior examples for sorting them so that they can be used to teach a Categorizer to recognize behaviors defined by you.",
        )
        boxsizer.Add(generate_behavior_examples_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Sort behavior examples
        sort_behavior_examples_button = wx.Button(
            panel, label="Sort Behavior Examples", size=(300, 40)
        )
        sort_behavior_examples_button.Bind(wx.EVT_BUTTON, self.sort_behavior_examples)
        wx.Button.SetToolTip(
            sort_behavior_examples_button,
            "Set shortcut keys for behavior categories to help sorting the behavior examples in an easier way. See Extended Guide for how to select and sort the behavior examples.",
        )
        boxsizer.Add(sort_behavior_examples_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Train categorizers
        train_categorizers_button = wx.Button(
            panel, label="Train Categorizers", size=(300, 40)
        )
        train_categorizers_button.Bind(wx.EVT_BUTTON, self.train_categorizers)
        wx.Button.SetToolTip(
            train_categorizers_button,
            "Customize a Categorizer and use the sorted behavior examples to train it so that it can recognize the behaviors of your interest during analysis.",
        )
        boxsizer.Add(train_categorizers_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 5, 0)

        # Test categorizers
        test_categorizers_button = wx.Button(
            panel, label="Test Categorizers", size=(300, 40)
        )
        test_categorizers_button.Bind(wx.EVT_BUTTON, self.test_categorizers)
        wx.Button.SetToolTip(
            test_categorizers_button,
            "Test trained Categorizers on the sorted ground-truth behavior examples (similar to the behavior examples used for training a Categorizer).",
        )
        boxsizer.Add(test_categorizers_button, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 50, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def generate_images(self, event):
        GenerateImages("Generate Image Examples")

    def train_detectors(self, event):
        TrainDetectors("Train Detectors")

    def test_detectors(self, event):
        TestDetectors("Test Detectors")

    def generate_behavior_examples(self, event):
        GenerateExamples("Generate Behavior Examples")

    def sort_behavior_examples(self, event):
        SortBehaviors("Sort Behavior Examples")

    def train_categorizers(self, event):
        TrainCategorizers("Train Categorizers")

    def test_categorizers(self, event):
        TestCategorizers("Test Categorizers")
