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
import sys
from .gui_app_icon import set_frame_icon, setup_application_icons

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




class InitialPanel(wx.Panel):
	"""Initial panel, the main window of LabGym."""

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
		"""Open the Preprocessing Module."""

		panel = PanelLv1_ProcessModule(self.notebook)
		title = 'Preprocessing Module'
		self.notebook.AddPage(panel, title, select=True)


	def window_train(self,event):
		"""Open the Training Module."""

		panel = PanelLv1_TrainingModule(self.notebook)
		title = 'Training Module'
		self.notebook.AddPage(panel, title, select=True)


	def window_analyze(self,event):
		"""Open the Analysis Module."""

		panel = PanelLv1_AnalysisModule(self.notebook)
		title = 'Analysis Module'
		self.notebook.AddPage(panel, title, select=True)



class PanelLv1_ProcessModule(wx.Panel):
	"""The Preprocessing Module."""

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
		"""Open the Preprocess Videos panel."""

		panel = PanelLv2_ProcessVideos(self.notebook)
		title = 'Preprocess Videos'
		self.notebook.AddPage(panel, title, select=True)


	def draw_markers(self,event):
		"""Open the Draw Markers panel."""

		panel = PanelLv2_DrawMarkers(self.notebook)
		title = 'Draw Markers'
		self.notebook.AddPage(panel, title, select=True)


class PanelLv1_TrainingModule(wx.Panel):
	"""The Training Module."""

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
		"""Open the Generate Image Examples panel."""

		panel = PanelLv2_GenerateImages(self.notebook)
		title = 'Generate Image Examples'
		self.notebook.AddPage(panel, title, select=True)


	def train_detectors(self,event):
		"""Open the Train Detectors panel."""

		panel = PanelLv2_TrainDetectors(self.notebook)
		title = 'Train Detectors'
		self.notebook.AddPage(panel, title, select=True)


	def test_detectors(self,event):
		"""Open the Test Detectors panel."""

		panel = PanelLv2_TestDetectors(self.notebook)
		title = 'Test Detectors'
		self.notebook.AddPage(panel, title, select=True)


	def generate_behaviorexamples(self,event):
		"""Open the Generate Behavior Examples panel."""

		panel = PanelLv2_GenerateExamples(self.notebook)
		title = 'Generate Behavior Examples'
		self.notebook.AddPage(panel, title, select=True)


	def sort_behaviorexamples(self,event):
		"""Open the Sort Behavior Examples panel."""

		panel = PanelLv2_SortBehaviors(self.notebook)
		title = 'Sort Behavior Examples'
		self.notebook.AddPage(panel, title, select=True)


	def train_categorizers(self,event):
		"""Open the Train Categorizers panel."""

		panel = PanelLv2_TrainCategorizers(self.notebook)
		title = 'Train Categorizers'
		self.notebook.AddPage(panel, title, select=True)


	def test_categorizers(self,event):
		"""Open the Test Categorizers panel."""

		panel = PanelLv2_TestCategorizers(self.notebook)
		title = 'Test Categorizers'
		self.notebook.AddPage(panel, title, select=True)



class PanelLv1_AnalysisModule(wx.Panel):
	"""The Analysis Module."""

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
		"""Open the Analyze Behaviors panel."""

		panel = PanelLv2_AnalyzeBehaviors(self.notebook)
		title = 'Analyze Behaviors'
		self.notebook.AddPage(panel, title, select=True)


	def mine_results(self,event):
		"""Open the Mine Results panel."""

		panel = PanelLv2_MineResults(self.notebook)
		title = 'Mine Results'
		self.notebook.AddPage(panel, title, select=True)


	def plot_behavior(self,event):
		"""Open the Generate Behavior Plot panel."""

		panel = PanelLv2_PlotBehaviors(self.notebook)
		title = 'Generate Behavior Plot'
		self.notebook.AddPage(panel, title, select=True)


	def calculate_distances(self,event):
		"""Open the Calculate Distances panel."""

		panel = PanelLv2_CalculateDistances(self.notebook)
		title = 'Calculate Distances'
		self.notebook.AddPage(panel, title, select=True)



class MainFrame(wx.Frame):
	"""Main frame and its notebook."""

	def __init__(self):
		super().__init__(None, title=f'LabGym v{__version__}')
		self.SetSize((750, 600))
		
		# Set the app icon within GUI
		set_frame_icon(self, context='normal')  # Set normal icon first
		if sys.platform.startswith("win"):
			set_frame_icon(self, context='small', size=16)  # Override with small icon for title bar

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
	"""Display the main window."""
	app = wx.App()
	app.SetAppName("LabGym") # Set app name to influence WM_CLASS
	setup_application_icons()  # Set up all platform-specific icons
	
	MainFrame()  # Create the main frame and its notebook
	logger.info('Bobby\'s user interface initialized!')
	app.MainLoop()



if __name__=='__main__':  # pragma: no cover

	main_window()
