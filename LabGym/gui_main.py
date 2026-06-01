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
import sys
from .gui_app_icon import set_frame_icon, setup_application_icons

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Related third party imports.
import wx
import wx.aui
import wx.lib.agw.hyperlink as hl

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


class WorkflowMapPanel(wx.ScrolledWindow):			# scrollable panel — diagram is fixed-size, scrollbars appear if window is smaller
	"""Displays the LabGym workflow map at a fixed pixel canvas sized to the default LabGym window."""

	CANVAS_W = 1000								# matches LabGym's default window width (set in MainFrame.__init__)
	CANVAS_H = 560								# default window height (600) minus ~40px for the notebook tab bar

	def __init__(self, parent):
		super().__init__(parent)					# run wx.ScrolledWindow's own setup
		self.SetBackgroundColour(wx.WHITE)			# make the panel background white
		self.SetScrollRate(10, 10)					# scroll 10 pixels per step when dragging the scrollbar
		self.SetVirtualSize(self.CANVAS_W, self.CANVAS_H)	# tell wx the total scrollable area
		self.Bind(wx.EVT_PAINT, self.on_paint)		# call on_paint whenever wx needs to redraw this panel

	def on_paint(self, event):
		dc = wx.PaintDC(self)						# create a drawing context which is required in an EVT_PAINT handler
		dc.SetBackground(wx.Brush(wx.WHITE))		# set white background for the clear
		dc.Clear()									# erase the physical visible area before adjusting for scroll
		self.PrepareDC(dc)							# shift the DC origin to account for the current scroll position
		self._draw(dc)								# hand off to the main drawing method

	def _draw(self, dc):
		import math								# needed for diagonal arrow angle calculations
		W, H = self.CANVAS_W, self.CANVAS_H		# fixed canvas dimensions — diagram never rescales

		VW, VH = 1780, 540						# virtual coordinate space — all positions below use this grid
		scale = min(W / VW, H / VH) * 0.95		# compute scale so the diagram fills the canvas with a 5% margin
		ox = (W - VW * scale) / 2				# horizontal offset to centre the diagram on the canvas
		oy = (H - VH * scale) / 2				# vertical offset to centre the diagram on the canvas

		def px(v): return int(ox + v * scale)	# convert a virtual x-coordinate to a real screen pixel
		def py(v): return int(oy + v * scale)	# convert a virtual y-coordinate to a real screen pixel
		def ps(v): return max(1, int(v * scale))# convert a virtual size/thickness to pixels (minimum 1)

		# Section fill and ink (border + arrow) colors
		s1_fill = wx.Colour(255, 210, 210)		# super light red  — section 1 (Collect, Preprocessing)
		s1_ink  = wx.Colour(160, 55, 55)		# darker red       — borders and arrows in section 1
		s2_fill = wx.Colour(210, 228, 255)		# super light blue — section 2 (Tracking and top/bottom branches)
		s2_ink  = wx.Colour(55, 95, 165)		# darker blue      — borders and arrows in section 2
		s3_fill = wx.Colour(255, 228, 195)		# super light orange — section 3 (Categorizer pipeline)
		s3_ink  = wx.Colour(175, 100, 20)		# darker orange    — borders and arrows in section 3

		font      = wx.Font(max(11, ps(16)), wx.FONTFAMILY_DEFAULT,
		                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)	# body text font, scales with window size
		bold_font = wx.Font(max(16, ps(26)), wx.FONTFAMILY_DEFAULT,
		                    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)	# bold font used for the title

		def draw_box(cx, cy, bw, bh, lines, fill, ink):
			dc.SetPen(wx.Pen(ink, ps(1)))
			dc.SetBrush(wx.Brush(fill))
			dc.DrawRoundedRectangle(px(cx - bw/2), py(cy - bh/2),
			                        ps(bw), ps(bh), ps(5))
			dc.SetFont(font)
			dc.SetTextForeground(wx.BLACK)
			lh = dc.GetCharHeight()
			top = py(cy - bh/2) + (ps(bh) - lh * len(lines)) // 2
			for i, line in enumerate(lines):
				lw, _ = dc.GetTextExtent(line)
				dc.DrawText(line, px(cx) - lw // 2, top + i * lh)

		def h_arr(x1, y1, x2, y2, ink):
			dc.SetPen(wx.Pen(ink, ps(2)))
			dc.SetBrush(wx.Brush(ink))
			dc.DrawLine(px(x1), py(y1), px(x2), py(y2))
			ah, al = ps(5), ps(9)
			dc.DrawPolygon([(px(x2),    py(y2)),
			                (px(x2)-al, py(y2)-ah),
			                (px(x2)-al, py(y2)+ah)])

		def v_line(x, y1, y2, ink):
			dc.SetPen(wx.Pen(ink, ps(2)))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			dc.DrawLine(px(x), py(y1), px(x), py(y2))

		def diag_arr(x1, y1, x2, y2, ink, lines=()):
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
				# draw horizontal label lines offset perpendicular to the arrow shaft (left side)
				perp_x, perp_y = uy, -ux			# 90 degrees left of arrow direction in screen coords
				offset = ps(50)						# pixels to push text away from the shaft
				cx_label = px((x1 + x2) / 2) + int(perp_x * offset)
				cy_label = py((y1 + y2) / 2) + int(perp_y * offset)
				dc.SetFont(font)
				dc.SetTextForeground(wx.BLACK)
				lh = dc.GetCharHeight()
				top = cy_label - (lh * len(lines)) // 2
				for i, line in enumerate(lines):
					lw, _ = dc.GetTextExtent(line)
					dc.DrawText(line, cx_label - lw // 2, top + i * lh)


		# TITLE
		dc.SetFont(bold_font)
		dc.SetTextForeground(wx.BLACK)
		title = 'LabGym Workflow Map'
		tw, _ = dc.GetTextExtent(title)
		dc.DrawText(title, px(890) - tw // 2, py(10))		# centred at virtual x=890 (midpoint of VW=1780)


		# ARROWS
		# All horizontal connecting arrows have a shaft length of 25 units

		# main row — left to right
		h_arr( 103, 290,  128, 290, s1_ink)	# Collect Footage -> Preprocessing
		h_arr( 278, 290,  303, 290, s1_ink)	# Preprocessing -> Tracking
		h_arr(1129, 290, 1154, 290, s2_ink)	# Train Detector right -> Generate and sort left
		h_arr(1310, 290, 1335, 290, s3_ink)	# Generate and sort -> Train Categorizer
		h_arr(1465, 290, 1490, 290, s3_ink)	# Train Categorizer -> Test Categorizer
		h_arr(1620, 290, 1645, 290, s3_ink)	# Test Categorizer -> Analyze Behaviors

		# diagonal arrows — symmetric ~37° angles up and down from Tracking
		diag_arr(468, 256, 576, 180, s2_ink, ['Dynamic', 'Background'])	# Tracking top-right -> Detector
		diag_arr(468, 324, 576, 399, s2_ink, ['Static', 'Background'])		# Tracking bottom-right -> Background Subtraction

		# top branch
		h_arr(686, 155, 711, 155, s2_ink)		# Detector -> Generate Images  (25 units)
		v_line(831, 130, 183, s2_ink)			# fork stick at Generate Images right edge
		h_arr(831, 130, 856, 130, s2_ink)		# upper fork -> Roboflow       (25 units)
		h_arr(831, 183, 856, 183, s2_ink)		# lower fork -> EZannot         (25 units)
		h_arr(966, 130, 988, 130, s2_ink)		# Roboflow -> convergence stick
		h_arr(966, 183, 988, 183, s2_ink)		# EZannot  -> convergence stick
		v_line(988, 130, 183, s2_ink)			# convergence stick before Train Detector
		h_arr(988, 155, 1013, 155, s2_ink)		# convergence -> Train Detector (25 units)


		# BOXES

		# main row
		draw_box(  55, 290,  95,  62, ['Collect', 'Footage'],                        s1_fill, s1_ink)
		draw_box( 203, 290, 150,  60, ['Preprocessing'],                              s1_fill, s1_ink)
		draw_box( 386, 290, 165,  68, ['Tracking /', 'Animal Detection'],             s2_fill, s2_ink)
		draw_box(1232, 290, 155,  90, ['Generate and', 'sort behavior', 'examples'], s3_fill, s3_ink)
		draw_box(1400, 290, 130,  62, ['Train', 'Categorizer'],                      s3_fill, s3_ink)
		draw_box(1555, 290, 130,  62, ['Test', 'Categorizer'],                       s3_fill, s3_ink)
		draw_box(1695, 290, 100,  62, ['Analyze', 'Behaviors'],                      s3_fill, s3_ink)

		# top branch — all section 2
		draw_box( 631, 155, 110,  62, ['Detector'],                                  s2_fill, s2_ink)
		draw_box( 771, 155, 120,  62, ['Generate', 'Images'],                        s2_fill, s2_ink)
		draw_box( 911, 130, 110,  50, ['Roboflow'],                                  s2_fill, s2_ink)	# upper of the stacked pair
		draw_box( 911, 183, 110,  50, ['EZannot'],                                   s2_fill, s2_ink)	# lower of the stacked pair
		draw_box(1071, 155, 115,  62, ['Train', 'Detector'],                         s2_fill, s2_ink)

		# bottom branch — section 2
		draw_box( 651, 427, 150,  68, ['Background', 'Subtraction'],                 s2_fill, s2_ink)




class MainFrame(wx.Frame):
	"""Main frame and its notebook."""

	def __init__(self):
		super().__init__(None, title=f'LabGym v{__version__}')

		self.SetSize((1000, 600))

		# Set the app icon within GUI
		set_frame_icon(self, context='normal')  # Set normal icon first
		if sys.platform.startswith("win"):
			set_frame_icon(self, context='small', size=16)  # Override with small icon for title bar

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
