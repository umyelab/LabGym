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



from .tools import preprocess_video
import wx
import os
import cv2
import shutil
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib import pyplot as plt
import time
import re
from natsort import natsorted



class WindowLv1_PreprossData(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_PreprossData,self).__init__(parent=None,title=title,size=(500,165))
		self.dispaly_window()

	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,20,0)

		button_processvideos=wx.Button(panel,label='Preprocess Videos',size=(300,40))
		button_processvideos.Bind(wx.EVT_BUTTON,self.process_videos)
		boxsizer.Add(button_processvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)

		button_sortexamples=wx.Button(panel,label='Sort Behavior Examples',size=(300,40))
		button_sortexamples.Bind(wx.EVT_BUTTON,self.sort_examples)
		boxsizer.Add(button_sortexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,20,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def process_videos(self,event):

		WindowLv2_ProcessVideos('Preprocess Videos')


	def sort_examples(self,event):

		WindowLv2_SortingHat('Sort Behavior Examples')



class WindowLv2_ProcessVideos(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_ProcessVideos,self).__init__(parent=None,title=title,size=(1000,390))
		self.path_to_videos=None
		self.result_path=None
		self.trim_video=False
		self.t=0
		self.duration=0
		self.enhance_contrast=False
		self.contrast=1.0
		self.crop_frame=False
		self.left=0
		self.right=0
		self.top=0
		self.bottom=0

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s)\nfor preprocessing',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		self.text_inputvideos=wx.StaticText(panel,label='The same preprocessing methods will be applied in all videos.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store\nthe processed videos',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		self.text_outputfolder=wx.StaticText(panel,label='Will create a subfolder for each video under this folder.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startanalyze=wx.BoxSizer(wx.HORIZONTAL)
		button_startanalyze=wx.Button(panel,label='Specify when the preprocessing\nshould begin (unit: second)',size=(300,40))
		button_startanalyze.Bind(wx.EVT_BUTTON,self.specify_timing)
		self.text_startanalyze=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startanalyze.Add(button_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startanalyze.Add(self.text_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startanalyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify whether to trim a video\ninto shorter video clips',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		self.text_duration=wx.StaticText(panel,label='Default: not to trim a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_cropframe=wx.BoxSizer(wx.HORIZONTAL)
		button_cropframe=wx.Button(panel,label='Specify whether to crop\nthe video frames',size=(300,40))
		button_cropframe.Bind(wx.EVT_BUTTON,self.crop_frames)
		self.text_cropframe=wx.StaticText(panel,label='Cropping to exclude irrelevant area in video frames can greatly increase processing speed.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_cropframe.Add(button_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_cropframe.Add(self.text_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)

		module_enhancecontrast=wx.BoxSizer(wx.HORIZONTAL)
		button_enhancecontrast=wx.Button(panel,label='Specify whether to enhance\nthe contrast in videos',size=(300,40))
		button_enhancecontrast.Bind(wx.EVT_BUTTON,self.enhance_contrasts)
		self.text_enhancecontrast=wx.StaticText(panel,label='Enhancing contrast can greatly increase tracking accuracy in background subtraction-based detection.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_enhancecontrast.Add(button_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_enhancecontrast.Add(self.text_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)

		button_preprocessvideos=wx.Button(panel,label='Start to preprocess the videos',size=(300,40))
		button_preprocessvideos.Bind(wx.EVT_BUTTON,self.preprocess_videos)
		boxsizer.Add(button_preprocessvideos,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_videos(self,event):

		wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'
		dialog=wx.FileDialog(self,'Select video(s)','','',wildcard,style=wx.FD_MULTIPLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			self.path_to_videos.sort()
			path=os.path.dirname(self.path_to_videos[0])
			self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+'.')
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Processed videos will be in: '+self.result_path+'.')
		dialog.Destroy()


	def specify_timing(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the beginning time of preprocessing','The unit is second:','Beginning time of preprocessing',0,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.t=float(dialog.GetValue())
			if self.t<0:
				self.t=0
			self.text_startanalyze.SetLabel('preprocessing will begin at the: '+str(self.t)+' second.')
		dialog.Destroy()
		

	def input_duration(self,event):

		dialog=wx.MessageDialog(self,'Whether to trim a video?','Trim videos?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.trim_video=True
		else:
			self.trim_video=False
		dialog.Destroy()

		if self.trim_video is True:
			dialog=wx.NumberEntryDialog(self,'Enter the duration of each trimmed clip','The unit is second:','Trimmed clip duration',0,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.duration=int(dialog.GetValue())
				if self.duration!=0:
					self.text_duration.SetLabel('The duration of each trimmed video clip is '+str(self.duration)+' seconds.')
				else:
					self.text_duration.SetLabel('Will not trim the videos.')
			dialog.Destroy()


	def crop_frames(self,event):

		if self.path_to_videos is None:

			wx.MessageBox('No video selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			capture=cv2.VideoCapture(self.path_to_videos[0])
			while True:
				retval,frame=capture.read()
				break
			capture.release()
			frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

			plt.imshow(frame)
			plt.show()

			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter the coordinates (integers) of the cropping window','Format:[left,right,top,bottom]')
				if dialog.ShowModal()==wx.ID_OK:
					coordinates=list(dialog.GetValue().split(','))
					if len(coordinates)==4:
						try:
							self.left=int(coordinates[0])
							self.right=int(coordinates[1])
							self.top=int(coordinates[2])
							self.bottom=int(coordinates[3])
							self.crop_frame=True
							stop=True
							self.text_cropframe.SetLabel('The cropping window is from left: '+str(self.left)+' to right: '+str(self.right)+', from top: '+str(self.top)+' to bottom: '+str(self.bottom)+'.')
						except:
							self.crop_frame=False
							wx.MessageBox('Please enter 4 integers.','Error',wx.OK|wx.ICON_ERROR)
							self.text_cropframe.SetLabel('Not to crop the frames')
					else:
						self.crop_frame=False
						wx.MessageBox('Please enter the coordinates (integers) in correct format.','Error',wx.OK|wx.ICON_ERROR)
						self.text_cropframe.SetLabel('Not to crop the frames')
				else:
					self.crop_frame=False
					self.text_cropframe.SetLabel('Not to crop the frames')
					stop=True
				dialog.Destroy()
			plt.close()


	def enhance_contrasts(self,event):

		if self.path_to_videos is None:

			wx.MessageBox('No video selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			capture=cv2.VideoCapture(self.path_to_videos[0])
			while True:
				retval,frame=capture.read()
				break
			capture.release()
			frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter the fold changes for contrast enhancement','A number between 1.0~5.0')
				if dialog.ShowModal()==wx.ID_OK:
					contrast=dialog.GetValue()
					try:
						self.contrast=float(contrast)
						show_frame=frame*self.contrast
						show_frame[show_frame>255]=255
						show_frame=np.uint8(show_frame)
						plt.imshow(show_frame)
						plt.show()
						dialog1=wx.MessageDialog(self,'Apply the current contrast value?','Apply value?',wx.YES_NO|wx.ICON_QUESTION)
						if dialog1.ShowModal()==wx.ID_YES:
							stop=True
							self.enhance_contrast=True
							self.text_enhancecontrast.SetLabel('The contrast enhancement fold change is: '+str(self.contrast)+'.')
						else:
							self.enhance_contrast=False
							self.text_enhancecontrast.SetLabel('Not to enhance contrast.')
						dialog1.Destroy()
					except:
						self.enhance_contrast=False
						wx.MessageBox('Please enter a float number between 1.0~5.0.','Error',wx.OK|wx.ICON_ERROR)
						self.text_enhancecontrast.SetLabel('Not to enhance contrast.')
				else:
					self.enhance_contrast=False
					stop=True
					self.text_enhancecontrast.SetLabel('Not to enhance contrast.')
				plt.close()
				dialog.Destroy()



	def preprocess_videos(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder.','Error',wx.OK|wx.ICON_ERROR)

		else:

			for i in self.path_to_videos:

				print('Start to preprocess video(s)...')
				preprocess_video(i,self.result_path,trim_video=self.trim_video,start_t=self.t,duration=self.duration,enhance_contrast=self.enhance_contrast,contrast=self.contrast,crop_frame=self.crop_frame,left=self.left,right=self.right,top=self.top,bottom=self.bottom)



###################################################################################################################
# below is modified from Isabelle Baker's LabGymSortingHat repo: https://github.com/IsabelleBaker/LabGymSortingHat
###################################################################################################################

class SortingHat():

	def __init__(self):
		self.behavior_names = []
		self.behavior_key_mapping = []
		self.input_image_directory = None
		self.output_image_directory = None
		self.remove_empty_frames = True
		self.image_display_sizes = 0, 0
		self.undo_key = None
		self.right_arrow = 316
		self.left_arrow = 314
		self.behavior_sample_paths = None
		self.category_directories = None
		self.category_strings = None
		self.undo_list = [[], [], []]
		self.label_scale = 20
		self.label_height = np.inf
		self.label_width = np.inf
		self.current_index = 0
		self.image_name = None
		self.video_name = None
		self.cap = None
		self.display_image = None
		self.video_location = None
		self.video = None
		self.video_location = None
		self.video = None
		self.video_frames = []
		self.timer_interval = None

	def prepare_hat(self, behavior_names=[], behavior_key_mapping=[],input_image_directory='', output_image_directory=os.getcwd(),remove_empty_frames=True, image_display_sizes=(600, 600), undo_key='U'):
		self.behavior_names = behavior_names
		self.behavior_key_mapping = behavior_key_mapping
		self.input_image_directory = input_image_directory
		self.output_image_directory = output_image_directory
		self.remove_empty_frames = remove_empty_frames
		self.image_display_sizes = image_display_sizes
		self.undo_key = undo_key
		self.behavior_sample_paths = []

		for root, dirs, files in os.walk(self.input_image_directory, topdown=False):
			for name in files:
				if name.endswith('.avi'):
					self.behavior_sample_paths.append((root, name[:-4]))
		if not self.behavior_sample_paths:
			wx.MessageBox("No Behavior Examples in the Input folder", "Complete!", wx.OK | wx.ICON_INFORMATION)
		self.behavior_sample_paths = natsorted(self.behavior_sample_paths)
		self.category_directories = []
		self.category_strings = []
		for i in range(len(self.behavior_names)):
			self.category_strings.append((self.behavior_key_mapping[i]) + ': ' + self.behavior_names[i])
			if not os.path.exists(os.path.join(self.output_image_directory, self.behavior_names[i])):
				os.makedirs(os.path.join(self.output_image_directory, self.behavior_names[i]))
			self.category_directories.append(
				os.path.join(self.output_image_directory, self.behavior_names[i]))
		self.category_strings.append("U: Undo")
		self.category_strings.append("<-: Prev")
		self.category_strings.append("->: Next")
		self.scale_text()
		self.update_image_pointer()

	def scale_text(self):
		self.label_scale = 100
		self.label_height = np.inf
		self.label_width = np.inf
		for j in range(len(self.category_strings)):
			while self.label_height > (self.image_display_sizes[1] / len(self.category_strings)) * .7:
				self.label_scale = self.label_scale * .9
				(self.label_width, self.label_height), baseline = cv2.getTextSize(self.category_strings[j],cv2.FONT_HERSHEY_SIMPLEX,self.label_scale,int(2 * self.label_scale))
				self.label_height = self.label_height + baseline
			while self.label_width > (self.image_display_sizes[0] * 2 * .1):
				self.label_scale = self.label_scale * .9
				(self.label_width, self.label_height), baseline = cv2.getTextSize(self.category_strings[j],cv2.FONT_HERSHEY_SIMPLEX,self.label_scale,int(2 * self.label_scale))
				self.label_height = self.label_height + baseline

	def update_image_pointer(self):
		while True:
			self.image_name = os.path.join(self.behavior_sample_paths[self.current_index][0],self.behavior_sample_paths[self.current_index][1] + ".jpg")
			self.video_name = os.path.join(self.behavior_sample_paths[self.current_index][0],self.behavior_sample_paths[self.current_index][1] + ".avi")
			try:
				self.display_image = cv2.imread(self.image_name)
				self.display_image = cv2.resize(self.display_image, dsize=self.image_display_sizes,interpolation=cv2.INTER_CUBIC)
				self.display_image = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
			except:
				print(f"The pattern image was not present: {self.image_name}")
				self.behavior_sample_paths.remove(self.behavior_sample_paths[self.current_index])
				return
			try:
				self.cap = cv2.VideoCapture(self.video_name)
			except:
				print(f"The animation was not present: {self.image_name}")
				self.behavior_sample_paths.remove(self.behavior_sample_paths[self.current_index])
				return
			if self.remove_empty_frames:
				found_empty = False
				while True:
					_, frame = self.cap.read()
					if frame is None:
						break
					if not frame.any():
						found_empty = True
						break
				if found_empty:
					self.behavior_sample_paths.remove(self.behavior_sample_paths[self.current_index])
					print("Found empty frame in: " + self.behavior_sample_paths[self.current_index][0] + "/" +
						self.behavior_sample_paths[self.current_index][1])
					if not self.behavior_sample_paths:
						return
				else:
					self.cap.set(cv2.CAP_PROP_POS_MSEC, 0)
					return

	def load_new_video(self):
		self.video_frames = []
		try:
			self.video = self.cap
			self.display_image = self.display_image
		except:
			print(f"The animation was not present: {self.image_name}")
			self.behavior_sample_paths.remove(self.behavior_sample_paths[self.current_index])
			return
		while True:
			_, frame = self.video.read()
			if frame is None:
				break
			else:
				self.video_frames.append(cv2.resize(frame, self.image_display_sizes))
				frame = cv2.resize(frame, dsize=self.image_display_sizes, interpolation=cv2.INTER_CUBIC)
				horizontal_concat = np.concatenate((self.display_image, frame), axis=1)

				for j in range(len(self.category_strings)):
					cv2.putText(horizontal_concat, self.category_strings[j],(int(self.image_display_sizes[0] - self.label_width / 2),self.label_height * (j + 1) + 1),cv2.FONT_HERSHEY_SIMPLEX, self.label_scale, (255, 0, 0), int(self.label_scale * 2))
				self.video_frames[-1] = horizontal_concat
				height, width = self.video_frames[-1].shape[:2]
				image = wx.Image(width, height)
				image.SetData(self.video_frames[-1])
				self.video_frames[-1] = image.ConvertToBitmap()
		self.timer_interval = self.video.get(cv2.CAP_PROP_FPS)



class SortingHatFrame(wx.Frame):

	def __init__(self, parent, input_directory=os.getcwd(), output_directory=os.path.join(os.getcwd(), 'output/'),categories=["junk"], category_mapping=["0"]):
		wx.Frame.__init__(self, parent, style=wx.WANTS_CHARS | wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER,title="SortingHat", size=(1200, 600))
		self.sort = SortingHat()
		self.sort.prepare_hat(categories,category_mapping,input_directory,output_directory,True,(600, 600))
		self.panel = wx.Panel(self, wx.ID_ANY, size=(1200, 600))
		self.Centre()
		self.panel.Bind(wx.EVT_TIMER, self.evt_timer)
		self.panel.timer = wx.Timer(self.panel)
		self.sort.update_image_pointer()
		self.sort.load_new_video()
		self.video_frame = 0
		self.panel.Bind(wx.EVT_KEY_DOWN, self.evt_on_key_event)
		self.Bind(wx.EVT_PAINT, self.evt_on_paint)
		self.Bind(wx.EVT_SIZE, self.evt_on_resize)
		self.panel.timer.Start(milliseconds=(int(1000 / self.sort.timer_interval)))

	def restart_timer(self):
		self.panel.timer.Stop()
		self.panel.timer.Start(milliseconds=(int(1000 / self.sort.timer_interval)))

	def evt_on_key_event(self, event):
		k = event.GetKeyCode()
		if (k == self.sort.left_arrow) and (self.sort.current_index > 0):
			self.sort.current_index -= 1
			self.sort.update_image_pointer()
			self.sort.load_new_video()
			self.restart_timer()
			return
		elif (k == self.sort.right_arrow) and (self.sort.current_index >= 0) and (self.sort.current_index < (len(self.sort.behavior_sample_paths) - 1)):
			self.sort.current_index += 1
			self.sort.update_image_pointer()
			self.sort.load_new_video()
			self.restart_timer()
			return
		elif str(chr(k)) in self.sort.behavior_key_mapping:
			file_name = self.sort.behavior_sample_paths[self.sort.current_index][1]
			shutil.move(self.sort.image_name,os.path.join(self.sort.category_directories[self.sort.behavior_key_mapping.index(str(chr(k)))],file_name + ".jpg"))
			shutil.move(self.sort.video_name,os.path.join(self.sort.category_directories[self.sort.behavior_key_mapping.index(str(chr(k)))],file_name + ".avi"))
			self.sort.undo_list[0].append([self.sort.category_directories[self.sort.behavior_key_mapping.index(str(chr(k)))], file_name])
			self.sort.undo_list[1].append(self.sort.current_index)
			self.sort.undo_list[2].append(self.sort.behavior_sample_paths[self.sort.current_index])
			self.sort.behavior_sample_paths.remove(self.sort.behavior_sample_paths[self.sort.current_index])
			if not self.sort.behavior_sample_paths:
				wx.MessageBox("Done Sorting Behavior Examples", "Complete!", wx.OK | wx.ICON_INFORMATION)
				self.Close()
			elif self.sort.current_index >= (len(self.sort.behavior_sample_paths) - 1):
				self.sort.current_index -= 1
				self.sort.update_image_pointer()
				self.sort.load_new_video()
				self.restart_timer()
			else:
				self.sort.update_image_pointer()
				self.sort.load_new_video()
				self.restart_timer()
			return
		elif (str(chr(k)) == self.sort.undo_key) and (len(self.sort.undo_list[0]) > 0):
			sorted_path = self.sort.undo_list[0][-1][0]
			original_path = self.sort.undo_list[2][-1][0]
			image_name = self.sort.undo_list[0][-1][1] + ".jpg"
			video_name = self.sort.undo_list[0][-1][1] + ".avi"
			shutil.move(os.path.join(sorted_path, image_name), os.path.join(original_path, image_name))
			shutil.move(os.path.join(sorted_path, video_name), os.path.join(original_path, video_name))
			self.sort.behavior_sample_paths.insert(self.sort.undo_list[1][-1], self.sort.undo_list[2][-1])
			self.sort.undo_list[0].pop()
			self.sort.undo_list[1].pop()
			self.sort.undo_list[2].pop()
			self.sort.update_image_pointer()
			self.sort.load_new_video()
			self.restart_timer()
			return
		else:
			return

	def evt_timer(self, event):
		if self.Size != (self.sort.image_display_sizes[0] * 2, self.sort.image_display_sizes[0]):
			self.sort.update_image_pointer()
			self.sort.load_new_video()
			self.restart_timer()
		self.evt_on_paint(None)
		if self.video_frame == 0: time.sleep(0.5)
		self.video_frame += 1

	def evt_on_paint(self, event):
		dc = wx.BufferedPaintDC(self)
		if self.video_frame < len(self.sort.video_frames):
			frame = self.sort.video_frames[self.video_frame]
		else:
			self.video_frame = 0
			frame = self.sort.video_frames[self.video_frame]
		dc.DrawBitmap(frame, 0, 0, False)

	def evt_on_resize(self, event):
		temp = self.Size
		self.panel.size = temp
		self.sort.scale_text()
		self.sort.update_image_pointer()
		self.sort.load_new_video()
		self.restart_timer()
		self.sort.image_display_sizes = (int(temp[0] / 2 + 0.5), temp[1] - 20)

	def onClose(self, event):
		self.Close()



class WindowLv2_SortingHat(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_SortingHat,self).__init__(parent=None,title=title,size=(1000,250))
		self.input_directory = None
		self.output_directory = None
		self.categories = []
		self.category_mapping = []
		self.undo_key = 'U'

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that stores\nunsorted behavior examples',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.evt_get_input_directory)
		self.text_inputfolder=wx.StaticText(panel,label='Each example pair contains an animation and a pattern image generated by LabGym.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe sorted behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON, self.evt_get_output_directory)
		self.text_outputfolder=wx.StaticText(panel,label='Behavior examples of the same behavior type are stored in a subfolder with the behavior name.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_entercategories=wx.BoxSizer(wx.HORIZONTAL)
		button_entercategories=wx.Button(panel,label='Enter the behavior names and\ncorresponding shortcut keys',size=(300,40))
		button_entercategories.Bind(wx.EVT_BUTTON,self.evt_enter_categories)
		self.text_entercategories=wx.StaticText(panel,label="Every pair of behavior name and shortcut key should be in format of 'behaviorname{key}'.",style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_entercategories.Add(button_entercategories,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_entercategories.Add(self.text_entercategories,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_entercategories,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_sort=wx.Button(panel,label='Sort behavior examples',size=(300,40))
		button_sort.Bind(wx.EVT_BUTTON,self.evt_start_sorting)
		boxsizer.Add(button_sort,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)

	def evt_get_input_directory(self, event):
		dlg = wx.DirDialog(None, "Choose input directory", "",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self.input_directory = dlg.GetPath()
			self.text_inputfolder.SetLabel('Unsorted behavior examples are in: '+self.input_directory)
		dlg.Destroy()

	def evt_get_output_directory(self, event):
		dlg = wx.DirDialog(None, "Choose output directory", "",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self.output_directory = dlg.GetPath()
			self.text_outputfolder.SetLabel('Sorted behavior examples will be in: '+self.output_directory)
		dlg.Destroy()

	def evt_enter_categories(self, event):
		existing_category_mappings = ""
		if self.category_mapping:
			for i in range(len(self.category_mapping)):
				existing_category_mappings += str(self.categories[i]) + "{" + str(self.category_mapping[i]) + "}"
				if i < (len(self.category_mapping) - 1):
					existing_category_mappings += ","
		dlg = wx.TextEntryDialog(self, 'Enter Name-Key pairs separated by commas.  ''\n\nFormat: behaviorname1{key1},behaviorname2{key2},etc''\n', 'Behavior Name and Key Entry', value=existing_category_mappings)
		while True:
			if dlg.ShowModal() == wx.ID_OK:
				txt = dlg.GetValue()
				temp_categories = []
				temp_category_mapping = []
				if len(txt):
					x = txt.split(",")
					for i in range(len(x)):
						temp = str(x[i].strip())
						temp2 = re.split('{|}', temp)
						if len(temp2) > 1:
							if len(temp2[1].strip()) == 1:
								if str(temp2[1].strip()) == self.undo_key.upper() or str(temp2[1].strip()) == self.undo_key.lower():
									temp_category_mapping = []
									temp_categories = []
									wx.MessageBox(temp2[1].strip() + " is reserved as the Undo Key Value\n""Check your entry names and keys", "Error",wx.OK | wx.ICON_INFORMATION)
								elif (temp2[1].strip() in temp_category_mapping) or (str(temp2[0].strip()) in temp_categories):
									temp_category_mapping = []
									temp_categories = []
									wx.MessageBox("Behavior Name and Key Mapping Duplicate Found. \n ""Check your entry names and keys", "Error",wx.OK | wx.ICON_INFORMATION)
								else:
									temp_category_mapping.extend(temp2[1].strip())
									temp_categories.append(str(temp2[0].strip()))
							else:
								temp_category_mapping = []
								temp_categories = []
								wx.MessageBox("Behavior Name and Key Mapping Incorrect \n ""Key must be only a single character \n""Format: behaviorname{character}","Error", wx.OK | wx.ICON_INFORMATION)
								break
						else:
							temp_category_mapping = []
							temp_categories = []
							wx.MessageBox("Behavior Name and Key Mapping Incorrect", "Error", wx.OK | wx.ICON_INFORMATION)
							break
					if temp_category_mapping:
						self.category_mapping = temp_category_mapping
						self.categories = temp_categories
						self.text_entercategories.SetLabel("Entered 'behaviorname{shortcutkey}' pairs: "+txt)
						return
			else:
				break

	def evt_start_sorting(self, event):
		if self.input_directory is None:
			wx.MessageBox("No Input Directory Provided", "Error", wx.OK | wx.ICON_INFORMATION)
		elif self.output_directory is None:
			wx.MessageBox("No Output Directory Provided", "Error", wx.OK | wx.ICON_INFORMATION)
		elif len(self.categories) == 0:
			wx.MessageBox("No Behavior Names and Key Provided", "Error", wx.OK | wx.ICON_INFORMATION)
		else:
			Hat = SortingHatFrame(None, self.input_directory, self.output_directory, self.categories,self.category_mapping)
			Hat.Show()


