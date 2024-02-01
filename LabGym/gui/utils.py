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

from typing import Callable, Tuple

import wx


WX_VIDEO_WILDCARD = "Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov"
WX_IMAGE_WILDCARD = "Image files(*.jpg;*.jpeg;*.png;*.tiff;*.bmp)|*.jpg;*.JPG;*.jpeg;*.JPEG;*.png;*.PNG;*.tiff;*.TIFF;*.bmp;*.BMP"


class LabGymWindow(wx.Frame):
    """A base class for LabGym windows.

    LabGym windows currently contain a list of buttons with StaticText to their
    right, indicating the current configuration state, as well as a submit
    button at the bottom to run the function with the user-supplied
    configuration (see the LabGym GitHub for an example).

    A combination of a Button and StaticText is called a "module", and new
    modules can be added easily using the `add_module()` method. Since each
    StaticText needs to be updated as the program state changes, use the
    `module_text()` method to create a StaticText instance with the given
    initial text.

    Attributes:
        panel: A panel to contain everything.
        boxsizer: A vertically-oriented BoxSizer in which the modules are
            placed.
    """

    MODULE_TOP_MARGIN = 10
    BOTTOM_MARGIN = 5

    def __init__(self, title: str, size: Tuple[int, int]):
        super().__init__(parent=None, title=title, size=size)
        self.panel = wx.Panel(self)
        self.boxsizer = wx.BoxSizer(wx.VERTICAL)

    def add_module(
        self,
        button_label: str,
        button_handler: Callable,
        tool_tip: str,
        text: wx.StaticText,
    ):
        """Add a button and text box to the main sizer.

        Args:
            button_label: The button label.
            button_handler: The function to handle the button press.
            tool_tip: The text displayed when the user hovers over the button.
            text: The wx.StaticText to be displayed next to the button.
        """
        module = wx.BoxSizer(wx.HORIZONTAL)
        button = wx.Button(self.panel, label=button_label, size=(300, 40))
        button.Bind(wx.EVT_BUTTON, button_handler)
        wx.Button.SetToolTip(button, tool_tip)
        module.Add(button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module.Add(text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        self.boxsizer.Add(0, self.MODULE_TOP_MARGIN, 0)
        self.boxsizer.Add(module, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

    def module_text(self, label: str) -> wx.StaticText:
        """Return a wx.StaticText instance with the given label."""
        return wx.StaticText(
            self.panel, label=label, style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )

    def add_submit_button(self, label: str, handler: Callable, tool_tip: str):
        """Add a submit button.

        Args:
            label: The button label.
            handler: The function to handle the button press.
            tool_tip: The text displayed when the user hovers over the button.
        """
        button = wx.Button(self.panel, label=label, size=(300, 40))
        button.Bind(wx.EVT_BUTTON, handler)
        wx.Button.SetToolTip(button, tool_tip)
        self.boxsizer.Add(0, self.MODULE_TOP_MARGIN, 0)
        self.boxsizer.Add(button, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        self.boxsizer.Add(0, self.BOTTOM_MARGIN, 0)

    def display_window(self):
        """Display the window to the user.

        Call this method AFTER adding all elements.
        """
        self.panel.SetSizer(self.boxsizer)
        self.Center()
        self.Show()


class BehaviorMode:
    NON_INTERACTIVE = 0
    INTERACT_BASIC = 1
    INTERACT_ADVANCED = 2
    STATIC_IMAGES = 3
