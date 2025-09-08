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


# Standard library imports.
# import json
import logging
from pathlib import Path
import sys
from importlib.resources import files

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger =  logging.getLogger(__name__)  # pylint: disable=wrong-import-position
logger.debug('loading %s', __file__)  # pylint: disable=wrong-import-position

# Related third party imports.
import wx
import wx.aui
import wx.lib.agw.hyperlink as hl

# Local application/library specific imports.
from LabGym import __version__
logger.debug('importing %s ...', '.gui_categorizer')
from .gui_categorizer import PanelLv2_GenerateExamples,PanelLv2_TrainCategorizers,PanelLv2_SortBehaviors,PanelLv2_TestCategorizers
logger.debug('importing %s done', '.gui_categorizer')
from .gui_detector import PanelLv2_GenerateImages,PanelLv2_TrainDetectors,PanelLv2_TestDetectors
from .gui_preprocessor import PanelLv2_ProcessVideos,PanelLv2_DrawMarkers
from .gui_analyzer import PanelLv2_AnalyzeBehaviors,PanelLv2_MineResults,PanelLv2_PlotBehaviors,PanelLv2_CalculateDistances


def _icon_relpath(use_fallback=False) -> str:
	# Prefer .ico on Windows; otherwise, use PNG
	if sys.platform.startswith("win"):
		if use_fallback:
			# Use fallback ICO for small icon sizes (like taskbar)
			fallback_ico = files("LabGym") / "assets/icons/fallback.ico"
			if fallback_ico.is_file():
				return "assets/icons/fallback.ico"
		else:
			# Use main ICO for normal window icons
			ico = files("LabGym") / "assets/icons/labgym.ico"
			if ico.is_file():
				return "assets/icons/labgym.ico"

	# default to PNG (works on all)
	return "assets/icons/labgym.png"


def _set_frame_icon(frame) -> None:
	# Sets the window/titlebar icon on all OSes via wx
	# Use fallback ICO on Windows for better small-size display in title bar
	try:
		import wx
		# On Windows, use fallback ICO for title bar (small size context)
		# On other platforms, use main icon
		use_fallback = sys.platform.startswith("win")
		icon_rel = _icon_relpath(use_fallback=use_fallback)
		icon_file = files("LabGym") / icon_rel
		if icon_file.is_file():
			# Create wx.Icon with explicit size for better Windows compatibility
			icon = wx.Icon(str(icon_file), wx.BITMAP_TYPE_ANY)
			if icon.IsOk():
				frame.SetIcon(icon)
				logger.info("Set frame icon using %s: %s", 
					"fallback ICO" if use_fallback else "main icon", icon_file)
			else:
				logger.warning("Failed to create valid wx.Icon from %s", icon_file)
		else:
			logger.warning("Icon file not found: %s", icon_file)
	except Exception as e:
		logger.warning("Failed to set frame icon: %r", e)
		pass # non-fatal error, fails gracefully


def _set_windows_small_icon(frame) -> None:
	# Specifically sets a small icon for Windows title bar using fallback ICO
	if not sys.platform.startswith("win"):
		return
	try:
		import wx
		# Use fallback ICO which should have better small-size optimization
		fallback_ico = files("LabGym") / "assets/icons/fallback.ico"
		if fallback_ico.is_file():
			# Try to create icon with specific size (16x16 for title bar)
			icon = wx.Icon(str(fallback_ico), wx.BITMAP_TYPE_ICO, 16, 16)
			if not icon.IsOk():
				# Fallback to any size from the ICO
				icon = wx.Icon(str(fallback_ico), wx.BITMAP_TYPE_ANY)
			
			if icon.IsOk():
				frame.SetIcon(icon)
				logger.info("Set Windows title bar icon using fallback ICO (16x16): %s", fallback_ico)
			else:
				logger.warning("Failed to create valid wx.Icon from fallback ICO: %s", fallback_ico)
		else:
			logger.warning("Fallback ICO file not found: %s", fallback_ico)
	except Exception as e:
		logger.warning("Failed to set Windows small icon: %r", e)
		pass # Non-fatal error, fails gracefully


def _set_windows_taskbar_icon_with_fallback() -> None:
	# Sets the Windows taskbar icon using fallback ICO for better small-size visibility
	if not sys.platform.startswith("win"):
		return
	try:
		import ctypes
		import wx
		
		# Set AppUserModelID first - this is crucial for proper taskbar icon association
		app_id = "umyelab.LabGym.1.0"
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
		logger.info("Set Windows AppUserModelID to: %s", app_id)
		
		# Force use of fallback ICO for taskbar (small size context)
		icon_rel = _icon_relpath(use_fallback=True)
		icon_file = files("LabGym") / icon_rel
		if icon_file.is_file():
			# Create wx.Icon from fallback ICO
			icon = wx.Icon(str(icon_file), wx.BITMAP_TYPE_ANY)
			if icon.IsOk():
				# Get the main app instance and set its icon
				app = wx.GetApp()
				if app:
					app.SetAppDisplayName("LabGym")
					# Note: wxPython doesn't have a direct way to set taskbar icon
					# The AppUserModelID above should help Windows associate the correct icon
					logger.info("Using fallback ICO for taskbar (optimized for small sizes): %s", icon_file)
			else:
				logger.warning("Failed to create valid wx.Icon from fallback ICO: %s", icon_file)
		else:
			logger.warning("Fallback ICO file not found: %s", icon_file)
			
	except Exception as e:
		logger.warning("Failed to set Windows taskbar icon with fallback: %r", e)
		pass # Non-fatal error, fails gracefully


def _get_icon_for_size(icon_size=16) -> str:
	# Returns the appropriate icon file based on the requested size
	# For small sizes (<= 24px), use fallback ICO; for larger sizes, use main ICO
	if sys.platform.startswith("win"):
		if icon_size <= 24:
			# Use fallback ICO for small sizes (taskbar, window controls, etc.)
			fallback_ico = files("LabGym") / "assets/icons/fallback.ico"
			if fallback_ico.is_file():
				return str(fallback_ico)
		else:
			# Use main ICO for larger sizes (window title bar, etc.)
			main_ico = files("LabGym") / "assets/icons/labgym.ico"
			if main_ico.is_file():
				return str(main_ico)
	
	# Default to PNG for non-Windows or if ICO files not found
	png_file = files("LabGym") / "assets/icons/labgym.png"
	return str(png_file) if png_file.is_file() else ""


def _set_macos_dock_icon() -> None:
	# Sets the Dock title icon at runtime on macOS (use of optional PyObjC)
	if sys.platform != "darwin":
		return
	try:
		from AppKit import NSApplication, NSImage
		baseIconDir = files("LabGym")
		icns = baseIconDir / "assets/icons/labgym.icns"
		png = baseIconDir / "assets/icons/labgym.png"

		icon_path = str(icns if icns.is_file() else png)
		img = NSImage.alloc().initWithContentsOfFile_(icon_path)
		if img:
			NSApplication.sharedApplication().setApplicationIconImage_(img)
		else:
			logger.warning("NSImage failed to load dock icon from %s", icon_path)
	except Exception as e:
		logger.warning("Dock icon set failed: %r", e)
		pass # PyObjC missing, not compatble with PyObjC, etc.


class InitialPanel(wx.Panel):

	'''
	The main window of LabGym
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		self.text_welcome=wx.StaticText(panel,label='Welcome to LabGym!',style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(0,60,0)
		boxsizer.Add(self.text_welcome,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,60,0)
		self.text_developers=wx.StaticText(panel,
			label='Created by Yujia Hu and Bing Ye\n\nLife Sciences Institute, University of Michigan\n\n\n\nContributor list:\n\nJie Zhou, Rohan Satapathy, John Ruckstuhl, Brendon O. Waston, Carrie R. Ferrario,\n\nKelly Goss, Isabelle Baker, M. Victor Struman, Bobby Tomlinson',style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(self.text_developers,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,60,0)

		links=wx.BoxSizer(wx.HORIZONTAL)
		homepage=hl.HyperLinkCtrl(panel,0,'Home Page',URL='https://github.com/umyelab/LabGym')
		userguide=hl.HyperLinkCtrl(panel,0,'Extended Guide',URL='https://github.com/yujiahu415/LabGym/blob/master/LabGym_extended_user_guide.pdf')
		links.Add(homepage,0,wx.LEFT|wx.EXPAND,10)
		links.Add(userguide,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(links,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		module_modules=wx.BoxSizer(wx.HORIZONTAL)
		button_preprocess=wx.Button(panel,label='Preprocessing Module',size=(200,40))
		button_preprocess.Bind(wx.EVT_BUTTON,self.window_preprocess)
		wx.Button.SetToolTip(button_preprocess,'Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.')
		button_train=wx.Button(panel,label='Training Module',size=(200,40))
		button_train.Bind(wx.EVT_BUTTON,self.window_train)
		wx.Button.SetToolTip(button_train,'Teach LabGym to recognize the animals / objects of your interest and identify their behaviors that are defined by you.')
		button_analyze=wx.Button(panel,label='Analysis Module',size=(200,40))
		button_analyze.Bind(wx.EVT_BUTTON,self.window_analyze)
		wx.Button.SetToolTip(button_analyze,'Use LabGym to track the animals / objects of your interest, identify and quantify their behaviors, and display the statistically significant findings.')
		module_modules.Add(button_preprocess,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_modules.Add(button_train,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_modules.Add(button_analyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_modules,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def window_preprocess(self,event):

		panel = PanelLv1_ProcessModule(self.notebook)
		title = 'Preprocessing Module'
		self.notebook.AddPage(panel, title, select=True)


	def window_train(self,event):

		panel = PanelLv1_TrainingModule(self.notebook)
		title = 'Training Module'
		self.notebook.AddPage(panel, title, select=True)


	def window_analyze(self,event):

		panel = PanelLv1_AnalysisModule(self.notebook)
		title = 'Analysis Module'
		self.notebook.AddPage(panel, title, select=True)



class PanelLv1_ProcessModule(wx.Panel):

	'''
	The Preprocessing Module
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,40,0)

		button_processvideos=wx.Button(panel,label='Preprocess Videos',size=(300,40))
		button_processvideos.Bind(wx.EVT_BUTTON,self.process_videos)
		wx.Button.SetToolTip(button_processvideos,'Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.')
		boxsizer.Add(button_processvideos,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_drawmarkers=wx.Button(panel,label='Draw Markers',size=(300,40))
		button_drawmarkers.Bind(wx.EVT_BUTTON,self.draw_markers)
		wx.Button.SetToolTip(button_drawmarkers,'Draw locational markers in videos.')
		boxsizer.Add(button_drawmarkers,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def process_videos(self,event):

		panel = PanelLv2_ProcessVideos(self.notebook)
		title = 'Preprocess Videos'
		self.notebook.AddPage(panel, title, select=True)


	def draw_markers(self,event):

		panel = PanelLv2_DrawMarkers(self.notebook)
		title = 'Draw Markers'
		self.notebook.AddPage(panel, title, select=True)


class PanelLv1_TrainingModule(wx.Panel):

	'''
	The Training Module
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,60,0)

		button_generateimages=wx.Button(panel,label='Generate Image Examples',size=(300,40))
		button_generateimages.Bind(wx.EVT_BUTTON,self.generate_images)
		wx.Button.SetToolTip(button_generateimages,'Extract frames from videos for annotating animals / objects in them so that they can be used to train a Detector to detect animals / objects of your interest. See Extended Guide for how to select images to annotate.')
		boxsizer.Add(button_generateimages,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		link_annotate=wx.lib.agw.hyperlink.HyperLinkCtrl(panel,0,'\nAnnotate images with EZannot\n',URL='https://github.com/yujiahu415/EZannot')
		boxsizer.Add(link_annotate,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_traindetectors=wx.Button(panel,label='Train Detectors',size=(300,40))
		button_traindetectors.Bind(wx.EVT_BUTTON,self.train_detectors)
		wx.Button.SetToolTip(button_traindetectors,'There are two detection methods in LabGym, the Detector-based method is more versatile (useful in any recording conditions and complex interactive behaviors) but slower than the other background subtraction-based method (requires static background and stable illumination in videos).')
		boxsizer.Add(button_traindetectors,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_testdetectors=wx.Button(panel,label='Test Detectors',size=(300,40))
		button_testdetectors.Bind(wx.EVT_BUTTON,self.test_detectors)
		wx.Button.SetToolTip(button_testdetectors,'Test trained Detectors on the annotated ground-truth image dataset (similar to the image dataset used for training a Detector).')
		boxsizer.Add(button_testdetectors,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,50,0)

		button_generatebehaviorexamples=wx.Button(panel,label='Generate Behavior Examples',size=(300,40))
		button_generatebehaviorexamples.Bind(wx.EVT_BUTTON,self.generate_behaviorexamples)
		wx.Button.SetToolTip(button_generatebehaviorexamples,'Generate behavior examples for sorting them so that they can be used to teach a Categorizer to recognize behaviors defined by you.')
		boxsizer.Add(button_generatebehaviorexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_sortbehaviorexamples=wx.Button(panel,label='Sort Behavior Examples',size=(300,40))
		button_sortbehaviorexamples.Bind(wx.EVT_BUTTON,self.sort_behaviorexamples)
		wx.Button.SetToolTip(button_sortbehaviorexamples,'Set shortcut keys for behavior categories to help sorting the behavior examples in an easier way. See Extended Guide for how to select and sort the behavior examples.')
		boxsizer.Add(button_sortbehaviorexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_traincategorizers=wx.Button(panel,label='Train Categorizers',size=(300,40))
		button_traincategorizers.Bind(wx.EVT_BUTTON,self.train_categorizers)
		wx.Button.SetToolTip(button_traincategorizers,'Customize a Categorizer and use the sorted behavior examples to train it so that it can recognize the behaviors of your interest during analysis.')
		boxsizer.Add(button_traincategorizers,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_testcategorizers=wx.Button(panel,label='Test Categorizers',size=(300,40))
		button_testcategorizers.Bind(wx.EVT_BUTTON,self.test_categorizers)
		wx.Button.SetToolTip(button_testcategorizers,'Test trained Categorizers on the sorted ground-truth behavior examples (similar to the behavior examples used for training a Categorizer).')
		boxsizer.Add(button_testcategorizers,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,50,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def generate_images(self,event):

		panel = PanelLv2_GenerateImages(self.notebook)
		title = 'Generate Image Examples'
		self.notebook.AddPage(panel, title, select=True)


	def train_detectors(self,event):

		panel = PanelLv2_TrainDetectors(self.notebook)
		title = 'Train Detectors'
		self.notebook.AddPage(panel, title, select=True)


	def test_detectors(self,event):

		panel = PanelLv2_TestDetectors(self.notebook)
		title = 'Test Detectors'
		self.notebook.AddPage(panel, title, select=True)


	def generate_behaviorexamples(self,event):

		panel = PanelLv2_GenerateExamples(self.notebook)
		title = 'Generate Behavior Examples'
		self.notebook.AddPage(panel, title, select=True)


	def sort_behaviorexamples(self,event):

		panel = PanelLv2_SortBehaviors(self.notebook)
		title = 'Sort Behavior Examples'
		self.notebook.AddPage(panel, title, select=True)


	def train_categorizers(self,event):

		panel = PanelLv2_TrainCategorizers(self.notebook)
		title = 'Train Categorizers'
		self.notebook.AddPage(panel, title, select=True)


	def test_categorizers(self,event):

		panel = PanelLv2_TestCategorizers(self.notebook)
		title = 'Test Categorizers'
		self.notebook.AddPage(panel, title, select=True)



class PanelLv1_AnalysisModule(wx.Panel):

	'''
	The Analysis Module
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,40,0)

		button_analyzebehaviors=wx.Button(panel,label='Analyze Behaviors',size=(300,40))
		button_analyzebehaviors.Bind(wx.EVT_BUTTON,self.analyze_behaviors)
		wx.Button.SetToolTip(button_analyzebehaviors,'Automatically track animals / objects of your interest, identify and quantify their behaviors in videos.')
		boxsizer.Add(button_analyzebehaviors,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_mineresults=wx.Button(panel,label='Mine Results',size=(300,40))
		button_mineresults.Bind(wx.EVT_BUTTON,self.mine_results)
		wx.Button.SetToolTip(button_mineresults,'Automatically mine the analysis results to display the data details that show statistically significant differences among groups of your selection.')
		boxsizer.Add(button_mineresults,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_rasterplot=wx.Button(panel,label='Generate Behavior Plot',size=(300,40))
		button_rasterplot.Bind(wx.EVT_BUTTON,self.plot_behavior)
		wx.Button.SetToolTip(button_rasterplot,'Generate a behavior plot given an all_events.xlsx file.')
		boxsizer.Add(button_rasterplot,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_calculatedistances=wx.Button(panel,label='Calculate Distances',size=(300,40))
		button_calculatedistances.Bind(wx.EVT_BUTTON,self.calculate_distances)
		wx.Button.SetToolTip(button_calculatedistances,'Using LabGym analysis results to calculate: 1. The shortest distances among the locations where animals perform the selected behaviors for the first time, in chronological order. 2. The total traveling distances of the actual route the animals.')
		boxsizer.Add(button_calculatedistances,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def analyze_behaviors(self,event):

		panel = PanelLv2_AnalyzeBehaviors(self.notebook)
		title = 'Analyze Behaviors'
		self.notebook.AddPage(panel, title, select=True)


	def mine_results(self,event):

		panel = PanelLv2_MineResults(self.notebook)
		title = 'Mine Results'
		self.notebook.AddPage(panel, title, select=True)


	def plot_behavior(self,event):

		panel = PanelLv2_PlotBehaviors(self.notebook)
		title = 'Generate Behavior Plot'
		self.notebook.AddPage(panel, title, select=True)


	def calculate_distances(self,event):

		panel = PanelLv2_CalculateDistances(self.notebook)
		title = 'Calculate Distances'
		self.notebook.AddPage(panel, title, select=True)



class MainFrame(wx.Frame):
	"""Main frame and its notebook.

	(The MainFrame obj is the) main frame and its notebook.
	The notebook is initialized with one panel, the Welcome panel.
	"""

	def __init__(self):
		super().__init__(None, title=f'LabGym v{__version__}')
		self.SetSize((750, 600))

		# sets the app icon within GUI
		_set_frame_icon(self)
		# On Windows, also set a specific small icon for better title bar display
		_set_windows_small_icon(self)

		# Create the aui_manager to manage this frame/window.
		self.aui_manager = wx.aui.AuiManager()
		self.aui_manager.SetManagedWindow(self)

		# Create the notebook.
		self.notebook = wx.aui.AuiNotebook(self)
		# Add the notebook as a pane to the aui_manager.
		self.aui_manager.AddPane(
			self.notebook,
			wx.aui.AuiPaneInfo().CenterPane(),
			)

		# Add panel as a page to the notebook.
		panel = InitialPanel(self.notebook)
		title = 'Welcome'
		self.notebook.AddPage(panel, title, select=True)

		# Use a sizer to ensure the notebook fills the frame.
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(sizer)

		# Batch apply changes to any managed panes.
		self.aui_manager.Update()
		self.Show()  # display the frame


def main_window():

	app=wx.App()
	_set_macos_dock_icon() # no-op on non-macOS or if no PyObjC
	_set_windows_taskbar_icon_with_fallback() # no-op on non-Windows, uses fallback ICO
	
	# Log icon usage for debugging
	if sys.platform.startswith("win"):
		logger.info("Windows detected - using fallback ICO for small icon contexts")
		logger.info("Main ICO: %s", str(files("LabGym") / "assets/icons/labgym.ico"))
		logger.info("Fallback ICO: %s", str(files("LabGym") / "assets/icons/fallback.ico"))
	
	MainFrame()  # Create the main frame and its notebook
	logger.info('Bobby\'s  user interface initialized!')
	app.MainLoop()



if __name__=='__main__':  # pragma: no cover

	main_window()
