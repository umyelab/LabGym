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
import time



class WindowLv2_ProcessVideos(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_ProcessVideos,self).__init__(parent=None,title=title,size=(1000,330))
		self.path_to_videos=None
		self.result_path=None
		self.trim_video=False
		self.time_windows=[]
		self.enhance_contrast=False
		self.contrast=1.0
		self.crop_frame=False
		self.left=0
		self.right=0
		self.top=0
		self.bottom=0
		self.decode_t=False

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
		wx.Button.SetToolTip(button_cropframe,'Cropping frames to exclude irrelevant areas can increase the analysis efficiency. You need to specify the 4 corner points of the cropping window. This cropping window will be applied for all videos selected.')
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


	def input_duration(self,event):

		dialog=wx.MessageDialog(self,'Whether to trim a video?','Trim videos?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.trim_video=True
		else:
			self.trim_video=False
		dialog.Destroy()

		if self.trim_video is True:
			methods=['Decode from filenames: "_stt_" and "_edt_"','Enter time points']
			dialog=wx.SingleChoiceDialog(self,message='Specify the time windows for trimming videos',caption='Time windows for trimming videos',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Decode from filenames: "_stt_" and "_edt_"':
					self.decode_t=True
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

				preprocess_video(i,self.result_path,trim_video=self.trim_video,time_windows=self.time_windows,enhance_contrast=self.enhance_contrast,contrast=self.contrast,crop_frame=self.crop_frame,left=self.left,right=self.right,top=self.top,bottom=self.bottom)

			print('Preprocessing completed!')



class WindowLv2_SortBehaviors(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_SortBehaviors,self).__init__(parent=None,title=title,size=(1000,240))
		self.input_path=None
		self.result_path=None
		self.keys_behaviors={}
		self.keys_behaviorpaths={}

		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

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

			while stop is False:

				if moved is True:
					moved=False
					shutil.move(os.path.join(self.input_path,example_name+'.avi'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.avi'))
					shutil.move(os.path.join(self.input_path,example_name+'.jpg'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.jpg'))

				animations=[i for i in os.listdir(self.input_path) if i.endswith('.avi')]
				animations.sort()

				if len(animations)>0 and index<len(animations):

					example_name=animations[index].split('.')[0]

					animation=cv2.VideoCapture(os.path.join(self.input_path,example_name+'.avi'))
					fps=round(animation.get(cv2.CAP_PROP_FPS))
					pattern_image=cv2.resize(cv2.imread(os.path.join(self.input_path,example_name+'.jpg')),(600,600),interpolation=cv2.INTER_AREA)

					while True:

						ret,frame=animation.read()
						if not ret:
							animation.set(cv2.CAP_PROP_POS_FRAMES,0)
							continue

						frame=cv2.resize(frame,(600,600),interpolation=cv2.INTER_AREA)
						combined=np.hstack((frame,pattern_image))

						n=1
						for i in ['o: Prev','p: Next','q: Quit','u: Undo']:
							cv2.putText(combined,i,(550,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
							n+=1
						n+=1
						for i in self.keys_behaviors:
							cv2.putText(combined,i+': '+self.keys_behaviors[i],(550,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
							n+=1

						cv2.imshow('Sorting Behavior Examples',combined)
						cv2.moveWindow('Sorting Behavior Examples',50,0)

						key=cv2.waitKey(int(1000/fps)) & 0xFF

						for shortcutkey in self.keys_behaviorpaths:
							if key==ord(shortcutkey):
								example_name=animations[index].split('.')[0]
								actions.append([shortcutkey,example_name])
								moved=True
								break
						if moved is True:
							break

						if key==ord('u'):
							if len(actions)>0:
								last=actions.pop()
								shortcutkey=last[0]
								example_name=last[1]
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

					animation.release()

				else:
					if len(animations)==0:
						wx.MessageBox('Behavior example sorting completed!','Completed!',wx.OK|wx.ICON_INFORMATION)
						stop=True
					else:
						index=0

			cv2.destroyAllWindows()


