'''
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
'''


'''GUI utils module for LabGym.
This module provides additional utility functions for the LabGym GUI. Currently, it contains a function to add a new page or select existing page if it already exists.
'''

import wx
import wx.lib.buttons as wxbuttons

# Section colour constants — match the workflow-map fill colours
INFO_COLOUR_S1   = wx.Colour(255, 210, 210)  # light red    — 1. Video Prep
INFO_COLOUR_S2   = wx.Colour(210, 228, 255)  # light blue   — 2. Tracking
INFO_COLOUR_S3   = wx.Colour(255, 228, 195)  # light orange — 3. Classification
INFO_COLOUR_GREY = wx.Colour(220, 220, 220)  # light grey   — Post-classification


def add_info_button(panel, boxsizer, colour):
	"""Insert a coloured 'i' button at the top-right of a panel's vertical sizer.

	Clicking the button switches the main notebook to the Workflow Map tab (index 1).
	Use one of INFO_COLOUR_S1/S2/S3/GREY as the colour argument.
	"""
	bar = wx.BoxSizer(wx.HORIZONTAL)
	bar.AddStretchSpacer()
	btn = wxbuttons.GenButton(panel, label='i', size=(28, 28))
	btn.SetBackgroundColour(colour)
	btn.SetForegroundColour(wx.Colour(60, 60, 60))
	btn.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD))
	btn.SetToolTip('View Workflow Map')
	bar.Add(btn, 0, wx.RIGHT | wx.TOP, 6)
	boxsizer.Add(bar, 0, wx.EXPAND)

	def _go_to_workflow(evt):
		frame = wx.GetTopLevelParent(panel)
		if hasattr(frame, 'notebook'):
			frame.notebook.SetSelection(1)

	btn.Bind(wx.EVT_BUTTON, _go_to_workflow)


def add_or_select_notebook_page(notebook, panel_factory, title):
	"""Helper function to add a new page or select existing page if it already exists.

	Args:
		notebook: The notebook widget
		panel_factory: A function that creates the panel (to avoid creating unnecessary panels)
		title: The title of the page to check for
	"""
	# Special case: Don't allow replacing the Home tab
	if title == 'Home':
		# Just select the Home tab if it exists
		for i in range(notebook.GetPageCount()):
			if notebook.GetPageText(i) == 'Home':
				notebook.SetSelection(i)
				return

	# Checks if a page with this title already exists
	for i in range(notebook.GetPageCount()):
		if notebook.GetPageText(i) == title:
			# Page exists, select it instead of creating a new one
			notebook.SetSelection(i)
			return

	# Page doesn't exist, create and add it
	panel = panel_factory()	# panel factory, as opposed to an actual panel

	# panel factory: instead of directlycreating panels themselves, panel factories (lambda functions) are created and only create GUI panels when needed.


	notebook.AddPage(panel, title, select=True)
