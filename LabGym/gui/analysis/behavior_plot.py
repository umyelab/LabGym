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

from pathlib import Path
from typing import Tuple

import wx
from matplotlib.colors import cnames

from LabGym.gui.analysis.analyze_behaviors import ColorPicker
from LabGym.gui.utils import LabGymWindow
from LabGym.tools import get_behaviors_from_all_events, parse_all_events_file, plot_events


class BehaviorPlot(LabGymWindow):
    """A window that allows the user to generate a behavior plot.

    Attributes:
        event_probability:
            A dictionary with the keys as with the keys as the ID of each
            animal and the values are lists of lists, where each sub-list
            has a length of 2 and is in one of the following formats:
                - ["NA", -1], indicating the animal wasn't detected during
                  this time point.
                - [behavior, probability], where behavior is the name of
                  the behavior and probability is a float between 0 and 1.
        time_points:
            A list of floats containing the time points for each behavior
            for each animal, which is in the leftmost column in the original
            file.
        results_folder:
            The Path to the folder in which to store the behavior plot.
        names_and_colors:
            A dictionary with keys as behavior names and values as lists
            or tuples containing two strings, where the first string is
            '#ffffff' and the second string is the hex color code of the
            color corresponding to the behavior.
        figsize:
            A tuple (width, height) containing the size of the plot in inches.
    """

    def __init__(self):
        super().__init__(title="Generate Behavior Plot", size=(1000, 230))
        self.events_probability: dict | None = None
        self.time_points: list[float] | None = None
        self.results_folder: Path | None = None
        self.names_and_colors: dict[str, Tuple[str, str]] | None = None
        self.figsize: Tuple[int, int] | None = None

        self.text_all_events_file = self.module_text("None.")
        self.add_module(
            button_label="Select the\nall_events.xlsx file",
            button_handler=self.select_all_events_file,
            tool_tip="",
            text=self.text_all_events_file,
        )

        self.text_results_folder = self.module_text("None.")
        self.add_module(
            button_label="Select folder to store\nbehavior plot",
            button_handler=self.select_results_folder,
            tool_tip="",
            text=self.text_results_folder,
        )

        self.text_colors = self.module_text("None.")
        self.add_module(
            button_label="Select colors\nfor each behavior",
            button_handler=self.select_colors,
            tool_tip="",
            text=self.text_colors,
        )

        self.add_submit_button(
            "Generate Behavior Plot",
            self.generate_behavior_plot,
            "",
        )

        self.display_window()

    def select_all_events_file(self, event):
        """Select the all_events.xlsx file."""
        dialog = wx.FileDialog(
            self,
            "Select the all_events.xlsx file.",
            "",
            wildcard="all_events file (*.xlsx)|*.xlsx",
            style=wx.FD_OPEN,
        )
        if dialog.ShowModal() == wx.ID_OK:
            all_events_file = Path(dialog.GetPath())
            self.events_probability, self.time_points = parse_all_events_file(all_events_file)
            self.text_all_events_file.SetLabel(f"all_events.xlsx path: {all_events_file}")
        dialog.Destroy()

    def select_results_folder(self, event):
        """Select the folder to store the behavior plot."""
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.results_folder = Path(dialog.GetPath())
            self.text_results_folder.SetLabel(f"Results folder: {self.results_folder}")
        dialog.Destroy()

    def select_colors(self, event):
        """Select the color for each behavior."""
        if self.events_probability is None:
            wx.MessageBox(
                "No all_events.xlsx file selected!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        behaviors = get_behaviors_from_all_events(self.events_probability)

        # Get a list of hex codes of decent looking colors from matplotlib.
        # The reason #ffffff is here is for plot_events to create a gradient
        # from pure white to the color the user selects to represent the
        # probability.
        # TODO: Move the logic of creating the gradient into plot_events()
        colors = [("#ffffff", str(hex_code)) for hex_code in cnames.values()]

        self.names_and_colors = {}
        for color, behavior in zip(colors, behaviors):
            dialog = ColorPicker(f"Color for {behavior}", color[1])
            if dialog.ShowModal() == wx.ID_OK:
                (r, g, b, _) = dialog.color_picker.GetColour()
                hex_code = f"#{r:02x}{g:02x}{b:02x}"
                self.names_and_colors[behavior] = ("#ffffff", hex_code)
            else:
                self.names_and_colors[behavior] = color

        self.text_colors.SetLabel(
            "Colors: " + ", ".join([f"{behavior}: {color}" for behavior, (_, color) in self.names_and_colors.items()])
        )

    def generate_behavior_plot(self, event):
        """Generate the behavior plot with the given parameters."""
        if self.events_probability is None or self.time_points is None:
            wx.MessageBox(
                "No all_events.xlsx file selected!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return
        if self.results_folder is None:
            wx.MessageBox(
                "No results folder selected!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return
        if self.names_and_colors is None:
            wx.MessageBox(
                "No behavior colors selected!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        plot_events(
            str(self.results_folder),
            self.events_probability,
            self.time_points,
            self.names_and_colors,
            list(self.names_and_colors.keys()),
        )
