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

from LabGym import __version__

from .analysis import AnalysisModule
from .preprocessing import PreprocessingModule
from .training import TrainingModule


class MainWindow(wx.Frame):
    """The main LabGym window."""

    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(750, 440))
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        # Welcome text
        self.welcome_text = wx.StaticText(
            panel,
            label="Welcome to LabGym!",
            style=wx.ALIGN_CENTER | wx.ST_ELLIPSIZE_END,
        )
        boxsizer.Add(0, 60, 0)
        boxsizer.Add(self.welcome_text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        boxsizer.Add(0, 60, 0)

        # Developers text
        self.developers_text = wx.StaticText(
            panel,
            label="Developed by Yujia Hu, Rohan Satapathy, M. Victor Struman, Kelly Goss, Isabelle Baker\n\nBing Ye Lab, Life Sciences Institute, University of Michigan",
            style=wx.ALIGN_CENTER | wx.ST_ELLIPSIZE_END,
        )
        boxsizer.Add(self.developers_text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        boxsizer.Add(0, 60, 0)

        # Links to GitHub and extended user guide
        links = wx.BoxSizer(wx.HORIZONTAL)
        homepage = wx.lib.agw.hyperlink.HyperLinkCtrl(
            panel, 0, "Home Page", URL="https://github.com/umyelab/LabGym"
        )
        userguide = wx.lib.agw.hyperlink.HyperLinkCtrl(
            panel,
            0,
            "Extended Guide",
            URL="https://github.com/yujiahu415/LabGym/blob/master/LabGym%20user%20guide_v2.2.pdf",
        )
        links.Add(homepage, 0, wx.LEFT | wx.EXPAND, 10)
        links.Add(userguide, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(links, 0, wx.ALIGN_CENTER, 50)
        boxsizer.Add(0, 50, 0)

        # Main modules
        modules = wx.BoxSizer(wx.HORIZONTAL)
        preprocessing_button = wx.Button(
            panel, label="Preprocessing Module", size=(200, 40)
        )
        preprocessing_button.Bind(wx.EVT_BUTTON, self.open_preprocessing_module)
        wx.Button.SetToolTip(
            preprocessing_button,
            "Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.",
        )
        training_button = wx.Button(panel, label="Training Module", size=(200, 40))
        training_button.Bind(wx.EVT_BUTTON, self.open_training_module)
        wx.Button.SetToolTip(
            training_button,
            "Teach LabGym to recognize the animals / objects of your interest and identify their behaviors that are defined by you.",
        )
        analysis_button = wx.Button(panel, label="Analysis Module", size=(200, 40))
        analysis_button.Bind(wx.EVT_BUTTON, self.open_analysis_module)
        wx.Button.SetToolTip(
            analysis_button,
            "Use LabGym to track the animals / objects of your interest, identify and quantify their behaviors, and display the statistically significant findings.",
        )
        modules.Add(preprocessing_button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        modules.Add(training_button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        modules.Add(analysis_button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(modules, 0, wx.ALIGN_CENTER, 50)
        boxsizer.Add(0, 50, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def open_preprocessing_module(self, event):
        """Opens the preprocessing module."""
        PreprocessingModule()

    def open_training_module(self, event):
        """Opens the training module."""
        TrainingModule()

    def open_analysis_module(self, event):
        """Opens the analysis module."""
        AnalysisModule()


def gui():
    app = wx.App()
    MainWindow(f"LabGym v{__version__}")
    print("The user interface initialized!")
    app.MainLoop()


if __name__ == "__main__":
    gui()
