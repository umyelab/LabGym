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



import wx
import os
import shutil
from pathlib import Path
from .analyzebehaviors import AnalyzeAnimal
from .categorizers import Categorizers



the_absolute_current_path=str(Path(__file__).resolve().parent)



class WindowLv1_GenerateExamples(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_GenerateExamples,self).__init__(parent=None,title=title,size=(1000,480))
		self.use_detector=False
		self.detector_path=None
		self.path_to_detector=None
		self.detection_threshold=0.5
		self.background_path=None
		self.path_to_videos=None
		self.result_path=None
		self.framewidth=None
		self.delta=10000
		self.decode_animalnumber=False
		self.animal_number=1
		self.autofind_t=False
		self.decode_t=False
		self.t=0
		self.duration=0
		self.decode_extraction=False
		self.ex_start=0
		self.ex_end=None
		# 0: animals birghter than the background; 1: animals darker than the background; 2: hard to tell
		self.animal_vs_bg=0
		self.stable_illumination=True
		self.length=15
		self.skip_redundant=1
		self.include_bodyparts=False
		self.std=0
		self.background_free=True

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s) to\ngenerate behavior examples',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		self.text_inputvideos=wx.StaticText(panel,label='Can select multiple videos.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store the\ngenerated behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_outputfolder=wx.StaticText(panel,label='Will create a subfolder for each video under this folder.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startgenerate=wx.BoxSizer(wx.HORIZONTAL)
		button_startgenerate=wx.Button(panel,label='Specify when generating behavior examples\nshould begin (unit: second)',size=(300,40))
		button_startgenerate.Bind(wx.EVT_BUTTON,self.specify_timing)
		self.text_startgenerate=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startgenerate.Add(button_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startgenerate.Add(self.text_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify how long generating examples\nshould last (unit: second)',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		self.text_duration=wx.StaticText(panel,label='Default: lasts until the end of video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_animalnumber=wx.BoxSizer(wx.HORIZONTAL)
		button_animalnumber=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_animalnumber.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		self.text_animalnumber=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_animalnumber.Add(button_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_animalnumber.Add(self.text_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_detection=wx.BoxSizer(wx.HORIZONTAL)
		button_detection=wx.Button(panel,label='Specify the method to\ndetect animals or objects',size=(300,40))
		button_detection.Bind(wx.EVT_BUTTON,self.select_method)
		self.text_detection=wx.StaticText(panel,label='Background subtraction (default): faster but needs static background; Detectors: versatile but slow.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_detection.Add(button_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detection.Add(self.text_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_length)
		self.text_length=wx.StaticText(panel,label='The duration of a behavior episode (should be the same across all behaviors).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_skipredundant=wx.BoxSizer(wx.HORIZONTAL)
		button_skipredundant=wx.Button(panel,label='Specify how many frames to skip when\ngenerating two consecutive behavior examples',size=(300,40))
		button_skipredundant.Bind(wx.EVT_BUTTON,self.specify_redundant)
		self.text_skipredundant=wx.StaticText(panel,label='Default: no frame to skip (generate a behavior example every frame).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_skipredundant.Add(button_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_skipredundant.Add(self.text_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_generate=wx.Button(panel,label='Start to generate behavior examples',size=(300,40))
		button_generate.Bind(wx.EVT_BUTTON,self.generate_data)
		boxsizer.Add(button_generate,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_videos(self,event):

		wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'
		dialog=wx.FileDialog(self,'Select video(s)','','',wildcard,style=wx.FD_MULTIPLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			path=os.path.dirname(self.path_to_videos[0])
			dialog2=wx.MessageDialog(self,'Proportional resize the video frames?\nSelect "No" if dont know what it is.','(Optional) resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				dialog3=wx.NumberEntryDialog(self,'Enter the desired frame width','The unit is pixel:','Desired frame width',480,1,10000)
				if dialog3.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog3.GetValue())
					if self.framewidth<10:
						self.framewidth=10
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (proportionally resize framewidth to '+str(self.framewidth)+').')
				else:
					self.framewidth=None
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
				dialog3.Destroy()
			else:
				self.framewidth=None
				self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
			dialog2.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Generate behavior examples in: '+self.result_path+'.')
		dialog.Destroy()


	def specify_timing(self,event):

		dialog=wx.MessageDialog(self,'light on and off in videos?','Illumination shifts?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.delta=1.2
		else:
			self.delta=10000
		dialog.Destroy()

		if self.delta==1.2:
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

		dialog=wx.NumberEntryDialog(self,'Enter the duration for generating examples','The unit is second:','Duration for generating examples',0,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.duration=int(dialog.GetValue())
			if self.duration!=0:
				self.text_duration.SetLabel('The generation of behavior examples lasts for '+str(self.duration)+' seconds.')
			else:
				self.text_duration.SetLabel('The generation of behavior examples lasts for the entire duration of a video.')
		dialog.Destroy()


	def specify_animalnumber(self,event):

		methods=['Decode from filenames: "_nn_"','Enter the number of animals']
		dialog=wx.SingleChoiceDialog(self,message='Enter the number of animals in a video',caption='The number of animals in a video',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Enter the number of animals':
				dialog2=wx.NumberEntryDialog(self,'','The number of animals:','Animal number',1,1,100)
				if dialog2.ShowModal()==wx.ID_OK:
					self.decode_animalnumber=False
					self.animal_number=int(dialog2.GetValue())
					self.text_animalnumber.SetLabel('The total number of animals in a video is '+str(self.animal_number)+'.')
				dialog2.Destroy()
			else:
				self.decode_animalnumber=True
				self.text_animalnumber.SetLabel('Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.')
		dialog.Destroy()


	def select_method(self,event):

		methods=['Subtract background (much faster but requires static background & stable illumination)','Use trained Detectors (versatile, good for social behaviors but much slower)']
		dialog=wx.SingleChoiceDialog(self,message='How to detect the animals?',caption='Detection methods',choices=methods)

		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()

			if method=='Subtract background (much faster but requires static background & stable illumination)':

				self.use_detector=False

				contrasts=['Animal brighter than background','Animal darker than background','Hard to tell']
				dialog1=wx.SingleChoiceDialog(self,message='Select the scenario that fits your experiments best',caption='Which fits best?',choices=contrasts)

				if dialog1.ShowModal()==wx.ID_OK:
					contrast=dialog1.GetStringSelection()
					if contrast=='Animal brighter than background':
						self.animal_vs_bg=0
						self.text_detection.SetLabel('Background subtraction: animal brighter than background.')
					elif contrast=='Animal darker than background':
						self.animal_vs_bg=1
						self.text_detection.SetLabel('Background subtraction: animal darker than background.')
					else:
						self.animal_vs_bg=2
						self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker than background.')
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

				if self.detector_path is None:
					self.detector_path=os.path.join(the_absolute_current_path,'detectors')

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
							self.path_to_detector=dialog2.GetPaths()
						dialog2.Destroy()
						self.text_detection.SetLabel('The path to the Detector is: '+self.path_to_detector+'.')
					else:
						self.path_to_detector=os.path.join(self.detector_path,detector)
						self.text_detection.SetLabel('Detector: '+detector+'.')
				dialog1.Destroy()

		dialog.Destroy()



	def input_length(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the number of frames\nfor a behavior example','Enter a number\n(minimum=3):','Behavior episode duration',15,1,1000)
		if dialog.ShowModal()==wx.ID_OK:
			self.length=int(dialog.GetValue())
			if self.length<3:
				self.length=3
			self.text_length.SetLabel('The duration of a behavior example is: '+str(self.length)+' frames.')
		dialog.Destroy()


	def specify_redundant(self,event):

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
			dialog.Destroy()

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
					if self.decode_animalnumber is True:
						for x in filename:
							if len(x)>0:
								if x[0]=='n':
									self.animal_number=int(x[1:])
					if self.decode_t is True:
						for x in filename:
							if len(x)>0:
								if x[0]=='b':
									self.t=float(x[1:])
					if self.decode_extraction is True:
						for x in filename:
							if len(x)>0:
								if x[:2]=='xs':
									self.ex_start=int(x[2:])
								if x[:2]=='xe':
									self.ex_end=int(x[2:])

					AA=AnalyzeAnimal()

					if self.use_detector is False:
						AA.prepare_analysis(i,self.result_path,self.animal_number,delta=self.delta,framewidth=self.framewidth,stable_illumination=self.stable_illumination,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,path_background=self.background_path,autofind_t=self.autofind_t,t=self.t,duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,length=self.length,animal_vs_bg=self.animal_vs_bg,use_detector=False)
						AA.generate_data(background_free=self.background_free,skip_redundant=self.skip_redundant)
					else:
						AA.prepare_analysis(i,self.result_path,self.animal_number,delta=self.delta,framewidth=self.framewidth,stable_illumination=self.stable_illumination,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,path_background=self.background_path,autofind_t=self.autofind_t,t=self.t,duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,length=self.length,animal_vs_bg=self.animal_vs_bg,use_detector=True)
						AA.generate_data_dynamic(self.path_to_detector,background_free=self.background_free,skip_redundant=self.skip_redundant)
						


class WindowLv1_TrainCategorizers(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_TrainCategorizers,self).__init__(parent=None,title=title,size=(1000,550))
		# the file path storing orginal examples
		self.file_path=None
		# the new path for renamed, labeled examples
		self.new_path=None
		self.animation_analyzer=True
		self.level_tconv=2
		self.level_conv=2
		self.dim_tconv=32
		self.dim_conv=32
		self.channel=1
		self.length=15
		self.aug_methods=[]
		# also perform augmentation for validation data
		self.augvalid=True
		# the path to all prepared training examples
		self.data_path=None
		self.model_path=os.path.join(the_absolute_current_path,'models')
		self.path_to_categorizer=os.path.join(the_absolute_current_path,'models','New_model')
		# for storing training reports
		self.out_path=None
		self.include_bodyparts=False
		self.std=0
		# resize the frames and pattern images before data augmentation
		self.resize=None
		self.background_free=True

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe sorted behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_filepath)
		self.text_inputexamples=wx.StaticText(panel,label='All examples for each behavior should be sorted into a subfolder named with the behavior name.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(self.text_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_renameexample=wx.BoxSizer(wx.HORIZONTAL)
		button_renameexample=wx.Button(panel,label='Select a new folder to store\nall the prepared behavior examples',size=(300,40))
		button_renameexample.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_renameexample=wx.StaticText(panel,label='All examples will be prepared (renamed to put a label / behavior name).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_renameexample.Add(button_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_renameexample.Add(self.text_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_prepare=wx.Button(panel,label='Start to prepare the training examples',size=(300,40))
		button_prepare.Bind(wx.EVT_BUTTON,self.rename_files)
		boxsizer.Add(button_prepare,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,20,0)

		module_categorizertype=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizertype=wx.Button(panel,label='Specify the type / complexity of\nthe Categorizer to train',size=(300,40))
		button_categorizertype.Bind(wx.EVT_BUTTON,self.specify_categorizer)
		self.text_categorizertype=wx.StaticText(panel,label='Default: Categorizer w/ both Animation Analyzer and Pattern Recognizer.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizertype.Add(button_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizertype.Add(self.text_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_categorizershape=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizershape=wx.Button(panel,label='Specify the input shape for\nAnimation Analyzer / Pattern Recognizer',size=(300,40))
		button_categorizershape.Bind(wx.EVT_BUTTON,self.set_categorizer)
		self.text_categorizershape=wx.StaticText(panel,label='Default: (width,height,channel) is (32,32,1) / (32,32,3).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizershape.Add(button_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizershape.Add(self.text_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_timesteps)
		self.text_length=wx.StaticText(panel,label='Enter the duration (how many frames) of an animation / pattern image in the training examples.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_trainingfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_trainingfolder=wx.Button(panel,label='Select the folder that stores\nall the prepared training examples',size=(300,40))
		button_trainingfolder.Bind(wx.EVT_BUTTON,self.select_datapath)
		self.text_trainingfolder=wx.StaticText(panel,label='This is the folder that stores all the prepared training examples.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_trainingfolder.Add(button_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_trainingfolder.Add(self.text_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_augmentation=wx.BoxSizer(wx.HORIZONTAL)
		button_augmentation=wx.Button(panel,label='Specify the methods to\naugment training examples',size=(300,40))
		button_augmentation.Bind(wx.EVT_BUTTON,self.specify_augmentation)
		self.text_augmentation=wx.StaticText(panel,label='If dont know how to select, use default or leave it as it is.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_augmentation.Add(button_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_augmentation.Add(self.text_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_report=wx.BoxSizer(wx.HORIZONTAL)
		button_report=wx.Button(panel,label='Select a folder to\nexport training reports',size=(300,40))
		button_report.Bind(wx.EVT_BUTTON,self.select_reportpath)
		self.text_report=wx.StaticText(panel,label='This is the folder to store the reports of training history and metrics.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_report.Add(button_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_report.Add(self.text_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_train=wx.Button(panel,label='Start to train the Categorizer',size=(300,40))
		button_train.Bind(wx.EVT_BUTTON,self.train_categorizer)
		boxsizer.Add(button_train,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_inputexamples.SetLabel('Path to sorted behavior examples: '+self.file_path+'.')
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a new directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.new_path=dialog.GetPath()
			self.text_renameexample.SetLabel('Will copy and rename the examples to: '+self.new_path+'.')
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Reducing frame size can speed up training\nSelect "No" if dont know what it is.','Resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.NumberEntryDialog(self,'Enter the desired width dimension','No smaller than the\ndesired input dimension of the Categorizer:','Frame dimension',32,1,300)
			if dialog1.ShowModal()==wx.ID_OK:
				self.resize=int(dialog1.GetValue())
			if self.resize<16:
				self.resize=16
			self.text_renameexample.SetLabel('Will copy, rename, and resize (to '+str(self.resize)+') the examples to: '+self.new_path+'.')
			dialog1.Destroy()
		else:
			self.resize=None
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Are the animations (if any) in\ntraining examples background free?','Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.background_free=True
		else:
			self.background_free=False
		dialog.Destroy()


	def rename_files(self,event):

		if self.file_path is None or self.new_path is None:
			wx.MessageBox('Please select a folder that stores the sorted examples /\na new folder to store prepared training examples!','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			CA.rename_label(self.file_path,self.new_path,resize=self.resize,background_free=self.background_free)


	def specify_categorizer(self,event):

		categorizer_types=['Categorizer w/ both Animation Analyzer and Pattern Recognizer','Categorizer w/ Pattern Recognizer only (much faster but maybe less accurate)']

		shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
		shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'

		dialog=wx.SingleChoiceDialog(self,message='Select the Categorizer type',caption='Categorizer types',choices=categorizer_types)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer_tp=dialog.GetStringSelection()
			if categorizer_tp=='Categorizer w/ Pattern Recognizer only (much faster but maybe less accurate)':
				self.animation_analyzer=False
				dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog2.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog2.GetValue())
				dialog2.Destroy()
				self.text_categorizertype.SetLabel('Categorizer type: Categorizer with only Pattern Recognizer (level '+str(self.level_conv)+').')
				self.text_categorizershape.SetLabel('Input shapes: '+shape_conv+'.')
			else:
				self.animation_analyzer=True
				dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Animation Analyzer level',2,1,7)
				if dialog2.ShowModal()==wx.ID_OK:
					self.level_tconv=int(dialog2.GetValue())
				dialog2.Destroy()
				dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog2.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog2.GetValue())
				dialog2.Destroy()
				self.text_categorizertype.SetLabel('Categorizer type: Categorizer with both Animation Analyzer (level '+str(self.level_tconv)+') and Pattern Recognizer (level '+str(self.level_conv)+').')
				self.text_categorizershape.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv+'.')
		dialog.Destroy()


	def set_categorizer(self,event):

		if self.animation_analyzer is True:
			dialog=wx.NumberEntryDialog(self,'Input dimension of Animation Analyzer\nlarger dimension = wider network','Enter a number:','Animation Analyzer input',32,1,300)
			if dialog.ShowModal()==wx.ID_OK:
				self.dim_tconv=int(dialog.GetValue())
			dialog.Destroy()
			dialog=wx.MessageDialog(self,'Grayscale input of Animation Analyzer?\nSelect "Yes" if the color of animals is behavior irrelevant.','Grayscale Animation Analyzer?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.channel=1
			else:
				self.channel=3
			dialog.Destroy()

		dialog=wx.NumberEntryDialog(self,'Input dimension of Pattern Recognizer\nlarger dimension = wider network','Enter a number:','Input the dimension',32,1,300)
		if dialog.ShowModal()==wx.ID_OK:
			self.dim_conv=int(dialog.GetValue())
		dialog.Destroy()

		shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
		shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'

		if self.animation_analyzer is False:
			self.text_categorizershape.SetLabel('Input shapes: Pattern Recognizer'+shape_conv+'.')
		else:
			self.text_categorizershape.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv+'.')


	def input_timesteps(self,event):

		dialog=wx.NumberEntryDialog(self,'The number of frames of\na behavior example','Enter a number (minimum=3):','Behavior episode duration',15,1,1000)
		if dialog.ShowModal()==wx.ID_OK:
			self.length=int(dialog.GetValue())
			if self.length<3:
				self.length=3
			self.text_length.SetLabel('The duration of a behavior example is :'+str(self.length)+'.')
		dialog.Destroy()


	def select_datapath(self,event):

		dialog=wx.MessageDialog(self,'Are the animations (in any) in\ntraining examples background free?','Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.background_free=True
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

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.data_path=dialog.GetPath()
			if self.include_bodyparts is True:
				if self.background_free is True:
					self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
				else:
					self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
			else:
				if self.background_free is True:
					self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/o bodyparts in: '+self.data_path+'.')
				else:
					self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/o bodyparts in: '+self.data_path+'.')				
		dialog.Destroy()


	def specify_augmentation(self,event):

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
			self.text_augmentation.SetLabel('Augment both training and validation examples with: '+selected+'.')
		else:
			self.augvalid=False
			self.text_augmentation.SetLabel('Augment training examples with: '+selected+'.')
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

			do_nothing=False
				
			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter a name for the Categorizer to train','Categorizer name')
				if dialog.ShowModal()==wx.ID_OK:
					if dialog.GetValue()!='':
						self.path_to_categorizer=os.path.join(self.model_path,dialog.GetValue())
						if not os.path.isdir(self.path_to_categorizer):
							os.mkdir(self.path_to_categorizer)
							stop=True
						else:
							wx.MessageBox('The name already exists.','Error',wx.OK|wx.ICON_ERROR)
				else:
					do_nothing=True
					stop=True
				dialog.Destroy()

			if do_nothing is False:
				if self.animation_analyzer is False:
					CA=Categorizers()
					CA.train_pattern_recognizer(self.data_path,self.path_to_categorizer,self.out_path,dim=self.dim_conv,channel=3,time_step=self.length,level=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free)
				else:
					CA=Categorizers()
					CA.train_combnet(self.data_path,self.path_to_categorizer,self.out_path,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,level_tconv=self.level_tconv,level_conv=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free)	



class WindowLv1_TestCategorizers(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_TestCategorizers,self).__init__(parent=None,title=title,size=(1000,250))
		self.model_path=os.path.join(the_absolute_current_path,'models')
		self.path_to_categorizer=None
		self.groundtruth_path=None
		self.result_path=None

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_selecttest=wx.BoxSizer(wx.HORIZONTAL)
		button_selecttest=wx.Button(panel,label='Select a Categorizer\nto test',size=(300,40))
		button_selecttest.Bind(wx.EVT_BUTTON,self.select_model)
		self.text_selecttest=wx.StaticText(panel,label='The behavior names of groundtruth examples should match those in the selected Categorizer.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selecttest.Add(button_selecttest,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selecttest.Add(self.text_selecttest,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_selecttest,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selecttruth=wx.BoxSizer(wx.HORIZONTAL)
		button_selecttruth=wx.Button(panel,label='Select the folder that stores the sorted\ngroundtruth behavior examples',size=(300,40))
		button_selecttruth.Bind(wx.EVT_BUTTON,self.select_groundtruthpath)
		self.text_selecttruth=wx.StaticText(panel,label='All groundtruth examples for each behavior should be sorted into a subfolder named with the behavior name.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selecttruth.Add(button_selecttruth,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selecttruth.Add(self.text_selecttruth,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selecttruth,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_testreport=wx.BoxSizer(wx.HORIZONTAL)
		button_testreport=wx.Button(panel,label='Select a folder to\nexport testing reports',size=(300,40))
		button_testreport.Bind(wx.EVT_BUTTON,self.select_reportpath)
		self.text_testreport=wx.StaticText(panel,label='This is the folder to store the reports of testing results.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_testreport.Add(button_testreport,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_testreport.Add(self.text_testreport,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_testreport,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)

		testanddelete=wx.BoxSizer(wx.HORIZONTAL)
		button_test=wx.Button(panel,label='Test the selected Categorizer',size=(300,40))
		button_test.Bind(wx.EVT_BUTTON,self.test_model)
		button_delete=wx.Button(panel,label='Delete a Categorizer',size=(300,40))
		button_delete.Bind(wx.EVT_BUTTON,self.remove_model)
		testanddelete.Add(button_test,0,wx.RIGHT,50)
		testanddelete.Add(button_delete,0,wx.LEFT,50)
		boxsizer.Add(testanddelete,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_model(self,event):

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to test',caption='Categorizer to test',choices=categorizers)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			self.path_to_categorizer=os.path.join(self.model_path,categorizer)
			self.text_selecttest.SetLabel('Categorizer to test: '+categorizer+'.')
		dialog.Destroy()


	def select_groundtruthpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.groundtruth_path=dialog.GetPath()
			self.text_selecttruth.SetLabel('Path to groundtruth examples: '+self.groundtruth_path+'.')
		dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_testreport.SetLabel('Testing reports will be in: '+self.result_path+'.')
		dialog.Destroy()


	def test_model(self,event):

		if self.path_to_categorizer is None or self.groundtruth_path is None or self.result_path is None:
			wx.MessageBox('No Categorizer / path to groundtruth examples / path to testing results selected.','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			CA.test_categorizer(self.groundtruth_path,self.path_to_categorizer,self.result_path)


	def remove_model(self,event):

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
			dialog2=wx.MessageDialog(self,'Delete '+str(categorizer)+'?','CANNOT be restored!',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				shutil.rmtree(os.path.join(self.model_path,categorizer))
			dialog2.Destroy()
		dialog.Destroy()


