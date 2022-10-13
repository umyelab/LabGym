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
import json
from urllib import request
import matplotlib as mpl
from pathlib import Path
import pandas as pd
from .analyzebehaviors import AnalyzeAnimal
from .tools import plot_evnets
from .network import DeepNetwork
from collections import OrderedDict



the_absolute_current_path=str(Path(__file__).resolve().parent)
current_version=1.6

try:

	latest_version=float(list(json.loads(request.urlopen('https://pypi.python.org/pypi/LabGym/json').read())['releases'].keys())[-1])
	if latest_version>current_version:
		print('A newer version '+'('+str(latest_version)+')'+' of LabGym is available. You may upgrade it by "python3 -m pip install --upgrade LabGym".\nFor the details of new changes, check: "https://github.com/umyelab/LabGym".')

except:
	
	pass



# a separate dialog for select colors
class ColorPicker(wx.Dialog):

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



# class the window for generating datasets
class WindowLv1_Generator(wx.Frame):

	def __init__(self,title):

		# if want to adjust the size, add arg 'size=(x,y)'
		super(WindowLv1_Generator,self).__init__(parent=None,title=title,size=(1000,550))
		# if not None, will load background images from path
		self.background_path=None
		# path to all video files
		self.path_to_videos=None
		# the result path
		self.result_path=None
		# the width dimension of the frame
		self.framewidth=None
		# the increase of light intensity on optogenetic stimulation onset
		self.delta=10000
		# if not 0, decode animal number from filename (_nn_), the 'n' immediately after the letter 'n'
		self.auto_animalnumber=0
		# the number of animal in a video
		self.animal_number=1
		# if 0, do not allow animal collision
		self.animal_collision=0
		# the number of animal allowed to be entangled
		self.entangle_number=1
		# if 0, link new animal to deregistered animal, otherwise never re-link if an animal is deregistered
		self.deregister=1
		# the method to find the start_t in croping the video: 0--optogenetics, 1--self.t
		self.auto=1
		# if self.auto is else, start_t=self.t
		self.t=0
		# the duration of the clip of interest
		self.duration=0
		# if 1, decode the background extration time window from '_xs_' and '_xe'
		self.x_code=0
		# the start time point for background extraction
		self.ex_start=0
		# the end time point for background extraction, if None, use the entire video
		self.ex_end=None
		# if 1, decode the contour area estimation time window from '_ss_' and '_se'
		self.s_code=0
		# the start time point for estimation of animal contour area
		self.es_start=0
		# the end time point for estimation of animal contour area, if None, use the entire video
		self.es_end=None
		# 0, animals birghter than the background; 1, animals darker than the background; 2, hard to tell
		self.invert=0
		# use optogenetic method (0) or threshold (1) or edge detection (2)
		self.method=0
		# minimum: if 0, use minimum, otherwise use stable value detector for background extraction
		self.minimum=0
		# the length for Animation Analyzer inputs/data clip length
		self.length=15
		# if !=0, skip the redundant frames
		self.skip_redundant=1
		# if 0, include the inner contours of animal body parts in pattern images
		self.inner_code=1
		# std for excluding static pixels in inners
		self.std=0
		# if 0, do not include background in animations
		self.background_free=0

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_1=wx.BoxSizer(wx.HORIZONTAL)
		button_1=wx.Button(panel,label='Select the video(s) to\ngenerate behavior examples',size=(300,40))
		button_1.Bind(wx.EVT_BUTTON,self.select_videos)
		self.text_1=wx.StaticText(panel,label='Can select multiple videos.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_1.Add(button_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_1.Add(self.text_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_2=wx.BoxSizer(wx.HORIZONTAL)
		button_2=wx.Button(panel,label='Select a folder to store the\ngenerated behavior examples',size=(300,40))
		button_2.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_2=wx.StaticText(panel,label='Will create a subfolder for each video under this folder.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_2.Add(button_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_2.Add(self.text_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_3=wx.BoxSizer(wx.HORIZONTAL)
		button_3=wx.Button(panel,label='Specify when generating behavior examples\nshould begin (unit: second)',size=(300,40))
		button_3.Bind(wx.EVT_BUTTON,self.specify_timing)
		self.text_3=wx.StaticText(panel,label='Default: at the 1st second.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_3.Add(button_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_3.Add(self.text_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_4=wx.BoxSizer(wx.HORIZONTAL)
		button_4=wx.Button(panel,label='Specify how long generating examples\nshould last (unit: second)',size=(300,40))
		button_4.Bind(wx.EVT_BUTTON,self.input_duration)
		self.text_4=wx.StaticText(panel,label='Default: lasts until the end of a video.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_4.Add(button_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_4.Add(self.text_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_5=wx.BoxSizer(wx.HORIZONTAL)
		button_5=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_5.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		self.text_5=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_5.Add(button_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_5.Add(self.text_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_6=wx.BoxSizer(wx.HORIZONTAL)
		button_6=wx.Button(panel,label='Specify the scenario that\nfits your experiments best',size=(300,40))
		button_6.Bind(wx.EVT_BUTTON,self.select_method)
		self.text_6=wx.StaticText(panel,label='Background subtraction is used to detect animals in each frame.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_6.Add(button_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_6.Add(self.text_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_7=wx.BoxSizer(wx.HORIZONTAL)
		button_7=wx.Button(panel,label='Specify the time window for\nbackground extraction',size=(300,40))
		button_7.Bind(wx.EVT_BUTTON,self.specify_extraction)
		self.text_7=wx.StaticText(panel,label='A time window during which the animals are NOT static.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_7.Add(button_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_7.Add(self.text_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_8=wx.BoxSizer(wx.HORIZONTAL)
		button_8=wx.Button(panel,label='Specify the time window for\nestimating the animal size',size=(300,40))
		button_8.Bind(wx.EVT_BUTTON,self.specify_estimation)
		self.text_8=wx.StaticText(panel,label='A time window during which all the animals are present in the video.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_8.Add(button_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_8.Add(self.text_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_9=wx.BoxSizer(wx.HORIZONTAL)
		button_9=wx.Button(panel,label='Specify the number of frames\nfor an animation',size=(300,40))
		button_9.Bind(wx.EVT_BUTTON,self.input_length)
		self.text_9=wx.StaticText(panel,label='The duration of a behavior episode (should be the same across all behaviors).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_9.Add(button_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_9.Add(self.text_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_10=wx.BoxSizer(wx.HORIZONTAL)
		button_10=wx.Button(panel,label='Specify how many frames to skip when\ngenerating two consecutive behavior examples',
			size=(300,40))
		button_10.Bind(wx.EVT_BUTTON,self.specify_redundant)
		self.text_10=wx.StaticText(panel,label='Default: no frame to skip (generate a behavior example every frame).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_10.Add(button_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_10.Add(self.text_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_11=wx.Button(panel,label='Start to generate behavior examples',size=(300,40))
		button_11.Bind(wx.EVT_BUTTON,self.generate_data)
		boxsizer.Add(button_11,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
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
			self.text_1.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path)
			dialog2=wx.MessageDialog(self,'Proportional resize the video frames?\nSelect "No" if dont know what it is.',
				'(Optional) resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				dialog3=wx.NumberEntryDialog(self,'Enter the desired frame width','The unit is pixel:',
					'Desired frame width',1000,1,10000)
				if dialog3.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog3.GetValue())
					if self.framewidth<10:
						self.framewidth=10
				else:
					self.framewidth=None
				dialog3.Destroy()
			else:
				self.framewidth=None
			dialog2.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_2.SetLabel('Generate behavior examples in: '+self.result_path)

		dialog.Destroy()


	def specify_timing(self,event):

		dialog=wx.MessageDialog(self,'Sudden increase / decrease of illumination in videos?','Sudden illumination changes?',
			wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.delta=1.2
		else:
			self.delta=10000
		dialog.Destroy()

		if self.delta==1.2:
			methods=['Automatic (for optogenetics)','Decode from filenames: "_bt_"','Enter a time point']
		else:
			methods=['Decode from filenames: "_bt_"','Enter a time point']

		dialog=wx.SingleChoiceDialog(self,message='Specify beginning time to generate behavior examples',
			caption='Beginning time for generator',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Automatic (for optogenetics)':
				self.auto=0
				self.text_3.SetLabel('Automatically find the beginning time (when illumination changes).')
			elif method=='Decode from filenames: "_bt_"':
				self.auto=-1
				self.text_3.SetLabel(
					'Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".')
			else:
				self.auto=1
				dialog2=wx.NumberEntryDialog(self,'Enter beginning time to generate examples','The unit is second:',
					'Beginning time to generate examples',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.t=float(dialog2.GetValue())
					if self.t<0:
						self.t=0
					self.text_3.SetLabel('Start to generate behavior examples at the: '+str(self.t)+' second.')
				dialog2.Destroy()
		dialog.Destroy()


	def input_duration(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the duration for generating examples','The unit is second:',
			'Duration for generating examples',0,0,100000000000000)

		if dialog.ShowModal()==wx.ID_OK:
			self.duration=int(dialog.GetValue())
			if self.duration!=0:
				self.text_4.SetLabel('The generation of behavior examples lasts for '+str(self.duration)+' seconds.')

		dialog.Destroy()


	def specify_animalnumber(self,event):

		methods=['Decode from filenames: "_nn_"','Enter the number of animals']
		dialog=wx.SingleChoiceDialog(self,message='Enter the number of animals in a video',
			caption='The number of animals in a video',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Enter the number of animals':
				dialog2=wx.NumberEntryDialog(self,'',
					'The number of animals:','Animal number',1,1,100)
				if dialog2.ShowModal()==wx.ID_OK:
					self.auto_animalnumber=0
					self.animal_number=int(dialog2.GetValue())
					self.text_5.SetLabel('The total number of animals in a video is '+str(self.animal_number)+'.')
				dialog2.Destroy()
			else:
				self.auto_animalnumber=1
				self.text_5.SetLabel('Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.')
		dialog.Destroy()

		if self.animal_number>1 or self.auto_animalnumber==1:
			dialog=wx.MessageDialog(self,
				'(For multiple animals) exclude entangled animals?\nIf not, merged animals are considered as a whole.',
				'Exclude entangled animals?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.animal_collision=0
			else:
				self.animal_collision=1
			dialog.Destroy()


	def select_method(self,event):

		contrasts=['Animal brighter than background','Animal darker than background','Hard to tell']
		dialog=wx.SingleChoiceDialog(self,message='Select the scenario that fits your experiments best',
			caption='Which fits best?',choices=contrasts)
		if dialog.ShowModal()==wx.ID_OK:
			contrast=dialog.GetStringSelection()
			if contrast=='Animal brighter than background':
				self.invert=0
				self.text_6.SetLabel('Background subtraction: animal brighter than the background.')
			elif contrast=='Animal darker than background':
				self.invert=1
				self.text_6.SetLabel('Background subtraction: animal darker than the background.')
			else:
				self.invert=2
				self.text_6.SetLabel('Background subtraction: animal partially brighter, partially darker than the background.')
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
			'(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog2.ShowModal()==wx.ID_OK:
				self.background_path=dialog2.GetPath()
			dialog2.Destroy()
		else:
			self.background_path=None
			if self.invert!=2:
				dialog2=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
					'(Optional) unstable illumination?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog2.ShowModal()==wx.ID_YES:
					self.minimum=1
				else:
					self.minimum=0
				dialog2.Destroy()
		dialog.Destroy()

		# these are for versions < 1.5

		'''
		methods=['Background subtraction','Basic thresholding','Basic edge detection']
		dialog=wx.SingleChoiceDialog(self,message='Select a method to detect animals',
			caption='Methods to detect animals',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Background subtraction':
				self.method=0
				dialog2=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
					'(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog2.ShowModal()==wx.ID_YES:
					dialog3=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
					if dialog3.ShowModal()==wx.ID_OK:
						self.background_path=dialog3.GetPath()
					dialog3.Destroy()
				else:
					self.background_path=None
					if self.invert!=2:
						dialog3=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
						'(Optional) unstable illumination',wx.YES_NO|wx.ICON_QUESTION)
						if dialog3.ShowModal()==wx.ID_YES:
							self.minimum=1
						else:
							self.minimum=0
						dialog3.Destroy()
				dialog2.Destroy()
			elif method=='Basic thresholding':
				self.method=1
			else:
				self.method=2
			self.text_6.SetLabel('Detect animals by: '+method+'.')
		dialog.Destroy()
		'''

	def specify_extraction(self,event):

		if self.method!=0:

			wx.MessageBox('No need to specify this since the method\nto detect animals is not "Background subtraction".',
				'Error',wx.OK|wx.ICON_ERROR)

		else:

			methods=['Use the entire duration of a video','Decode from filenames: "_xst_" and "_xet_"','Enter two time points']
			dialog=wx.SingleChoiceDialog(self,message='Specify the time window for background extraction',
				caption='Time window for background extraction',choices=methods)

			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Use the entire duration of a video':
					self.x_code=0
					self.text_7.SetLabel('Use the entire duration of the video for background extraction.')
				elif method=='Decode from filenames: "_xst_" and "_xet_"':
					self.x_code=1
					self.text_7.SetLabel(
						'Decode from the filenames: the "t" immediately after the letters "xs" (start) / "xe" (end).')
				else:
					self.x_code=0
					dialog2=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:',
						'Start time for background extraction',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.ex_start=int(dialog2.GetValue())
					dialog2.Destroy()
					dialog2=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:',
						'End time for background extraction',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.ex_end=int(dialog2.GetValue())
						if self.ex_end==0:
							self.ex_end=None
					dialog2.Destroy()
					if self.ex_end is None:
						self.text_7.SetLabel('The start / end time for background extraction is (in seconds): '+
							str(self.ex_start)+' / the end of the video')
					else:
						self.text_7.SetLabel('The start / end time for background extraction is (in seconds): '+
							str(self.ex_start)+' / '+str(self.ex_end))

			dialog.Destroy()


	def specify_estimation(self,event):

		methods=['Use the entire duration of a video','Decode from filenames: "_sst_" and "_set_"','Enter two time points']
		dialog=wx.SingleChoiceDialog(self,message='Specify the time window for estimating the animal size',
			caption='Time window for estimating animal size',choices=methods)

		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Use the entire duration of a video':
				self.s_code=0
				self.text_8.SetLabel('Use the entire duration of the video for estimating the animal size.')
			elif method=='Decode from filenames: "_sst_" and "_set_"':
				self.s_code=1
				self.text_8.SetLabel(
					'Decode from the filenames: the "t" immediately after the letters "ss" (start) / "se" (end).')
			else:
				self.s_code=0
				dialog2=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:',
					'Start time for estimating the animal size',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.es_start=int(dialog2.GetValue())
				dialog2.Destroy()
				dialog2=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:',
					'End time for estimating the animal size',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.es_end=int(dialog2.GetValue())
					if self.es_end==0:
						self.es_end=None
				dialog2.Destroy()
				if self.es_end is None:
					self.text_8.SetLabel('The start / end time for estimating the animal size is (in seconds): '+
						str(self.es_start)+' / the end of the video')
				else:
					self.text_8.SetLabel('The start / end time for estimating the animal size is (in seconds): '+
						str(self.es_start)+' / '+str(self.es_end))
				
		dialog.Destroy()


	def input_length(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the number of frames\nfor an animation','Enter a number\n(minimum=3):',
			'Duration of animation',15,1,1000)

		if dialog.ShowModal()==wx.ID_OK:
			self.length=int(dialog.GetValue())
			if self.length<3:
				self.length=3
			self.text_9.SetLabel('The duration of an animation: '+str(self.length)+' frames.')

		dialog.Destroy()


	def specify_redundant(self,event):

		dialog=wx.NumberEntryDialog(self,'How many frames to skip?','Enter a number:',
		'Interval for generating examples',15,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.skip_redundant=int(dialog.GetValue())
			self.text_10.SetLabel('Generate a pair of example every '+str(self.skip_redundant)+' frames.')
		else:
			self.skip_redundant=1
			self.text_10.SetLabel('Generate a pair of example at every frame.')

		dialog.Destroy()


	def generate_data(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=True

			dialog=wx.MessageDialog(self,'Include background in animations? Select "No"\nif background is behavior irrelevant.',
				'Including background?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.background_free=1
			else:
				self.background_free=0
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Include body parts in pattern images?\nSelect "No" if limb movement is neglectable.',
				'Including body parts?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.inner_code=0
				dialog2=wx.NumberEntryDialog(self,
					'Leave it as it is if dont know what it is.','Enter a number between 0 and 255:',
					'STD for motionless pixels',0,0,255)
				if dialog2.ShowModal()==wx.ID_OK:
					self.std=int(dialog2.GetValue())
				else:
					self.std=0
				dialog2.Destroy()
			else:
				self.inner_code=1
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Start to generate behavior examples?',
				'Start to generate examples?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				do_nothing=False
			else:
				do_nothing=True
			dialog.Destroy()

			if do_nothing is False:
	
				for i in self.path_to_videos:

					filename=os.path.splitext(os.path.basename(i))[0].split('_')
					if self.auto_animalnumber!=0:
						for x in filename:
							if len(x)>0:
								if x[0]=='n':
									self.animal_number=int(x[1:])
					if self.auto==-1:
						for x in filename:
							if len(x)>0:
								if x[0]=='b':
									self.t=float(x[1:])
					if self.x_code==1:
						for x in filename:
							if len(x)>0:
								if x[:2]=='xs':
									self.ex_start=int(x[2:])
								if x[:2]=='xe':
									self.ex_end=int(x[2:])
					if self.s_code==1:
						for x in filename:
							if len(x)>0:
								if x[:2]=='ss':
									self.es_start=int(x[2:])
								if x[:2]=='se':
									self.es_end=int(x[2:])

					if self.animal_number==1:
						self.entangle_number=1
					else:
						if self.animal_collision==0:
							self.entangle_number=1
						else:
							self.entangle_number=self.animal_number

					self.deregister=0

					AA=AnalyzeAnimal()
					AA.prepare_analysis(i,self.result_path,self.delta,self.animal_number,self.entangle_number,names_and_colors=None,
						framewidth=self.framewidth,method=self.method,minimum=self.minimum,
						analyze=1,path_background=self.background_path,auto=self.auto,t=self.t,duration=self.duration,
						ex_start=self.ex_start,ex_end=self.ex_end,es_start=self.es_start,es_end=self.es_end,
						length=self.length,invert=self.invert)
					AA.generate_data(deregister=self.deregister,inner_code=self.inner_code,
						std=self.std,background_free=self.background_free,skip_redundant=self.skip_redundant)
						


# class the window for training deep neural networks
class WindowLv1_Trainer(wx.Frame):

	def __init__(self,title):

		# if want to adjust the size, add arg 'size=(x,y)'
		super(WindowLv1_Trainer,self).__init__(parent=None,title=title,size=(1000,600))
		# the file path (used for renaming labels)
		self.file_path=None
		# if 0, normalize the files during renaming labels
		self.normalize=0
		# the new path (used for renamed, normalized flies)
		self.new_path=None
		# 0: Pattern Recognizer, 1: Animation Analyzer, 2 Categorizer
		self.network=2
		# if 1, resume the training from a previous check point
		self.resume=0
		# the level of Animation Analyzer
		self.level_tconv=2
		# the level of Pattern Recognizer
		self.level_conv=2
		# the dimension of Animation Analyzer
		self.dim_tconv=32
		# the dimension of Pattern Recognizer
		self.dim_conv=32
		# the channel for Animation Analyzer
		self.channel=1
		# the number of input frames
		self.length=15
		# the data augmentation methods
		self.aug_methods=[]
		# if 0, also perform augmentation for validation data
		self.augvalid=1
		# the data path
		self.data_path=None
		# the model path
		self.model_path=os.path.join(the_absolute_current_path,'models')
		# the path to model
		self.path_to_model=os.path.join(the_absolute_current_path,'models','New_model')
		# the out path for storing training reports or testing reports
		self.out_path=None
		# if 0, include the inner contours of animal body parts in pattern images
		self.inner_code=0
		# std for excluding static pixels in inners
		self.std=0
		# resize the frames and pattern images before data augmentation
		self.resize=None
		# if 0, do not include background in animations
		self.background_free=0

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_1=wx.BoxSizer(wx.HORIZONTAL)
		button_1=wx.Button(panel,label='Select the folder that stores\nthe sorted behavior examples',size=(300,40))
		button_1.Bind(wx.EVT_BUTTON,self.select_filepath)
		self.text_1=wx.StaticText(panel,label='All examples for each behavior should be sorted into a subfolder under the behavior name.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_1.Add(button_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_1.Add(self.text_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_2=wx.BoxSizer(wx.HORIZONTAL)
		button_2=wx.Button(panel,label='Select a new folder to store\nall the prepared behavior examples',size=(300,40))
		button_2.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_2=wx.StaticText(panel,label='All examples will be prepared (renamed to put a label / behavior name).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_2.Add(button_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_2.Add(self.text_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_3=wx.BoxSizer(wx.HORIZONTAL)
		button_3=wx.Button(panel,label='Specify the normalization of\nthe behavior examples',size=(300,40))
		button_3.Bind(wx.EVT_BUTTON,self.specify_normalization)
		self.text_3=wx.StaticText(panel,label='Normalization is performed by rescaling the range of pixel intensity to 0~255 in each animation.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_3.Add(button_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_3.Add(self.text_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_4=wx.Button(panel,label='Start to prepare the training examples',size=(300,40))
		button_4.Bind(wx.EVT_BUTTON,self.rename_files)
		boxsizer.Add(button_4,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,20,0)

		module_5=wx.BoxSizer(wx.HORIZONTAL)
		button_5=wx.Button(panel,label='Specify the type / complexity of\nthe Categorizer to train',size=(300,40))
		button_5.Bind(wx.EVT_BUTTON,self.specify_network)
		self.text_5=wx.StaticText(panel,label='Default: Categorizer with both Animation Analyzer and Pattern Recognizer.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_5.Add(button_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_5.Add(self.text_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_6=wx.BoxSizer(wx.HORIZONTAL)
		button_6=wx.Button(panel,label='Specify the input shape for\nAnimation Analyzer / Pattern Recognizer',size=(300,40))
		button_6.Bind(wx.EVT_BUTTON,self.set_network)
		self.text_6=wx.StaticText(panel,label='Default: (width,height,channel) is (32,32,1) / (32,32,3).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_6.Add(button_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_6.Add(self.text_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_7=wx.BoxSizer(wx.HORIZONTAL)
		button_7=wx.Button(panel,label='Specify the number of frames for\nan animation to train the Categorizer',size=(300,40))
		button_7.Bind(wx.EVT_BUTTON,self.input_timesteps)
		self.text_7=wx.StaticText(panel,
			label='Enter the duration (how many frames) of the animations in the training examples.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_7.Add(button_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_7.Add(self.text_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_8=wx.BoxSizer(wx.HORIZONTAL)
		button_8=wx.Button(panel,label='Select the folder that stores\nall the prepared training examples',size=(300,40))
		button_8.Bind(wx.EVT_BUTTON,self.select_datapath)
		self.text_8=wx.StaticText(panel,label='This is the folder that stores all the prepared training examples.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_8.Add(button_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_8.Add(self.text_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_9=wx.BoxSizer(wx.HORIZONTAL)
		button_9=wx.Button(panel,label='Specify the methods for\ndata augmentation',size=(300,40))
		button_9.Bind(wx.EVT_BUTTON,self.specify_augmentation)
		self.text_9=wx.StaticText(panel,label='If dont know how to select, use default or leave it as it is.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_9.Add(button_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_9.Add(self.text_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_10=wx.BoxSizer(wx.HORIZONTAL)
		button_10=wx.Button(panel,label='Select a folder to\nexport training reports',size=(300,40))
		button_10.Bind(wx.EVT_BUTTON,self.select_reportpath)
		self.text_10=wx.StaticText(panel,label='This is the folder to store the reports of training history and metrics.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_10.Add(button_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_10.Add(self.text_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_11=wx.Button(panel,label='Start to train the Categorizer',size=(300,40))
		button_11.Bind(wx.EVT_BUTTON,self.train_network)
		boxsizer.Add(button_11,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_1.SetLabel('Path to sorted behavior examples: '+self.file_path)

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a new directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.new_path=dialog.GetPath()
			self.text_2.SetLabel('Will copy and rename the examples to: '+self.new_path)
		dialog.Destroy()
		dialog=wx.MessageDialog(self,'Reducing frame size can speed up training\nSelect "No" if dont know what it is.',
			'Resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.NumberEntryDialog(self,'Enter the desired width dimension',
				'No smaller than the\ndesired input dimension of the Categorizer:','Frame dimension',32,1,300)
			if dialog1.ShowModal()==wx.ID_OK:
				self.resize=int(dialog1.GetValue())
			if self.resize<16:
				self.resize=16
			dialog1.Destroy()
		else:
			self.resize=None
		dialog.Destroy()
		dialog=wx.MessageDialog(self,'Are the animations in training examples\nbackground free?',
			'Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.background_free=0
		else:
			self.background_free=1
		dialog.Destroy()
				

	def specify_normalization(self,event):

		dialog=wx.MessageDialog(self,'Normalize the animations in training examples?\nSelect "Yes" if dont know what it is.',
			'Perform normalization?',wx.YES_NO|wx.ICON_QUESTION)

		if dialog.ShowModal()==wx.ID_YES:
			self.normalize=0
		else:
			self.normalize=1

		dialog.Destroy()


	def rename_files(self,event):

		if self.file_path is None or self.new_path is None:
			wx.MessageBox(
				'Please select a folder that stores the sorted examples /\na new folder to store prepared training data!',
				'Error',wx.OK|wx.ICON_ERROR)
		else:
			DN=DeepNetwork()
			DN.rename_label(self.file_path,self.new_path,normalize=self.normalize,resize=self.resize,
				background_free=self.background_free)


	def specify_network(self,event):

		# these are for versions < 1.5

		'''
		dialog=wx.MessageDialog(self,'Continue to train an existing network?\nSelect "No" if dont know what it is.',
			'Continue previous training?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			models=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
			models.sort()
			dialog2=wx.SingleChoiceDialog(self,message='Select a neural network to continue training',
				caption='Continue to train a neural network',choices=models)
			if dialog2.ShowModal()==wx.ID_OK:
				model=dialog2.GetStringSelection()
				self.path_to_model=os.path.join(self.model_path,model)
				self.resume=1
				self.text_5.SetLabel('Continue to train an existing network.')
				self.text_6.SetLabel('Automatically load from the path to the trained network.')
				self.text_7.SetLabel('Automatically load from the path to the trained network.')
			dialog2.Destroy()
		else:
			self.resume=0
			shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'
			if self.network==0:
				self.text_5.SetLabel('Network type: Pattern Recognizer')
				self.text_6.SetLabel('Input shapes: '+shape_conv)
			elif self.network==1:
				self.text_5.SetLabel('Network type: Animation Analyzer')
				self.text_6.SetLabel('Input shapes: '+shape_tconv)
			else:
				self.text_5.SetLabel('Network type: Categorizer (Animation Analyzer+Pattern Recognizer)')
				self.text_6.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv)
			self.text_7.SetLabel('The number of frames for assessing behaviors is :'+str(self.length)+'.')
			self.text_5.SetLabel('Use Categorizer (default) unless you have a reason to use others.')
			self.text_6.SetLabel('Default: (width,height,channel) is (32,32,1) / (32,32,3).')
			self.text_7.SetLabel('The length of the scanning window for categorizing behaviors.')
		dialog.Destroy()
		'''

		if self.resume==0:

			network_types=['Categorizer with both Animation Analyzer and Pattern Recognizer',
			'Categorizer w/o Animation Analyzer (much faster but less accurate)']

			shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'

			# these are for versions < 1.5

			'''
			dialog=wx.SingleChoiceDialog(self,message='Select the Categorizer type',
				caption='Categorizer types',choices=network_types)
			if dialog.ShowModal()==wx.ID_OK:
				network_type=dialog.GetStringSelection()
				if network_type=='Categorizer w/o Animation Analyzer (much faster but less accurate)':
					self.network=0
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Pattern Recognizer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_conv=int(dialog2.GetValue())
					dialog2.Destroy()
					self.text_5.SetLabel('Categorizer type: '+network_type+
						'; Level: '+str(self.level_conv))
					self.text_6.SetLabel('Input shapes: '+shape_conv)
				elif network_type=='Convolutional recurrent network (Animation Analyzer)':
					self.network=1
					dialog2=wx.NumberEntryDialog(self,'Network level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Animation Analyzer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_tconv=int(dialog2.GetValue())
					dialog2.Destroy()
					self.text_5.SetLabel('Network type: '+network_type+
						'; Level: '+str(self.level_tconv))
					self.text_6.SetLabel('Input shapes: '+shape_tconv)
				else:
					self.network=2
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Animation Analyzer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_tconv=int(dialog2.GetValue())
					dialog2.Destroy()
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Pattern Recognizer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_conv=int(dialog2.GetValue())
					dialog2.Destroy()
					self.text_5.SetLabel('Categorizer type: Categorizer w/ both Animation Analyzer (level '+str(self.level_tconv)+
						') and Pattern Recognizer (level '+str(self.level_conv)+')')
					self.text_6.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv)
			dialog.Destroy()
			'''
			
			dialog=wx.SingleChoiceDialog(self,message='Select the Categorizer type',
				caption='Categorizer types',choices=network_types)
			if dialog.ShowModal()==wx.ID_OK:
				network_type=dialog.GetStringSelection()
				if network_type=='Categorizer w/o Animation Analyzer (much faster but less accurate)':
					self.network=0
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Pattern Recognizer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_conv=int(dialog2.GetValue())
					dialog2.Destroy()
					self.text_5.SetLabel('Categorizer type: '+network_type+
						'; Level: '+str(self.level_conv))
					self.text_6.SetLabel('Input shapes: '+shape_conv)
				else:
					self.network=2
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Animation Analyzer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_tconv=int(dialog2.GetValue())
					dialog2.Destroy()
					dialog2=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)',
						'Pattern Recognizer level',2,1,7)
					if dialog2.ShowModal()==wx.ID_OK:
						self.level_conv=int(dialog2.GetValue())
					dialog2.Destroy()
					self.text_5.SetLabel('Categorizer type: Categorizer with both Animation Analyzer (level '+str(self.level_tconv)+
						') and Pattern Recognizer (level '+str(self.level_conv)+')')
					self.text_6.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv)
			dialog.Destroy()


	def set_network(self,event):

		if self.resume==1:

			wx.MessageBox('Automatically loaded from the trained Categorizer!',
				'Warning',wx.OK|wx.ICON_WARNING)

		else:

			if self.network>0:
				dialog=wx.NumberEntryDialog(self,'Input dimension of Animation Analyzer\nlarger dimension = wider network',
					'Enter a number:','Animation Analyzer input',32,1,300)
				if dialog.ShowModal()==wx.ID_OK:
					self.dim_tconv=int(dialog.GetValue())
				dialog.Destroy()

			if self.network!=1:
				dialog=wx.NumberEntryDialog(self,'Input dimension of Pattern Recognizer\nlarger dimension = wider network',
					'Enter a number:','Input the dimension',32,1,300)
				if dialog.ShowModal()==wx.ID_OK:
					self.dim_conv=int(dialog.GetValue())
				dialog.Destroy()

			if self.network>0:
				dialog=wx.MessageDialog(self,
					'Grayscale input of Animation Analyzer?\nSelect "Yes" if the color of animals is behavior irrelevant.',
					'Grayscale Animation Analyzer?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.channel=1
				else:
					self.channel=3
				dialog.Destroy()

			shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'

			if self.network==0:
				self.text_6.SetLabel('Input shapes: Pattern Recognizer'+shape_conv)
			elif self.network==1:
				self.text_6.SetLabel('Input shapes: Animation Analyzer'+shape_tconv)
			else:
				self.text_6.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv)


	def input_timesteps(self,event):

		if self.resume==1:

			wx.MessageBox('Automatically loaded from the trained Categorizer!',
				'Warning',wx.OK|wx.ICON_WARNING)

		else:

			dialog=wx.NumberEntryDialog(self,'The number of frames of an animation\nin the training examples',
				'Enter a number (minimum=3):','Duration of animation',15,1,1000)
			if dialog.ShowModal()==wx.ID_OK:
				self.length=int(dialog.GetValue())
				if self.length<3:
					self.length=3
				self.text_7.SetLabel('The duration of an animation (the time step) is :'+str(self.length)+'.')
			dialog.Destroy()


	def select_datapath(self,event):

		dialog=wx.MessageDialog(self,'Are the animations in training examples\nbackground free?',
			'Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.background_free=0
		else:
			self.background_free=1
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Do the pattern images in training examples\ninclude body parts?',
			'Body parts in pattern images?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.inner_code=0
			dialog2=wx.NumberEntryDialog(self,'Should match the STD of the pattern images in training examples.',
				'Enter a number between 0 and 255:','STD for motionless pixels',0,0,255)
			if dialog2.ShowModal()==wx.ID_OK:
				self.std=int(dialog2.GetValue())
			else:
				self.std=0
			dialog2.Destroy()
		else:
			self.inner_code=1
		dialog.Destroy()

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.data_path=dialog.GetPath()
			self.text_8.SetLabel('Path to all training examples: '+self.data_path)
		dialog.Destroy()


	def specify_augmentation(self,event):

		dialog=wx.MessageDialog(self,'Use default augmentation methods?\nSelect "Yes" if dont know how to specify.',
				'Use default augmentation?',wx.YES_NO|wx.ICON_QUESTION)

		if dialog.ShowModal()==wx.ID_YES:

			selected='default'
			self.aug_methods=['default']

		else:

			# these are for versions < 1.5

			'''
			aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening',
			'random dimming','random shearing','random rescaling','random deletion','exclude original']
			'''

			aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening',
			'random dimming','random shearing','random rescaling','random deletion']
			selected=''

			dialog1=wx.MultiChoiceDialog(self,message='Data augmentation methods',
				caption='Augmentation methods',choices=aug_methods)
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
				self.aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening',
				'random dimming']
				
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Also augment the validation data?\nSelect "No" if dont know what it is.',
				'Augment validation data?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.augvalid=0
		else:
			self.augvalid=1

		self.text_9.SetLabel('Data augmentation methods: '+selected+'.')


	def select_reportpath(self,event):

		dialog=wx.MessageDialog(self,'Export the training reports?','Export training reports?',wx.YES_NO|wx.ICON_QUESTION)

		if dialog.ShowModal()==wx.ID_YES:

			dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog2.ShowModal()==wx.ID_OK:
				self.out_path=dialog2.GetPath()
				self.text_10.SetLabel('Training reports will be in: '+self.out_path)
			dialog2.Destroy()

		else:

			self.out_path=None

		dialog.Destroy()


	def train_network(self,event):

		if self.data_path is None:

			wx.MessageBox('No path to training examples.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=False

			if self.resume==1:
				# load all parameters from the check point
				parameters=pd.read_csv(os.path.join(self.path_to_model,'model_parameters.txt'))

				if 'dim_conv' in list(parameters.keys()):
					self.dim_conv=int(parameters['dim_conv'][0])
				if 'dim_tconv' in list(parameters.keys()):
					self.dim_tconv=int(parameters['dim_tconv'][0])
				self.channel=int(parameters['channel'][0])
				self.length=int(parameters['time_step'][0])
				if self.length<3:
					self.length=3
				self.network=int(parameters['network'][0])
				if 'level_tconv' in list(parameters.keys()):
					self.level_tconv=int(parameters['level_tconv'][0])
				if 'level_conv' in list(parameters.keys()):
					self.level_conv=int(parameters['level_conv'][0])
				self.inner_code=int(parameters['inner_code'][0])
				self.std=int(parameters['std'][0])
				self.background_free=int(parameters['background_free'][0])

			else:
				
				stop=False
				while stop is False:
					dialog=wx.TextEntryDialog(self,'Enter a name for the Categorizer to train','Categorizer name')
					if dialog.ShowModal()==wx.ID_OK:
						if dialog.GetValue()!='':
							self.path_to_model=os.path.join(self.model_path,dialog.GetValue())
							if not os.path.isdir(self.path_to_model):
								os.mkdir(self.path_to_model)
								stop=True
							else:
								wx.MessageBox('The name already exists.','Error',wx.OK|wx.ICON_ERROR)
					else:
						do_nothing=True
						stop=True
					dialog.Destroy()

			if do_nothing is False:
				if self.network==0:
					DN=DeepNetwork()
					DN.train_cnn(self.data_path,self.path_to_model,self.out_path,dim=self.dim_conv,channel=3,
						time_step=self.length,level=self.level_conv,resume=self.resume,
						aug_methods=self.aug_methods,augvalid=self.augvalid,inner_code=self.inner_code,
						std=self.std,background_free=self.background_free)
				elif self.network==1:
					DN=DeepNetwork()
					DN.train_crnn(self.data_path,self.path_to_model,self.out_path,dim=self.dim_tconv,channel=self.channel,
						time_step=self.length,level=self.level_tconv,resume=self.resume,
						aug_methods=self.aug_methods,augvalid=self.augvalid,inner_code=self.inner_code,std=self.std,
						background_free=self.background_free)
				else:
					DN=DeepNetwork()
					DN.train_combnet(self.data_path,self.path_to_model,self.out_path,dim_tconv=self.dim_tconv,
						dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,
						level_tconv=self.level_tconv,level_conv=self.level_conv,resume=self.resume,
						aug_methods=self.aug_methods,augvalid=self.augvalid,inner_code=self.inner_code,std=self.std,
						background_free=self.background_free)	



# class the window for testing deep neural networks
class WindowLv1_Tester(wx.Frame):

	def __init__(self,title):

		# if want to adjust the size, add arg 'size=(x,y)'
		super(WindowLv1_Tester,self).__init__(parent=None,title=title,size=(1000,300))
		# the model path
		self.model_path=os.path.join(the_absolute_current_path,'models')
		# the path to model
		self.path_to_model=None
		# the path to the groundtruth data
		self.groundtruth_path=None
		# the path for storing testing reports
		self.result_path=None

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_1=wx.BoxSizer(wx.HORIZONTAL)
		button_1=wx.Button(panel,label='Select a Categorizer\nto test',size=(300,40))
		button_1.Bind(wx.EVT_BUTTON,self.select_model)
		self.text_1=wx.StaticText(panel,
			label='The behavior names of groundtruth examples should match those in the selected Categorizer.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_1.Add(button_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_1.Add(self.text_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_2=wx.BoxSizer(wx.HORIZONTAL)
		button_2=wx.Button(panel,label='Select the folder that stores the sorted\ngroundtruth behavior examples',size=(300,40))
		button_2.Bind(wx.EVT_BUTTON,self.select_groundtruthpath)
		self.text_2=wx.StaticText(panel,
			label='All groundtruth examples for each behavior should be sorted into a subfolder under the behavior name.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_2.Add(button_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_2.Add(self.text_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_3=wx.BoxSizer(wx.HORIZONTAL)
		button_3=wx.Button(panel,label='Select a folder to\nexport testing reports',size=(300,40))
		button_3.Bind(wx.EVT_BUTTON,self.select_reportpath)
		self.text_3=wx.StaticText(panel,label='This is the folder to store the reports of testing results.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_3.Add(button_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_3.Add(self.text_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_4=wx.Button(panel,label='Test the selected Categorizer',size=(300,40))
		button_4.Bind(wx.EVT_BUTTON,self.test_model)
		boxsizer.Add(button_4,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		button_5=wx.Button(panel,label='Delete a Categorizer',size=(300,40))
		button_5.Bind(wx.EVT_BUTTON,self.remove_model)
		boxsizer.Add(button_5,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_model(self,event):

		models=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in models:
			models.remove('__pycache__')
		if '__init__' in models:
			models.remove('__init__')
		if '__init__.py' in models:
			models.remove('__init__.py')
		models.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to test',
			caption='Categorizer to test',choices=models)
		if dialog.ShowModal()==wx.ID_OK:
			model=dialog.GetStringSelection()
			self.path_to_model=os.path.join(self.model_path,model)
			self.text_1.SetLabel('Categorizer to test: '+model+'.')
		dialog.Destroy()


	def select_groundtruthpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.groundtruth_path=dialog.GetPath()
			self.text_2.SetLabel('Path to groundtruth examples: '+self.groundtruth_path)

		dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_3.SetLabel('Testing reports will be in: '+self.result_path)

		dialog.Destroy()


	def test_model(self,event):

		if self.path_to_model is None or self.groundtruth_path is None or self.result_path is None:

			wx.MessageBox('No Categorizer / path to groundtruth examples / path to testing results selected.',
				'Error',wx.OK|wx.ICON_ERROR)

		else:

			DN=DeepNetwork()
			DN.test_network(self.groundtruth_path,self.path_to_model,self.result_path)


	def remove_model(self,event):

		models=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in models:
			models.remove('__pycache__')
		if '__init__' in models:
			models.remove('__init__')
		if '__init__.py' in models:
			models.remove('__init__.py')
		models.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to delete',
			caption='Delete a Categorizer',choices=models)

		if dialog.ShowModal()==wx.ID_OK:
			model=dialog.GetStringSelection()
			dialog2=wx.MessageDialog(self,'Delete '+str(model)+'?',
				'CANNOT be restored!',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				shutil.rmtree(os.path.join(self.model_path,model))
			dialog2.Destroy()
		
		dialog.Destroy()



# class the window for analyzing behaviors
class WindowLv1_Analyzer(wx.Frame):

	def __init__(self,title):

		# if want to adjust the size, add arg 'size=(x,y)'
		super(WindowLv1_Analyzer,self).__init__(parent=None,title=title,size=(1000,600))
		# if not None, will load background images from path
		self.background_path=None
		# the parent path of the models
		self.model_path=None
		# the path to deep neural network model
		self.model=None
		# path to all video files
		self.path_to_videos=None
		# the result path
		self.result_path=None
		# the width dimension of the frame
		self.framewidth=None
		# the increase of light intensity on optogenetic stimulation onset
		self.delta=10000
		# if not 0, decode animal number from filename (_nn_), the 'n' immediately after the letter 'n'
		self.auto_animalnumber=0
		# the number of animal in a video
		self.animal_number=1
		# if 0, do not allow animal collision
		self.animal_collision=0
		# the number of animal allowed to be entangled
		self.entangle_number=1
		# if 0, link new animal to deregistered animal, otherwise never re-link if an animal is deregistered
		self.deregister=1
		# the method to find the start_t in croping the video: 0--optogenetics, 1--self.t
		self.auto=1
		# if self.auto is else, start_t=self.t
		self.t=0
		# the duration of the clip of interest
		self.duration=0
		# if 1, decode the background extration time window from '_xs_' and '_xe'
		self.x_code=0
		# the start time point for background extraction
		self.ex_start=0
		# the end time point for background extraction, if None, use the entire video
		self.ex_end=None
		# if 1, decode the contour area estimation time window from '_ss_' and '_se'
		self.s_code=0
		# the start time point for estimation of animal contour area
		self.es_start=0
		# the end time point for estimation of animal contour area, if None, use the entire video
		self.es_end=None
		# all the behavior names and their representing colors
		self.behaviornames_and_colors=OrderedDict()
		# the dimension of Animation Analyzer
		self.dim_tconv=32
		# the dimension of Pattern Recognizer
		self.dim_conv=64
		# the channel of Animation Analyzer
		self.channel=1
		# the number of input frames, or time window for calculating motion parameters if not to categorize behaviors
		self.length=15
		# 0, animals birghter than the background; 1, animals darker than the background; 2, hard to tell
		self.invert=0
		# use optogenetic method (0) or threshold (1) or edge detection (2)
		self.method=0
		# minimum: if 0, use minimum, otherwise use stable value detector for background extraction
		self.minimum=0
		# network: if 0, use Pattern Recognizer, if 1, use Animation Analyzer, if 2, use Categorizer
		self.network=2
		# behaviors for annotation and plots
		self.to_include=['all']
		# all the parameters
		self.parameters=[]
		# if 0, include the inner contours of animal body parts in pattern images
		self.inner_code=1
		# std for excluding static pixels in inners
		self.std=0
		# uncertain: the differece between the highest probability and second highest probability to decide an uncertain behavior
		self.uncertain=0
		# show_legend: if 0, display the legends (all names in colors for behavioral categories) in the annotated video
		self.show_legend=0
		# if 0, do not include background in animations
		self.background_free=0
		# if 0, normalize the distance (in pixel) to the animal contour area
		self.normalize_distance=0

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_1=wx.BoxSizer(wx.HORIZONTAL)
		button_1=wx.Button(panel,label='Select a Categorizer for\nbehavior classification',size=(300,40))
		button_1.Bind(wx.EVT_BUTTON,self.select_model)
		self.text_1=wx.StaticText(panel,label='The fps of the videos to analyze should match that of the selected Categorizer.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_1.Add(button_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_1.Add(self.text_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_2=wx.BoxSizer(wx.HORIZONTAL)
		button_2=wx.Button(panel,label='Select the video(s)\nfor behavior analysis',size=(300,40))
		button_2.Bind(wx.EVT_BUTTON,self.select_videos)
		self.text_2=wx.StaticText(panel,label='Can select multiple videos for an analysis batch (one raster plot for one batch).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_2.Add(button_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_2.Add(self.text_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_3=wx.BoxSizer(wx.HORIZONTAL)
		button_3=wx.Button(panel,label='Select a folder to store\nthe analysis results',size=(300,40))
		button_3.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_3=wx.StaticText(panel,label='Will create a subfolder for each video under this folder.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_3.Add(button_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_3.Add(self.text_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_4=wx.BoxSizer(wx.HORIZONTAL)
		button_4=wx.Button(panel,label='Specify when the analysis\nshould begin (unit: second)',size=(300,40))
		button_4.Bind(wx.EVT_BUTTON,self.specify_timing)
		self.text_4=wx.StaticText(panel,label='Default: at the 1st second of the video(s).',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_4.Add(button_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_4.Add(self.text_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_5=wx.BoxSizer(wx.HORIZONTAL)
		button_5=wx.Button(panel,label='Specify the analysis duration\n(unit: second)',size=(300,40))
		button_5.Bind(wx.EVT_BUTTON,self.input_duration)
		self.text_5=wx.StaticText(panel,label='Default: from the specified beginning time to the end of a video.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_5.Add(button_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_5.Add(self.text_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_5,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_6=wx.BoxSizer(wx.HORIZONTAL)
		button_6=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_6.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		self.text_6=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_6.Add(button_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_6.Add(self.text_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_6,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_7=wx.BoxSizer(wx.HORIZONTAL)
		button_7=wx.Button(panel,label='Specify the scenario that\nfits your experiments best',size=(300,40))
		button_7.Bind(wx.EVT_BUTTON,self.select_method)
		self.text_7=wx.StaticText(panel,label='Background subtraction is used to detect animals in each frame.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_7.Add(button_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_7.Add(self.text_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_7,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_8=wx.BoxSizer(wx.HORIZONTAL)
		button_8=wx.Button(panel,label='Specify the time window for\nbackground extraction',size=(300,40))
		button_8.Bind(wx.EVT_BUTTON,self.specify_extraction)
		self.text_8=wx.StaticText(panel,label='A time window during which the animals are NOT static.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_8.Add(button_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_8.Add(self.text_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_8,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_9=wx.BoxSizer(wx.HORIZONTAL)
		button_9=wx.Button(panel,label='Specify the time window for\nestimating the animal size',size=(300,40))
		button_9.Bind(wx.EVT_BUTTON,self.specify_estimation)
		self.text_9=wx.StaticText(panel,label='A time window during which all the animals are present in the video.',
			style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_9.Add(button_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_9.Add(self.text_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_9,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_10=wx.BoxSizer(wx.HORIZONTAL)
		button_10=wx.Button(panel,label='Select the behaviors for\nannotations and plots',size=(300,40))
		button_10.Bind(wx.EVT_BUTTON,self.select_behaviors)
		self.text_10=wx.StaticText(panel,label='Default: all the behaviors listed in the selected Categorizer.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_10.Add(button_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_10.Add(self.text_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_10,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_11=wx.BoxSizer(wx.HORIZONTAL)
		button_11=wx.Button(panel,label='Select the quantitative measurements\nfor each behavior',size=(300,40))
		button_11.Bind(wx.EVT_BUTTON,self.select_parameters)
		self.text_11=wx.StaticText(panel,label='Default: none.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_11.Add(button_11,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_11.Add(self.text_11,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_11,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_12=wx.Button(panel,label='Start to analyze the behaviors',size=(300,40))
		button_12.Bind(wx.EVT_BUTTON,self.analyze_behaviors)
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_12,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_model(self,event):

		if self.model_path is None:
			self.model_path=os.path.join(the_absolute_current_path,'models')

		models=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in models:
			models.remove('__pycache__')
		if '__init__' in models:
			models.remove('__init__')
		if '__init__.py' in models:
			models.remove('__init__.py')
		models.sort()
		if 'No behavior classification, just track animals and quantify motion kinematics' not in models:
			models.append('No behavior classification, just track animals and quantify motion kinematics')
		if 'Choose a new directory of the Categorizer' not in models:
			models.append('Choose a new directory of the Categorizer')

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer for behavior classification',
			caption='Select a Categorizer',choices=models)

		if dialog.ShowModal()==wx.ID_OK:
			model=dialog.GetStringSelection()
			if model=='Choose a new directory of the Categorizer':
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.model=dialog1.GetPaths()
				dialog1.Destroy()
				self.text_1.SetLabel('The path to the Categorizer is: '+self.model)
			elif model=='No behavior classification, just track animals and quantify motion kinematics':
				self.model=None
				dialog1=wx.NumberEntryDialog(self,
					'Specify a time window used for measuring\nmotion kinematics of tracked animals',
					'Enter the number of\nframes (minimum=3):','Time window for calculating kinematics',15,1,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.length=int(dialog1.GetValue())
					if self.length<3:
						self.length=3
				dialog1.Destroy()
				self.text_1.SetLabel(
					'No behavior classification; the time window to measure kinematics of tracked animals is: '+str(self.length)+' frames.')
				self.text_10.SetLabel('No behavior classification. Just track animals and quantify motion kinematics.')
			else:
				self.model=os.path.join(self.model_path,model)
				self.text_1.SetLabel('Categorizer: '+model+'.')

			if self.model is not None:

				# these are for versions < 1.5

				'''
				dialog=wx.MessageDialog(self,'Set a uncertain threshold?\nSelect "No" if dont know what it is.',
					'(Optional) set uncertain threshold',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					dialog1=wx.NumberEntryDialog(self,
						'The probability difference between the most\nand the 2nd most likely categories of a behavior',
						'Enter a number\nbetween 0 and 100:','The threshold for uncertainty',0,0,100)
					if dialog1.ShowModal()==wx.ID_OK:
						self.uncertain=int(dialog1.GetValue())/100
					else:
						self.uncertain=0
					dialog1.Destroy()
				else:
					self.uncertain=0
				dialog.Destroy()
				'''

				# get all parameters for the network model
				parameters=pd.read_csv(os.path.join(self.model,'model_parameters.txt'))

				complete_colors=list(mpl.colors.cnames.values())
				colors=[]
				for c in complete_colors:
					colors.append(['#ffffff',c])

				self.behaviornames_and_colors=OrderedDict()

				for behavior_name in list(parameters['classnames']):
					index=list(parameters['classnames']).index(behavior_name)
					if index<len(colors):
						self.behaviornames_and_colors[behavior_name]=colors[index]
					else:
						self.behaviornames_and_colors[behavior_name]=['#ffffff','#ffffff']

				if 'dim_conv' in list(parameters.keys()):
					self.dim_conv=int(parameters['dim_conv'][0])
				if 'dim_tconv' in list(parameters.keys()):
					self.dim_tconv=int(parameters['dim_tconv'][0])
				self.channel=int(parameters['channel'][0])
				self.length=int(parameters['time_step'][0])
				if self.length<3:
					self.length=3
				self.network=int(parameters['network'][0])
				self.inner_code=int(parameters['inner_code'][0])
				self.std=int(parameters['std'][0])
				self.background_free=int(parameters['background_free'][0])

		dialog.Destroy()


	def select_videos(self,event):

		wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'
		dialog=wx.FileDialog(self,'Select video(s)','','',wildcard,style=wx.FD_MULTIPLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			path=os.path.dirname(self.path_to_videos[0])
			self.text_2.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path)
			dialog2=wx.MessageDialog(self,'Proportional resize the video frames?\nSelect "No" if dont know what it is.',
				'(Optional) resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				dialog3=wx.NumberEntryDialog(self,'Enter the desired frame width','The unit is pixel:',
					'Desired frame width',1000,1,10000)
				if dialog3.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog3.GetValue())
					if self.framewidth<10:
						self.framewidth=10
				else:
					self.framewidth=None
				dialog3.Destroy()
			else:
				self.framewidth=None
			dialog2.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_3.SetLabel('Results will be in: '+self.result_path)

		dialog.Destroy()


	def specify_timing(self,event):

		dialog=wx.MessageDialog(self,'Sudden increase / decrease of illumination in videos?','Sudden illumination changes?',
			wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.delta=1.2
		else:
			self.delta=10000
		dialog.Destroy()

		if self.delta==1.2:
			methods=['Automatic (for optogenetics)','Decode from filenames: "_bt_"','Enter a time point']
		else:
			methods=['Decode from filenames: "_bt_"','Enter a time point']

		dialog=wx.SingleChoiceDialog(self,message='Specify beginning time of analysis',
			caption='Beginning time of analysis',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Automatic (for optogenetics)':
				self.auto=0
				self.text_4.SetLabel('Automatically find the beginning time (when illumination changes).')
			elif method=='Decode from filenames: "_bt_"':
				self.auto=-1
				self.text_4.SetLabel(
					'Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".')
			else:
				self.auto=1
				dialog2=wx.NumberEntryDialog(self,'Enter the beginning time of analysis','The unit is second:',
					'Beginning time of analysis',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.t=float(dialog2.GetValue())
					if self.t<0:
						self.t=0
					self.text_4.SetLabel('Analysis will begin at the: '+str(self.t)+' second.')
				dialog2.Destroy()
		dialog.Destroy()


	def input_duration(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the duration of the analysis','The unit is second:',
			'Analysis duration',0,0,100000000000000)

		if dialog.ShowModal()==wx.ID_OK:
			self.duration=int(dialog.GetValue())
			if self.duration!=0:
				self.text_5.SetLabel('The analysis duration is '+str(self.duration)+' seconds.')

		dialog.Destroy()


	def specify_animalnumber(self,event):

		methods=['Decode from filenames: "_nn_"','Enter the number of animals']
		dialog=wx.SingleChoiceDialog(self,message='Enter the number of animals in a video',
			caption='The number of animals in a video',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Enter the number of animals':
				dialog2=wx.NumberEntryDialog(self,'',
					'The number of animals:','Animal number',1,1,100)
				if dialog2.ShowModal()==wx.ID_OK:
					self.auto_animalnumber=0
					self.animal_number=int(dialog2.GetValue())
					self.text_6.SetLabel('The total number of animals in a video is '+str(self.animal_number)+'.')
				dialog2.Destroy()
			else:
				self.auto_animalnumber=1
				self.text_6.SetLabel('Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.')
		dialog.Destroy()

		if self.animal_number>1 or self.auto_animalnumber==1:
			dialog=wx.MessageDialog(self,
				'(For multiple animals) exclude entangled animals from analysis?\nIf not, merged animal are analyzed as a whole.',
				'Exclude entangled animals?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.animal_collision=0
				dialog1=wx.MessageDialog(self,
				'Allow to relink the reappeared animals\nto the IDs that are lost track?',
				'Relink IDs?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.deregister=0
				else:
					self.deregister=1
				dialog1.Destroy()
			else:
				self.animal_collision=1
			dialog.Destroy()


	def select_method(self,event):

		contrasts=['Animal brighter than background','Animal darker than background','Hard to tell']
		dialog=wx.SingleChoiceDialog(self,message='Select the scenario that fits your experiments best',
			caption='Which fits best?',choices=contrasts)
		if dialog.ShowModal()==wx.ID_OK:
			contrast=dialog.GetStringSelection()
			if contrast=='Animal brighter than background':
				self.invert=0
				self.text_7.SetLabel('Background subtraction: animal brighter than the background.')
			elif contrast=='Animal darker than background':
				self.invert=1
				self.text_7.SetLabel('Background subtraction: animal darker than the background.')
			else:
				self.invert=2
				self.text_7.SetLabel('Background subtraction: animal partially brighter, partially darker than the background.')
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
			'(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog2.ShowModal()==wx.ID_OK:
				self.background_path=dialog2.GetPath()
			dialog2.Destroy()
		else:
			self.background_path=None
			if self.invert!=2:
				dialog2=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
					'(Optional) unstable illumination?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog2.ShowModal()==wx.ID_YES:
					self.minimum=1
				else:
					self.minimum=0
				dialog2.Destroy()
		dialog.Destroy()

		# these are for versions < 1.5

		'''
		methods=['Background subtraction','Basic thresholding','Basic edge detection']
		dialog=wx.SingleChoiceDialog(self,message='Select a method to detect animals',
			caption='Methods to detect animals',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Background subtraction':
				self.method=0
				dialog2=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.',
					'(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog2.ShowModal()==wx.ID_YES:
					dialog3=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
					if dialog3.ShowModal()==wx.ID_OK:
						self.background_path=dialog3.GetPath()
					dialog3.Destroy()
				else:
					self.background_path=None
					if self.invert!=2:
						dialog3=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.',
						'(Optional) unstable illumination',wx.YES_NO|wx.ICON_QUESTION)
						if dialog3.ShowModal()==wx.ID_YES:
							self.minimum=1
						else:
							self.minimum=0
						dialog3.Destroy()
				dialog2.Destroy()
			elif method=='Basic thresholding':
				self.method=1
			else:
				self.method=2
			self.text_7.SetLabel('Detect animals by: '+method+'.')
		dialog.Destroy()
		'''


	def specify_extraction(self,event):

		if self.method!=0:

			wx.MessageBox('No need to specify this since the method\nto detect animals is not "Background subtraction".',
				'Error',wx.OK|wx.ICON_ERROR)

		else:

			methods=['Use the entire duration of a video','Decode from filenames: "_xst_" and "_xet_"','Enter two time points']
			dialog=wx.SingleChoiceDialog(self,message='Specify the time window for background extraction',
				caption='Time window for background extraction',choices=methods)

			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Use the entire duration of a video':
					self.x_code=0
					self.text_8.SetLabel('Use the entire duration of the video for background extraction.')
				elif method=='Decode from filenames: "_xst_" and "_xet_"':
					self.x_code=1
					self.text_8.SetLabel(
						'Decode from the filenames: the "t" immediately after the letters "xs" (start) / "xe" (end).')
				else:
					self.x_code=0
					dialog2=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:',
						'Start time for background extraction',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.ex_start=int(dialog2.GetValue())
					dialog2.Destroy()
					dialog2=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:',
						'End time for background extraction',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.ex_end=int(dialog2.GetValue())
						if self.ex_end==0:
							self.ex_end=None
					dialog2.Destroy()
					if self.ex_end is None:
						self.text_8.SetLabel('The start / end time for background extraction is (in seconds): '+
							str(self.ex_start)+' / the end of the video')
					else:
						self.text_8.SetLabel('The start / end time for background extraction is (in seconds): '+
							str(self.ex_start)+' / '+str(self.ex_end))

			dialog.Destroy()


	def specify_estimation(self,event):

		methods=['Use the entire duration of a video','Decode from filenames: "_sst_" and "_set_"','Enter two time points']
		dialog=wx.SingleChoiceDialog(self,message='Specify the time window for estimating the animal size',
			caption='Time window for estimating animal size',choices=methods)

		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()
			if method=='Use the entire duration of a video':
				self.s_code=0
				self.text_9.SetLabel('Use the entire duration of the video for estimating the animal size.')
			elif method=='Decode from filenames: "_sst_" and "_set_"':
				self.s_code=1
				self.text_9.SetLabel(
					'Decode from the filenames: the "t" immediately after the letters "ss" (start) / "se" (end).')
			else:
				self.s_code=0
				dialog2=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:',
					'Start time for estimating the animal size',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.es_start=int(dialog2.GetValue())
				dialog2.Destroy()
				dialog2=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:',
					'End time for estimating the animal size',0,0,100000000000000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.es_end=int(dialog2.GetValue())
					if self.es_end==0:
						self.es_end=None
				dialog2.Destroy()
				if self.es_end is None:
					self.text_9.SetLabel('The start / end time for estimating the animal size is (in seconds): '+
						str(self.es_start)+' / the end of the video')
				else:
					self.text_9.SetLabel('The start / end time for estimating the animal size is (in seconds): '+
						str(self.es_start)+' / '+str(self.es_end))
				
		dialog.Destroy()


	def select_behaviors(self,event):

		if self.model is None:

			wx.MessageBox('No Categorizer selected! The behavior names are listed in the Categorizer.',
				'Error',wx.OK|wx.ICON_ERROR)

		else:

			behaviors=list(self.behaviornames_and_colors.keys())
			dialog=wx.MultiChoiceDialog(self,message='Select behaviors',
				caption='Behaviors to annotate',choices=behaviors)
			if dialog.ShowModal()==wx.ID_OK:
				self.to_include=[behaviors[i] for i in dialog.GetSelections()]
			else:
				self.to_include=behaviors
			dialog.Destroy()

			if len(self.to_include)==0:
				self.to_include=behaviors
			if self.to_include[0]=='all':
				self.to_include=behaviors

			complete_colors=list(mpl.colors.cnames.values())
			colors=[]
			for c in complete_colors:
				colors.append(['#ffffff',c])
			
			dialog=wx.MessageDialog(self,
				'Specify the color to represent\nthe behaviors in annotations and plots?',
				'Specify colors for behaviors?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				names_colors={}
				n=0
				while n<len(self.to_include):
					dialog2=ColorPicker(self,'Color for '+self.to_include[n],[self.to_include[n],colors[n]])
					if dialog2.ShowModal()==wx.ID_OK:
						(r,b,g,_)=dialog2.color_picker.GetColour()
						new_color='#%02x%02x%02x'%(r,b,g)
						self.behaviornames_and_colors[self.to_include[n]]=['#ffffff',new_color]
						names_colors[self.to_include[n]]=new_color
					else:
						if n<len(colors):
							names_colors[self.to_include[n]]=colors[n][1]
							self.behaviornames_and_colors[self.to_include[n]]=colors[n]
					dialog2.Destroy()
					n+=1
				self.text_10.SetLabel('Selected: '+str(names_colors)+'.')
			else:
				for color in colors:
					index=colors.index(color)
					if index<len(self.to_include):
						behavior_name=list(self.behaviornames_and_colors.keys())[index]
						self.behaviornames_and_colors[behavior_name]=color
				self.text_10.SetLabel('Selected: '+str(self.to_include)+' with default colors.')
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Show legend of behavior names in the annotated video?',
				'Legend in video?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.show_legend=0
			else:
				self.show_legend=1
			dialog.Destroy()


	def select_parameters(self,event):

		if self.model is None:
			parameters=['angle','3 areal parameters','3 length parameters','4 locomotion parameters']
		else:
			parameters=['angle','count','duration','latency','3 areal parameters','3 length parameters','4 locomotion parameters']

		dialog=wx.MultiChoiceDialog(self,message='Select quantitative measurements',
			caption='Quantitative measurements',choices=parameters)
		if dialog.ShowModal()==wx.ID_OK:
			self.parameters=[parameters[i] for i in dialog.GetSelections()]
		else:
			self.parameters=[]
		dialog.Destroy()

		if len(self.parameters)==0:
			self.parameters=[]

		self.text_11.SetLabel('Selected: '+str(self.parameters))

		dialog=wx.MessageDialog(self,
			'Normalize the distances by the size of an animal? If no, all distances will be output in pixels.',
			'Normalize the distances?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.normalize_distance=0
		else:
			self.normalize_distance=1
		dialog.Destroy()


	def analyze_behaviors(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / result folder.','Error',wx.OK|wx.ICON_ERROR)

		else:

			all_events=OrderedDict()
			event_data=OrderedDict()
			all_lengths=[]

			if self.model is None:
				self.to_include=[]
			else:
				if self.to_include[0]=='all':
					self.to_include=list(self.behaviornames_and_colors.keys())

			for i in self.path_to_videos:
				filename=os.path.splitext(os.path.basename(i))[0].split('_')
				if self.auto_animalnumber!=0:
					for x in filename:
						if len(x)>0:
							if x[0]=='n':
								self.animal_number=int(x[1:])
				if self.auto==-1:
					for x in filename:
						if len(x)>0:
							if x[0]=='b':
								self.t=float(x[1:])
				if self.x_code==1:
					for x in filename:
						if len(x)>0:
							if x[:2]=='xs':
								self.ex_start=int(x[2:])
							if x[:2]=='xe':
								self.ex_end=int(x[2:])
				if self.s_code==1:
					for x in filename:
						if len(x)>0:
							if x[:2]=='ss':
								self.es_start=int(x[2:])
							if x[:2]=='se':
								self.es_end=int(x[2:])

				if self.animal_number==1:
					self.entangle_number=1
					self.deregister=0
				else:
					if self.animal_collision==0:
						self.entangle_number=1
					else:
						self.entangle_number=self.animal_number
						self.deregister=0

				AA=AnalyzeAnimal()
				if self.model is None:
					analyze=1
				else:
					analyze=0
				AA.prepare_analysis(i,self.result_path,self.delta,self.animal_number,self.entangle_number,
					names_and_colors=self.behaviornames_and_colors,framewidth=self.framewidth,method=self.method,
					minimum=self.minimum,analyze=analyze,path_background=self.background_path,auto=self.auto,t=self.t,
					duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,es_start=self.es_start,es_end=self.es_end,
					length=self.length,invert=self.invert)
				AA.acquire_parameters(deregister=self.deregister,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,
					channel=self.channel,network=self.network,inner_code=self.inner_code,std=self.std,
					background_free=self.background_free)
				if self.model is not None:
					AA.categorize_behaviors(self.model,network=self.network,uncertain=self.uncertain)
				AA.export_results(normalize=self.normalize_distance,included_parameters=self.parameters)
				AA.annotate_video(self.to_include,show_legend=self.show_legend)

				if self.model is not None:
					for n in list(AA.event_probability.keys()):
						all_events[len(all_events.keys())]=AA.event_probability[n]
						all_lengths.append(len(AA.event_probability[n]))

			if self.model is not None:

				for n in list(all_events.keys()):
					event_data[len(event_data.keys())]=all_events[n][:min(all_lengths)]
				time_points=AA.all_time[:min(all_lengths)]
			
				all_events_df=pd.DataFrame.from_dict(event_data,orient='index',columns=time_points)
				if min(all_lengths)<16000:
					all_events_df.to_excel(os.path.join(self.result_path,'all_events.xlsx'),float_format='%.2f')
				else:
					all_events_df.to_csv(os.path.join(self.result_path,'all_events.csv'),float_format='%.2f')

				plot_evnets(self.result_path,event_data,time_points,self.behaviornames_and_colors,
					self.to_include,width=0,height=0)

				folders=[i for i in os.listdir(self.result_path) if os.path.isdir(os.path.join(self.result_path,i))]

				for behavior_name in list(self.behaviornames_and_colors.keys()):
					all_summary=pd.DataFrame()
					for folder in folders:
						individual_summary=os.path.join(self.result_path,folder,behavior_name,'all_summary.xlsx')
						if os.path.exists(individual_summary) is True:
							all_summary=all_summary.append(pd.read_excel(individual_summary), ignore_index=True)
					all_summary.to_excel(os.path.join(self.result_path,behavior_name+'_summary.xlsx'),float_format='%.2f')



# class the most initial input window
class InitialWindow(wx.Frame):

	def __init__(self,title):

		# if want to adjust the size, add arg 'size=(x,y)'
		super(InitialWindow,self).__init__(parent=None,title=title,size=(450,550))
		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		self.text_1=wx.StaticText(panel,label='Welcome to LabGym!\n\nVersion '+str(current_version),
			style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(0,50,0)
		boxsizer.Add(self.text_1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,50,0)
		self.text_3=wx.StaticText(panel,
			label='Developed by Yujia Hu\n\nBing Ye Lab, Life Sciences Institute\nUniversity of Michigan',
			style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(self.text_3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,50,0)

		button1=wx.Button(panel,label='Generate Behavior Examples')
		boxsizer.Add(button1,0,wx.LEFT|wx.RIGHT|wx.EXPAND,40)
		button1.Bind(wx.EVT_BUTTON,self.generate_datasets)
		boxsizer.Add(0,30,0)

		button2=wx.Button(panel,label='Train Categorizers')
		boxsizer.Add(button2,0,wx.LEFT|wx.RIGHT|wx.EXPAND,40)
		button2.Bind(wx.EVT_BUTTON,self.train_networks)
		boxsizer.Add(0,30,0)

		button3=wx.Button(panel,label='Test Categorizers')
		boxsizer.Add(button3,0,wx.LEFT|wx.RIGHT|wx.EXPAND,40)
		button3.Bind(wx.EVT_BUTTON,self.test_networks)
		boxsizer.Add(0,30,0)

		button4=wx.Button(panel,label='Analyze Behaviors')
		boxsizer.Add(button4,0,wx.LEFT|wx.RIGHT|wx.EXPAND,40)
		button4.Bind(wx.EVT_BUTTON,self.analyze_behaviors)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def generate_datasets(self,event):

		WindowLv1_Generator('Generate Behavior Examples')


	def train_networks(self,event):

		WindowLv1_Trainer('Train Categorizers')

	def test_networks(self,event):

		WindowLv1_Tester('Test Categorizers')


	def analyze_behaviors(self,event):

		WindowLv1_Analyzer('Analyze Behaviors')




def gui():

	the_absolute_current_path=str(Path(__file__).resolve().parent)

	app=wx.App()
	
	InitialWindow('LabGym version '+str(current_version))

	print('The user interface initialized!')
	
	app.MainLoop()




if __name__=='__main__':

	gui()








