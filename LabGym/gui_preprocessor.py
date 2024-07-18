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
import numpy as np



class WindowLv2_ProcessVideos(wx.Frame):

	'''
	The 'Preprocess Videos' functional unit
	'''

	def __init__(self,title):

		super(WindowLv2_ProcessVideos,self).__init__(parent=None,title=title,size=(1000,400))
		self.path_to_videos=None # path to a batch of videos for preprocessing
		self.framewidth=None # if not None, will resize the video frame keeping the original w:h ratio
		self.result_path=None # the folder for storing preprocessed videos
		self.trim_video=False # whether to trim videos into shorter clips, different clips from the same video can be merged
		self.time_windows=[] # the time windows (short clips) for trimming the videos
		self.enhance_contrast=False # whether to enhance the contrast in videos
		self.decode_t=False # whether to decode the time windows for trimming the videos from '_stt' and '_edt_' in video file names
		self.contrast=1.0 # contrast enhancement factor
		self.crop_frame=False # whether to crop the frames of videos
		self.left=0 # frame cropping coordinates left
		self.right=0 # frame cropping coordinates right
		self.top=0 # frame cropping coordinates top
		self.bottom=0 # frame cropping coordinates bottom
		self.fps_new=None # the target fps to downsize

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s)\nfor preprocessing',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		wx.Button.SetToolTip(button_inputvideos,'Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.')
		self.text_inputvideos=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store\nthe processed videos',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify whether to enter time windows\nto form a trimmed video',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		wx.Button.SetToolTip(button_duration,'If "Yes", specify time windows by format: starttime1-endtime1,starttime2-endtime2,...to form the new, trimmed videos. See Extended Guide how to set different time windows for different videos.')
		self.text_duration=wx.StaticText(panel,label='Default: not to trim a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_cropframe=wx.BoxSizer(wx.HORIZONTAL)
		button_cropframe=wx.Button(panel,label='Specify whether to crop\nthe video frames',size=(300,40))
		button_cropframe.Bind(wx.EVT_BUTTON,self.crop_frames)
		wx.Button.SetToolTip(button_cropframe,'Cropping frames to exclude unnecessary areas can increase the analysis efficiency. You need to specify the 4 corner points of the cropping window. This cropping window will be applied for all videos selected.')
		self.text_cropframe=wx.StaticText(panel,label='Default: not to crop frames.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_cropframe.Add(button_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_cropframe.Add(self.text_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_cropframe,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_enhancecontrast=wx.BoxSizer(wx.HORIZONTAL)
		button_enhancecontrast=wx.Button(panel,label='Specify whether to enhance\nthe contrast in videos',size=(300,40))
		button_enhancecontrast.Bind(wx.EVT_BUTTON,self.enhance_contrasts)
		wx.Button.SetToolTip(button_enhancecontrast,'Enhancing video contrast will increase the detection accuracy especially when the detection method is background subtraction based. Enter a contrast value to see whether it is good to apply or re-enter it.')
		self.text_enhancecontrast=wx.StaticText(panel,label='Default: not to enhance contrast.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_enhancecontrast.Add(button_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_enhancecontrast.Add(self.text_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_enhancecontrast,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_reducefps=wx.BoxSizer(wx.HORIZONTAL)
		button_reducefps=wx.Button(panel,label='Specify whether to reduce\nthe video fps',size=(300,40))
		button_reducefps.Bind(wx.EVT_BUTTON,self.downsize_fps)
		wx.Button.SetToolTip(button_reducefps,'Reducing video fps can significantly increase the processing speed. High fps may not always benefit behavior identification especially when the behavior dynamics is not that fast.')
		self.text_reducefps=wx.StaticText(panel,label='Default: not to reduce video fps.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_reducefps.Add(button_reducefps,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_reducefps.Add(self.text_reducefps,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_reducefps,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_preprocessvideos=wx.Button(panel,label='Start to preprocess the videos',size=(300,40))
		button_preprocessvideos.Bind(wx.EVT_BUTTON,self.preprocess_videos)
		wx.Button.SetToolTip(button_preprocessvideos,'Preprocess each selected video.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_preprocessvideos,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_videos(self,event):

		wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov;*.mts)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov;*.mts'
		dialog=wx.FileDialog(self,'Select video(s)','','',wildcard,style=wx.FD_MULTIPLE)

		if dialog.ShowModal()==wx.ID_OK:

			self.path_to_videos=dialog.GetPaths()
			self.path_to_videos.sort()
			path=os.path.dirname(self.path_to_videos[0])
			dialog1=wx.MessageDialog(self,'Proportional resize the video frames?','(Optional) resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog1.ShowModal()==wx.ID_YES:
				dialog2=wx.NumberEntryDialog(self,'Enter the desired frame width','The unit is pixel:','Desired frame width',480,1,10000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog2.GetValue())
					if self.framewidth<10:
						self.framewidth=10
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (proportionally resize framewidth to '+str(self.framewidth)+').')
				else:
					self.framewidth=None
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
				dialog2.Destroy()
			else:
				self.framewidth=None
				self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
			dialog1.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Processed videos will be in: '+self.result_path+'.')
		dialog.Destroy()


	def input_duration(self,event):

		dialog=wx.MessageDialog(self,'Whether to trim a video?','Trim videos?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.trim_video=True
		else:
			self.trim_video=False
			self.text_duration.SetLabel('Not to trim the videos.')
		dialog.Destroy()

		if self.trim_video is True:
			methods=['Decode from filenames: "_stt_" and "_edt_"','Enter time points']
			dialog=wx.SingleChoiceDialog(self,message='Specify the time windows for trimming videos',caption='Time windows for trimming videos',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Decode from filenames: "_stt_" and "_edt_"':
					self.decode_t=True
					self.text_duration.SetLabel('The time windows to form the new, trimmed video will be decoded from filenames: "_stt_" and "_edt_".')
				else:
					self.decode_t=False
					dialog1=wx.TextEntryDialog(self,'Format: starttime1-endtime1,starttime2-endtime2,...','Enter the time windows (in seconds)')
					if dialog1.ShowModal()==wx.ID_OK:
						time_windows=dialog1.GetValue()
						self.time_windows=[]
						try:
							for i in time_windows.split(','):
								times=i.split('-')
								self.time_windows.append([times[0],times[1]])
							self.text_duration.SetLabel('The time windows to form the new, trimmed video: '+str(self.time_windows)+'.')
						except:
							self.trim_video=False
							self.text_duration.SetLabel('Not to trim the videos.')
							wx.MessageBox('Please enter the time windows in correct format!','Error',wx.OK|wx.ICON_ERROR)
					else:
						self.trim_video=False
						self.text_duration.SetLabel('Not to trim the videos.')
					dialog1.Destroy()
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

			if self.framewidth is not None:
				frame=cv2.resize(frame,(self.framewidth,int(frame.shape[0]*self.framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)
			
			canvas=np.copy(frame)
			h,w=frame.shape[:2]
			for y in range(0,h,50):
				cv2.line(canvas,(0,y),(w,y),(255,0,255),1)
				cv2.putText(canvas,str(y),(5,y+15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
			for x in range(0,w,50):
				cv2.line(canvas,(x,0),(x,h),(255,0,255),1)
				cv2.putText(canvas,str(x),(x+5,15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
			cv2.namedWindow('The first frame in coordinates',cv2.WINDOW_NORMAL)
			cv2.imshow('The first frame in coordinates',canvas)

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

			cv2.destroyAllWindows()
			

	def enhance_contrasts(self,event):

		if self.path_to_videos is None:

			wx.MessageBox('No video selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			capture=cv2.VideoCapture(self.path_to_videos[0])
			while True:
				retval,frame=capture.read()
				break
			capture.release()

			if self.framewidth is not None:
				frame=cv2.resize(frame,(self.framewidth,int(frame.shape[0]*self.framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

			stop=False
			while stop is False:
				cv2.destroyAllWindows()
				cv2.namedWindow('The first frame in coordinates',cv2.WINDOW_NORMAL)
				cv2.imshow('The first frame in coordinates',frame)
				dialog=wx.TextEntryDialog(self,'Enter the fold changes for contrast enhancement','A number between 1.0~5.0')
				if dialog.ShowModal()==wx.ID_OK:
					contrast=dialog.GetValue()
					try:
						self.contrast=float(contrast)
						show_frame=frame*self.contrast
						show_frame[show_frame>255]=255
						show_frame=np.uint8(show_frame)
						cv2.destroyAllWindows()
						cv2.namedWindow('The first frame in coordinates',cv2.WINDOW_NORMAL)
						cv2.imshow('The first frame in coordinates',show_frame)
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
				dialog.Destroy()
			cv2.destroyAllWindows()


	def downsize_fps(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the new fps','Enter a number:','Target fps',30,1,100)

		if dialog.ShowModal()==wx.ID_OK:
			self.fps_new=int(dialog.GetValue())
			self.text_reducefps.SetLabel('The target fps is: '+str(self.fps_new)+'.')
		else:
			self.fps_new=None
			self.text_reducefps.SetLabel('Default: not to reduce video fps.')

		dialog.Destroy()


	def preprocess_videos(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder.','Error',wx.OK|wx.ICON_ERROR)

		else:

			print('Start to preprocess video(s)...')

			for i in self.path_to_videos:

				if self.decode_t is True:
					self.time_windows=[]
					filename=os.path.splitext(os.path.basename(i))[0].split('_')
					starttime_windows=[x[2:] for x in filename if len(x)>2 and x[:2]=='st']
					endtime_windows=[x[2:] for x in filename if len(x)>2 and x[:2]=='ed']
					for x,startt in enumerate(starttime_windows):
						self.time_windows.append([startt,endtime_windows[x]])

				preprocess_video(i,self.result_path,self.framewidth,trim_video=self.trim_video,time_windows=self.time_windows,
					enhance_contrast=self.enhance_contrast,contrast=self.contrast,
					crop_frame=self.crop_frame,left=self.left,right=self.right,top=self.top,bottom=self.bottom,fps_new=self.fps_new)

			print('Preprocessing completed!')


