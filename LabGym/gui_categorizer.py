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
import json
import logging
import os
# from pathlib import Path
import shutil

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Related third party imports.
import cv2
import numpy as np
import wx
import wx.richtext
import wx.lib.buttons as wxbuttons

# Local application/library specific imports.
logger.debug('importing %s ...', '.analyzebehavior')
from .analyzebehavior import AnalyzeAnimal
logger.debug('importing %s done', '.analyzebehavior')
logger.debug('importing %s ...', '.analyzebehavior_dt')
from .analyzebehavior_dt import AnalyzeAnimalDetector
logger.debug('importing %s done', '.analyzebehavior_dt')
from .categorizer import Categorizers
from LabGym import config
from .tools import sort_examples_from_csv
from .gui_utils import (
	add_or_select_notebook_page,
	add_info_button,
	create_hyperlink,
	INFO_COLOUR_S3,
	count_prepared_examples,
	count_sorted_examples,
	counts_enable_diagnostics,
)


class PanelLv2_GenerateExamples(wx.Panel):

	'''
	The 'Generate Behavior Examples' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		# Get all of the values needed from config.get_config().
		self.config = config.get_config('detectors', 'models')

		self.behavior_mode=0 # 0: non-interactive behavior; 1: interact basic; 2: interact advanced; 3: static images
		self.use_detector=False # whether the Detector is used
		self.detector_path=None # the 'LabGym/detectors' folder, which stores all the trained Detectors
		self.path_to_detector=None # path to the Detector
		self.detection_threshold=0 # only for 'static images' behavior mode
		self.animal_kinds=[] # the total categories of animals / objects in a Detector
		self.background_path=None # if not None, load background images from path in 'background subtraction' detection method
		self.path_to_videos=None # path to a batch of videos for generating behavior examples
		self.result_path=None # the folder for storing the unsorted behavior examples
		self.framewidth=None # if not None, will resize the video frame keeping the original w:h ratio
		self.delta=10000 # the fold changes in illumination that determines the optogenetic stimulation onset
		self.decode_animalnumber=False # whether to decode animal numbers from '_nn_' in video file names
		self.animal_number=None # the number of animals / objects in a video
		self.autofind_t=False # whether to find stimulation onset automatically (only for optogenetics)
		self.decode_t=False # whether to decode start_t from '_bt_' in video file names
		self.t=0 # the start_t for generating behavior examples
		self.duration=0 # the duration for generating behavior examples
		self.decode_extraction=False # whether to decode time windows for background extraction from '_xst_' and '_xet_' in video file names
		self.ex_start=0 # start time for background extraction
		self.ex_end=None # end time for background extraction
		self.animal_vs_bg=0 # 0: animals birghter than the background; 1: animals darker than the background; 2: hard to tell
		self.stable_illumination=True # whether the illumination in videos is stable
		self.length=15 # the duration / length for a behavior example, is also the input time step for Animation Analyzer
		self.skip_redundant=1 # the interval (in frames) of two consecutively generated behavior example pairs
		self.include_bodyparts=False # whether to include body parts in the pattern images
		self.std=0 # a value between 0 and 255, higher value, less body parts will be included in the pattern images
		self.background_free=True # whether to include background in animations
		self.black_background=True # whether to set background black
		self.social_distance=0 # a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		self.color_costar=False # in 'interactive advanced' mode, whether to make the supporting roles RGB scale in animations

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_specifymode=wx.BoxSizer(wx.HORIZONTAL)
		button_specifymode=wx.Button(panel,label='Specify the mode of behavior\nexamples to generate',size=(300,40))
		button_specifymode.Bind(wx.EVT_BUTTON,self.specify_mode)
		wx.Button.SetToolTip(button_specifymode,'"Non-interactive" is for behaviors of each individual; "Interactive basic" is for interactive behaviors of all animals but not distinguishing each individual; "Interactive advanced" is slower in analysis than "basic" but distinguishes individuals during close body contact. "Static images" is for analyzing images not videos. See Extended Guide for details.')
		self.text_specifymode=wx.StaticText(panel,label='Default: Non-interactive: behaviors of each individuals (each example contains one animal / object)',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_specifymode.Add(button_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_specifymode.Add(self.text_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s) / image(s) to\ngenerate behavior examples',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		wx.Button.SetToolTip(button_inputvideos,'Select one or more videos / images. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) or image formats (jpg, jpeg, png, tiff, bmp) are supported except wmv format.')
		self.text_inputvideos=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store the\ngenerated behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video and stores the generated behavior examples. For "Static images" mode, all generated behavior examples will be in this folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_detection=wx.BoxSizer(wx.HORIZONTAL)
		button_detection=wx.Button(panel,label='Specify the method to\ndetect animals or objects',size=(300,40))
		button_detection.Bind(wx.EVT_BUTTON,self.select_method)
		wx.Button.SetToolTip(button_detection,'Background subtraction-based method is accurate and fast but needs static background and stable illumination in videos; Detectors-based method is accurate and versatile in any recording settings but is slow. See Extended Guide for details.')
		self.text_detection=wx.StaticText(panel,label='Default: Background subtraction-based method.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_detection.Add(button_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detection.Add(self.text_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startgenerate=wx.BoxSizer(wx.HORIZONTAL)
		button_startgenerate=wx.Button(panel,label='Specify when generating behavior examples\nshould begin (unit: second)',size=(300,40))
		button_startgenerate.Bind(wx.EVT_BUTTON,self.specify_timing)
		wx.Button.SetToolTip(button_startgenerate,'Enter a beginning time point for all videos or use "Decode from filenames" to let LabGym decode the different beginning time for different videos. See Extended Guide for details.')
		self.text_startgenerate=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startgenerate.Add(button_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startgenerate.Add(self.text_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify how long generating examples\nshould last (unit: second)',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		wx.Button.SetToolTip(button_duration,'The duration is the same for all the videos in one batch.')
		self.text_duration=wx.StaticText(panel,label='Default: from the specified beginning time to the end of a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_animalnumber=wx.BoxSizer(wx.HORIZONTAL)
		button_animalnumber=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_animalnumber.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		wx.Button.SetToolTip(button_animalnumber,'Enter a number for all videos or use "Decode from filenames" to let LabGym decode the different animal number for different videos. See Extended Guide for details.')
		self.text_animalnumber=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_animalnumber.Add(button_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_animalnumber.Add(self.text_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_length)
		wx.Button.SetToolTip(button_length,'The duration (the number of frames, an integer) of each behavior example, which should approximate the length of a behavior episode. This duration needs to be the same across all the behavior examples for training one Categorizer. See Extended Guide for details.')
		self.text_length=wx.StaticText(panel,label='Default: 15 frames.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_skipredundant=wx.BoxSizer(wx.HORIZONTAL)
		button_skipredundant=wx.Button(panel,label='Specify how many frames to skip when\ngenerating two consecutive behavior examples',size=(300,40))
		button_skipredundant.Bind(wx.EVT_BUTTON,self.specify_redundant)
		wx.Button.SetToolTip(button_skipredundant,'If two consecutively generated examples have many overlapping frames, they look similar, which makes training inefficient and sorting laborious. Specifying an interval (skipped frames) between two examples can address this. See Extended Guide for details.')
		self.text_skipredundant=wx.StaticText(panel,label='Default: no frame to skip (generate a behavior example every frame).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_skipredundant.Add(button_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_skipredundant.Add(self.text_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_generate=wx.Button(panel,label='Start to generate behavior examples',size=(300,40))
		button_generate.Bind(wx.EVT_BUTTON,self.generate_data)
		wx.Button.SetToolTip(button_generate,'Need to specify whether to include background and body parts in the generated behavior examples. See Extended Guide for details.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_generate,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def specify_mode(self,event):

		behavior_modes=['Non-interactive: behaviors of each individual (each example contains one animal / object)','Interactive basic: behaviors of all (each example contains all animals / objects)','Interactive advanced: behaviors of each individual and social groups (each example contains either one or multiple animals / objects)','Static images (non-interactive): behaviors of each individual in static images (each image contains one animal / object)']
		dialog=wx.SingleChoiceDialog(self,message='Specify the mode of behavior examples to generate',caption='Behavior-example mode',choices=behavior_modes)
		if dialog.ShowModal()==wx.ID_OK:
			behavior_mode=dialog.GetStringSelection()
			if behavior_mode=='Non-interactive: behaviors of each individual (each example contains one animal / object)':
				self.behavior_mode=0
			elif behavior_mode=='Interactive basic: behaviors of all (each example contains all animals / objects)':
				self.behavior_mode=1
			elif behavior_mode=='Interactive advanced: behaviors of each individual and social groups (each example contains either one or multiple animals / objects)':
				self.behavior_mode=2
				dialog1=wx.NumberEntryDialog(self,'Interactions happen within the interaction distance.','(See Extended Guide for details)\nHow many folds of square root of the animals area\nis the interaction distance (0=infinity far):','interaction distance (Enter an integer)',0,0,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.social_distance=int(dialog1.GetValue())
				else:
					self.social_distance=0
				dialog1.Destroy()
				dialog1=wx.MessageDialog(self,'Make both main and supporting characters RGB scale?\nSelect "No" if dont know what it is.','(Optional) RGB supporting characters?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.color_costar=True
				else:
					self.color_costar=False
				dialog1.Destroy()
				self.text_detection.SetLabel('Only Detector-based detection method is available for the selected behavior mode.')
			else:
				self.behavior_mode=3
				self.text_detection.SetLabel('Only Detector-based detection method is available for the selected behavior mode.')
				self.text_startgenerate.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_duration.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_animalnumber.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_length.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_skipredundant.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
		else:
			self.behavior_mode=0
			behavior_mode='Non-interactive: behaviors of each individual (each example contains one animal / object)'
		if self.behavior_mode==2:
			self.text_specifymode.SetLabel('Behavior mode: '+behavior_mode+' with interaction distance: '+str(self.social_distance)+' folds of the animal diameter.')
		else:
			self.text_specifymode.SetLabel('Behavior mode: '+behavior_mode+'.')
		dialog.Destroy()


	def select_videos(self,event):

		if self.behavior_mode>=3:
			wildcard='Image files(*.jpg;*.jpeg;*.png;*.tiff;*.bmp)|*.jpg;*.JPG;*.jpeg;*.JPEG;*.png;*.PNG;*.tiff;*.TIFF;*.bmp;*.BMP'
		else:
			wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'

		dialog=wx.FileDialog(self,'Select video(s) / image(s)','','',wildcard,style=wx.FD_MULTIPLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			self.path_to_videos.sort()
			path=os.path.dirname(self.path_to_videos[0])
			dialog1=wx.MessageDialog(self,'Proportional resize the video frames / images?\nSelect "No" if dont know what it is.','(Optional) resize the frames / images?',wx.YES_NO|wx.ICON_QUESTION)
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
			self.text_outputfolder.SetLabel('Generate behavior examples in: '+self.result_path+'.')
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

				self.use_detector=True
				self.animal_number={}
				self.detector_path = self.config['detectors']
				logger.debug('%s: %r', 'self.detector_path', self.detector_path)

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
						dialog2=wx.MultiChoiceDialog(self,message='Specify which animals/objects involved in behavior examples',caption='Animal/Object kind',choices=animal_names)
						if dialog2.ShowModal()==wx.ID_OK:
							self.animal_kinds=[animal_names[i] for i in dialog2.GetSelections()]
						else:
							self.animal_kinds=animal_names
						dialog2.Destroy()
					else:
						self.animal_kinds=animal_names
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

			dialog=wx.SingleChoiceDialog(self,message='Specify beginning time to generate behavior examples',caption='Beginning time for generator',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Automatic (for light on and off)':
					self.autofind_t=True
					self.decode_t=False
					self.text_startgenerate.SetLabel('Automatically find the onset of the 1st time when light on / off as the beginning time.')
				elif method=='Decode from filenames: "_bt_"':
					self.autofind_t=False
					self.decode_t=True
					self.text_startgenerate.SetLabel('Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".')
				else:
					self.autofind_t=False
					self.decode_t=False
					dialog2=wx.NumberEntryDialog(self,'Enter beginning time to generate examples','The unit is second:','Beginning time to generate examples',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.t=float(dialog2.GetValue())
						if self.t<0:
							self.t=0
						self.text_startgenerate.SetLabel('Start to generate behavior examples at the: '+str(self.t)+' second.')
					dialog2.Destroy()
			dialog.Destroy()


	def input_duration(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox("No need to specify this since the selected behavior mode is 'Static images'.",'Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'Enter the duration for generating examples','The unit is second:','Duration for generating examples',0,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.duration=int(dialog.GetValue())
				if self.duration!=0:
					self.text_duration.SetLabel('The generation of behavior examples lasts for '+str(self.duration)+' seconds.')
				else:
					self.text_duration.SetLabel('The generation of behavior examples lasts for the entire duration of a video.')
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


	def input_length(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'Enter the number of frames\nfor a behavior example','Enter a number\n(minimum=3):','Behavior episode duration',15,1,1000)
			if dialog.ShowModal()==wx.ID_OK:
				self.length=int(dialog.GetValue())
				if self.length<3:
					self.length=3
				self.text_length.SetLabel('The duration of a behavior example is: '+str(self.length)+' frames.')
			dialog.Destroy()


	def specify_redundant(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'How many frames to skip?','Enter a number:','Interval for generating examples',15,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.skip_redundant=int(dialog.GetValue())
				self.text_skipredundant.SetLabel('Generate a pair of example every '+str(self.skip_redundant)+' frames.')
			else:
				self.skip_redundant=1
				self.text_skipredundant.SetLabel('Generate a pair of example at every frame.')
			dialog.Destroy()


	def generate_data(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=True

			dialog=wx.MessageDialog(self,'Include background in animations? Select "No"\nif background is behavior irrelevant.','Including background?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.background_free=False
			else:
				self.background_free=True
				dialog1=wx.MessageDialog(self,'Set background black? "Yes"=black background;\n"No"=white background (if animals are black).','Black background?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.black_background=True
				else:
					self.black_background=False
				dialog1.Destroy()
			dialog.Destroy()

			if self.behavior_mode>=3:

				if self.path_to_detector is None:
					wx.MessageBox('You need to select a Detector.','Error',wx.OK|wx.ICON_ERROR)
				else:
					AAD=AnalyzeAnimalDetector()
					AAD.analyze_images_individuals(self.path_to_detector,self.path_to_videos,self.result_path,self.animal_kinds,generate=True,imagewidth=self.framewidth,detection_threshold=self.detection_threshold,background_free=self.background_free,black_background=self.black_background)

			else:

				dialog=wx.MessageDialog(self,'Include body parts in pattern images?\nSelect "No" if limb movement is neglectable.','Including body parts?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.include_bodyparts=True
					dialog2=wx.NumberEntryDialog(self,'Leave it as it is if dont know what it is.','Enter a number between 0 and 255:','STD for motionless pixels',0,0,255)
					if dialog2.ShowModal()==wx.ID_OK:
						self.std=int(dialog2.GetValue())
					else:
						self.std=0
					dialog2.Destroy()
				else:
					self.include_bodyparts=False
				dialog.Destroy()

				dialog=wx.MessageDialog(self,'Start to generate behavior examples?','Start to generate examples?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					do_nothing=False
				else:
					do_nothing=True
				dialog.Destroy()

				if do_nothing is False:

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

						if self.use_detector is False:
							AA=AnalyzeAnimal()
							AA.prepare_analysis(i,self.result_path,self.animal_number,delta=self.delta,framewidth=self.framewidth,stable_illumination=self.stable_illumination,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,animation_analyzer=False,path_background=self.background_path,autofind_t=self.autofind_t,t=self.t,duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,length=self.length,animal_vs_bg=self.animal_vs_bg)
							if self.behavior_mode==0:
								AA.generate_data(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							else:
								AA.generate_data_interact_basic(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
						else:
							AAD=AnalyzeAnimalDetector()
							AAD.prepare_analysis(self.path_to_detector,i,self.result_path,self.animal_number,self.animal_kinds,self.behavior_mode,framewidth=self.framewidth,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,animation_analyzer=False,t=self.t,duration=self.duration,length=self.length,social_distance=self.social_distance)
							if self.behavior_mode==0:
								AAD.generate_data(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							elif self.behavior_mode==1:
								AAD.generate_data_interact_basic(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							else:
								AAD.generate_data_interact_advance(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant,color_costar=self.color_costar)



class PanelLv2_SortBehaviors(wx.Panel):

	'''
	The 'Sort Behavior Examples' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)
		boxsizer.Add(0,40,0)

		button_sortexamples=wx.Button(panel,label='Sort Examples (LabGym UI)',size=(300,40))
		button_sortexamples.Bind(wx.EVT_BUTTON,self.sort_examples)
		wx.Button.SetToolTip(button_sortexamples,'Use LabGym sorting UI to sort behavior examples that are generated by LabGym.')
		boxsizer.Add(button_sortexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_sortexamplescsv=wx.Button(panel,label='Sort Examples (from .csv)',size=(300,40))
		button_sortexamplescsv.Bind(wx.EVT_BUTTON,self.sort_examples_csv)
		wx.Button.SetToolTip(button_sortexamplescsv,'Sort behavior examples that are generated by LabGym according to a .csv file that stores the frame-wise behavior labels annotated with other tools.')
		boxsizer.Add(button_sortexamplescsv,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		# Align with the centered 300px button column (same wx.ALIGN_CENTER as buttons above).
		boxsizer.Add(
			create_hyperlink(
				panel,
				'Sorting Behavior Examples using LabGym',
				'https://youtu.be/WDCJ2HdrYJo?si=O6orNTNZiwR1girH',
			),
			0, wx.ALIGN_CENTER, 10)
		boxsizer.Add(0, 10, 0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def sort_examples(self,event):

		title = 'Sort Examples (LabGym UI)'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv3_SortExamples(self.notebook), title)


	def sort_examples_csv(self,event):

		title = 'Sort Examples (from .csv)'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv3_SortExamplesCSV(self.notebook), title)



class PanelLv3_SortExamples(wx.Panel):

	'''
	The 'Sort Examples (LabGym UI)' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.input_path=None # the folder that stores unsorted behavior examples (one example is a pair of an animation and a pattern image)
		self.result_path=None # the folder that stores the sorted behavior examples
		self.keys_behaviors={} # stores the pairs of shortcut key-behavior name
		self.keys_behaviorpaths={} # stores the pairs of shortcut key-path to behavior examples

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that stores\nunsorted behavior examples',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.input_folder)
		wx.Button.SetToolTip(button_inputfolder,'Select a folder that stores the behavior examples generated by "Generate Behavior Examples" functional unit. All examples in this folder should be in pairs (animation + pattern image).')
		self.text_inputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe sorted behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.output_folder)
		wx.Button.SetToolTip(button_outputfolder,'A subfolder will be created for each behavior type under the behavior name.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_keynames=wx.BoxSizer(wx.HORIZONTAL)
		button_keynames=wx.Button(panel,label='Enter a single character shortcut key and\nthe corresponding behavior name',size=(300,40))
		button_keynames.Bind(wx.EVT_BUTTON,self.input_keys)
		wx.Button.SetToolTip(button_keynames,'Format: "shortcutkey-behaviorname". "o", "p", "q", and "u" are reserved for "Previous", "Next", "Quit", and "Undo". When hit a shortcut key, the behavior example pair will be moved to the folder named after the corresponding behavior name.')
		self.text_keynames=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_keynames.Add(button_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_keynames.Add(self.text_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_sort=wx.Button(panel,label='Sort behavior examples',size=(300,40))
		button_sort.Bind(wx.EVT_BUTTON,self.sort_behaviors)
		wx.Button.SetToolTip(button_sort,'You will see each example pair in the screen one by one and can use shortcut keys to sort them into folders of the behavior types.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_sort,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def input_folder(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.input_path=dialog.GetPath()
			self.text_inputfolder.SetLabel('Unsorted behavior examples are in: '+self.input_path+'.')
		dialog.Destroy()


	def output_folder(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Sorted behavior examples will be in: '+self.result_path+'.')
		dialog.Destroy()


	def input_keys(self,event):

		keynamepairs=''
		stop=False

		while stop is False:
			dialog=wx.TextEntryDialog(self,'Enter key-behaviorname pairs separated by ",".','Format: key1-name1,key2-name2,...',value=keynamepairs)
			if dialog.ShowModal()==wx.ID_OK:
				keynamepairs=dialog.GetValue()
				try:
					for pair in keynamepairs.split(','):
						key=pair.split('-')[0]
						name=pair.split('-')[1]
						if len(key)>1:
							wx.MessageBox('Key must be a single character.','Error',wx.OK|wx.ICON_ERROR)
							break
						if key in ['O','o','P','p','U','u','Q','q']:
							wx.MessageBox('The '+key+' is reserved. Please use another key.','Error',wx.OK|wx.ICON_ERROR)
							break
						else:
							self.keys_behaviors[key]=name
					self.text_keynames.SetLabel('The key-behaviorname pairs: '+keynamepairs+'.')
					stop=True
				except:
					wx.MessageBox('Please follow the correct format: key1-name1,key2-name2,....','Error',wx.OK|wx.ICON_ERROR)
			else:
				stop=True
		dialog.Destroy()


	def sort_behaviors(self,event):

		if self.input_path is None or self.result_path is None or len(self.keys_behaviors.items())==0:

			wx.MessageBox('No input / output folder or shortcut key - behavior name pair specified.','Error',wx.OK|wx.ICON_ERROR)

		else:

			for key in self.keys_behaviors:
				behavior_path=os.path.join(self.result_path,self.keys_behaviors[key])
				self.keys_behaviorpaths[key]=behavior_path
				os.makedirs(behavior_path,exist_ok=True)

			cv2.namedWindow('Sorting Behavior Examples',cv2.WINDOW_NORMAL)
			actions=[]
			index=0
			stop=False
			moved=False
			only_image=False

			check_animations=[i for i in os.listdir(self.input_path) if i.endswith('.avi')]
			if len(check_animations)==0:
				check_images=[i for i in os.listdir(self.input_path) if i.endswith('.jpg')]
				if len(check_images)==0:
					wx.MessageBox('No examples!','Error',wx.OK|wx.ICON_ERROR)
					stop=True
				else:
					only_image=True

			while stop is False:

				if moved:
					moved=False
					if only_image is False:
						shutil.move(os.path.join(self.input_path,example_name+'.avi'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.avi'))
					shutil.move(os.path.join(self.input_path,example_name+'.jpg'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.jpg'))

				pattern_images=[i for i in os.listdir(self.input_path) if i.endswith('.jpg')]
				pattern_images=sorted(pattern_images,key=lambda name:int(name.split('_len')[0].split('_')[-1]))

				if len(pattern_images)>0 and index<len(pattern_images):

					example_name=pattern_images[index].split('.jpg')[0]
					pattern_image=cv2.resize(cv2.imread(os.path.join(self.input_path,example_name+'.jpg')),(600,600),interpolation=cv2.INTER_AREA)

					if only_image is False:
						frame_count=example_name.split('_len')[0].split('_')[-1]
						animation=cv2.VideoCapture(os.path.join(self.input_path,example_name+'.avi'))
						fps=animation.get(cv2.CAP_PROP_FPS)

					while True:

						if only_image is False:
							ret,frame=animation.read()
							if not ret:
								animation.set(cv2.CAP_PROP_POS_FRAMES,0)
								continue
							frame=cv2.resize(frame,(600,600),interpolation=cv2.INTER_AREA)
							combined=np.hstack((frame,pattern_image))
							cv2.putText(combined,'frame count: '+frame_count,(10,15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							x_begin=550
						else:
							combined=pattern_image
							x_begin=5

						n=1
						for i in ['o: Prev','p: Next','q: Quit','u: Undo']:
							cv2.putText(combined,i,(x_begin,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							n+=1
						n+=1
						for i in self.keys_behaviors:
							cv2.putText(combined,i+': '+self.keys_behaviors[i],(x_begin,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							n+=1

						cv2.imshow('Sorting Behavior Examples',combined)
						cv2.moveWindow('Sorting Behavior Examples',50,0)

						if only_image is False:
							key=cv2.waitKey(int(1000/fps)) & 0xFF
						else:
							key=cv2.waitKey(1) & 0xFF

						for shortcutkey in self.keys_behaviorpaths:
							if key==ord(shortcutkey):
								example_name=pattern_images[index].split('.')[0]
								actions.append([shortcutkey,example_name])
								moved=True
								break
						if moved:
							break

						if key==ord('u'):
							if len(actions)>0:
								last=actions.pop()
								shortcutkey=last[0]
								example_name=last[1]
								if only_image is False:
									shutil.move(os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.avi'),os.path.join(self.input_path,example_name+'.avi'))
								shutil.move(os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.jpg'),os.path.join(self.input_path,example_name+'.jpg'))
								break
							else:
								wx.MessageBox('Nothing to undo.','Error',wx.OK|wx.ICON_ERROR)
								continue

						if key==ord('p'):
							index+=1
							break

						if key==ord('o'):
							if index>=1:
								index-=1
							break

						if key==ord('q'):
							stop=True
							break

					if only_image is False:
						animation.release()

				else:
					if len(pattern_images)==0:
						wx.MessageBox('Behavior example sorting completed!','Completed!',wx.OK|wx.ICON_INFORMATION)
						stop=True
					else:
						wx.MessageBox('This is the last behavior example!','To the end.',wx.OK|wx.ICON_INFORMATION)
						index=0

			cv2.destroyAllWindows()



class PanelLv3_SortExamplesCSV(wx.Panel):

	'''
	The 'Sort Examples (from .csv)' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.path_to_examples=None # path to unsorted behavior examples generated by LabGym, should also contain the annotation '.csv' file
		self.result_path=None # the folder for storing sorted behavior examples

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe unsorted behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_inpath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should directly store unsorted behavior examples generated by LabGym, as well as a .csv file that stores the frame-wise behavior labels.')
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(self.text_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store\nthe sorted behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'The sorted behavior examples will be in the selected folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_sortfromcsv=wx.Button(panel,label='Sort examples based on the .csv',size=(300,40))
		button_sortfromcsv.Bind(wx.EVT_BUTTON,self.sort_fromcsv)
		wx.Button.SetToolTip(button_sortfromcsv,'The unsorted behavior examples should be generated from the begining (the 0th second) of the video.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_sortfromcsv,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_inpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_examples=dialog.GetPath()
			self.text_inputexamples.SetLabel('Unsorted examples are in: '+self.path_to_examples+'.')
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Sorted examples will be in: '+self.result_path+'.')
		dialog.Destroy()


	def sort_fromcsv(self,event):

		if self.path_to_examples is None or self.result_path is None:
			wx.MessageBox('No input / output folder.','Error',wx.OK|wx.ICON_ERROR)
		else:
			sort_examples_from_csv(self.path_to_examples,self.result_path)



class PanelLv2_TrainCategorizers(wx.Panel):

	'''
	The 'Train Categorizers' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		# Get all of the values needed from config.get_config().
		self.config = config.get_config('models')

		self.file_path=None # the folder that stores sorted, unprepared behavior examples (each category is a subfolder)
		self.new_path=None # the folder that stores prepared behavior examples (contains all examples with a category tag in their names)
		self.behavior_mode=0 # 0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		self.animation_analyzer=True # whether to include Animation Analyzer in the Categorizers
		self.level_tconv=2 # complexity level of Animation Analyzer in Categorizer
		self.level_conv=2 # complexity level of Pattern Recognizer in Categorizer
		self.dim_tconv=32 # input dimension for Animation Analyzer in Categorizer
		self.dim_conv=32 # input dimension for Pattern Recognizer in Categorizer
		self.channel=1 # input channel for Animation Analyzer, 1--gray scale, 3--RGB scale
		self.length=15 # input time step for Animation Analyzer, also the duration / length for a behavior example
		self.aug_methods=[] # the methods for augment training and validation examples
		self.augvalid=True # whether to perform augmentation for validation data as well
		self.data_path=None # the folder that stores prepared behavior examples
		self.model_path = self.config['models']  # the 'LabGym/models' folder, which stores all the trained Categorizers
		logger.debug('%s: %r', 'self.model_path', self.model_path)
		self.path_to_categorizer = os.path.join(self.config['models'], 'New_model')  # path to the Categorizer
		logger.debug('%s: %r', 'self.path_to_categorizer', self.path_to_categorizer)
		self.out_path=None # the folder for storing the training reports
		self.include_bodyparts=False # whether to include body parts in the pattern images
		self.std=0 # a value between 0 and 255, higher value, less body parts will be included in the pattern images
		self.resize=None # resize the frames and pattern images before data augmentation
		self.background_free=True # whether to include background in animations
		self.black_background=True # whether to set background black
		self.social_distance=0 # a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		self.color_costar=False # in 'interactive advanced' mode, whether to make the supporting roles RGB scale in animations
		self.out_folder=None # if not None, the folder stores the augmented examples
		self.training_onfly=False # whether to train a Categorizer using behavior examples that are already augmented previously

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe sorted behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_filepath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders will be read by LabGym as the behavior names.')
		# Right-hand content: path label + compact count button (always present; Enable/Disable only)
		inputexamples_right=wx.BoxSizer(wx.VERTICAL)
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		self.button_view_sorted_counts=wx.Button(panel,label='View Behavior Counts',size=(200,28))
		self.button_view_sorted_counts.Bind(wx.EVT_BUTTON,self.show_sorted_count_popup)
		self.button_view_sorted_counts.Disable()
		wx.Button.SetToolTip(self.button_view_sorted_counts,'View example counts for each sorted behavior category.')
		inputexamples_right.Add(self.text_inputexamples,0,wx.EXPAND)
		inputexamples_right.Add(self.button_view_sorted_counts,0,wx.TOP,4)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(inputexamples_right,1,wx.EXPAND|wx.LEFT|wx.RIGHT,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_renameexample=wx.BoxSizer(wx.HORIZONTAL)
		button_renameexample=wx.Button(panel,label='Select a new folder to store\nall the prepared behavior examples',size=(300,40))
		button_renameexample.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_renameexample,'This folder will store all the prepared behavior examples and can be directly used for training. Preparing behavior examples is copying all examples into this folder and renaming them to put behavior name labels to their file names.')
		self.text_renameexample=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_renameexample.Add(button_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_renameexample.Add(self.text_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_prepare=wx.Button(panel,label='Start to prepare the training examples',size=(300,40))
		button_prepare.Bind(wx.EVT_BUTTON,self.rename_files)
		wx.Button.SetToolTip(button_prepare,'All prepared behavior examples will be stored in the same folder and ready to be input for training.')
		boxsizer.Add(button_prepare,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		module_categorizertype=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizertype=wx.Button(panel,label='Specify the type / complexity of\nthe Categorizer to train',size=(300,40))
		button_categorizertype.Bind(wx.EVT_BUTTON,self.specify_categorizer)
		wx.Button.SetToolTip(button_categorizertype,'Categorizer with both Animation Analyzer and Pattern Recognizer is slower but a little more accurate than that with Pattern Recognizer only. Higher complexity level means deeper and more complex network architecture. See Extended Guide for details.')
		self.text_categorizertype=wx.StaticText(panel,label='Default: Categorizer (Animation Analyzer LV2 + Pattern Recognizer LV2). Behavior mode: Non-interact (identify behavior for each individual).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizertype.Add(button_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizertype.Add(self.text_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_categorizershape=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizershape=wx.Button(panel,label='Specify the input shape for\nAnimation Analyzer / Pattern Recognizer',size=(300,40))
		button_categorizershape.Bind(wx.EVT_BUTTON,self.set_categorizer)
		wx.Button.SetToolTip(button_categorizershape,'The input frame / image size should be an even integer and larger than 8. The larger size, the wider of network architecture. Use large size only when there are detailed features in frames / images that are important for identifying behaviors. See Extended Guide for details.')
		self.text_categorizershape=wx.StaticText(panel,label='Default: (width,height,channel) is (32,32,1) / (32,32,3).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizershape.Add(button_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizershape.Add(self.text_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_timesteps)
		wx.Button.SetToolTip(button_length,'The duration (how many frames) of a behavior example. This info can be found in the filenames of the generated behavior examples, "_lenXX_" where "XX" is the number you need to enter here.')
		self.text_length=wx.StaticText(panel,label='Default: 15.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_trainingfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_trainingfolder=wx.Button(panel,label='Select the folder that stores\nall the prepared training examples',size=(300,40))
		button_trainingfolder.Bind(wx.EVT_BUTTON,self.select_datapath)
		wx.Button.SetToolTip(button_trainingfolder,'The folder that stores all the prepared behavior examples. If these are previously augmented, this folder should contain a "train" and a "vadilation" subfolder. If body parts are included, the STD value can be found in the filenames of the generated behavior examples with "_stdXX_" where "XX" is the STD value.')
		# Right-hand content: path label + compact count button (always present; Enable/Disable only)
		trainingfolder_right=wx.BoxSizer(wx.VERTICAL)
		self.text_trainingfolder=wx.StaticText(panel,label='None',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		self.button_view_counts=wx.Button(panel,label='View Behavior Counts',size=(200,28))
		self.button_view_counts.Bind(wx.EVT_BUTTON,self.show_count_popup)
		self.button_view_counts.Disable()
		wx.Button.SetToolTip(self.button_view_counts,'View example counts for each prepared training category.')
		trainingfolder_right.Add(self.text_trainingfolder,0,wx.EXPAND)
		trainingfolder_right.Add(self.button_view_counts,0,wx.TOP,4)
		module_trainingfolder.Add(button_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_trainingfolder.Add(trainingfolder_right,1,wx.EXPAND|wx.LEFT|wx.RIGHT,10)
		boxsizer.Add(module_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_augmentation=wx.BoxSizer(wx.HORIZONTAL)
		button_augmentation=wx.Button(panel,label='Specify the methods to\naugment training examples',size=(300,40))
		button_augmentation.Bind(wx.EVT_BUTTON,self.specify_augmentation)
		wx.Button.SetToolTip(button_augmentation,'Randomly manipulate the training examples to increase their amount and diversity and benefit the training. If the amount of examples less than 1,000 before augmentation, choose "Also augment the validation data". You can also export the augmented examples to save this step in future training. See Extended Guide for details.')
		self.text_augmentation=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_augmentation.Add(button_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_augmentation.Add(self.text_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_report=wx.BoxSizer(wx.HORIZONTAL)
		button_report=wx.Button(panel,label='Select a folder to\nexport training reports',size=(300,40))
		button_report.Bind(wx.EVT_BUTTON,self.select_reportpath)
		wx.Button.SetToolTip(button_report,'This is the folder to store the reports of training history and metrics. It is optional.')
		self.text_report=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_report.Add(button_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_report.Add(self.text_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_train=wx.Button(panel,label='Train the Categorizer',size=(300,40))
		button_train.Bind(wx.EVT_BUTTON,self.train_categorizer)
		wx.Button.SetToolTip(button_train,'Need to name the Categorizer to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.')
		boxsizer.Add(button_train,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def _count_examples(self,folder_path):
		return count_prepared_examples(folder_path)


	def _update_count_display(self,folder_path):
		counts=self._count_examples(folder_path)
		if not counts_enable_diagnostics(counts):
			self._counts={}
			self.button_view_counts.Disable()
			return
		self._counts=counts
		self.button_view_counts.Enable()


	def _iter_count_rows(self,counts):
		'''Yield behavior-name rows matching the 3-items-per-row body layout.'''
		names=sorted(counts)
		i=0
		while i<len(names):
			chunk=names[i:i+3]
			if len(chunk)==3:
				row_text='  |  '.join(f'{n}: {counts[n]} examples' for n in chunk)
				if len(row_text)>200:
					chunk=names[i:i+2]
			yield chunk
			i+=len(chunk)


	def _count_display_lines(self,counts,threshold):
		'''Return (count_rows, add_rows) for the body layout at the given threshold.'''
		count_rows=0
		add_rows=0
		for row in self._iter_count_rows(counts):
			count_rows+=1
			if any(counts[name]<threshold for name in row):
				add_rows+=1
		return count_rows,add_rows


	def _counts_area_height(self,counts,threshold,max_h):
		'''Natural height for the counts area; capped only when content exceeds max_h.

		Returns (display_height, needs_scroll).
		'''
		# Generous per-line budget so ordinary small datasets do not show a scrollbar
		count_row_h=26
		add_row_h=20
		pad=18
		count_rows,add_rows=self._count_display_lines(counts,threshold)
		natural=count_rows*count_row_h+add_rows*add_row_h+pad
		if natural<=max_h:
			return natural,False
		return max_h,True


	def _measure_popup_width(self,title,counts,threshold,min_w,max_w):
		'''Content-based width from longest title/legend/threshold/count line.'''
		dc=wx.ScreenDC()
		normal=wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		title_font=wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
		widths=[]
		dc.SetFont(title_font)
		widths.append(dc.GetTextExtent(title)[0])
		dc.SetFont(normal)
		widths.append(dc.GetTextExtent(
			f'Red text: Example count is below {threshold} (minimum threshold)')[0])
		widths.append(dc.GetTextExtent(
			'Yellow highlight: Example count is outside 1 population '
			'standard deviation from the mean')[0])
		# label + text field + Update button
		widths.append(dc.GetTextExtent('Minimum recommended examples:')[0]+70+72+24)
		for row in self._iter_count_rows(counts):
			line='  |  '.join(f'{n}: {counts[n]} examples' for n in row)
			widths.append(dc.GetTextExtent(line)[0])
			below=[(name,threshold-counts[name]) for name in row if counts[name]<threshold]
			if below:
				add_line='    add: '+', '.join(f'{n} ({needed})' for n,needed in below)
				widths.append(dc.GetTextExtent(add_line)[0])
		content_w=max(widths)+40
		return max(min_w,min(max_w,content_w))


	def _render_body(self,rtc,counts,threshold):
		# Population SD (divide by n, not n-1); yellow when |count - mean| > SD
		values=list(counts.values())
		mean=sum(values)/len(values)
		std=(sum((v-mean)**2 for v in values)/len(values))**0.5
		rtc.Clear()
		for row in self._iter_count_rows(counts):
			for i_item,name in enumerate(row):
				count=counts[name]
				attr=wx.richtext.RichTextAttr()
				attr.SetTextColour(wx.Colour(180,0,0) if count<threshold else wx.Colour(0,0,0))
				if std>0 and abs(count-mean)>std:
					attr.SetBackgroundColour(wx.YELLOW)
				rtc.BeginStyle(attr)
				rtc.WriteText(f'{name}: {count} examples')
				rtc.EndStyle()
				if i_item<len(row)-1:
					sep_attr=wx.richtext.RichTextAttr()
					sep_attr.SetTextColour(wx.Colour(0,0,0))
					sep_attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
					rtc.BeginStyle(sep_attr)
					rtc.WriteText('  |  ')
					rtc.EndStyle()
			rtc.WriteText('\n')
			below_t=[(name,threshold-counts[name]) for name in row if counts[name]<threshold]
			if below_t:
				add_attr=wx.richtext.RichTextAttr()
				add_attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
				add_attr.SetFontSize(10)
				add_attr.SetTextColour(wx.Colour(60,60,60))
				rtc.BeginStyle(add_attr)
				rtc.WriteText('    add: '+', '.join(f'{n} ({needed})' for n,needed in below_t)+'\n')
				rtc.EndStyle()


	def _show_behavior_count_popup(self,title,counts,threshold,set_threshold):
		'''Shared builder for prepared/sorted View Behavior Counts popups.'''
		bg=wx.Colour(255,255,255)
		fg=wx.Colour(0,0,0)
		btn_bg=wx.Colour(230,230,230)
		red_fg=wx.Colour(180,0,0)
		margin=10

		frame=self.GetTopLevelParent()
		fr=frame.GetRect()
		min_w=360
		max_w=max(min_w,min(720,fr.width-40))
		max_counts_h=max(120,min(360,fr.height//2))

		popup_w=self._measure_popup_width(title,counts,threshold,min_w,max_w)
		counts_h,needs_scroll=self._counts_area_height(counts,threshold,max_counts_h)

		popup=wx.PopupTransientWindow(self,wx.NO_BORDER)
		popup.SetBackgroundColour(bg)
		popup._applied_threshold=threshold

		def on_paint(evt,_p=popup):
			dc=wx.PaintDC(_p)
			dc.SetPen(wx.Pen(wx.BLACK,1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			w,h=_p.GetClientSize()
			dc.DrawRectangle(0,0,w,h)
		popup.Bind(wx.EVT_PAINT,on_paint)

		outer=wx.BoxSizer(wx.VERTICAL)

		# Title + close control (outside-click dismissal still works)
		title_row=wx.BoxSizer(wx.HORIZONTAL)
		title_lbl=wx.StaticText(popup,label=title,style=wx.ALIGN_CENTRE_HORIZONTAL)
		title_lbl.SetFont(wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD))
		title_lbl.SetForegroundColour(fg)
		title_lbl.SetBackgroundColour(bg)
		close_btn=wxbuttons.GenButton(popup,label='×',size=(24,24))
		close_btn.SetBackgroundColour(btn_bg)
		close_btn.SetForegroundColour(fg)
		close_btn.SetFont(wx.Font(14,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD))
		close_btn.SetBezelWidth(1)
		close_btn.SetUseFocusIndicator(False)
		close_btn.SetToolTip('Close')
		title_row.Add((24,24),0,wx.ALIGN_CENTER_VERTICAL)  # balance the close button
		title_row.Add(title_lbl,1,wx.ALIGN_CENTER_VERTICAL)
		title_row.Add(close_btn,0,wx.ALIGN_CENTER_VERTICAL)
		outer.Add(title_row,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Legend: plain StaticText rows (no RichTextCtrl / scrollbars)
		leg_font=wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

		leg1=wx.BoxSizer(wx.HORIZONTAL)
		red_sample=wx.StaticText(popup,label='Red text:')
		red_sample.SetFont(leg_font)
		red_sample.SetForegroundColour(red_fg)
		red_sample.SetBackgroundColour(bg)
		red_explain=wx.StaticText(
			popup,label=f' Example count is below {threshold} (minimum threshold)')
		red_explain.SetFont(leg_font)
		red_explain.SetForegroundColour(fg)
		red_explain.SetBackgroundColour(bg)
		leg1.Add(red_sample,0,wx.ALIGN_CENTER_VERTICAL)
		leg1.Add(red_explain,0,wx.ALIGN_CENTER_VERTICAL)
		outer.Add(leg1,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		leg2=wx.BoxSizer(wx.HORIZONTAL)
		# Small coloured chip so the sample is visible even when StaticText bg is ignored
		yl_chip=wx.Panel(popup)
		yl_chip.SetBackgroundColour(wx.YELLOW)
		yl_chip_s=wx.BoxSizer(wx.HORIZONTAL)
		yl_sample=wx.StaticText(yl_chip,label='Yellow highlight:')
		yl_sample.SetFont(leg_font)
		yl_sample.SetForegroundColour(fg)
		yl_sample.SetBackgroundColour(wx.YELLOW)
		yl_chip_s.Add(yl_sample,0,wx.ALL,1)
		yl_chip.SetSizer(yl_chip_s)
		yl_explain=wx.StaticText(
			popup,label=(
				' Example count is outside 1 population standard deviation '
				'from the mean'))
		yl_explain.SetFont(leg_font)
		yl_explain.SetForegroundColour(fg)
		yl_explain.SetBackgroundColour(bg)
		leg2.Add(yl_chip,0,wx.ALIGN_CENTER_VERTICAL)
		leg2.Add(yl_explain,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,2)
		outer.Add(leg2,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Threshold row (same white surface as the rest of the dialog)
		thr_row=wx.BoxSizer(wx.HORIZONTAL)
		thr_lbl=wx.StaticText(popup,label='Minimum recommended examples:')
		thr_lbl.SetFont(leg_font)
		thr_lbl.SetForegroundColour(fg)
		thr_lbl.SetBackgroundColour(bg)
		thr_txt=wx.TextCtrl(
			popup,value=str(threshold),size=(64,-1),
			style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT)
		thr_txt.SetForegroundColour(fg)
		thr_txt.SetBackgroundColour(bg)
		# GenButton paints its own colours; native wx.Button often does not on macOS
		btn=wxbuttons.GenButton(popup,label='Update',size=(72,26))
		btn.SetBackgroundColour(btn_bg)
		btn.SetForegroundColour(fg)
		btn.SetBezelWidth(1)
		btn.SetUseFocusIndicator(False)
		thr_row.Add(thr_lbl,0,wx.ALIGN_CENTER_VERTICAL)
		thr_row.Add(thr_txt,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,6)
		thr_row.Add(btn,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,6)
		outer.Add(thr_row,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Counts (RichTextCtrl kept only for mixed red/yellow inline formatting)
		rtc_style=wx.TE_READONLY|wx.NO_BORDER
		if not needs_scroll:
			rtc_style|=wx.TE_NO_VSCROLL
		rtc_counts=wx.richtext.RichTextCtrl(
			popup,size=(popup_w-2*margin,counts_h),style=rtc_style)
		rtc_counts.SetBackgroundColour(bg)
		rtc_counts.SetForegroundColour(fg)
		rtc_counts.SetEditable(False)
		rtc_counts.SetMinSize((popup_w-2*margin,counts_h))
		self._render_body(rtc_counts,counts,threshold)
		outer.Add(rtc_counts,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM,margin)

		popup.SetSizer(outer)
		outer.Layout()
		popup_h=outer.GetMinSize().height+2
		popup.SetClientSize(popup_w,popup_h)

		def _parse_threshold():
			s=thr_txt.GetValue().strip()
			if not s.isdigit():
				return None
			v=int(s)
			return v if v>=1 else None

		def _filter_threshold_char(evt):
			key=evt.GetKeyCode()
			if key in (
					wx.WXK_BACK,wx.WXK_DELETE,wx.WXK_TAB,wx.WXK_LEFT,wx.WXK_RIGHT,
					wx.WXK_HOME,wx.WXK_END,wx.WXK_RETURN,wx.WXK_NUMPAD_ENTER,
					wx.WXK_NUMPAD_DELETE):
				evt.Skip()
				return
			if wx.WXK_NUMPAD0<=key<=wx.WXK_NUMPAD9:
				evt.Skip()
				return
			if 32<=key<256 and chr(key).isdigit():
				evt.Skip()
				return
			# ignore non-digit characters

		def on_apply(evt):
			t=_parse_threshold()
			if t is None:
				thr_txt.SetValue(str(popup._applied_threshold))
				return
			popup._applied_threshold=t
			set_threshold(t)
			red_explain.SetLabel(f' Example count is below {t} (minimum threshold)')
			self._render_body(rtc_counts,counts,t)
			new_h,_=self._counts_area_height(counts,t,max_counts_h)
			rtc_counts.SetMinSize((popup_w-2*margin,new_h))
			rtc_counts.SetSize((popup_w-2*margin,new_h))
			outer.Layout()
			popup.SetClientSize(popup_w,outer.GetMinSize().height+2)

		thr_txt.Bind(wx.EVT_CHAR,_filter_threshold_char)
		thr_txt.Bind(wx.EVT_TEXT_ENTER,on_apply)
		btn.Bind(wx.EVT_BUTTON,on_apply)
		close_btn.Bind(wx.EVT_BUTTON,lambda evt:popup.Dismiss())

		ph=popup.GetSize().height
		popup.SetPosition(wx.Point(fr.x+(fr.width-popup_w)//2,fr.y+(fr.height-ph)//2))
		popup.Popup()


	def show_count_popup(self,event):
		counts=getattr(self,'_counts',{})
		if not counts_enable_diagnostics(counts):
			return
		if not hasattr(self,'_count_threshold'):
			self._count_threshold=250
		self._show_behavior_count_popup(
			'Prepared Training Examples',counts,self._count_threshold,
			lambda t:setattr(self,'_count_threshold',t))


	def _count_from_subfolders(self,folder_path):
		return count_sorted_examples(folder_path)


	def _update_sorted_count_display(self,folder_path):
		counts=self._count_from_subfolders(folder_path)
		if not counts_enable_diagnostics(counts):
			self._sorted_counts={}
			self.button_view_sorted_counts.Disable()
			return
		self._sorted_counts=counts
		self.button_view_sorted_counts.Enable()


	def show_sorted_count_popup(self,event):
		counts=getattr(self,'_sorted_counts',{})
		if not counts_enable_diagnostics(counts):
			return
		if not hasattr(self,'_sorted_count_threshold'):
			self._sorted_count_threshold=250
		self._show_behavior_count_popup(
			'Sorted Behavior Examples',counts,self._sorted_count_threshold,
			lambda t:setattr(self,'_sorted_count_threshold',t))


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_inputexamples.SetLabel('Path to sorted behavior examples: '+self.file_path+'.')
			self._update_sorted_count_display(self.file_path)
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a new directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.new_path=dialog.GetPath()
			self.text_renameexample.SetLabel('Will copy and rename the examples to: '+self.new_path+'.')
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Reducing frame / image size can speed up training\nSelect "No" if dont know what it is.','Resize the frames / images?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.NumberEntryDialog(self,'Enter the desired width dimension','No smaller than the\ndesired input dimension of the Categorizer:','Frame / image dimension',32,1,300)
			if dialog1.ShowModal()==wx.ID_OK:
				self.resize=int(dialog1.GetValue())
			if self.resize<16:
				self.resize=16
			self.text_renameexample.SetLabel('Will copy, rename, and resize (to '+str(self.resize)+') the examples to: '+self.new_path+'.')
			dialog1.Destroy()
		else:
			self.resize=None
		dialog.Destroy()


	def rename_files(self,event):

		if self.file_path is None or self.new_path is None:
			wx.MessageBox('Please select a folder that stores the sorted examples /\na new folder to store prepared training examples!','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			CA.rename_label(self.file_path,self.new_path,resize=self.resize)


	def specify_categorizer(self,event):

		behavior_modes=['Non-interact (identify behavior for each individual)','Interact basic (identify behavior for the interactive pair / group)','Interact advanced (identify behavior for both each individual and each interactive pair / group)','Static images (non-interactive): behaviors of each individual in static images (each image contains one animal / object)']
		dialog=wx.SingleChoiceDialog(self,message='Specify the mode of behavior for the Categorizer to identify',caption='Behavior mode',choices=behavior_modes)
		if dialog.ShowModal()==wx.ID_OK:
			behavior_mode=dialog.GetStringSelection()
			if behavior_mode=='Non-interact (identify behavior for each individual)':
				self.behavior_mode=0
			elif behavior_mode=='Interact basic (identify behavior for the interactive pair / group)':
				self.behavior_mode=1
			elif behavior_mode=='Interact advanced (identify behavior for both each individual and each interactive pair / group)':
				self.behavior_mode=2
				self.channel=3
				dialog1=wx.NumberEntryDialog(self,'Interactions happen within the interaction distance.',"How many folds of the animals's diameter\nis the interaction distance (0=inf):",'interaction distance (Enter an integer)',0,0,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.social_distance=int(dialog1.GetValue())
				else:
					self.social_distance=0
				dialog1.Destroy()
				dialog1=wx.MessageDialog(self,'Make both main and supporting characters RGB scale?\nSelect "No" if dont know what it is.','(Optional) RGB supporting characters?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.color_costar=True
				else:
					self.color_costar=False
				dialog1.Destroy()
			else:
				self.behavior_mode=3
				self.text_length.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
		dialog.Destroy()

		if self.behavior_mode>=3:
			categorizer_types=['Categorizer (Pattern Recognizer only) (faster / a little less accurate)']
		else:
			categorizer_types=['Categorizer (Animation Analyzer + Pattern Recognizer)','Categorizer (Pattern Recognizer only) (faster / a little less accurate)']
		dialog=wx.SingleChoiceDialog(self,message='Select the Categorizer type',caption='Categorizer types',choices=categorizer_types)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer_tp=dialog.GetStringSelection()
			if categorizer_tp=='Categorizer (Pattern Recognizer only) (faster / a little less accurate)':
				self.animation_analyzer=False
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog1.GetValue())
				dialog1.Destroy()
				level=self.level_conv
			else:
				self.animation_analyzer=True
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Animation Analyzer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_tconv=int(dialog1.GetValue())
				dialog1.Destroy()
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog1.GetValue())
				dialog1.Destroy()
				level=[self.level_tconv,self.level_conv]
		else:
			categorizer_tp=''
			level=''
		dialog.Destroy()

		if self.behavior_mode==0:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of each non-interactive individual.')
		elif self.behavior_mode==1:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of the interactive group.')
		elif self.behavior_mode==2:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of the interactive individuals and groups. interaction distance: '+str(self.social_distance)+' folds of the animal diameter.')
		else:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of each non-interactive individual in static images.')


	def set_categorizer(self,event):

		if self.animation_analyzer:
			dialog=wx.NumberEntryDialog(self,'Input dimension of Animation Analyzer\nlarger dimension = wider network','Enter a number:','Animation Analyzer input',32,1,300)
			if dialog.ShowModal()==wx.ID_OK:
				self.dim_tconv=int(dialog.GetValue())
			dialog.Destroy()
			if self.behavior_mode==2:
				self.channel=3
			else:
				dialog=wx.MessageDialog(self,'Grayscale input of Animation Analyzer?\nSelect "Yes" if the color of animals is behavior irrelevant.','Grayscale Animation Analyzer?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.channel=1
				else:
					self.channel=3
				dialog.Destroy()

		dialog=wx.NumberEntryDialog(self,'Input dimension of Pattern Recognizer\nlarger dimension = wider network','Enter a number:','Input the dimension',32,1,300)
		if dialog.ShowModal()==wx.ID_OK:
			self.dim_conv=int(dialog.GetValue())
			if self.behavior_mode>=3:
				dialog1=wx.MessageDialog(self,'Grayscale input?\nSelect "Yes" if the color of animals is behavior irrelevant.','Grayscale inputs?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.channel=1
				else:
					self.channel=3
				dialog.Destroy()
		dialog.Destroy()

		shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
		if self.behavior_mode>=3:
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+str(self.channel)+')'
		else:
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'
		if self.animation_analyzer is False:
			self.text_categorizershape.SetLabel('Input shapes: Pattern Recognizer'+shape_conv+'.')
		else:
			self.text_categorizershape.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv+'.')


	def input_timesteps(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'The number of frames of\na behavior example','Enter a number (minimum=3):','Behavior episode duration',15,1,1000)
			if dialog.ShowModal()==wx.ID_OK:
				self.length=int(dialog.GetValue())
				if self.length<3:
					self.length=3
				self.text_length.SetLabel('The duration of a behavior example is :'+str(self.length)+'.')
			dialog.Destroy()


	def select_datapath(self,event):

		dialog=wx.MessageDialog(self,'Are the behavior examples already augmented previously?','Examples already augmented?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.training_onfly=True
			self.text_augmentation.SetLabel('No need to do augmentation because the training data is already augmented.')
		else:
			self.training_onfly=False
			self.out_folder=None
		dialog.Destroy()

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.data_path=dialog.GetPath()
		dialog.Destroy()

		if self.data_path is None:

			wx.MessageBox('No data path has been specified.','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.behavior_mode>=3:

				self.include_bodyparts=False

				dialog=wx.MessageDialog(self,'Are the images in\ntraining examples background free?','Background-free images?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.background_free=True
					dialog1=wx.MessageDialog(self,'Are the background in images black? "Yes"=black background;\n"No"=white background.','Black background?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog1.ShowModal()==wx.ID_YES:
						self.black_background=True
					else:
						self.black_background=False
					dialog1.Destroy()
					self.text_trainingfolder.SetLabel('Static images w/o background in: '+self.data_path+'.')
				else:
					self.background_free=False
					self.text_trainingfolder.SetLabel('Static images w/ background in: '+self.data_path+'.')
				dialog.Destroy()

			else:

				if self.animation_analyzer:
					dialog=wx.MessageDialog(self,'Are the animations (in any) in\ntraining examples background free?','Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog.ShowModal()==wx.ID_YES:
						self.background_free=True
						dialog1=wx.MessageDialog(self,'Are the background in animations black?\n"Yes"=black background; "No"=white background.','Black background?',wx.YES_NO|wx.ICON_QUESTION)
						if dialog1.ShowModal()==wx.ID_YES:
							self.black_background=True
						else:
							self.black_background=False
						dialog1.Destroy()
					else:
						self.background_free=False
					dialog.Destroy()

				dialog=wx.MessageDialog(self,'Do the pattern images in training examples\ninclude body parts?','Body parts in pattern images?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.include_bodyparts=True
					dialog2=wx.NumberEntryDialog(self,'Should match the STD of the pattern images in training examples.','Enter a number between 0 and 255:','STD for motionless pixels',0,0,255)
					if dialog2.ShowModal()==wx.ID_OK:
						self.std=int(dialog2.GetValue())
					else:
						self.std=0
					dialog2.Destroy()
				else:
					self.include_bodyparts=False
				dialog.Destroy()

				if self.include_bodyparts:
					if self.animation_analyzer:
						if self.background_free:
							self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
						else:
							self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
					else:
						self.text_trainingfolder.SetLabel('Pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
				else:
					if self.animation_analyzer:
						if self.background_free:
							self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/o bodyparts in: '+self.data_path+'.')
						else:
							self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/o bodyparts in: '+self.data_path+'.')
					else:
						self.text_trainingfolder.SetLabel('Pattern images w/o bodyparts in: '+self.data_path+'.')

		if self.data_path is not None:
			self._update_count_display(self.data_path)


	def specify_augmentation(self,event):

		if self.training_onfly is True:

			wx.MessageBox('You chose to train a Categorizer using the examples that are already augmented. No need to augment them again.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.MessageDialog(self,'Export the augmented training examples? If yes, the Categorizer\nwill be trained on the exported, augmented examples to\navoid memory overload, but the training will be slower.','Export training examples?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog2.ShowModal()==wx.ID_OK:
					self.out_folder=dialog2.GetPath()
				dialog2.Destroy()
			else:
				self.out_folder=None
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Use default augmentation methods?\nSelect "Yes" if dont know how to specify.','Use default augmentation?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				selected='default'
				self.aug_methods=['default']
			else:
				aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening','random dimming','random shearing','random rescaling','random deletion']
				selected=''
				dialog1=wx.MultiChoiceDialog(self,message='Data augmentation methods',caption='Augmentation methods',choices=aug_methods)
				if dialog1.ShowModal()==wx.ID_OK:
					self.aug_methods=[aug_methods[i] for i in dialog1.GetSelections()]
					for i in dialog1.GetSelections():
						if selected=='':
							selected=selected+aug_methods[i]
						else:
							selected=selected+','+aug_methods[i]
				else:
					self.aug_methods=[]
				dialog1.Destroy()
			if len(self.aug_methods)<=0:
				selected='none'
			else:
				if self.aug_methods[0]=='default':
					self.aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening','random dimming']
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Also augment the validation data?\nSelect "No" if dont know what it is.','Augment validation data?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.augvalid=True
				if self.out_folder is None:
					self.text_augmentation.SetLabel('Augment both training and validation examples with: '+selected+'.')
				else:
					self.text_augmentation.SetLabel('Augment and export both training and validation examples with: '+selected+'.')
			else:
				self.augvalid=False
				if self.out_folder is None:
					self.text_augmentation.SetLabel('Augment training examples with: '+selected+'.')
				else:
					self.text_augmentation.SetLabel('Augment and export training examples with: '+selected+'.')
			dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.MessageDialog(self,'Export the training reports?','Export training reports?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog2.ShowModal()==wx.ID_OK:
				self.out_path=dialog2.GetPath()
				self.text_report.SetLabel('Training reports will be in: '+self.out_path+'.')
			dialog2.Destroy()
		else:
			self.out_path=None
		dialog.Destroy()


	def train_categorizer(self,event):

		if self.data_path is None:

			wx.MessageBox('No path to training examples.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.MessageDialog(self,'Export the trained Categorizer to a folder?','Export trained Categorizer?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.model_path=dialog1.GetPath()
				dialog1.Destroy()
			dialog.Destroy()

			do_nothing=False

			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter a name for the Categorizer to train','Categorizer name')
				if dialog.ShowModal()==wx.ID_OK:
					if dialog.GetValue()!='':
						self.path_to_categorizer=os.path.join(self.model_path,dialog.GetValue())
						if not os.path.isdir(self.path_to_categorizer):
							os.makedirs(self.path_to_categorizer)
							stop=True
						else:
							wx.MessageBox('The name already exists.','Error',wx.OK|wx.ICON_ERROR)
				else:
					do_nothing=True
					stop=True
				dialog.Destroy()

			if do_nothing is False:
				CA=Categorizers()
				if self.animation_analyzer is False:
					if self.behavior_mode>=3:
						self.length=0
						self.std=0
						self.include_bodyparts=False
					else:
						self.channel=3
					if self.training_onfly:
						CA.train_pattern_recognizer_onfly(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim=self.dim_conv,channel=self.channel,time_step=self.length,level=self.level_conv,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance)
					else:
						CA.train_pattern_recognizer(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim=self.dim_conv,channel=self.channel,time_step=self.length,level=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,out_folder=self.out_folder)
				else:
					if self.behavior_mode==2:
						self.channel=3
					if self.training_onfly:
						CA.train_combnet_onfly(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,level_tconv=self.level_tconv,level_conv=self.level_conv,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,color_costar=self.color_costar)
					else:
						CA.train_combnet(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,level_tconv=self.level_tconv,level_conv=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,color_costar=self.color_costar,out_folder=self.out_folder)



class PanelLv2_TestCategorizers(wx.Panel):

	'''
	The 'Test Categorizers' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		# Get all of the values needed from config.get_config().
		self.config = config.get_config('models')

		self.file_path=None # the folder that stores the ground-truth examples (each subfolder is a behavior category)
		self.model_path = self.config['models']  # the 'LabGym/models' folder, which stores all the trained Categorizers
		logger.debug('%s: %r', 'self.model_path', self.model_path)
		self.path_to_categorizer=None # path to the Categorizer
		self.out_path=None # for storing the testing reports

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_selectcategorizer=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcategorizer=wx.Button(panel,label='Select a Categorizer\nto test',size=(300,40))
		button_selectcategorizer.Bind(wx.EVT_BUTTON,self.select_categorizer)
		wx.Button.SetToolTip(button_selectcategorizer,'The behavioral names in ground-truth dataset should exactly match those in the selected Categorizer.')
		self.text_selectcategorizer=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcategorizer.Add(button_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcategorizer.Add(self.text_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe ground-truth behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_filepath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders are the ground-truth behavior names, which should match those in the selected Categorizer.')
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(self.text_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_report=wx.BoxSizer(wx.HORIZONTAL)
		button_report=wx.Button(panel,label='Select a folder to\nexport testing reports',size=(300,40))
		button_report.Bind(wx.EVT_BUTTON,self.select_reportpath)
		wx.Button.SetToolTip(button_report,'This is the folder to store the reports of testing results and metrics. It is optional.')
		self.text_report=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_report.Add(button_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_report.Add(self.text_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		testanddelete=wx.BoxSizer(wx.HORIZONTAL)
		button_test=wx.Button(panel,label='Test the Categorizer',size=(300,40))
		button_test.Bind(wx.EVT_BUTTON,self.test_categorizer)
		wx.Button.SetToolTip(button_test,'Test the selected Categorizer on the ground-truth behavior examples')
		button_delete=wx.Button(panel,label='Delete a Categorizer',size=(300,40))
		button_delete.Bind(wx.EVT_BUTTON,self.remove_categorizer)
		wx.Button.SetToolTip(button_delete,'Permanently delete a Categorizer. The deletion CANNOT be restored.')
		testanddelete.Add(button_test,0,wx.RIGHT,50)
		testanddelete.Add(button_delete,0,wx.LEFT,50)
		boxsizer.Add(0,5,0)
		boxsizer.Add(testanddelete,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_categorizer(self,event):

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()
		if 'Choose a new directory of the Categorizer' not in categorizers:
			categorizers.append('Choose a new directory of the Categorizer')

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to test',caption='Select a Categorizer',choices=categorizers)

		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			if categorizer=='Choose a new directory of the Categorizer':
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.path_to_categorizer=dialog1.GetPath()
				else:
					self.path_to_categorizer=None
				dialog1.Destroy()
				self.text_selectcategorizer.SetLabel('The path to the Categorizer to test is: '+self.path_to_categorizer+'.')
			else:
				self.path_to_categorizer=os.path.join(self.model_path,categorizer)
				self.text_selectcategorizer.SetLabel('Categorizer to test: '+categorizer+'.')

		dialog.Destroy()


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_inputexamples.SetLabel('Path to ground-truth behavior examples: '+self.file_path+'.')
		dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.MessageDialog(self,'Export the testing reports?','Export testing reports?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog1.ShowModal()==wx.ID_OK:
				self.out_path=dialog1.GetPath()
				self.text_report.SetLabel('Testing reports will be in: '+self.out_path+'.')
			dialog1.Destroy()
		else:
			self.out_path=None
		dialog.Destroy()


	def test_categorizer(self,event):

		if self.file_path is None or self.path_to_categorizer is None:
			wx.MessageBox('No Categorizer selected / path to ground-truth behavior examples.','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			CA.test_categorizer(self.file_path,self.path_to_categorizer,result_path=self.out_path)


	def remove_categorizer(self,event):

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to delete',caption='Delete a Categorizer',choices=categorizers)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			dialog1=wx.MessageDialog(self,'Delete '+str(categorizer)+'?','CANNOT be restored!',wx.YES_NO|wx.ICON_QUESTION)
			if dialog1.ShowModal()==wx.ID_YES:
				shutil.rmtree(os.path.join(self.model_path,categorizer))
			dialog1.Destroy()
		dialog.Destroy()
