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
import logging
from .gui_app_icon import set_frame_icon, setup_application_icons

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Related third party imports.
import wx
import wx.aui
import wx.html
import wx.lib.agw.hyperlink as hl
import webbrowser

# Local application/library specific imports.
from LabGym import __version__
from .gui_utils import add_or_select_notebook_page
logger.debug('importing %s ...', '.gui_categorizer')
from .gui_categorizer import PanelLv2_GenerateExamples,PanelLv2_TrainCategorizers,PanelLv2_SortBehaviors,PanelLv2_TestCategorizers
logger.debug('importing %s done', '.gui_categorizer')
from .gui_detector import PanelLv2_GenerateImages,PanelLv2_TrainDetectors,PanelLv2_TestDetectors
from .gui_preprocessor import PanelLv2_ProcessVideos,PanelLv2_DrawMarkers
from .gui_analyzer import PanelLv2_AnalyzeBehaviors,PanelLv2_MineResults,PanelLv2_PlotBehaviors,PanelLv2_CalculateDistances
from LabGym import selftest



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
			label='Created by Yujia Hu and Bing Ye\n\nLife Sciences Institute, University of Michigan\n\n\n\nContributor list:\n\nJie Zhou, John Ruckstuhl, Brendon O. Waston, Carrie R. Ferrario, Kelly Goss,\n\nRohan Satapathy, Bobby Tomlinson, Isabelle Baker, M. Victor Struman',style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(self.text_developers,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,60,0)

		homepage=hl.HyperLinkCtrl(panel,0,'Home Page',URL='https://www.labgym.org')
		boxsizer.Add(homepage,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		module_modules=wx.BoxSizer(wx.HORIZONTAL)
		button_preprocess=wx.Button(panel,label='Preprocessing Module',size=(250,40))
		button_preprocess.Bind(wx.EVT_BUTTON,self.window_preprocess)
		wx.Button.SetToolTip(button_preprocess,'Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.')
		button_train=wx.Button(panel,label='Training Module',size=(250,40))
		button_train.Bind(wx.EVT_BUTTON,self.window_train)
		wx.Button.SetToolTip(button_train,'Teach LabGym to recognize the animals / objects of your interest and identify their behaviors that are defined by you.')
		button_analyze=wx.Button(panel,label='Analysis Module',size=(250,40))
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

		title = 'Preprocessing Module'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv1_ProcessModule(self.notebook), title)


	def window_train(self,event):
		"""Open the Training Module."""

		title = 'Training Module'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv1_TrainingModule(self.notebook), title)


	def window_analyze(self,event):
		"""Open the Analysis Module."""

		title = 'Analysis Module'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv1_AnalysisModule(self.notebook), title)



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

		title = 'Preprocess Videos'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_ProcessVideos(self.notebook), title)


	def draw_markers(self,event):
		"""Open the Draw Markers panel."""

		title = 'Draw Markers'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_DrawMarkers(self.notebook), title)


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

		title = 'Generate Image Examples'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_GenerateImages(self.notebook), title)


	def train_detectors(self,event):
		"""Open the Train Detectors panel."""

		title = 'Train Detectors'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_TrainDetectors(self.notebook), title)


	def test_detectors(self,event):
		"""Open the Test Detectors panel."""

		title = 'Test Detectors'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_TestDetectors(self.notebook), title)


	def generate_behaviorexamples(self,event):
		"""Open the Generate Behavior Examples panel."""

		title = 'Generate Behavior Examples'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_GenerateExamples(self.notebook), title)


	def sort_behaviorexamples(self,event):
		"""Open the Sort Behavior Examples panel."""

		title = 'Sort Behavior Examples'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_SortBehaviors(self.notebook), title)


	def train_categorizers(self,event):
		"""Open the Train Categorizers panel."""

		title = 'Train Categorizers'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_TrainCategorizers(self.notebook), title)


	def test_categorizers(self,event):
		"""Open the Test Categorizers panel."""

		title = 'Test Categorizers'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_TestCategorizers(self.notebook), title)



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

		title = 'Analyze Behaviors'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_AnalyzeBehaviors(self.notebook), title)


	def mine_results(self,event):
		"""Open the Mine Results panel."""

		title = 'Mine Results'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_MineResults(self.notebook), title)


	def plot_behavior(self,event):
		"""Open the Generate Behavior Plot panel."""

		title = 'Generate Behavior Plot'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_PlotBehaviors(self.notebook), title)


	def calculate_distances(self,event):
		"""Open the Calculate Distances panel."""

		title = 'Calculate Distances'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv2_CalculateDistances(self.notebook), title)


# Popup content for each clickable workflow-map box: (section_title, box_title, description, guide_sections)
_BOX_POPUP = {
	'collect_footage': (
		'Video Prep',
		'Collect Footage',
		'This is the video collection stage. Before LabGym can track animals or classify behaviors, you need videos that clearly capture the animals and the behaviors of interest. Good video quality, appropriate lighting, and consistent recording conditions will make downstream tracking and classification much more accurate.',
		'Part 2, Part 3.5',
	),
	'preprocessing': (
		'Video Prep',
		'Preprocessing (Optional)',
		'This step involves modifying videos before analysis if needed. Examples include cropping, trimming, stabilizing recordings, adjusting contrast, or adding spatial markers. LabGym also includes tools that can help prepare videos for later analysis.',
		'Part 4.5, Part 4.6, Section l',
	),
	'tracking': (
		'Tracking',
		'Tracking / Animal Detection',
		'This is where LabGym finds and follows animals across video frames. Every animal receives an identity and location over time, creating the movement information needed for behavior classification later. LabGym can use either background subtraction or a trained detector depending on video complexity.',
		'Part 3.1, Part 4.1, Section ll',
	),
	'bg_sub': (
		'Tracking',
		'Background Subtraction',
		'For videos with stable lighting and a fixed background, LabGym automatically estimates the background and removes it. This leaves only the moving animal(s), making tracking faster and more reliable.',
		'Part 3.1, Part 4.1, Section lll A',
	),
	'detector': (
		'Tracking',
		'Detector',
		'When backgrounds are complicated, lighting changes, or animals frequently overlap, LabGym can use a trained object detector instead of simple background subtraction. The detector learns what the target animal looks like and identifies it directly in each frame.',
		'Part 3.1, Part 4.1, Section ll',
	),
	'generate_images': (
		'Tracking',
		'Generate Images',
		"LabGym extracts representative frames from your videos that will be used to train a detector. These images become the dataset that you'll later annotate with animal locations.",
		'Section ll A',
	),
	'roboflow': (
		'Tracking',
		'Roboflow OR EZannot',
		'These tools are used to annotate the generated images. You draw boxes around animals and label them so the detector can learn what the target animal looks like.',
		'Section ll B',
	),
	'train_detector': (
		'Tracking',
		'Train Detector',
		'LabGym uses the annotated images to train an object detection model. The resulting detector can then automatically locate animals in new videos.',
		'Section ll C, Section ll D',
	),
	'generate_examples': (
		'Classification',
		'Generate and Sort Behavior Examples',
		'LabGym tracks animals and automatically generates behavior examples. Each example contains both an animation and a "pattern image" that summarizes the animal\'s movement through time. Users then sort these examples into behavior categories such as grooming, rearing, or locomotion.',
		'Section lll A, Section lll B',
	),
	'train_categorizer': (
		'Classification',
		'Train Categorizer',
		'The categorized behavior examples are used to train LabGym\'s "Categorizer," the deep-learning model that identifies behaviors. It learns from both the raw animations and the movement-pattern images.',
		'Section lll C',
	),
	'test_categorizer': (
		'Classification',
		'Test Categorizer',
		'After training, LabGym evaluates how accurately the categorizer identifies behaviors it has not seen before. This helps determine whether more training examples are needed.',
		'Part 4.3, Section lll D',
	),
	'analyze_behaviors': (
		'Classification',
		'Analyze Behaviors',
		'The trained categorizer is applied to experimental videos. LabGym classifies behaviors frame-by-frame and records when each behavior occurs. It also generates quantitative measurements such as duration, frequency, and movement metrics.',
		'Part 4.4, Section lV',
	),
	'mine_results': (
		'Post Classification Analysis',
		'Mine Results',
		'LabGym exports spreadsheets and structured behavioral data that can be explored statistically. Users can compare groups, quantify treatment effects, or examine temporal patterns in behavior.',
		'Section lV B',
	),
	'generate_plot': (
		'Post Classification Analysis',
		'Generate Behavior Plot',
		'LabGym can visualize behavior occurrence over time using raster plots and other summaries. These plots help users quickly identify patterns, transitions, and temporal organization of behaviors.',
		'Section lV C',
	),
	'calc_distances': (
		'Post Classification Analysis',
		'Calculate Distances',
		'Using tracking information, LabGym computes movement-based measurements such as distance traveled, speed, and location-related metrics. These can be analyzed alongside behavior classifications.',
		'Part 4.4, Section lV',
	),
}

# Practical-guide page numbers keyed by reference text (lowercase for case-insensitive lookup)
_GUIDE_PAGES = {
	'part 2':        4,
	'part 3.1':      5,
	'part 3.5':      6,
	'part 4.1':      7,
	'part 4.3':      8,
	'part 4.4':      8,
	'part 4.5':      9,
	'part 4.6':      9,
	'section l':    14,
	'section ll':   16,
	'section ll a': 16,
	'section ll b': 18,
	'section ll c': 21,
	'section ll d': 23,
	'section lll a': 26,
	'section lll b': 31,
	'section lll c': 33,
	'section lll d': 37,
	'section lv':   38,
	'section lv b': 44,
	'section lv c': 44,
}


class BoxInfoPopup(wx.Frame):
	"""Info popup shown when clicking a workflow-map box. Closes on focus loss."""

	def __init__(self, parent, section, title, description, guide, fill, ink):
		super().__init__(None, style=wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.NO_BORDER)
		self.SetBackgroundColour(ink)  # ink peeks through as the border

		# Blend fill 50% toward white for a softer popup background
		pf = wx.Colour(
			fill.Red()   + (255 - fill.Red())   // 2,
			fill.Green() + (255 - fill.Green()) // 2,
			fill.Blue()  + (255 - fill.Blue())  // 2,
		)

		panel = wx.Panel(self)
		panel.SetBackgroundColour(pf)

		html_win = wx.html.HtmlWindow(panel, size=(440, 100), style=wx.html.HW_NO_SELECTION)
		html_win.SetBackgroundColour(pf)
		html_win.SetBorders(0)
		html_win.SetPage(self._make_html(section, title, description, guide, pf))
		html_win.Bind(wx.html.EVT_HTML_LINK_CLICKED, self._on_link)

		content_h = html_win.GetInternalRepresentation().GetHeight()
		html_win.SetMinSize((440, content_h + 4))

		inner = wx.BoxSizer(wx.VERTICAL)
		inner.Add(html_win, 0, wx.ALL, 20)
		panel.SetSizer(inner)
		panel.Fit()

		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(panel, 1, wx.ALL | wx.EXPAND, 3)  # 3px gap exposes ink-coloured frame background as border
		self.SetSizer(outer)
		self.Fit()

		frame = wx.GetTopLevelParent(parent)
		fx, fy = frame.GetPosition()
		fw, fh = frame.GetSize()
		pw, ph = self.GetSize()
		self.SetPosition((fx + (fw - pw) // 2, fy + (fh - ph) // 2))

		self._ready = False
		self.Bind(wx.EVT_ACTIVATE, self._on_activate)
		wx.CallLater(150, self._set_ready)

	def _set_ready(self):
		self._ready = True

	def _on_activate(self, evt):
		if self._ready and not evt.GetActive():
			wx.CallAfter(self.Close)
		evt.Skip()

	def _on_link(self, evt):
		webbrowser.open(evt.GetLinkInfo().GetHref())

	def _make_html(self, section, title, description, guide, fill):
		import html as _h
		bg = '#{:02X}{:02X}{:02X}'.format(fill.Red(), fill.Green(), fill.Blue())
		base = 'https://www.labgym.org/guides/practical-guide#page-'
		refs = []
		for ref in (r.strip() for r in guide.split(',')):
			page = _GUIDE_PAGES.get(ref.lower())
			refs.append(
				'<a href="{}{}">{}</a>'.format(base, page, _h.escape(ref)) if page
				else _h.escape(ref)
			)
		guide_html = ', '.join(refs)
		return (
			'<html><body bgcolor="{bg}">'
			'<center>'
			'<font size="+1"><b>{section}</b><br>{title}</font>'
			'<br><br>'
			'{desc}'
			'<br><br>'
			'Learn more in the following LabGym Practical Guide sections: {guide}'
			'</center>'
			'</body></html>'
		).format(
			bg=bg,
			section=_h.escape(section),
			title=_h.escape(title),
			desc=_h.escape(description, quote=False),
			guide=guide_html,
		)


class WorkflowMapPanel(wx.Panel):
	"""Displays the LabGym workflow map at a fixed scale for the fixed LabGym window size."""

	# Logical (virtual) coordinate space — source of truth for layout.
	VW = 2200
	VH = 660
	# Fixed drawing area: Workflow Map page client size inside FIXED_FRAME_SIZE (1100×650).
	CANVAS_W = 1100
	CANVAS_H = 560
	# One-time aspect-preserving fit of the logical map into the fixed canvas.
	SCALE = min(CANVAS_W / VW, CANVAS_H / VH)  # 0.5
	# Centre the scaled logical rect on the fixed canvas.
	OX = (CANVAS_W - VW * SCALE) / 2			# 0.0
	OY = (CANVAS_H - VH * SCALE) / 2			# 115.0

	def __init__(self, parent):
		super().__init__(parent)
		self.SetBackgroundColour(wx.WHITE)
		self._clickable_boxes = []				# list of (bx, by, bw, bh, fill, ink, popup_data) in client pixels
		self.Bind(wx.EVT_PAINT, self.on_paint)
		self.Bind(wx.EVT_LEFT_DOWN, self._on_box_click)

	def on_paint(self, event):
		dc = wx.PaintDC(self)
		dc.SetBackground(wx.Brush(wx.WHITE))
		dc.Clear()
		self._draw(dc)

	def _draw(self, dc):
		import math								# needed for diagonal arrow angle calculations
		self._clickable_boxes = []				# reset so hit-test rects match this paint
		W, H = self.CANVAS_W, self.CANVAS_H
		scale, ox, oy = self.SCALE, self.OX, self.OY

		def px(v): return int(ox + v * scale)	# logical x → client pixel
		def py(v): return int(oy + v * scale)	# logical y → client pixel
		def ps(v): return max(1, int(v * scale))# logical size/thickness → pixels (minimum 1)

		# Section fill and ink (border + arrow) colors
		s1_fill = wx.Colour(255, 210, 210)		# super light red    — section 1
		s1_ink  = wx.Colour(160, 55, 55)		# darker red         — section 1 borders and arrows
		s2_fill = wx.Colour(210, 228, 255)		# super light blue   — section 2
		s2_ink  = wx.Colour(55, 95, 165)		# darker blue        — section 2 borders and arrows
		s3_fill = wx.Colour(255, 228, 195)		# super light orange — section 3
		s3_ink  = wx.Colour(175, 100, 20)		# darker orange      — section 3 borders and arrows
		s4_fill = wx.Colour(235, 215, 255)		# light lavender     — section 4
		s4_ink  = wx.Colour(120, 60, 180)		# deeper purple      — section 4 borders

		font      = wx.Font(max(12, ps(16)), wx.FONTFAMILY_DEFAULT,
		                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)	# body text font at fixed map scale
		bold_font = wx.Font(max(18, ps(26)), wx.FONTFAMILY_DEFAULT,
		                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)	# large bold font for the main title
		head_font = wx.Font(max(15, ps(22)), wx.FONTFAMILY_DEFAULT,
		                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)	# smaller bold font for section headings

		dc.SetFont(font)
		lh = dc.GetCharHeight()			# single-line height in pixels
		MX = ps(14)						# horizontal margin each side in pixels
		MY = ps(8)						# vertical margin each side in pixels
		def hbh(n): return (lh * n + 2 * MY) / 2 / scale  # virtual half-box-height for n lines of text

		def draw_box(cx, cy, lines, fill, ink, key=None):
			dc.SetFont(font)
			dc.SetTextForeground(wx.BLACK)
			line_widths = [dc.GetTextExtent(l)[0] for l in lines]
			box_w = max(line_widths) + 2 * MX
			box_h = lh * len(lines) + 2 * MY
			bx = px(cx) - box_w // 2
			by = py(cy) - box_h // 2
			dc.SetPen(wx.Pen(ink, ps(1)))
			dc.SetBrush(wx.Brush(fill))
			dc.DrawRoundedRectangle(bx, by, box_w, box_h, ps(5))
			ty = by + MY
			for i, (line, lw) in enumerate(zip(lines, line_widths)):
				dc.DrawText(line, px(cx) - lw // 2, ty + i * lh)
			if key is not None:
				self._clickable_boxes.append((bx, by, box_w, box_h, fill, ink, _BOX_POPUP[key]))

		def v_arr(x, y1, y2, ink):				# vertical downward arrow with filled arrowhead
			dc.SetPen(wx.Pen(ink, ps(2)))
			dc.SetBrush(wx.Brush(ink))
			dc.DrawLine(px(x), py(y1), px(x), py(y2))
			ah, al = ps(5), ps(9)
			dc.DrawPolygon([(px(x),    py(y2)),
			                (px(x)-ah, py(y2)-al),
			                (px(x)+ah, py(y2)-al)])

		def diag_arr(x1, y1, x2, y2, ink, lines=(), label_dx=0, label_dy=0):
			dc.SetPen(wx.Pen(ink, ps(2)))
			dc.SetBrush(wx.Brush(ink))
			dc.DrawLine(px(x1), py(y1), px(x2), py(y2))
			dx_v, dy_v = x2 - x1, y2 - y1
			length = math.hypot(dx_v, dy_v)
			ux, uy = dx_v / length, dy_v / length
			ah, al = ps(5), ps(9)
			tip_x, tip_y = px(x2), py(y2)
			lft_x = int(tip_x - al * ux + ah * (-uy))
			lft_y = int(tip_y - al * uy + ah * ux)
			rgt_x = int(tip_x - al * ux - ah * (-uy))
			rgt_y = int(tip_y - al * uy - ah * ux)
			dc.DrawPolygon([(tip_x, tip_y), (lft_x, lft_y), (rgt_x, rgt_y)])
			if lines:
				perp_x, perp_y = uy, -ux			# 90 degrees left of arrow direction in screen coords
				if perp_y > 0:						# if that points downward, flip so label is always above the arrow
					perp_x, perp_y = -perp_x, -perp_y
				offset = ps(80)						# pixels to push text away from the shaft
				cx_label = px((x1 + x2) / 2) + int(perp_x * offset) + label_dx
				cy_label = py((y1 + y2) / 2) + int(perp_y * offset) + label_dy
				dc.SetFont(font)
				dc.SetTextForeground(wx.BLACK)
				lh = dc.GetCharHeight()
				top = cy_label - (lh * len(lines)) // 2
				for i, line in enumerate(lines):
					lw, _ = dc.GetTextExtent(line)
					dc.DrawText(line, cx_label - lw // 2, top + i * lh)

		def big_arr(x1, x2, cy):				# large grey section-transition arrow pointing right
			sh   = ps(8)						# shaft half-height (thinner than before)
			hw   = ps(16)						# arrowhead half-width
			neck = px(x2) - ps(26)				# x-pixel where the arrowhead begins
			dc.SetPen(wx.Pen(wx.Colour(130, 130, 130), ps(1)))
			dc.SetBrush(wx.Brush(wx.Colour(175, 175, 175)))
			dc.DrawPolygon([
				(px(x1), py(cy) - sh),
				(neck,   py(cy) - sh),
				(neck,   py(cy) - hw),
				(px(x2), py(cy)),
				(neck,   py(cy) + hw),
				(neck,   py(cy) + sh),
				(px(x1), py(cy) + sh),
			])


		# MAIN TITLE
		dc.SetFont(bold_font)
		dc.SetTextForeground(wx.BLACK)
		tw, _ = dc.GetTextExtent('LabGym Workflow Map')
		dc.DrawText('LabGym Workflow Map', (W - tw) // 2, py(65) // 3)

		# SECTION HEADINGS
		dc.SetFont(head_font)
		dc.SetTextForeground(wx.BLACK)
		for label, cx in [('1. Video Prep', 155), ('2. Tracking', 755), ('3. Classification', 1355)]:
			tw, _ = dc.GetTextExtent(label)
			dc.DrawText(label, px(cx) - tw // 2, py(65))
		lh_head = dc.GetCharHeight()
		for i, line in enumerate(['4. Post Classification', 'Analysis']):
			tw, _ = dc.GetTextExtent(line)
			dc.DrawText(line, px(1955) - tw // 2, py(65) + i * lh_head)


		# ── Section 1: Video Prep ──────────────────────────────────────────────
		v_arr(155, 154 + hbh(2), 259 - hbh(2), s1_ink)		# Collect Footage -> Preprocessing
		big_arr(380, 555, 65)								# section 1 -> section 2 transition (centred in gap, at subtitle height)

		# ── Section 2: Tracking ───────────────────────────────────────────────
		diag_arr(715, 148 + hbh(2), 540, 280 - hbh(2), s2_ink, ['Static', 'Background'],  label_dx=-ps(30), label_dy=ps(38))	# Tracking -> Background Subtraction (steeper angle)
		diag_arr(795, 148 + hbh(2), 950, 280 - hbh(1), s2_ink, ['Dynamic', 'Background'], label_dx= ps(30), label_dy=ps(25))	# Tracking -> Detector (steeper angle)
		v_arr(950, 280 + hbh(1), 380 - hbh(2), s2_ink)			# Detector -> Generate Images
		v_arr(933, 380 + hbh(2), 480 - hbh(2), s2_ink)			# Generate Images -> Roboflow OR EZannot (left fork)
		v_arr(967, 380 + hbh(2), 480 - hbh(2), s2_ink)			# Generate Images -> Roboflow OR EZannot (right fork)
		v_arr(950, 480 + hbh(2), 580 - hbh(2), s2_ink)			# Roboflow OR EZannot -> Train Detector
		big_arr(967, 1142, 65)									# section 2 -> section 3 transition (centred in gap, at subtitle height)

		# ── Section 3: Classification ─────────────────────────────────────────
		v_arr(1355, 164 + hbh(3), 278 - hbh(2), s3_ink)		# Generate and sort -> Train Categorizer
		v_arr(1355, 278 + hbh(2), 378 - hbh(2), s3_ink)		# Train Categorizer -> Test Categorizer
		v_arr(1355, 378 + hbh(2), 478 - hbh(2), s3_ink)		# Test Categorizer -> Analyze Behaviors
		big_arr(1567, 1742, 65)									# section 3 -> section 4 transition (centred in gap, at subtitle height)


		# BOXES

		# section 1
		draw_box( 155, 154, ['Collect', 'Footage'],                        s1_fill, s1_ink, 'collect_footage')
		draw_box( 155, 259, ['Preprocessing', '(Optional)'],                s1_fill, s1_ink, 'preprocessing')

		# section 2
		draw_box( 755, 148, ['Tracking /', 'Animal Detection'],             s2_fill, s2_ink, 'tracking')
		draw_box( 540, 280, ['Background', 'Subtraction'],                 s2_fill, s2_ink, 'bg_sub')
		draw_box( 950, 280, ['Detector'],                                  s2_fill, s2_ink, 'detector')
		draw_box( 950, 380, ['Generate', 'Images'],                        s2_fill, s2_ink, 'generate_images')
		draw_box( 950, 480, ['Roboflow OR', 'EZannot'],                    s2_fill, s2_ink, 'roboflow')
		draw_box( 950, 580, ['Train', 'Detector'],                         s2_fill, s2_ink, 'train_detector')

		# section 3
		draw_box(1355, 164, ['Generate and', 'Sort Behavior', 'Examples'], s3_fill, s3_ink, 'generate_examples')
		draw_box(1355, 278, ['Train', 'Categorizer'],                      s3_fill, s3_ink, 'train_categorizer')
		draw_box(1355, 378, ['Test', 'Categorizer'],                       s3_fill, s3_ink, 'test_categorizer')
		draw_box(1355, 478, ['Analyze', 'Behaviors'],                      s3_fill, s3_ink, 'analyze_behaviors')

		# section 4
		draw_box(1955, 195, ['Mine', 'Results'],           s4_fill, s4_ink, 'mine_results')
		draw_box(1955, 295, ['Generate', 'Behavior Plot'], s4_fill, s4_ink, 'generate_plot')
		draw_box(1955, 395, ['Calculate', 'Distances'],    s4_fill, s4_ink, 'calc_distances')

	def _on_box_click(self, evt):
		# Click coords are already in client space; box rects are recorded in the same space during paint.
		x, y = evt.GetPosition()
		for bx, by, bw, bh, fill, ink, data in self._clickable_boxes:
			if bx <= x < bx + bw and by <= y < by + bh:
				section, title, desc, guide = data
				popup = BoxInfoPopup(self, section, title, desc, guide, fill, ink)
				popup.Show()
				return
		evt.Skip()


class MainFrame(wx.Frame):
	"""Main frame and its notebook."""

	# Fixed outer window size — large enough for the full Workflow Map (canvas 1100×560) without scroll.
	# Height includes map client + notebook tabs + menubar/chrome (~90px). Not resizable.
	FIXED_FRAME_SIZE = (1100, 650)

	def __init__(self):
		# Disable resize border and maximize so the frame stays at FIXED_FRAME_SIZE.
		style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
		super().__init__(None, title=f'LabGym v{__version__}', style=style)

		self.SetSize(self.FIXED_FRAME_SIZE)
		self.SetMinSize(self.FIXED_FRAME_SIZE)
		self.SetMaxSize(self.FIXED_FRAME_SIZE)

		# Set the app icon within GUI (unified simplified artwork on all platforms)
		set_frame_icon(self)

		self.init_menubar()

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
		title = 'Home'
		self.notebook.AddPage(panel, title, select=True)
		workflow_panel = WorkflowMapPanel(self.notebook)
		self.notebook.AddPage(workflow_panel, 'Workflow Map', select=False)

		# Bind the close event to prevent Home tab from being closed
		self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_page_close)

		# Use a sizer to ensure the notebook fills the frame.
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(sizer)

		# Batch apply changes to any managed panes.
		self.aui_manager.Update()
		self.Centre()
		self.Show()  # display the frame

	def on_page_close(self, event):
		"""Handle page close events to prevent Home tab from being closed."""
		# Prevent the Home tab (index 0) from being closed
		if event.GetSelection() in (0, 1):
			event.Veto()
		else:
			# Allow other tabs to be closed normally
			event.Skip()

	def init_menubar(self):
		"""Add the Application Menu.

		On macOs,
		Change the Application Menu (aka traditional menu bar)
		from (a)
			Python
				(None)
		to (b)
			Python
				Services >
				----
				Hide LabGym
				Hide Others
				Show All
				----
				Quit LabGym
			Window
				Minimize
				Zoom
				Tile Window to Left of Screen
				Replace Tiled Window
				----
				Bring All to Front
				----
				LabGym v2.9.6
		to (c)
			Python
				Services >
				----
				Hide LabGym
				Hide Others
				Show All
				----
				Quit LabGym
			File
				(None)
			Window
				Minimize
				Zoom
				Tile Window to Left of Screen
				Replace Tiled Window
				----
				Bring All to Front
				----
				LabGym v2.9.6
			Help
				(search)


		In wxPython for macOS, the menu bar behaves differently than on Windows or Linux to align with Apple's Human Interface Guidelines (HIG). On macOS, the menu bar is global and always appears at the top of the screen rather than attached to individual windows.

Application Menu Management: wxPython automatically moves certain menu items to the standard macOS "Application" menu (the menu labeled with your app's name). Standard IDs like wx.ID_ABOUT, wx.ID_EXIT (mapped to Quit), and wx.ID_PREFERENCES are automatically relocated there.

Set the App Name: To change the name displayed in the Application menu from "Python" to your app's name, you must bundle your script into a .app package using tools like Py2app or Briefcase
		"""

		# 1. Create a MenuBar
		menubar = wx.MenuBar()

		# 2. Create individual Menus (the drop downs)
		# file_menu = wx.Menu()
		# help_menu = wx.Menu()
		misc_menu = wx.Menu()

		# 3. Add MenuItems to the Menus
		# Assign unique IDs (wx.ID_EXIT is a standard ID)
		# quit_item = file_menu.Append(
		#     wx.ID_EXIT, '&Quit\tCtrl+Q', 'Exit application')
		# about_item = help_menu.Append(
		#     wx.ID_ABOUT, '&About', 'About this program')
		selftest_item = misc_menu.Append(
			wx.ID_ANY, '&Selftest', 'Perform a selftest')

		# 4. Attach Menus to the MenuBar
		# menubar.Append(file_menu, '&File')
		# menubar.Append(help_menu, '&Help')
		#
		# but on macOS, some standard IDs are repositioned per HIG.
		# *  the About (wx.ID_ABOUT) is relocated under the
		#    left-most menu ("Python")
		# *  the Quit (wx.EXIT) is relocated under the left-most menu
		#    ("Python")
		menubar.Append(misc_menu, '&Misc')

		# 5. Attach the MenuBar to the Frame
		self.SetMenuBar(menubar)

		# 6. Bind events to the Frame
		# self.Bind(wx.EVT_MENU, self.on_quit, quit_item)
		# self.Bind(wx.EVT_MENU, self.on_about, about_item)
		self.Bind(wx.EVT_MENU, self.on_selftest, selftest_item)

	# def on_quit(self, event):
	#     self.Close(True)

	# def on_about(self, event):
	#     wx.MessageBox("A simple wxPython menu example", "About Me", wx.OK | wx.ICON_INFORMATION)

	def on_selftest(self, event):
		# lock out other GUI events until selftest is complete?
		# run selftest in a different context to avoid wx.App trouble?
		# start dev work by pytest on tests/test_dummy.py

		# This is problematic because wx.App is supposed to be singleton.
		# selftest.run_selftests()

		# This for now, until selftest.run_selftests_isolated() is
		# implemented.
		selftest.run_selftests_help()


def main_window():
	"""Display the main window."""
	app = wx.GetApp()  # reference to the currently running wx.App instance
	if app is None:
		app = wx.App()  # new wx.App object

	app.SetAppName("LabGym") # Set app name to influence WM_CLASS
	setup_application_icons()  # Set up all platform-specific icons

	MainFrame()  # Create the main frame and its notebook
	logger.info('User interface initialized!')
	app.MainLoop()



if __name__=='__main__':  # pragma: no cover

	main_window()
