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

from .analyze_behaviors import AnalyzeBehaviors
from .mine_results import MineResults
from ..utils import LabGymWindow


class AnalysisModule(LabGymWindow):
    def __init__(self):
        super().__init__(title="Analysis Module", size=(500, 220))
        
        self.add_submit_button(
            label="Analyze Behaviors",
            handler=self.analyze_behaviors,
            tool_tip="Automatically track animals / objects of your interest, identify and quantify their behaviors in videos."
        )
        
        self.add_submit_button(
            label="Mine Results",
            handler=self.mine_results,
            tool_tip="Automatically mine the analysis results to display the data details that show statistically significant differences among groups of your selection."
        )

        self.display_window()

    def analyze_behaviors(self, event):
        AnalyzeBehaviors()

    def mine_results(self, event):
        MineResults()
