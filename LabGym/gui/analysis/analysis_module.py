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

from .analyze_behaviors import WindowLv2_AnalyzeBehaviors
from .mine_results import WindowLv2_MineResults


class AnalysisModule(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Analysis Module", size=(500, 220))
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        boxsizer.Add(0, 40, 0)

        button_analyzebehaviors = wx.Button(
            panel, label="Analyze Behaviors", size=(300, 40)
        )
        button_analyzebehaviors.Bind(wx.EVT_BUTTON, self.analyze_behaviors)
        wx.Button.SetToolTip(
            button_analyzebehaviors,
            "Automatically track animals / objects of your interest, identify and quantify their behaviors in videos.",
        )
        boxsizer.Add(button_analyzebehaviors, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 20, 0)

        button_mineresults = wx.Button(panel, label="Mine Results", size=(300, 40))
        button_mineresults.Bind(wx.EVT_BUTTON, self.mine_results)
        wx.Button.SetToolTip(
            button_mineresults,
            "Automatically mine the analysis results to display the data details that show statistically significant differences among groups of your selection.",
        )
        boxsizer.Add(button_mineresults, 0, wx.ALIGN_CENTER, 10)
        boxsizer.Add(0, 30, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def analyze_behaviors(self, event):
        WindowLv2_AnalyzeBehaviors("Analyze Behaviors")

    def mine_results(self, event):
        WindowLv2_MineResults("Mine Results")
