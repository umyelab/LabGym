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

import os

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


def behavior_label_from_filename(filename):
	"""Return the prepared-example category label matching categorizer training.

	LabGym training takes the final underscore-delimited segment of the stem.
	Filenames without an underscore yield None and are ignored by counting.
	"""
	base = os.path.splitext(os.path.basename(filename))[0]
	if '_' not in base:
		return None
	return base.split('_')[-1]


def _list_media_for_counts(entries):
	"""Prefer AVI listings in a directory; otherwise use JPG listings."""
	avis = [f for f in entries if f.endswith('.avi')]
	if avis:
		return avis
	return [f for f in entries if f.endswith('.jpg')]


def _count_prepared_files_in_dir(dir_path):
	"""Count prepared examples in a single flat directory (no recursion)."""
	try:
		entries = os.listdir(dir_path)
	except OSError:
		return {}
	counts = {}
	for f in _list_media_for_counts(entries):
		label = behavior_label_from_filename(f)
		if label is None:
			continue
		counts[label] = counts.get(label, 0) + 1
	return counts


def count_prepared_examples(folder_path):
	"""Count prepared training examples by behavior label.

	Supports:
	- flat prepared folders (files directly under folder_path); or
	- onfly layout with train/ plus validation/ (or counting-only vadilation/).

	Split mode is used only when train/ and either validation/ or vadilation/
	exist; counts are summed across recognized split directories (not recursive
	below those directories). Incomplete split layouts fall back to flat-root scan.
	"""
	if not folder_path:
		return {}
	try:
		os.listdir(folder_path)
	except OSError:
		return {}

	train_path = os.path.join(folder_path, 'train')
	validation_path = os.path.join(folder_path, 'validation')
	vadilation_path = os.path.join(folder_path, 'vadilation')
	has_train = os.path.isdir(train_path)
	has_validation = os.path.isdir(validation_path)
	has_vadilation = os.path.isdir(vadilation_path)

	if has_train and (has_validation or has_vadilation):
		counts = {}
		for path in (train_path, validation_path, vadilation_path):
			if not os.path.isdir(path):
				continue
			for label, n in _count_prepared_files_in_dir(path).items():
				counts[label] = counts.get(label, 0) + n
		return counts

	return _count_prepared_files_in_dir(folder_path)


def count_sorted_examples(folder_path):
	"""Count sorted behavior examples per immediate behavior subfolder name.

	AVI-over-JPG precedence applies independently within each subfolder.
	Empty behavior subfolders are included with count 0.
	"""
	if not folder_path:
		return {}
	try:
		names = os.listdir(folder_path)
	except OSError:
		return {}
	counts = {}
	for name in names:
		path = os.path.join(folder_path, name)
		if not os.path.isdir(path):
			continue
		try:
			entries = os.listdir(path)
		except OSError:
			counts[name] = 0
			continue
		counts[name] = len(_list_media_for_counts(entries))
	return counts


def counts_enable_diagnostics(counts):
	"""True when at least one category has one or more counted examples."""
	return any(n > 0 for n in counts.values()) if counts else False


def compute_workflow_map_transform(
		client_w, client_h, vw=2200, vh=660,
		fallback_w=1100, fallback_h=560):
	"""Compute (client_w, client_h, scale, ox, oy) for the Workflow Map layout.

	Tiny or invalid client dimensions fall back to nominal sizes so drawing and
	hit tests remain well-defined during early layout passes.
	"""
	try:
		cw, ch = int(client_w), int(client_h)
	except Exception:
		cw, ch = 0, 0
	if cw < 1 or ch < 1:
		cw, ch = fallback_w, fallback_h
	scale = min(cw / vw, ch / vh)
	if scale <= 0:
		scale = min(fallback_w / vw, fallback_h / vh)
	ox = (cw - vw * scale) / 2
	oy = (ch - vh * scale) / 2
	return cw, ch, scale, ox, oy


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


def select_notebook_page(notebook, page) -> bool:
	"""Select a notebook page by stored page-object identity (not index or title).

	Returns True if the page was found and selected.
	"""
	if notebook is None or page is None:
		return False
	for i in range(notebook.GetPageCount()):
		if notebook.GetPage(i) is page:
			notebook.SetSelection(i)
			return True
	return False


def is_protected_notebook_page(page, protected_pages) -> bool:
	"""Return True when page is one of the protected main-frame page objects."""
	if page is None:
		return False
	for protected in protected_pages:
		if protected is not None and page is protected:
			return True
	return False


def add_info_button(panel, boxsizer, colour):
	"""Insert a coloured 'i' button at the top-right of a panel's vertical sizer.

	Clicking the button selects the main frame's stored Workflow Map page object
	(``frame.workflow_map_page``) regardless of its notebook index or displayed title.
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
		notebook = getattr(frame, 'notebook', None)
		workflow_page = getattr(frame, 'workflow_map_page', None)
		select_notebook_page(notebook, workflow_page)

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
