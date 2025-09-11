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
