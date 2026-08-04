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
import wx.lib.agw.hyperlink as hl
import wx.lib.buttons as wxbuttons

from .gui_appearance import select_for_appearance

# Section colour constants — match the workflow-map fill colours
INFO_COLOUR_S1   = wx.Colour(255, 210, 210)  # light red    — 1. Video Prep
INFO_COLOUR_S2   = wx.Colour(210, 228, 255)  # light blue   — 2. Tracking
INFO_COLOUR_S3   = wx.Colour(255, 228, 195)  # light orange  — 3. Classification
INFO_COLOUR_S4   = wx.Colour(235, 215, 255)  # light lavender — 4. Post-Classification Analysis
INFO_COLOUR_GREY = wx.Colour(220, 220, 220)  # light grey    — fallback

# Shared cyan/teal hyperlink family for all LabGym GUI links (AGW + HTML).
# Normal and visited are identical so AGW and browsers never show purple.
_LINK_LIGHT_NORMAL    = wx.Colour(0, 140, 158)    # darker cyan/teal on light surfaces
_LINK_DARK_NORMAL     = wx.Colour(70, 230, 240)   # brighter cyan on dark surfaces
_LINK_LIGHT_ROLLOVER  = wx.Colour(0, 175, 195)    # lighter cyan (same family)
_LINK_DARK_ROLLOVER   = wx.Colour(140, 245, 255)  # brighter cyan (same family)


def _colour_to_hex(colour) -> str:
	"""Format a wx.Colour as #RRGGBB for HTML/CSS."""
	return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())


def hyperlink_colours():
	"""Return (normal, visited, rollover) wx.Colour for the current appearance.

	Visited is always identical to normal.
	"""
	normal = select_for_appearance(_LINK_LIGHT_NORMAL, _LINK_DARK_NORMAL)
	rollover = select_for_appearance(_LINK_LIGHT_ROLLOVER, _LINK_DARK_ROLLOVER)
	return normal, normal, rollover


def hyperlink_html_style():
	"""Return (link_hex, visited_hex, hover_hex) for HTML anchors.

	Uses the same cyan family as AGW HyperLinkCtrl. Visited matches normal.
	"""
	normal, visited, rollover = hyperlink_colours()
	return (
		_colour_to_hex(normal),
		_colour_to_hex(visited),
		_colour_to_hex(rollover),
	)


def style_hyperlink(link):
	"""Apply the shared cyan appearance-aware style to an AGW HyperLinkCtrl.

	Sets normal/visited/rollover colours, enables rollover, refreshes the link,
	and binds a light restyle when the OS system colours change (if supported).
	Preserves URL and browser-opening behaviour.
	"""
	if link is None:
		return link

	def _apply(_event=None):
		try:
			if not link:  # destroyed
				return
			normal, visited, rollover = hyperlink_colours()
			link.SetColours(link=normal, visited=visited, rollover=rollover)
			link.EnableRollover(True)
			try:
				# Keep internal visited flag from forcing a purple brand; colours already match.
				link.SetVisited(False)
			except Exception:
				pass
			link.UpdateLink(True)
		except RuntimeError:
			# Window may already be destroyed.
			pass

	_apply()

	if not getattr(link, '_labgym_hyperlink_styled', False):
		link._labgym_hyperlink_styled = True
		if hasattr(wx, 'EVT_SYS_COLOUR_CHANGED'):
			link.Bind(wx.EVT_SYS_COLOUR_CHANGED, lambda evt: (_apply(), evt.Skip()))
		# Some platforms update appearance on reactivation.
		frame = wx.GetTopLevelParent(link)
		if frame is not None:
			def _on_activate(evt):
				if evt.GetActive():
					_apply()
				evt.Skip()
			frame.Bind(wx.EVT_ACTIVATE, _on_activate)

	return link


def create_hyperlink(parent, label, url):
	"""Create an AGW HyperLinkCtrl with LabGym's shared cyan link style."""
	link = hl.HyperLinkCtrl(parent, -1, label, URL=url)
	return style_hyperlink(link)


# Backwards-compatible alias for earlier tutorial-only helper name.
create_tutorial_hyperlink = create_hyperlink


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
	btn.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
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
