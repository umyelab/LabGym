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

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import json
import logging
import os
from pathlib import Path

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger =  logging.getLogger(__name__)  # pylint: disable=wrong-import-position
logger.debug('loading %s', __file__)  # pylint: disable=wrong-import-position

# Related third party imports.
import matplotlib as mpl
import pandas as pd
import torch
import wx

# Local application/library specific imports.
from .analyzebehavior import AnalyzeAnimal
from .analyzebehavior_dt import AnalyzeAnimalDetector
from LabGym import config
from .minedata import data_mining
from .tools import plot_events, parse_all_events_file, calculate_distances


the_absolute_current_path=str(Path(__file__).resolve().parent)


class ColorPicker(wx.Dialog):

	'''
	A window for select a color for each behavior
	'''

	def __init__(self,parent,title,name_and_color):

		super(ColorPicker,self).__init__(parent=None,title=title,size=(200,200))

		self.name_and_color=name_and_color
		name=self.name_and_color[0]
		hex_color=self.name_and_color[1][1].lstrip('#')
		color=tuple(int(hex_color[i:i+2],16) for i in (0,2,4))

		boxsizer=wx.BoxSizer(wx.VERTICAL)

		self.color_picker=wx.ColourPickerCtrl(self,colour=color)

		button=wx.Button(self,wx.ID_OK,label='Apply')

		boxsizer.Add(0,10,0)
		boxsizer.Add(self.color_picker,0,wx.ALL|wx.CENTER,10)
		boxsizer.Add(button,0,wx.ALL|wx.CENTER,10)
		boxsizer.Add(0,10,0)

		self.SetSizer(boxsizer)



class WindowLv2_AnalyzeBehaviors(wx.Frame):

	'''
	The 'Analyze Behaviors' functional unit
	'''

	def __init__(self,title):

		super(WindowLv2_AnalyzeBehaviors,self).__init__(parent=None,title=title,size=(1000,530))

		# Get all of the values needed from config.get_config().
		self._config = config.get_config()

		self.behavior_mode=0 # 0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		self.use_detector=False # whether the Detector is used
		self.detector_path=None # the 'LabGym/detectors' folder, which stores all the trained Detectors
		self.path_to_detector=None # path to the Detector
		self.detector_batch=1 # for batch processing use if GPU is available
		self.detection_threshold=0 # only for 'static images' behavior mode
		self.animal_kinds=[] # the total categories of animals / objects in a Detector
		self.background_path=None # if not None, load background images from path in 'background subtraction' detection method
		self.model_path=None # the 'LabGym/models' folder, which stores all the trained Categorizers
		self.path_to_categorizer=None # path to the Categorizer
		self.path_to_videos=None # path to a batch of videos for analysis
		self.result_path=None # the folder for storing analysis outputs
		self.framewidth=None # if not None, will resize the video frame keeping the original w:h ratio
		self.delta=10000 # the fold changes in illumination that determines the optogenetic stimulation onset
		self.decode_animalnumber=False # whether to decode animal numbers from '_nn_' in video file names
		self.animal_number=None # the number of animals / objects in a video
		self.autofind_t=False # whether to find stimulation onset automatically (only for optogenetics)
		self.decode_t=False # whether to decode start_t from '_bt_' in video file names
		self.t=0 # the start_t for analysis
		self.duration=0 # the duration of the analysis
		self.decode_extraction=False # whether to decode time windows for background extraction from '_xst_' and '_xet_' in video file names
		self.ex_start=0 # start time for background extraction
		self.ex_end=None # end time for background extraction
		self.behaviornames_and_colors={} # behavior names in the Categorizer and their representative colors for annotation
		self.dim_tconv=8 # input dimension for Animation Analyzer in Categorizer
		self.dim_conv=8 # input dimension for Pattern Recognizer in Categorizer
		self.channel=1 # input channel for Animation Analyzer, 1--gray scale, 3--RGB scale
		self.length=15 # input time step for Animation Analyzer, also the duration / length for a behavior example
		self.animal_vs_bg=0 # 0: animals birghter than the background; 1: animals darker than the background; 2: hard to tell
		self.stable_illumination=True # whether the illumination in videos is stable
		self.animation_analyzer=True # whether to include Animation Analyzer in the Categorizers
		self.animal_to_include=[] # the animals / obejcts that will be annotated in the annotated videos / behavior plots
		self.ID_colors=[(255,255,255)] # the colors for animals / obejcts identities that will be annotated in the annotated videos
		self.behavior_to_include=['all'] # behaviors that will be annotated in the annotated videos / behavior plots
		self.parameter_to_analyze=[] # quantitative measures that will be included in the quantification
		self.include_bodyparts=False # whether to include body parts in the pattern images
		self.std=0 # a value between 0 and 255, higher value, less body parts will be included in the pattern images
		self.uncertain=0 # a threshold between the highest the 2nd highest probablity of behaviors to determine if output an 'NA' in behavior classification
		self.min_length=None # the minimum length (in frames) a behavior should last, can be used to filter out the brief false positives
		self.show_legend=True # whether to show legend of behavior names in the annotated videos
		self.background_free=True # whether to include background in animations
		self.black_background=True # whether to set background black
		self.normalize_distance=True # whether to normalize the distance (in pixel) to the animal contour area
		self.social_distance=0 # a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		self.specific_behaviors={} # sex or identity-specific behaviors
		self.correct_ID=False # whether to use sex or identity-specific behaviors to guide ID correction when ID switching is likely to happen

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_selectcategorizer=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcategorizer=wx.Button(panel,label='Select a Categorizer for\nbehavior classification',size=(300,40))
		button_selectcategorizer.Bind(wx.EVT_BUTTON,self.select_categorizer)
		wx.Button.SetToolTip(button_selectcategorizer,'The fps of the videos to analyze should match that of the selected Categorizer. Uncertain level determines the threshold for the Categorizer to output an ‘NA’ for behavioral classification. See Extended Guide for details.')
		self.text_selectcategorizer=wx.StaticText(panel,label='Default: no behavior classification, just track animals and quantify motion kinematics.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcategorizer.Add(button_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcategorizer.Add(self.text_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s) / image(s)\nfor behavior analysis',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		wx.Button.SetToolTip(button_inputvideos,'Select one or more videos / images for a behavior analysis batch. If analyzing videos, one analysis batch will yield one raster plot showing the behavior events of all the animals in all selected videos. For "Static images" mode, each annotated images will be in this folder. See Extended Guide for details.')
		self.text_inputvideos=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store\nthe analysis results',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'If analyzing videos, will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video and stores the detailed analysis results for this video. For "Static images" mode, all results will be in this folder. See Extended Guide for details.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_detection=wx.BoxSizer(wx.HORIZONTAL)
		button_detection=wx.Button(panel,label='Specify the method to\ndetect animals or objects',size=(300,40))
		button_detection.Bind(wx.EVT_BUTTON,self.select_method)
		wx.Button.SetToolTip(button_detection,'Background subtraction-based method is accurate and fast but requires static background and stable illumination in videos; Detectors-based method is accurate and versatile in any recording settings but is slow. See Extended Guide for details.')
		self.text_detection=wx.StaticText(panel,label='Default: Background subtraction-based method.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_detection.Add(button_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detection.Add(self.text_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startanalyze=wx.BoxSizer(wx.HORIZONTAL)
		button_startanalyze=wx.Button(panel,label='Specify when the analysis\nshould begin (unit: second)',size=(300,40))
		button_startanalyze.Bind(wx.EVT_BUTTON,self.specify_timing)
		wx.Button.SetToolTip(button_startanalyze,'Enter a beginning time point for all videos in one analysis batch or use "Decode from filenames" to let LabGym decode the different beginning time for different videos. See Extended Guide for details.')
		self.text_startanalyze=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startanalyze.Add(button_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startanalyze.Add(self.text_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify the analysis duration\n(unit: second)',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		wx.Button.SetToolTip(button_duration,'The duration is the same for all the videos in a same analysis batch.')
		self.text_duration=wx.StaticText(panel,label='Default: from the specified beginning time to the end of a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_animalnumber=wx.BoxSizer(wx.HORIZONTAL)
		button_animalnumber=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_animalnumber.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		wx.Button.SetToolTip(button_animalnumber,'Enter a number for all videos in one analysis batch or use "Decode from filenames" to let LabGym decode the different animal number for different videos. See Extended Guide for details.')
		self.text_animalnumber=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_animalnumber.Add(button_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_animalnumber.Add(self.text_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectbehaviors=wx.BoxSizer(wx.HORIZONTAL)
		button_selectbehaviors=wx.Button(panel,label='Select the behaviors for\nannotations and plots',size=(300,40))
		button_selectbehaviors.Bind(wx.EVT_BUTTON,self.select_behaviors)
		wx.Button.SetToolTip(button_selectbehaviors,'The behavior categories are determined by the selected Categorizer. Select which behaviors to show in the annotated videos / images and the raster plot (only for videos). See Extended Guide for details.')
		self.text_selectbehaviors=wx.StaticText(panel,label='Default: No Categorizer selected, no behavior selected.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectbehaviors.Add(button_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectbehaviors.Add(self.text_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectparameters=wx.BoxSizer(wx.HORIZONTAL)
		button_selectparameters=wx.Button(panel,label='Select the quantitative measurements\nfor each behavior',size=(300,40))
		button_selectparameters.Bind(wx.EVT_BUTTON,self.select_parameters)
		wx.Button.SetToolTip(button_selectparameters,'If select "not to normalize distances", all distances will be output in pixels. If select "normalize distances", all distances will be normalized to the animal size. See Extended Guide for details.')
		self.text_selectparameters=wx.StaticText(panel,label='Default: none.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectparameters.Add(button_selectparameters,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectparameters.Add(self.text_selectparameters,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectparameters,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_analyze=wx.Button(panel,label='Start to analyze the behaviors',size=(300,40))
		button_analyze.Bind(wx.EVT_BUTTON,self.analyze_behaviors)
		wx.Button.SetToolTip(button_analyze,'If analyzing videos, will output a raster plot for all behavior events in all videos, an annotated video copy for each video, various spreadsheets storing quantification results for each selected behavior parameter. For "Static images" mode, will output annotated image copies and spreadsheet storing behavior count and probability.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_analyze,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_categorizer(self,event):

		if self.model_path is None:
			self.model_path = self._config['models']

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()
		if 'No behavior classification, just track animals and quantify motion kinematics' not in categorizers:
			categorizers.append('No behavior classification, just track animals and quantify motion kinematics')
		if 'Choose a new directory of the Categorizer' not in categorizers:
			categorizers.append('Choose a new directory of the Categorizer')

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer for behavior classification',caption='Select a Categorizer',choices=categorizers)

		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			if categorizer=='Choose a new directory of the Categorizer':
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.path_to_categorizer=dialog1.GetPath()
				dialog1.Destroy()
				dialog1=wx.NumberEntryDialog(self,"Enter the Categorizer's uncertainty level (0~100%)","If probability difference between\n1st- and 2nd-likely behaviors\nis less than uncertainty,\nclassfication outputs an 'NA'. Enter 0 if don't know how to set.",'Uncertainty level',0,0,100)
				if dialog1.ShowModal()==wx.ID_OK:
					uncertain=dialog1.GetValue()
					self.uncertain=uncertain/100
				else:
					uncertain=0
					self.uncertain=0
				dialog1.Destroy()
				if self.path_to_categorizer is not None:
					parameters=pd.read_csv(os.path.join(self.path_to_categorizer,'model_parameters.txt'))
					if 'behavior_kind' in parameters:
						self.behavior_mode=int(parameters['behavior_kind'][0])
					else:
						self.behavior_mode=0
				if self.behavior_mode<3:
					dialog1=wx.MessageDialog(self,"Set a minimum length (in frames) for a behavior episode\nto output 'NA' if the duration of a identified behavior\nis shorter than the minimun length?",'Minimum length?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog1.ShowModal()==wx.ID_YES:
						dialog2=wx.NumberEntryDialog(self,'Enter the minimun length (in frames)',"If the duration of a identified behavior\nis shorter than the minimun length,\nthe behavior categorization will output as 'NA'.",'Minimum length',2,1,10000)
						if dialog2.ShowModal()==wx.ID_OK:
							self.min_length=int(dialog2.GetValue())
							if self.min_length<2:
								self.min_length=2
						else:
							self.min_length=None
						dialog2.Destroy()
					else:
						self.min_length=None
					dialog1.Destroy()
				if self.min_length is None:
					self.text_selectcategorizer.SetLabel('The path to the Categorizer is: '+self.path_to_categorizer+' with uncertainty of '+str(uncertain)+'%.')
				else:
					self.text_selectcategorizer.SetLabel('The path to the Categorizer is: '+self.path_to_categorizer+' with uncertainty of '+str(uncertain)+'%; minimun length of '+str(self.min_length)+'.')
				self.text_selectbehaviors.SetLabel('All the behaviors in the selected Categorizer with default colors.')
			elif categorizer=='No behavior classification, just track animals and quantify motion kinematics':
				self.path_to_categorizer=None
				self.behavior_mode=0
				dialog1=wx.NumberEntryDialog(self,'Specify a time window used for measuring\nmotion kinematics of the tracked animals','Enter the number of\nframes (minimum=3):','Time window for calculating kinematics',15,1,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.length=int(dialog1.GetValue())
					if self.length<3:
						self.length=3
				dialog1.Destroy()
				self.text_selectcategorizer.SetLabel('No behavior classification; the time window to measure kinematics of tracked animals is: '+str(self.length)+' frames.')
				self.text_selectbehaviors.SetLabel('No behavior classification. Just track animals and quantify motion kinematics.')
			else:
				self.path_to_categorizer=os.path.join(self.model_path,categorizer)
				dialog1=wx.NumberEntryDialog(self,"Enter the Categorizer's uncertainty level (0~100%)","If probability difference between\n1st- and 2nd-likely behaviors\nis less than uncertainty,\nclassfication outputs an 'NA'.",'Uncertainty level',0,0,100)
				if dialog1.ShowModal()==wx.ID_OK:
					uncertain=dialog1.GetValue()
					self.uncertain=uncertain/100
				else:
					uncertain=0
					self.uncertain=0
				dialog1.Destroy()
				if self.path_to_categorizer is not None:
					parameters=pd.read_csv(os.path.join(self.path_to_categorizer,'model_parameters.txt'))
					if 'behavior_kind' in parameters:
						self.behavior_mode=int(parameters['behavior_kind'][0])
					else:
						self.behavior_mode=0
				if self.behavior_mode<3:
					dialog1=wx.MessageDialog(self,"Set a minimum length (in frames) for a behavior episode\nto output 'NA' if the duration of a identified behavior\nis shorter than the minimun length?",'Minimum length?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog1.ShowModal()==wx.ID_YES:
						dialog2=wx.NumberEntryDialog(self,'Enter the minimun length (in frames)',"If the duration of a identified behavior\nis shorter than the minimun length,\nthe behavior categorization will output as 'NA'.",'Minimum length',2,1,10000)
						if dialog2.ShowModal()==wx.ID_OK:
							self.min_length=int(dialog2.GetValue())
							if self.min_length<2:
								self.min_length=2
						else:
							self.min_length=None
						dialog2.Destroy()
					else:
						self.min_length=None
					dialog1.Destroy()
				if self.min_length is None:
					self.text_selectcategorizer.SetLabel('Categorizer: '+categorizer+' with uncertainty of '+str(uncertain)+'%.')
				else:
					self.text_selectcategorizer.SetLabel('Categorizer: '+categorizer+' with uncertainty of '+str(uncertain)+'%; minimun length of '+str(self.min_length)+'.')
				self.text_selectbehaviors.SetLabel('All the behaviors in the selected Categorizer with default colors.')

			if self.path_to_categorizer is not None:

				parameters=pd.read_csv(os.path.join(self.path_to_categorizer,'model_parameters.txt'))
				complete_colors=list(mpl.colors.cnames.values())
				colors=[]
				for c in complete_colors:
					colors.append(['#ffffff',c])
				self.behaviornames_and_colors={}

				for behavior_name in list(parameters['classnames']):
					index=list(parameters['classnames']).index(behavior_name)
					if index<len(colors):
						self.behaviornames_and_colors[behavior_name]=colors[index]
					else:
						self.behaviornames_and_colors[behavior_name]=['#ffffff','#ffffff']

				if 'dim_conv' in parameters:
					self.dim_conv=int(parameters['dim_conv'][0])
				if 'dim_tconv' in parameters:
					self.dim_tconv=int(parameters['dim_tconv'][0])
				self.channel=int(parameters['channel'][0])
				self.length=int(parameters['time_step'][0])
				if self.length<3:
					self.length=3
				categorizer_type=int(parameters['network'][0])
				if categorizer_type==2:
					self.animation_analyzer=True
				else:
					self.animation_analyzer=False
				if int(parameters['inner_code'][0])==0:
					self.include_bodyparts=True
				else:
					self.include_bodyparts=False
				self.std=int(parameters['std'][0])
				if int(parameters['background_free'][0])==0:
					self.background_free=True
				else:
					self.background_free=False
				if 'behavior_kind' in parameters:
					self.behavior_mode=int(parameters['behavior_kind'][0])
				else:
					self.behavior_mode=0
				if self.behavior_mode==2:
					self.social_distance=int(parameters['social_distance'][0])
					if self.social_distance==0:
						self.social_distance=float('inf')
					self.text_detection.SetLabel('Only Detector-based detection method is available for the selected Categorizer.')
				if self.behavior_mode==3:
					self.text_detection.SetLabel('Only Detector-based detection method is available for the selected Categorizer.')
					self.text_startanalyze.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
					self.text_duration.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
					self.text_animalnumber.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
					self.text_selectparameters.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				if 'black_background' in parameters:
					if int(parameters['black_background'][0])==1:
						self.black_background=False

		dialog.Destroy()


	def select_videos(self,event):

		if self.behavior_mode==3:
			wildcard='Image files(*.jpg;*.jpeg;*.png;*.tiff;*.bmp)|*.jpg;*.JPG;*.jpeg;*.JPEG;*.png;*.PNG;*.tiff;*.TIFF;*.bmp;*.BMP'
		else:
			wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'

		dialog=wx.FileDialog(self,'Select video(s) / image(s)','','',wildcard,style=wx.FD_MULTIPLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			self.path_to_videos.sort()
			path=os.path.dirname(self.path_to_videos[0])
			dialog1=wx.MessageDialog(self,'Proportional resize the video frames / images? Reducing frame / image size\nis highly recommended. But select "No" if dont know what it is.','(Optional) resize the frames / images?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog1.ShowModal()==wx.ID_YES:
				dialog2=wx.NumberEntryDialog(self,'Enter the desired frame / image width','The unit is pixel:','Desired frame / image width',480,1,10000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog2.GetValue())
					if self.framewidth<10:
						self.framewidth=10
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (proportionally resize frame / image width to '+str(self.framewidth)+').')
				else:
					self.framewidth=None
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (original frame / image size).')
				dialog2.Destroy()
			else:
				self.framewidth=None
				self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (original frame / image size).')
			dialog1.Destroy()
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Results will be in: '+self.result_path+'.')
		dialog.Destroy()


	def select_method(self,event):

		if self.behavior_mode<=1:
			methods=['Subtract background (fast but requires static background & stable illumination)','Use trained Detectors (versatile but slow)']
		else:
			methods=['Use trained Detectors (versatile but slow)']

		dialog=wx.SingleChoiceDialog(self,message='How to detect the animals?',caption='Detection methods',choices=methods)

		if dialog.ShowModal()==wx.ID_OK:

			method=dialog.GetStringSelection()

			if method=='Subtract background (fast but requires static background & stable illumination)':

				self.use_detector=False
				self.animal_kinds=[]
				self.animal_number=None
				self.animal_to_include=[]
				self.ID_colors=[(255,255,255)]
				self.text_detection.SetLabel('Default: Background subtraction-based method.')
				self.text_animalnumber.SetLabel('Default: 1.')

				contrasts=['Animal brighter than background','Animal darker than background','Hard to tell']
				dialog1=wx.SingleChoiceDialog(self,message='Select the scenario that fits your videos best',caption='Which fits best?',choices=contrasts)

				if dialog1.ShowModal()==wx.ID_OK:
					contrast=dialog1.GetStringSelection()
					if contrast=='Animal brighter than background':
						self.animal_vs_bg=0
					elif contrast=='Animal darker than background':
						self.animal_vs_bg=1
					else:
						self.animal_vs_bg=2
					dialog2=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.','(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog2.ShowModal()==wx.ID_YES:
						dialog3=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
						if dialog3.ShowModal()==wx.ID_OK:
							self.background_path=dialog3.GetPath()
						dialog3.Destroy()
					else:
						self.background_path=None
						if self.animal_vs_bg!=2:
							dialog3=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.','(Optional) unstable illumination?',wx.YES_NO|wx.ICON_QUESTION)
							if dialog3.ShowModal()==wx.ID_YES:
								self.stable_illumination=False
							else:
								self.stable_illumination=True
							dialog3.Destroy()
					dialog2.Destroy()

					if self.background_path is None:
						ex_methods=['Use the entire duration (default but NOT recommended)','Decode from filenames: "_xst_" and "_xet_"','Enter two time points']
						dialog2=wx.SingleChoiceDialog(self,message='Specify the time window for background extraction',caption='Time window for background extraction',choices=ex_methods)
						if dialog2.ShowModal()==wx.ID_OK:
							ex_method=dialog2.GetStringSelection()
							if ex_method=='Use the entire duration (default but NOT recommended)':
								self.decode_extraction=False
								if self.animal_vs_bg==0:
									self.text_detection.SetLabel('Background subtraction: animal brighter, using the entire duration.')
								elif self.animal_vs_bg==1:
									self.text_detection.SetLabel('Background subtraction: animal darker, using the entire duration.')
								else:
									self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using the entire duration.')
							elif ex_method=='Decode from filenames: "_xst_" and "_xet_"':
								self.decode_extraction=True
								if self.animal_vs_bg==0:
									self.text_detection.SetLabel('Background subtraction: animal brighter, using time window decoded from filenames "_xst_" and "_xet_".')
								elif self.animal_vs_bg==1:
									self.text_detection.SetLabel('Background subtraction: animal darker, using time window decoded from filenames "_xst_" and "_xet_".')
								else:
									self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window decoded from filenames "_xst_" and "_xet_".')
							else:
								self.decode_extraction=False
								dialog3=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:','Start time for background extraction',0,0,100000000000000)
								if dialog3.ShowModal()==wx.ID_OK:
									self.ex_start=int(dialog3.GetValue())
								dialog3.Destroy()
								dialog3=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:','End time for background extraction',0,0,100000000000000)
								if dialog3.ShowModal()==wx.ID_OK:
									self.ex_end=int(dialog3.GetValue())
									if self.ex_end==0:
										self.ex_end=None
								dialog3.Destroy()
								if self.animal_vs_bg==0:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal brighter, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal brighter, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
								elif self.animal_vs_bg==1:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal darker, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal darker, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
								else:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
						dialog2.Destroy()

				dialog1.Destroy()

			else:

				self.animal_number={}
				self.detector_path = self._config['detectors']
				self.text_animalnumber.SetLabel('Default: 1.')

				detectors=[i for i in os.listdir(self.detector_path) if os.path.isdir(os.path.join(self.detector_path,i))]
				if '__pycache__' in detectors:
					detectors.remove('__pycache__')
				if '__init__' in detectors:
					detectors.remove('__init__')
				if '__init__.py' in detectors:
					detectors.remove('__init__.py')
				detectors.sort()
				if 'Choose a new directory of the Detector' not in detectors:
					detectors.append('Choose a new directory of the Detector')

				dialog1=wx.SingleChoiceDialog(self,message='Select a Detector for animal detection',caption='Select a Detector',choices=detectors)
				if dialog1.ShowModal()==wx.ID_OK:
					detector=dialog1.GetStringSelection()
					if detector=='Choose a new directory of the Detector':
						dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
						if dialog2.ShowModal()==wx.ID_OK:
							self.path_to_detector=dialog2.GetPath()
						dialog2.Destroy()
					else:
						self.path_to_detector=os.path.join(self.detector_path,detector)
					with open(os.path.join(self.path_to_detector,'model_parameters.txt')) as f:
						model_parameters=f.read()
					animal_names=json.loads(model_parameters)['animal_names']
					if len(animal_names)>1:
						dialog2=wx.MultiChoiceDialog(self,message='Specify which animals/objects involved in analysis',caption='Animal/Object kind',choices=animal_names)
						if dialog2.ShowModal()==wx.ID_OK:
							self.animal_kinds=[animal_names[i] for i in dialog2.GetSelections()]
						else:
							self.animal_kinds=animal_names
						dialog2.Destroy()
					else:
						self.animal_kinds=animal_names
					if self.behavior_mode==1:
						self.animal_to_include=[self.animal_kinds[0]]
					else:
						self.animal_to_include=self.animal_kinds
					if self.behavior_mode>=3:
						dialog2=wx.NumberEntryDialog(self,"Enter the Detector's detection threshold (0~100%)","The higher detection threshold,\nthe higher detection accuracy,\nbut the lower detection sensitivity.\nEnter 0 if don't know how to set.",'Detection threshold',0,0,100)
						if dialog2.ShowModal()==wx.ID_OK:
							detection_threshold=dialog2.GetValue()
							self.detection_threshold=detection_threshold/100
						self.text_detection.SetLabel('Detector: '+detector+' (detection threshold: '+str(detection_threshold)+'%); The animals/objects: '+str(self.animal_kinds)+'.')
						dialog2.Destroy()
					else:
						for animal_name in self.animal_kinds:
							self.animal_number[animal_name]=1
						self.text_animalnumber.SetLabel('The number of '+str(self.animal_kinds)+' is: '+str(list(self.animal_number.values()))+'.')
						self.text_detection.SetLabel('Detector: '+detector+'; '+'The animals/objects: '+str(self.animal_kinds)+'.')
				dialog1.Destroy()

				if self.path_to_detector is None:
					self.use_detector=False
					self.animal_kinds=[]
					self.animal_number=None
					self.animal_to_include=[]
					self.ID_colors=[(255,255,255)]
					self.text_detection=wx.StaticText(panel,label='Default: Background subtraction-based method.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
					self.text_animalnumber=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
				else:
					self.use_detector=True
					if self.behavior_mode<3:
						if torch.cuda.is_available():
							dialog1=wx.NumberEntryDialog(self,'Enter the batch size for faster processing','GPU is available in this device for Detectors.\nYou may use batch processing for faster speed.','Batch size',1,1,100)
							if dialog1.ShowModal()==wx.ID_OK:
								self.detector_batch=int(dialog1.GetValue())
							else:
								self.detector_batch=1
							dialog1.Destroy()

		dialog.Destroy()


	def specify_timing(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.use_detector is False:
				dialog=wx.MessageDialog(self,'light on and off in videos?','Illumination shifts?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.delta=1.2
				else:
					self.delta=10000
				dialog.Destroy()

			if self.delta==1.2 and self.use_detector is False:
				methods=['Automatic (for light on and off)','Decode from filenames: "_bt_"','Enter a time point']
			else:
				methods=['Decode from filenames: "_bt_"','Enter a time point']

			dialog=wx.SingleChoiceDialog(self,message='Specify beginning time of analysis',caption='Beginning time of analysis',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Automatic (for light on and off)':
					self.autofind_t=True
					self.decode_t=False
					self.text_startanalyze.SetLabel('Automatically find the onset of the 1st time when light on / off as the beginning time.')
				elif method=='Decode from filenames: "_bt_"':
					self.autofind_t=False
					self.decode_t=True
					self.text_startanalyze.SetLabel('Decode the beginning time from the filenames: the "t" immediately after the letter "b"" in "_bt_".')
				else:
					self.autofind_t=False
					self.decode_t=False
					dialog2=wx.NumberEntryDialog(self,'Enter the beginning time of analysis','The unit is second:','Beginning time of analysis',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.t=float(dialog2.GetValue())
						if self.t<0:
							self.t=0
						self.text_startanalyze.SetLabel('Analysis will begin at the: '+str(self.t)+' second.')
					dialog2.Destroy()
			dialog.Destroy()


	def input_duration(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'Enter the duration of the analysis','The unit is second:','Analysis duration',0,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.duration=int(dialog.GetValue())
				if self.duration!=0:
					self.text_duration.SetLabel('The analysis duration is '+str(self.duration)+' seconds.')
				else:
					self.text_duration.SetLabel('The analysis duration is from the specified beginning time to the end of a video.')
			dialog.Destroy()


	def specify_animalnumber(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			methods=['Decode from filenames: "_nn_"','Enter the number of animals']

			dialog=wx.SingleChoiceDialog(self,message='Specify the number of animals in a video',caption='The number of animals in a video',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Enter the number of animals':
					self.decode_animalnumber=False
					if self.use_detector:
						self.animal_number={}
						for animal_name in self.animal_kinds:
							dialog1=wx.NumberEntryDialog(self,'','The number of '+str(animal_name)+': ',str(animal_name)+' number',1,1,100)
							if dialog1.ShowModal()==wx.ID_OK:
								self.animal_number[animal_name]=int(dialog1.GetValue())
							else:
								self.animal_number[animal_name]=1
							dialog1.Destroy()
						self.text_animalnumber.SetLabel('The number of '+str(self.animal_kinds)+' is: '+str(list(self.animal_number.values()))+'.')
					else:
						dialog1=wx.NumberEntryDialog(self,'','The number of animals:','Animal number',1,1,100)
						if dialog1.ShowModal()==wx.ID_OK:
							self.animal_number=int(dialog1.GetValue())
						else:
							self.animal_number=1
						self.text_animalnumber.SetLabel('The total number of animals in a video is '+str(self.animal_number)+'.')
						dialog1.Destroy()
				else:
					self.decode_animalnumber=True
					self.text_animalnumber.SetLabel('Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.')
			dialog.Destroy()

			if len(self.animal_kinds)>1:
				if self.behavior_mode==1:
					self.animal_to_include=[self.animal_kinds[0]]
				else:
					dialog=wx.MultiChoiceDialog(self,message='Specify which animals/objects to annotate',caption='Animal/Object to annotate',choices=self.animal_kinds)
					if dialog.ShowModal()==wx.ID_OK:
						self.animal_to_include=[self.animal_kinds[i] for i in dialog.GetSelections()]
					else:
						self.animal_to_include=self.animal_kinds
					dialog.Destroy()
			else:
				self.animal_to_include=self.animal_kinds

			dialog=wx.MessageDialog(self,'Specify the colors (default is white) for animal/object identities?','Specify colors for IDs?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				complete_colors=list(mpl.colors.cnames.values())
				colors=[]
				for c in complete_colors:
					colors.append(['#ffffff',c])
				self.ID_colors=[]
				if len(self.animal_to_include)>1:
					n=0
					while n<len(self.animal_to_include):
						dialog1=ColorPicker(self,self.animal_to_include[n],[self.animal_to_include[n],colors[n]])
						if dialog1.ShowModal()==wx.ID_OK:
							(r,b,g,_)=dialog1.color_picker.GetColour()
							self.ID_colors.append((b,g,r))
						else:
							self.ID_colors.append((255,255,255))
						dialog1.Destroy()
						n+=1
				else:
					dialog1=ColorPicker(self,'Animal/object color',['animal/object',colors[0]])
					if dialog1.ShowModal()==wx.ID_OK:
						(r,b,g,_)=dialog1.color_picker.GetColour()
						self.ID_colors.append((b,g,r))
					else:
						self.ID_colors.append((255,255,255))
					dialog1.Destroy()
			else:
				if len(self.animal_to_include)>1:
					self.ID_colors=[]
					for animal_name in self.animal_to_include:
						self.ID_colors.append((255,255,255))
				else:
					self.ID_colors=[(255,255,255)]
			dialog.Destroy()


	def select_behaviors(self,event):

		if self.path_to_categorizer is None:

			wx.MessageBox('No Categorizer selected! The behavior names are listed in the Categorizer.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.MultiChoiceDialog(self,message='Select behaviors',caption='Behaviors to annotate',choices=list(self.behaviornames_and_colors.keys()))
			if dialog.ShowModal()==wx.ID_OK:
				self.behavior_to_include=[list(self.behaviornames_and_colors.keys())[i] for i in dialog.GetSelections()]
			else:
				self.behavior_to_include=list(self.behaviornames_and_colors.keys())
			dialog.Destroy()

			if len(self.behavior_to_include)==0:
				self.behavior_to_include=list(self.behaviornames_and_colors.keys())
			if self.behavior_to_include[0]=='all':
				self.behavior_to_include=list(self.behaviornames_and_colors.keys())

			if self.behavior_mode==2:
				dialog=wx.MessageDialog(self,'Specify individual-specific behaviors? e.g., sex-specific behaviors only occur in a specific sex and\ncan be used to maintain the correct ID of this individual during the entire analysis.','Individual-specific behaviors?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					for animal_name in self.animal_kinds:
						dialog1=wx.MultiChoiceDialog(self,message='Select individual-specific behaviors for '+str(animal_name),caption='Individual-specific behaviors for '+str(animal_name),choices=self.behavior_to_include)
						if dialog1.ShowModal()==wx.ID_OK:
							self.specific_behaviors[animal_name]={}
							self.correct_ID=True
							specific_behaviors=[self.behavior_to_include[i] for i in dialog1.GetSelections()]
							for specific_behavior in specific_behaviors:
								self.specific_behaviors[animal_name][specific_behavior]=None
						dialog1.Destroy()
				else:
					self.correct_ID=False
				dialog.Destroy()

			complete_colors=list(mpl.colors.cnames.values())
			colors=[]
			for c in complete_colors:
				colors.append(['#ffffff',c])

			dialog=wx.MessageDialog(self,'Specify the color to represent\nthe behaviors in annotations and plots?','Specify colors for behaviors?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				names_colors={}
				n=0
				while n<len(self.behavior_to_include):
					dialog2=ColorPicker(self,self.behavior_to_include[n],[self.behavior_to_include[n],colors[n]])
					if dialog2.ShowModal()==wx.ID_OK:
						(r,b,g,_)=dialog2.color_picker.GetColour()
						new_color='#%02x%02x%02x'%(r,b,g)
						self.behaviornames_and_colors[self.behavior_to_include[n]]=['#ffffff',new_color]
						names_colors[self.behavior_to_include[n]]=new_color
					else:
						if n<len(colors):
							names_colors[self.behavior_to_include[n]]=colors[n][1]
							self.behaviornames_and_colors[self.behavior_to_include[n]]=colors[n]
					dialog2.Destroy()
					n+=1
				if self.correct_ID:
					self.text_selectbehaviors.SetLabel('Selected: '+str(list(names_colors.keys()))+'. Specific behaviors: '+str(self.specific_behaviors)+'.')
				else:
					self.text_selectbehaviors.SetLabel('Selected: '+str(list(names_colors.keys()))+'.')
			else:
				for color in colors:
					index=colors.index(color)
					if index<len(self.behavior_to_include):
						behavior_name=list(self.behaviornames_and_colors.keys())[index]
						self.behaviornames_and_colors[behavior_name]=color
				if self.correct_ID:
					self.text_selectbehaviors.SetLabel('Selected: '+str(self.behavior_to_include)+' with default colors. Specific behaviors:'+str(self.specific_behaviors)+'.')
				else:
					self.text_selectbehaviors.SetLabel('Selected: '+str(self.behavior_to_include)+' with default colors.')
			dialog.Destroy()

			if self.behavior_mode!=3:
				dialog=wx.MessageDialog(self,'Show legend of behavior names in the annotated video?','Legend in video?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.show_legend=True
				else:
					self.show_legend=False
				dialog.Destroy()


	def select_parameters(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.path_to_categorizer is None:
				parameters=['3 areal parameters','3 length parameters','4 locomotion parameters']
			else:
				if self.behavior_mode==1:
					parameters=['count','duration','latency']
				else:
					parameters=['count','duration','latency','3 areal parameters','3 length parameters','4 locomotion parameters']

			dialog=wx.MultiChoiceDialog(self,message='Select quantitative measurements',caption='Quantitative measurements',choices=parameters)
			if dialog.ShowModal()==wx.ID_OK:
				self.parameter_to_analyze=[parameters[i] for i in dialog.GetSelections()]
			else:
				self.parameter_to_analyze=[]
			dialog.Destroy()

			if len(self.parameter_to_analyze)<=0:
				self.parameter_to_analyze=[]
				self.normalize_distance=False
				self.text_selectparameters.SetLabel('NO parameter selected.')
			else:
				if '4 locomotion parameters' in self.parameter_to_analyze:
					dialog=wx.MessageDialog(self,'Normalize the distances by the size of an animal? If no, all distances will be output in pixels.','Normalize the distances?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog.ShowModal()==wx.ID_YES:
						self.normalize_distance=True
						self.text_selectparameters.SetLabel('Selected: '+str(self.parameter_to_analyze)+'; with normalization of distance.')
					else:
						self.normalize_distance=False
						self.text_selectparameters.SetLabel('Selected: '+str(self.parameter_to_analyze)+'; NO normalization of distance.')
					dialog.Destroy()
				else:
					self.normalize_distance=False
					self.text_selectparameters.SetLabel('Selected: '+str(self.parameter_to_analyze)+'.')


	def analyze_behaviors(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / result folder.','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.behavior_mode==3:

				if self.path_to_categorizer is None or self.path_to_detector is None:
					wx.MessageBox('You need to select a Categorizer / Detector.','Error',wx.OK|wx.ICON_ERROR)
				else:
					if len(self.animal_to_include)==0:
						self.animal_to_include=self.animal_kinds
					if self.detector_batch<=0:
						self.detector_batch=1
					if self.behavior_to_include[0]=='all':
						self.behavior_to_include=list(self.behaviornames_and_colors.keys())
					AAD=AnalyzeAnimalDetector()
					AAD.analyze_images_individuals(self.path_to_detector,self.path_to_videos,self.result_path,self.animal_kinds,path_to_categorizer=self.path_to_categorizer,
						generate=False,animal_to_include=self.animal_to_include,behavior_to_include=self.behavior_to_include,names_and_colors=self.behaviornames_and_colors,
						imagewidth=self.framewidth,dim_conv=self.dim_conv,channel=self.channel,detection_threshold=self.detection_threshold,uncertain=self.uncertain,
						background_free=self.background_free,black_background=self.black_background,social_distance=0)

			else:

				all_events={}
				event_data={}
				all_time=[]

				if self.use_detector:
					for animal_name in self.animal_kinds:
						all_events[animal_name]={}
					if len(self.animal_to_include)==0:
						self.animal_to_include=self.animal_kinds
					if self.detector_batch<=0:
						self.detector_batch=1

				if self.path_to_categorizer is None:
					self.behavior_to_include=[]
				else:
					if self.behavior_to_include[0]=='all':
						self.behavior_to_include=list(self.behaviornames_and_colors.keys())

				for i in self.path_to_videos:

					filename=os.path.splitext(os.path.basename(i))[0].split('_')
					if self.decode_animalnumber:
						if self.use_detector:
							self.animal_number={}
							number=[x[1:] for x in filename if len(x)>1 and x[0]=='n']
							for a,animal_name in enumerate(self.animal_kinds):
								self.animal_number[animal_name]=int(number[a])
						else:
							for x in filename:
								if len(x)>1:
									if x[0]=='n':
										self.animal_number=int(x[1:])
					if self.decode_t:
						for x in filename:
							if len(x)>1:
								if x[0]=='b':
									self.t=float(x[1:])
					if self.decode_extraction:
						for x in filename:
							if len(x)>2:
								if x[:2]=='xs':
									self.ex_start=int(x[2:])
								if x[:2]=='xe':
									self.ex_end=int(x[2:])

					if self.animal_number is None:
						if self.use_detector:
							self.animal_number={}
							for animal_name in self.animal_kinds:
								self.animal_number[animal_name]=1
						else:
							self.animal_number=1

					if self.path_to_categorizer is None:
						self.behavior_mode=0
						categorize_behavior=False
					else:
						categorize_behavior=True

					if self.use_detector is False:

						AA=AnalyzeAnimal()
						AA.prepare_analysis(i,self.result_path,self.animal_number,delta=self.delta,names_and_colors=self.behaviornames_and_colors,
							framewidth=self.framewidth,stable_illumination=self.stable_illumination,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,
							include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=categorize_behavior,animation_analyzer=self.animation_analyzer,
							path_background=self.background_path,autofind_t=self.autofind_t,t=self.t,duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,
							length=self.length,animal_vs_bg=self.animal_vs_bg)
						if self.behavior_mode==0:
							AA.acquire_information(background_free=self.background_free,black_background=self.black_background)
							AA.craft_data()
							interact_all=False
						else:
							AA.acquire_information_interact_basic(background_free=self.background_free,black_background=self.black_background)
							interact_all=True
						if self.path_to_categorizer is not None:
							AA.categorize_behaviors(self.path_to_categorizer,uncertain=self.uncertain,min_length=self.min_length)
						AA.annotate_video(self.ID_colors,self.behavior_to_include,show_legend=self.show_legend,interact_all=interact_all)
						AA.export_results(normalize_distance=self.normalize_distance,parameter_to_analyze=self.parameter_to_analyze)

						if self.path_to_categorizer is not None:
							for n in AA.event_probability:
								all_events[len(all_events)]=AA.event_probability[n]
							if len(all_time)<len(AA.all_time):
								all_time=AA.all_time

					else:

						AAD=AnalyzeAnimalDetector()
						AAD.prepare_analysis(self.path_to_detector,i,self.result_path,self.animal_number,self.animal_kinds,self.behavior_mode,
							names_and_colors=self.behaviornames_and_colors,framewidth=self.framewidth,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,
							include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=categorize_behavior,animation_analyzer=self.animation_analyzer,
							t=self.t,duration=self.duration,length=self.length,social_distance=self.social_distance)
						if self.behavior_mode==1:
							AAD.acquire_information_interact_basic(batch_size=self.detector_batch,background_free=self.background_free,black_background=self.black_background)
						else:
							AAD.acquire_information(batch_size=self.detector_batch,background_free=self.background_free,black_background=self.black_background)
						if self.behavior_mode!=1:
							AAD.craft_data()
						if self.path_to_categorizer is not None:
							AAD.categorize_behaviors(self.path_to_categorizer,uncertain=self.uncertain,min_length=self.min_length)
						if self.correct_ID:
							AAD.correct_identity(self.specific_behaviors)
						AAD.annotate_video(self.animal_to_include,self.ID_colors,self.behavior_to_include,show_legend=self.show_legend)
						AAD.export_results(normalize_distance=self.normalize_distance,parameter_to_analyze=self.parameter_to_analyze)

						if self.path_to_categorizer is not None:
							for animal_name in self.animal_kinds:
								for n in AAD.event_probability[animal_name]:
									all_events[animal_name][len(all_events[animal_name])]=AAD.event_probability[animal_name][n]
							if len(all_time)<len(AAD.all_time):
								all_time=AAD.all_time

				if self.path_to_categorizer is not None:

					max_length=len(all_time)

					if self.use_detector is False:

						for n in all_events:
							event_data[len(event_data)]=all_events[n]+[['NA',-1]]*(max_length-len(all_events[n]))
						all_events_df=pd.DataFrame(event_data,index=all_time)
						all_events_df.to_excel(os.path.join(self.result_path,'all_events.xlsx'),float_format='%.2f',index_label='time/ID')
						plot_events(self.result_path,event_data,all_time,self.behaviornames_and_colors,self.behavior_to_include,width=0,height=0)
						folders=[i for i in os.listdir(self.result_path) if os.path.isdir(os.path.join(self.result_path,i))]
						folders.sort()
						for behavior_name in self.behaviornames_and_colors:
							all_summary=[]
							for folder in folders:
								individual_summary=os.path.join(self.result_path,folder,behavior_name,'all_summary.xlsx')
								if os.path.exists(individual_summary):
									all_summary.append(pd.read_excel(individual_summary))
							if len(all_summary)>=1:
								all_summary=pd.concat(all_summary,ignore_index=True)
								all_summary.to_excel(os.path.join(self.result_path,behavior_name+'_summary.xlsx'),float_format='%.2f',index_label='ID/parameter')

					else:

						for animal_name in self.animal_to_include:
							for n in all_events[animal_name]:
								event_data[len(event_data)]=all_events[animal_name][n]+[['NA',-1]]*(max_length-len(all_events[animal_name][n]))
							event_data[len(event_data)]=[['NA',-1]]*max_length
						del event_data[len(event_data)-1]
						all_events_df=pd.DataFrame(event_data,index=all_time)
						all_events_df.to_excel(os.path.join(self.result_path,'all_events.xlsx'),float_format='%.2f',index_label='time/ID')
						plot_events(self.result_path,event_data,all_time,self.behaviornames_and_colors,self.behavior_to_include,width=0,height=0)
						folders=[i for i in os.listdir(self.result_path) if os.path.isdir(os.path.join(self.result_path,i))]
						folders.sort()
						for animal_name in self.animal_kinds:
							for behavior_name in self.behaviornames_and_colors:
								all_summary=[]
								for folder in folders:
									individual_summary=os.path.join(self.result_path,folder,behavior_name,animal_name+'_all_summary.xlsx')
									if os.path.exists(individual_summary):
										all_summary.append(pd.read_excel(individual_summary))
								if len(all_summary)>=1:
									all_summary=pd.concat(all_summary,ignore_index=True)
									all_summary.to_excel(os.path.join(self.result_path,animal_name+'_'+behavior_name+'_summary.xlsx'),float_format='%.2f',index_label='ID/parameter')

			print('Analysis completed!')



class WindowLv2_MineResults(wx.Frame):

	'''
	The 'Mine Results' functional unit
	'''

	def __init__(self,title):

		super(WindowLv2_MineResults,self).__init__(parent=None,title=title,size=(1000,260))
		self.file_path=None # the path to LabGym analysis results
		self.result_path=None # the folder to store data mining results
		self.dataset=None # store the dataset in RAM
		self.paired=False # whether the data is paired
		self.control=None # the dataset of the control group
		self.pval=0.05 # the p value that decides whether the statistical tests are significant to show
		self.file_names=None # the names of the LabGym analysis results folders
		self.control_file_name=None # the name of the control folder

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that contains\nthe LabGym analysis output folders',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.select_filepath)
		wx.Button.SetToolTip(button_inputfolder,'Put all LabGym analysis output folders of different batches (each folder contains one raster plot for one batch) that you want to compare into this folder.')
		self.text_inputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectcontrol=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcontrol=wx.Button(panel,label='Select the\ncontrol group',size=(300,40))
		button_selectcontrol.Bind(wx.EVT_BUTTON, self.select_control)
		wx.Button.SetToolTip(button_selectcontrol,'For multiple-group comparison, you can select one group as control for post-hoc comparison. If no control is selected, post-hoc comparison will be performed between each pair of the two groups.')
		self.text_selectcontrol=wx.StaticText(panel,label='Default: no control group.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcontrol.Add(button_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcontrol.Add(self.text_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe data mining results',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_result_path)
		wx.Button.SetToolTip(button_outputfolder,'A spreadsheet containing all data mining results will be stored in this folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_minedata=wx.Button(panel,label='Start to mine data',size=(300,40))
		button_minedata.Bind(wx.EVT_BUTTON,self.mine_data)
		wx.Button.SetToolTip(button_minedata,'Parametric / non-parametric tests will be automatically selected according to the data distribution, to compare the mean / median of different groups. See Extended Guide for details.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_minedata,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_filepath(self,event):

		dialog=wx.MessageDialog(self,'Is the data paired?','Paired data?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.paired=True
		else:
			self.paired=False
		dialog.Destroy()

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			if self.paired:
				self.text_inputfolder.SetLabel('Paired input data is in: '+self.file_path+'.')
			else:
				self.text_inputfolder.SetLabel('Unpaired input data is in: '+self.file_path+'.')
		dialog.Destroy()


	def select_control(self,event):

		dialog=wx.SingleChoiceDialog(self,'Select the folder for the control group.','Ignore if you wish to compare all groups',choices=[i for i in os.listdir(self.file_path) if os.path.isdir(os.path.join(self.file_path,i))],style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			control_path=dialog.GetStringSelection()
			self.text_selectcontrol.SetLabel('The control group is: '+control_path+'.')
			self.control=self.read_folder(os.path.join(self.file_path,control_path))
			self.control_file_name=os.path.split(control_path)[1]
		else:
			self.control=None
			self.text_selectcontrol.SetLabel('No control group.')
		dialog.Destroy()


	def select_result_path(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Mining results are in: '+self.result_path+'.')
		dialog.Destroy()


	def read_folder(self,folder):

		folder=folder.replace('\\','/')
		filelist={}
		df={}
		for i in os.listdir(folder):
			if (i.endswith('_summary.xlsx') or i.endswith('_summary.xls') or i.endswith('_summary.XLS')):
				behavior_name=i.split('_')[-2]
				filelist[behavior_name]=os.path.join(folder,i)
		if len(filelist)==0:
			print('No "_summary.xlsx" excel file found!')
		else:
			for behavior_name in filelist:
				dataset=pd.read_excel(r''+filelist[behavior_name])
				dataset=dataset.drop(columns=['ID/parameter'])
				df[behavior_name]=dataset
		return df


	def read_all_folders(self):

		data=[]
		filenames=[]
		for file in os.listdir(self.file_path):
			subfolder=os.path.join(self.file_path,file)
			if os.path.isdir(subfolder):
				folder_data=self.read_folder(subfolder)
				if len(folder_data)>0:
					data.append(folder_data)
					filenames.append(os.path.split(subfolder)[1])
				else:
					print("Improper file / file structure in: "+subfolder+'.')
		self.dataset=data
		self.file_names=filenames

	def control_organization(self):

		if self.control is None:
			return
		del_idx=self.file_names.index(self.control_file_name)
		self.dataset.pop(del_idx)
		self.file_names.insert(0,self.file_names.pop(del_idx))


	def mine_data(self,event):

		if self.file_path is None or self.result_path is None:

			wx.MessageBox('No input / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.TextEntryDialog(self,'Enter a p-value to determine statistical significance','Default p-value is 0.05','0.05')
			if dialog.ShowModal()==wx.ID_OK:
				self.pval=float(dialog.GetValue())
			dialog.Destroy()

			print('Start to mine analysis results...')

			self.read_all_folders()
			self.control_organization()
			DM=data_mining(self.dataset,self.control,self.paired,self.result_path,self.pval,self.file_names)
			DM.statistical_analysis()



class WindowLv2_PlotBehaviors(wx.Frame):

	'''
	The 'Plot Behaviors' functional unit
	'''

	def __init__(self,title):

		super(WindowLv2_PlotBehaviors,self).__init__(parent=None,title=title,size=(1000,260))
		self.events_probability=None # read from 'all_events.xsls' to store the behavior events and probability of each animal / object
		self.time_points=None # the frame-wise time points of the events_probablity
		self.results_folder=None # the folder that stores the ouput behavior plot
		self.names_and_colors=None # the user-defined color for each behavior

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputfile=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfile=wx.Button(panel,label='Select the\nall_events.xlsx file',size=(300,40))
		button_inputfile.Bind(wx.EVT_BUTTON,self.input_file)
		wx.Button.SetToolTip(button_inputfile,'The all_events.xlsx file should be as the same format as that of LabGym output, which can be found in the analysis result folder.')
		self.text_inputfile=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfile.Add(button_inputfile,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfile.Add(self.text_inputfile,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfile,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select folder to store\nthe behavior plot',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_result_path)
		wx.Button.SetToolTip(button_outputfolder,'Behavior plot is a raster plot containing all behavior events / probability over time.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectcolors=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcolors=wx.Button(panel,label='Select colors\nfor each behavior',size=(300,40))
		button_selectcolors.Bind(wx.EVT_BUTTON,self.select_colors)
		wx.Button.SetToolTip(button_selectcolors,'Select colors for annotating each behavior.')
		self.text_selectcolors=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcolors.Add(button_selectcolors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcolors.Add(self.text_selectcolors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectcolors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_plotbehavior=wx.Button(panel,label='Generate behavior plot',size=(300,40))
		button_plotbehavior.Bind(wx.EVT_BUTTON,self.plot_behavior)
		wx.Button.SetToolTip(button_plotbehavior,'Generate a behavior plot for a selected all_events.xlsx file that is in LabGym output format.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_plotbehavior,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def input_file(self,event):

		dialog=wx.FileDialog(self,'Select the all_events.xlsx file.','',wildcard='all_events file (*.xlsx)|*.xlsx',style=wx.FD_OPEN)
		if dialog.ShowModal()==wx.ID_OK:
			all_events_file=Path(dialog.GetPath())
			self.names_and_colors={}
			self.events_probability,self.time_points,behavior_names=parse_all_events_file(all_events_file)
			colors=[('#ffffff',str(hex_code)) for hex_code in mpl.colors.cnames.values()]
			for color,behavior in zip(colors,behavior_names):
				self.names_and_colors[behavior]=color
			self.text_inputfile.SetLabel(f'all_events.xlsx path: {all_events_file}')
		dialog.Destroy()


	def select_result_path(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.results_folder=dialog.GetPath()
			self.text_outputfolder.SetLabel(f'Results folder: {self.results_folder}')
		dialog.Destroy()


	def select_colors(self,event):

		if self.events_probability is None or self.names_and_colors is None:
			wx.MessageBox('No all_events.xlsx file selected!','Error',wx.OK | wx.ICON_ERROR)
		else:
			for behavior in self.names_and_colors:
				dialog=ColorPicker(self,f'{behavior}',[behavior,self.names_and_colors[behavior]])
				if dialog.ShowModal()==wx.ID_OK:
					(r,b,g,_)=dialog.color_picker.GetColour()
					new_color='#%02x%02x%02x'%(r,b,g)
					self.names_and_colors[behavior]=('#ffffff',new_color)
			self.text_selectcolors.SetLabel('Colors: '+', '.join([f'{behavior}:{color}' for behavior,(_,color) in self.names_and_colors.items()]))


	def plot_behavior(self,event):

		if self.events_probability is None or self.time_points is None or self.results_folder is None or self.names_and_colors is None:
			wx.MessageBox('No input file / output folder / behavior colors selected.','Error',wx.OK|wx.ICON_ERROR)
		else:
			plot_events(self.results_folder,self.events_probability,self.time_points,self.names_and_colors,list(self.names_and_colors.keys()))



class WindowLv2_CalculateDistances(wx.Frame):

	'''
	The 'Calculate Distances' functional unit
	'''

	def __init__(self,title):

		super(WindowLv2_CalculateDistances,self).__init__(parent=None,title=title,size=(1000,260))
		self.path_to_analysis_results=None # the folder that stores LabGym analysis results
		self.out_path=None # the folder to store the calculated distances
		self.behavior_to_include=None # the behaviors used in calculation

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that stores\nLabGym analysis results',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.select_inputpath)
		wx.Button.SetToolTip(button_inputfolder,'This is the folder that stores the raster plot after LabGym behavioral analysis')
		self.text_inputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe calculated distances',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outputpath)
		wx.Button.SetToolTip(button_outputfolder,'In this folder there will be a spreadsheet storing the calculated distances for each video.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectbehaviors=wx.BoxSizer(wx.HORIZONTAL)
		button_selectbehaviors=wx.Button(panel,label='Select behaviors to be\nincluded in the calculation',size=(300,40))
		button_selectbehaviors.Bind(wx.EVT_BUTTON,self.select_behaviors)
		wx.Button.SetToolTip(button_selectbehaviors,'The locations where the animals perform the selected behaviors for the first time will be used to calculate shortest distances among these locations, as well as the total traveling distances of the actual route.')
		self.text_selectbehaviors=wx.StaticText(panel,label='All identified behaviors in the experiments.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectbehaviors.Add(button_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectbehaviors.Add(self.text_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectbehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_calculatedistances=wx.Button(panel,label='Start to calculate distances',size=(300,40))
		button_calculatedistances.Bind(wx.EVT_BUTTON,self.calculate_distances)
		wx.Button.SetToolTip(button_calculatedistances,'Two types of distances will be calculated: 1. The shortest distances among the locations where animals perform the selected behaviors for the first time. 2. The total traveling distances of the actual route.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_calculatedistances,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_inputpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_analysis_results=dialog.GetPath()
			self.text_inputfolder.SetLabel('Selected: '+self.path_to_analysis_results+'.')
		dialog.Destroy()


	def select_outputpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.out_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Calculated distances are in: '+self.out_path+'.')
		dialog.Destroy()


	def select_behaviors(self,event):

		if self.path_to_analysis_results is None:

			wx.MessageBox('No input folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			behavior_names=[]
			for i in os.listdir(self.path_to_analysis_results):
				if os.path.isdir(os.path.join(self.path_to_analysis_results,i)):
					for behavior in os.listdir(os.path.join(self.path_to_analysis_results,i)):
						if os.path.isdir(os.path.join(self.path_to_analysis_results,i,behavior)):
							if behavior not in behavior_names:
								behavior_names.append(behavior)

			if len(behavior_names)==0:
				wx.MessageBox('No identified behavior in the LabGym analysis results.','Error',wx.OK|wx.ICON_ERROR)
			else:
				dialog=wx.MultiChoiceDialog(self,message='Select behaviors',caption='Behaviors to include',choices=behavior_names)
				if dialog.ShowModal()==wx.ID_OK:
					self.behavior_to_include=[behavior_names[i] for i in dialog.GetSelections()]
				else:
					self.behavior_to_include=behavior_names
				dialog.Destroy()
				if len(self.behavior_to_include)==0:
					self.behavior_to_include=behavior_names
				self.text_selectbehaviors.SetLabel('Behaviors to include: '+str(self.behavior_to_include)+'.')


	def calculate_distances(self,event):

		if self.path_to_analysis_results is None or self.out_path is None or self.behavior_to_include is None:

			wx.MessageBox('No input / output folder / behaviors selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			all_data=[]
			names=[]

			for filename in os.listdir(self.path_to_analysis_results):
				filefolder=os.path.join(self.path_to_analysis_results,filename)
				if os.path.isdir(filefolder):
					calculate_distances(filefolder,filename,self.behavior_to_include,self.out_path)

			for file in os.listdir(self.out_path):
				if file.endswith('_distance_calculation.xlsx') or file.endswith('_distance_calculation.xls') or file.endswith('_distance_calculation.XLSX') or file.endswith('_distance_calculation.XLS'):
					individual_data=os.path.join(self.out_path,file)
					if os.path.exists(individual_data):
						all_data.append(pd.read_excel(individual_data))
						names.append(file.split('_distance_calculation')[0])

			if len(all_data)>=1:
				all_data=pd.concat(all_data,keys=names,names=['File name','ID/parameter'])
				all_data.drop(all_data.columns[0],axis=1,inplace=True)
				all_data.to_excel(os.path.join(self.out_path,'all_summary.xlsx'),float_format='%.2f')
