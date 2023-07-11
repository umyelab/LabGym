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



from .tools import *
import os
import gc
import cv2
import datetime
import numpy as np
import math
from scipy.spatial import distance
from collections import deque
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import pandas as pd
import seaborn as sb
import functools
import operator



class AnalyzeAnimal():

	def __init__(self):

		self.path_to_video=None
		self.basename=None
		self.fps=None
		self.framewidth=None
		self.frameheight=None
		self.kernel=3
		self.results_path=None
		self.dim_tconv=8
		self.dim_conv=8
		self.channel=1
		self.include_bodyparts=False
		self.std=0
		self.categorize_behavior=False
		self.animation_analyzer=True
		self.delta=None
		self.animal_number=None
		self.autofind_t=False
		self.t=0
		self.duration=5
		self.length=None
		self.animal_area=None
		self.animal_vs_bg=None
		self.background=None
		self.background_low=None
		self.background_high=None
		self.skipped_frames=[]
		self.all_time=[]
		self.total_analysis_framecount=None
		self.to_deregister={}
		self.count_to_deregister=None
		self.register_counts={}
		self.animal_contours={}
		self.animal_centers={}
		self.animal_existingcenters={}
		self.animal_heights={}
		self.animal_inners={}
		self.animal_blobs={}
		self.animations={}
		self.pattern_images={}
		self.event_probability={}
		self.all_behavior_parameters={}
		

	def prepare_analysis(self,
		path_to_video,
		results_path,
		animal_number,
		delta=1.2, # an estimated fold change (1.2) of the light intensity for optogenetics only
		names_and_colors=None, # the behavior names and their representing colors
		framewidth=None, # the width of the frame to resize
		stable_illumination=True, # whether the illumination in videos is stable
		dim_tconv=8, # input dim of Animation Analyzer
		dim_conv=8, # input dim of Pattern Recognizer
		channel=1, # color of Animation Analyzer
		include_bodyparts=False, # whether to include body parts in pattern images
		std=0, # for excluding static pixels in pattern images
		categorize_behavior=True, # whether to categorize behaviors or just track animals without behavioral categorization
		animation_analyzer=True, # whether to include Animation Analyzer
		path_background=None, # if not None, load backgrounds (need to put the background images under the name 'background.jpg', 'background_low.jpg' and 'background_high.jpg' in the 'path_background' path)
		autofind_t=False, # whether to use the time point of the first time of illumination change as start_t
		t=0, # if autofind_t is False, t is the start_t
		duration=5, # the duration for example generation / analysis
		ex_start=0, # the start time point for background extraction
		ex_end=None, # the end time point for background extraction, if None, use the entire video
		length=15, # the duration (number of frames) of a behavior example (a behavior episode)
		animal_vs_bg=0 # 0: animals brighter than the background; 1: animals darker than the background; 2: hard to tell
		):
		
		print('Preparation started...')
		print(datetime.datetime.now())

		self.path_to_video=path_to_video
		self.basename=os.path.basename(self.path_to_video)
		self.framewidth=framewidth
		self.results_path=os.path.join(results_path,os.path.splitext(self.basename)[0])
		self.animal_number=animal_number
		self.dim_tconv=dim_tconv
		self.dim_conv=dim_conv
		self.channel=channel
		self.include_bodyparts=include_bodyparts
		self.std=std
		self.categorize_behavior=categorize_behavior
		self.animation_analyzer=animation_analyzer
		self.autofind_t=autofind_t
		self.t=t
		self.duration=duration
		self.length=length
		os.makedirs(self.results_path,exist_ok=True)
		capture=cv2.VideoCapture(self.path_to_video)
		self.fps=round(capture.get(cv2.CAP_PROP_FPS))
		self.count_to_deregister=self.fps*2

		if self.duration<=0:
			self.total_analysis_framecount=int(capture.get(cv2.CAP_PROP_FRAME_COUNT))+1
		else:
			self.total_analysis_framecount=int(self.fps*self.duration)+1

		while True:
			retval,frame=capture.read()
			break
		capture.release()

		print('Video fps: '+str(self.fps))
		print('The original video framesize: '+str(int(frame.shape[0]))+' X '+str(int(frame.shape[1])))

		if self.framewidth is not None:
			self.frameheight=int(frame.shape[0]*self.framewidth/frame.shape[1])
			self.background=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)
			print('The resized video framesize: '+str(self.frameheight)+' X '+str(self.framewidth))
		else:
			self.background=frame
		framesize=min(self.background.shape[0],self.background.shape[1])

		if framesize/self.animal_number<250:
			self.kernel=3
		elif framesize/self.animal_number<500:
			self.kernel=5
		elif framesize/self.animal_number<1000:
			self.kernel=7
		elif framesize/self.animal_number<1500:
			self.kernel=9
		else:
			self.kernel=11

		self.delta=delta
		self.autofind_t=autofind_t
		self.animal_vs_bg=animal_vs_bg
		if self.autofind_t is True:
			es_start=None
		else:
			es_start=self.t
		constants=estimate_constants(self.path_to_video,self.delta,self.animal_number,framewidth=self.framewidth,frameheight=self.frameheight,stable_illumination=stable_illumination,ex_start=ex_start,ex_end=ex_end,t=es_start,duration=self.duration,animal_vs_bg=self.animal_vs_bg,path_background=path_background,kernel=self.kernel)
		self.animal_area=constants[4]
		self.background=constants[0]
		self.background_low=constants[1]
		self.background_high=constants[2]
		cv2.imwrite(os.path.join(self.results_path,'background.jpg'),constants[0])
		cv2.imwrite(os.path.join(self.results_path,'background_low.jpg'),constants[1])
		cv2.imwrite(os.path.join(self.results_path,'background_high.jpg'),constants[2])
		if self.autofind_t is True:
			self.t=constants[3]

		if self.categorize_behavior is True:
			for behavior_name in names_and_colors:
				self.all_behavior_parameters[behavior_name]={}
				self.all_behavior_parameters[behavior_name]['color']=names_and_colors[behavior_name]
				for parameter_name in ['acceleration','count','distance','duration','intensity_area','intensity_length','latency','magnitude_area','magnitude_length','probability','speed','velocity','vigor_area','vigor_length']:
					self.all_behavior_parameters[behavior_name][parameter_name]={}
		else:
			self.dim_conv=8
			self.animation_analyzer=False
			for parameter_name in ['acceleration','distance','intensity_area','intensity_length','magnitude_area','magnitude_length','speed','velocity','vigor_area','vigor_length']:
				self.all_behavior_parameters[parameter_name]={}

		for i in range(self.animal_number):
			self.to_deregister[i]=0
			self.register_counts[i]=None
			self.animal_contours[i]=[None]*self.total_analysis_framecount
			self.animal_centers[i]=[None]*self.total_analysis_framecount
			self.animal_existingcenters[i]=(-10000,-10000)
			self.animal_heights[i]=[None]*self.total_analysis_framecount
			if self.include_bodyparts is True:
				self.animal_inners[i]=deque(maxlen=self.length)
			if self.animation_analyzer is True:
				self.animal_blobs[i]=deque([np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')],maxlen=self.length)*self.length
				self.animations[i]=[np.zeros((self.length,self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')]*self.total_analysis_framecount
			self.pattern_images[i]=[np.zeros((self.dim_conv,self.dim_conv,3),dtype='uint8')]*self.total_analysis_framecount

		print('Prepration completed!')


	def track_animal(self,frame_count_analyze,contours,centers,heights,inners=None,blobs=None):

		unused_existing_indices=list(self.animal_existingcenters)
		existing_centers=list(self.animal_existingcenters.values())
		unused_new_indices=list(range(len(centers)))
		dt_flattened=distance.cdist(existing_centers,centers).flatten()
		dt_sort_index=dt_flattened.argsort()
		length=len(centers)

		for idx in dt_sort_index:
			index_in_existing=int(idx/length)
			index_in_new=int(idx%length)
			if index_in_existing in unused_existing_indices:
				if index_in_new in unused_new_indices:
					unused_existing_indices.remove(index_in_existing)
					unused_new_indices.remove(index_in_new)
					if self.register_counts[index_in_existing] is None:
						self.register_counts[index_in_existing]=frame_count_analyze
					self.to_deregister[index_in_existing]=0
					self.animal_contours[index_in_existing][frame_count_analyze]=contours[index_in_new]
					center=centers[index_in_new]
					self.animal_centers[index_in_existing][frame_count_analyze]=center
					self.animal_existingcenters[index_in_existing]=center
					self.animal_heights[index_in_existing][frame_count_analyze]=heights[index_in_new]
					if self.animation_analyzer is True:
						blob=blobs[index_in_new]
						blob=img_to_array(cv2.resize(blob,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA))
						self.animal_blobs[index_in_existing].append(blob)
						self.animations[index_in_existing][frame_count_analyze]=np.array(self.animal_blobs[index_in_existing])
					if self.include_bodyparts is True:
						self.animal_inners[index_in_existing].append(inners[index_in_new])
						pattern_image=generate_patternimage(self.background,self.animal_contours[index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],inners=self.animal_inners[index_in_existing],std=self.std)
					else:
						pattern_image=generate_patternimage(self.background,self.animal_contours[index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],inners=None,std=0)
					pattern_image=cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA)
					self.pattern_images[index_in_existing][frame_count_analyze]=np.array(pattern_image)

		if len(unused_existing_indices)>0:
			for i in unused_existing_indices:
				if self.to_deregister[i]<=self.count_to_deregister:
					self.to_deregister[i]+=1		
				else:
					self.animal_existingcenters[i]=(-10000,-10000)
				if self.animation_analyzer is True:
					self.animal_blobs[i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
				if self.include_bodyparts is True:
					self.animal_inners[i].append(None)


	def acquire_information(self,background_free=True):

		print('Acquiring information in each frame...')
		print(datetime.datetime.now())

		capture=cv2.VideoCapture(self.path_to_video)

		background=self.background
		background_low=self.background_low
		background_high=self.background_high
		if self.animal_vs_bg==1:
			background=np.uint8(255-background)
			background_low=np.uint8(255-background_low)
			background_high=np.uint8(255-background_high)

		frame_count=frame_count_analyze=0
		if background_free is False:
			temp_frames=deque(maxlen=self.length)
			animation=deque([np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')],maxlen=self.length)*self.length

		start_t=round((self.t-self.length/self.fps),2)
		if start_t<0:
			start_t=0.00
		if self.duration==0:
			end_t=float('inf')
		else:
			end_t=start_t+self.duration

		while True:

			retval,frame=capture.read()
			time=round((frame_count+1)/self.fps,2)

			if time>=end_t or frame is None:
				break

			if time>=start_t:

				self.all_time.append(round((time-start_t),2))
				
				if (frame_count_analyze+1)%1000==0:
					print(str(frame_count_analyze+1)+' frames processed...')
					print(datetime.datetime.now())

				if self.framewidth is not None:
					frame=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)

				if background_free is False:
					temp_frames.append(frame)

				(contours,centers,heights,inners,blobs)=contour_frame(frame,self.animal_number,background,background_low,background_high,self.delta,self.animal_area,animal_vs_bg=self.animal_vs_bg,include_bodyparts=self.include_bodyparts,animation_analyzer=self.animation_analyzer,channel=self.channel,kernel=self.kernel)

				if len(contours)==0:

					self.skipped_frames.append(frame_count_analyze)

					for i in self.animal_centers:
						if self.animation_analyzer is True:
							self.animal_blobs[i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
						if self.include_bodyparts is True:
							self.animal_inners[i].append(None)

				else:

					self.track_animal(frame_count_analyze,contours,centers,heights,inners=inners,blobs=blobs)

					if self.animation_analyzer is True:
						if background_free is False:
							for i in self.animal_centers:
								for n,f in enumerate(temp_frames):
									if self.animal_contours[i][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1][n] is None:
										blob=np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')
									else:
										blob=extract_blob_background(f,self.animal_contours[i][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],contour=None,channel=self.channel,background_free=False)
										blob=cv2.resize(blob,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA)
									animation.append(img_to_array(blob))
								self.animations[i][frame_count_analyze]=np.array(animation)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		print('Information acquisition completed!')


	def acquire_information_interact_basic(self,background_free=True):

		print('Acquiring information in each frame...')
		print(datetime.datetime.now())

		if self.animation_analyzer is True:
			self.animations[0]=[np.zeros((self.length,self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')]*self.total_analysis_framecount
		self.pattern_images[0]=[np.zeros((self.dim_conv,self.dim_conv,3),dtype='uint8')]*self.total_analysis_framecount
		self.animal_contours[0]=[None]*self.total_analysis_framecount
		self.animal_centers[0]=[None]*self.total_analysis_framecount

		background=self.background
		background_low=self.background_low
		background_high=self.background_high
		if self.animal_vs_bg==1:
			background=np.uint8(255-background)
			background_low=np.uint8(255-background_low)
			background_high=np.uint8(255-background_high)

		capture=cv2.VideoCapture(self.path_to_video)
		frame_count=frame_count_analyze=0
		temp_frames=deque(maxlen=self.length)
		temp_contours=deque(maxlen=self.length)
		temp_inners=deque(maxlen=self.length)
		animation=deque([np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')],maxlen=self.length)*self.length

		start_t=round((self.t-self.length/self.fps),2)
		if start_t<0:
			start_t=0.00
		if self.duration==0:
			end_t=float('inf')
		else:
			end_t=start_t+self.duration

		while True:

			retval,frame=capture.read()
			time=round((frame_count+1)/self.fps,2)

			if time>=end_t or frame is None:
				break

			if time>=start_t:

				self.all_time.append(round((time-start_t),2))
				
				if (frame_count_analyze+1)%1000==0:
					print(str(frame_count_analyze+1)+' frames processed...')
					print(datetime.datetime.now())

				if self.framewidth is not None:
					frame=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)

				temp_frames.append(frame)

				(contours,centers,heights,inners,blobs)=contour_frame(frame,self.animal_number,background,background_low,background_high,self.delta,self.animal_area,animal_vs_bg=self.animal_vs_bg,include_bodyparts=self.include_bodyparts,animation_analyzer=False,channel=self.channel,kernel=self.kernel)

				if len(contours)==0:

					self.skipped_frames.append(frame_count_analyze)

					temp_contours.append(None)
					temp_inners.append(None)
					animation.append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))

				else:

					temp_contours.append(contours)
					temp_inners.append(inners)
					length=len(temp_frames)
					if length==1:
						self.register_counts[0]=frame_count_analyze
					self.animal_contours[0][frame_count_analyze]=contours

					(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,functools.reduce(operator.iconcat,temp_contours,[]))
					self.animal_centers[0][frame_count_analyze]=(x_lf+5,y_bt+10)

					pattern_image=generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,temp_contours,temp_inners,std=self.std)
					self.pattern_images[0][frame_count_analyze]=np.array(cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA))

					if self.animation_analyzer is True:
						for i,f in enumerate(temp_frames):
							if self.animal_contours[0][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1][n] is None:
								blob=np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')
							else:
								blob=extract_blob_all(f,y_bt,y_tp,x_lf,x_rt,contours=temp_contours[i],channel=self.channel,background_free=background_free)
							blob=cv2.resize(blob,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA)
							animation.append(img_to_array(blob))
							self.animations[0][frame_count_analyze]=np.array(animation)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		self.animations[0]=self.animations[0][:len(self.all_time)]
		self.pattern_images[0]=self.pattern_images[0][:len(self.all_time)]
		self.animal_contours[0]=self.animal_contours[0][:len(self.all_time)]
		self.animal_centers[0]=self.animal_centers[0][:len(self.all_time)]

		print('Information acquisition completed!')


	def craft_data(self):

		print('Crafting data...')
		print(datetime.datetime.now())

		lengths=[]
		length=len(self.all_time)
		to_delete=[]
		IDs=list(self.animal_centers.keys())

		for i in IDs:
			check=0
			for x in self.animal_heights[i]:
				if x is not None:
					check+=1
			lengths.append(check)
			if self.register_counts[i] is None:
				to_delete.append(i)

		if len(IDs)==len(to_delete):
			to_delete.remove(np.argsort(lengths)[-1])

		for i in IDs:
			if i in to_delete:
				del self.to_deregister[i]
				del self.register_counts[i]
				del self.animal_centers[i]
				del self.animal_existingcenters[i]
				del self.animal_contours[i]
				del self.animal_heights[i]
				if self.include_bodyparts is True:
					del self.animal_inners[i]
				if self.animation_analyzer is True:
					del self.animal_blobs[i]
					del self.animations[i]
				del self.pattern_images[i]

		for i in self.animal_centers:
			self.animal_centers[i]=self.animal_centers[i][:length]
			self.animal_contours[i]=self.animal_contours[i][:length]
			self.animal_heights[i]=self.animal_heights[i][:length]
			if self.animation_analyzer is True:
				self.animations[i]=self.animations[i][:length]
			self.pattern_images[i]=self.pattern_images[i][:length]

		print('Data crafting completed!')


	def categorize_behaviors(self,path_to_categorizer,uncertain=0):

		print('Categorizing behaviors...')
		print(datetime.datetime.now())

		IDs=list(self.pattern_images.keys())

		if self.animation_analyzer is True:
			animations=self.animations[IDs[0]]
		pattern_images=self.pattern_images[IDs[0]]

		if len(self.pattern_images)>1:
			for n in IDs[1:]:
				if self.animation_analyzer is True:
					animations+=self.animations[n]
				pattern_images+=self.pattern_images[n]

		del self.animations
		del self.pattern_images
		gc.collect()

		if self.animation_analyzer is True:
			inputs=[np.array(animations,dtype='float32')/255.0,np.array(pattern_images,dtype='float32')/255.0]
		else:
			inputs=np.array(pattern_images,dtype='float32')/255.0

		categorizer=load_model(path_to_categorizer)
		predictions=categorizer.predict(inputs,batch_size=32)

		for behavior_name in self.all_behavior_parameters:
			for i in IDs:
				self.all_behavior_parameters[behavior_name]['probability'][i]=[np.nan]*len(self.all_time)
				self.event_probability[i]=[['NA',-1]]*len(self.all_time)

		idx=0
		for n in IDs:
			i=self.length+self.register_counts[n]
			idx+=i
			while i<len(self.animal_contours[n]):
				if self.animal_contours[n][i] is not None:
					check=0
					for c in self.animal_contours[n][i-self.length+1:i+1]:
						if c is None:
							check+=1
					if check<=self.length/2:
						prediction=predictions[idx]
						behavior_names=list(self.all_behavior_parameters.keys())
						for behavior_name in behavior_names:
							if len(behavior_names)==2:
								if behavior_names.index(behavior_name)==0:
									probability=1-prediction[0]
								else:
									probability=prediction[0]
							else:
								probability=prediction[behavior_names.index(behavior_name)]
							self.all_behavior_parameters[behavior_name]['probability'][n][i]=probability
						if len(behavior_names)==2:
							if prediction[0]>0.5:
								if prediction[0]-(1-prediction[0])>uncertain:
									self.event_probability[n][i]=[behavior_names[1],prediction[0]]
							if prediction[0]<0.5:
								if (1-prediction[0])-prediction[0]>uncertain:
									self.event_probability[n][i]=[behavior_names[0],1-prediction[0]]
						else:
							if sorted(prediction)[-1]-sorted(prediction)[-2]>uncertain:
								self.event_probability[n][i]=[behavior_names[np.argmax(prediction)],max(prediction)]
				
				idx+=1
				i+=1

		del predictions
		gc.collect()

		print('Behavioral categorization completed!')


	def annotate_video(self,behavior_to_annotate=None,show_legend=True,interact_all=False):

		print('Annotating video...')
		print(datetime.datetime.now())

		text_scl=max(min(self.background.shape[0],self.background.shape[1])/960,0.5)
		text_tk=max(1,int(min(self.background.shape[0],self.background.shape[1])/960))

		if self.categorize_behavior is True:
			colors={}
			for behavior_name in self.all_behavior_parameters:
				if self.all_behavior_parameters[behavior_name]['color'][1][0]!='#':
					colors[behavior_name]=(255,255,255)
				else:
					hex_color=self.all_behavior_parameters[behavior_name]['color'][1].lstrip('#')
					color=tuple(int(hex_color[i:i+2],16) for i in (0,2,4))
					colors[behavior_name]=color[::-1]
			
			if len(behavior_to_annotate)!=len(self.all_behavior_parameters):
				for behavior_name in self.all_behavior_parameters:
					if behavior_name not in behavior_to_annotate:
						del colors[behavior_name]
			
			if show_legend is True:	
				scl=self.background.shape[0]/1024
				if 25*(len(colors)+1)<self.background.shape[0]:
					intvl=25
				else:
					intvl=int(self.background.shape[0]/(len(colors)+1))

		capture=cv2.VideoCapture(self.path_to_video)
		writer=None
		frame_count=frame_count_analyze=index=0

		start_t=round((self.t-self.length/self.fps),2)
		if start_t<0:
			start_t=0.00
		if self.duration==0:
			end_t=float('inf')
		else:
			end_t=start_t+self.duration

		while True:
			retval,frame=capture.read()
			time=round((frame_count+1)/self.fps,2)

			if time>=end_t or frame is None:
				break

			if time>=start_t:

				if self.framewidth is not None:
					frame=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)

				if self.categorize_behavior is True:
					if show_legend is True:
						n=1
						for i in colors:
							cv2.putText(frame,i,(10,intvl*n),cv2.FONT_HERSHEY_SIMPLEX,scl,colors[i],text_tk)
							n+=1

				if frame_count_analyze not in self.skipped_frames:

					for i in self.animal_contours:

						if frame_count_analyze<len(self.animal_contours[i]):

							if self.animal_contours[i][frame_count_analyze] is not None:

								cx=self.animal_centers[i][frame_count_analyze][0]
								cy=self.animal_centers[i][frame_count_analyze][1]

								if interact_all is False:
									cv2.putText(frame,str(i),(cx-10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
									cv2.circle(frame,(cx,cy),int(text_tk*3),(255,0,0),-1)

								if self.categorize_behavior is True:
									if self.event_probability[i][frame_count_analyze][0]=='NA':
										if interact_all is True:
											cv2.drawContours(frame,self.animal_contours[i][frame_count_analyze],-1,(255,255,255),1)
										else:
											cv2.drawContours(frame,[self.animal_contours[i][frame_count_analyze]],0,(255,255,255),1)
										cv2.putText(frame,'NA',(cx+10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
									else:
										name=self.event_probability[i][frame_count_analyze][0]
										probability=str(round(self.event_probability[i][frame_count_analyze][1]*100))+'%'
										if name in colors:
											color=colors[self.event_probability[i][frame_count_analyze][0]]
											if interact_all is True:
												cv2.drawContours(frame,self.animal_contours[i][frame_count_analyze],-1,color,1)
											else:
												cv2.drawContours(frame,[self.animal_contours[i][frame_count_analyze]],0,color,1)
											cv2.putText(frame,name+' '+probability,(cx+10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,color,text_tk)
										else:
											if interact_all is True:
												cv2.drawContours(frame,self.animal_contours[i][frame_count_analyze],-1,(255,255,255),1)
											else:
												cv2.drawContours(frame,[self.animal_contours[i][frame_count_analyze]],0,(255,255,255),1)
											cv2.putText(frame,'NA',(cx+10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
								else:
									cv2.drawContours(frame,[self.animal_contours[i][frame_count_analyze]],0,(255,255,255),1)

					index+=1

				if writer is None:
					(h,w)=frame.shape[:2]
					writer=cv2.VideoWriter(os.path.join(self.results_path,'Annotated video.avi'),cv2.VideoWriter_fourcc(*'MJPG'),self.fps,(w,h),True)

				writer.write(frame)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()
		writer.release()

		print('Video annotation completed!')


	def analyze_parameters(self,normalize_distance=True,parameter_to_analyze=[]):

		all_parameters=[]
		if '3 length parameters' in parameter_to_analyze:
			all_parameters+=['intensity_length','magnitude_length','vigor_length']
		if '3 areal parameters' in parameter_to_analyze:
			all_parameters+=['intensity_area','magnitude_area','vigor_area']
		if '4 locomotion parameters' in parameter_to_analyze:
			all_parameters+=['acceleration','speed','velocity']

		if self.categorize_behavior is True:

			for behavior_name in self.all_behavior_parameters:

				for i in self.event_probability:
					if 'count' in parameter_to_analyze:
						self.all_behavior_parameters[behavior_name]['count'][i]=0
					if 'duration' in parameter_to_analyze:
						self.all_behavior_parameters[behavior_name]['duration'][i]=0.0
					if '4 locomotion parameters' in parameter_to_analyze:
						self.all_behavior_parameters[behavior_name]['distance'][i]=0.0
					if 'latency' in parameter_to_analyze:
						self.all_behavior_parameters[behavior_name]['latency'][i]='NA'
			
				for parameter_name in all_parameters:
					for i in self.event_probability:
						self.all_behavior_parameters[behavior_name][parameter_name][i]=[np.nan]*len(self.all_time)

		else:

			for i in self.animal_contours:
				if '4 locomotion parameters' in parameter_to_analyze:
					self.all_behavior_parameters['distance'][i]=0.0
				for parameter_name in all_parameters:
					self.all_behavior_parameters[parameter_name][i]=[np.nan]*len(self.all_time)
				
		if len(parameter_to_analyze)>0:

			for i in self.animal_contours:

				n=self.length+self.register_counts[i]

				while n<len(self.animal_contours[i]):

					if self.categorize_behavior is True:

						behavior_name=self.event_probability[i][n][0]

						if behavior_name!='NA':

							if 'count' in parameter_to_analyze:
								if behavior_name!=self.event_probability[i][n-1][0]:
									self.all_behavior_parameters[behavior_name]['count'][i]+=1
									
							if 'duration' in parameter_to_analyze:
								self.all_behavior_parameters[behavior_name]['duration'][i]+=round(1/self.fps,2)

							if 'latency' in parameter_to_analyze:
								if self.all_behavior_parameters[behavior_name]['latency'][i]=='NA':
									self.all_behavior_parameters[behavior_name]['latency'][i]=self.all_time[n]

							if '3 length parameters' in parameter_to_analyze:
								heights_diffs=[]
								for h in self.animal_heights[i][n-self.length+1:n+1]:
									if h is None or self.animal_heights[i][n] is None:
										height_diff=0.0
									else:
										height_diff=abs(h-self.animal_heights[i][n])/h	
									heights_diffs.append(height_diff)
								magnitude_length=max(heights_diffs)
								vigor_length=magnitude_length/((self.length-np.argmax(heights_diffs))/self.fps)
								intensity_length=sum(heights_diffs)/(self.length/self.fps)
								if magnitude_length>0:
									self.all_behavior_parameters[behavior_name]['magnitude_length'][i][n]=magnitude_length
								if vigor_length>0:
									self.all_behavior_parameters[behavior_name]['vigor_length'][i][n]=vigor_length
								if intensity_length>0:
									self.all_behavior_parameters[behavior_name]['intensity_length'][i][n]=intensity_length

							if '4 locomotion parameters' in parameter_to_analyze:
								distance_traveled=0.0
								d=n-self.length
								while d<n-1:
									start_center=self.animal_centers[i][d]
									end_center=self.animal_centers[i][d+1]
									if start_center is None or end_center is None:
										dt=0.0
									else:
										dt=math.dist(end_center,start_center)
									distance_traveled+=dt
									d+=1
								if normalize_distance is True:
									calibrator=math.sqrt(self.animal_area)
									distance_traveled=distance_traveled/calibrator
								speed=distance_traveled/(self.length/self.fps)
								end_center=self.animal_centers[i][n]
								if end_center is not None:
									displacements=[]
									for ct in self.animal_centers[i][n-self.length+1:n+1]:
										if ct is None:
											displacements.append(0)
										else:
											displacements.append(math.dist(end_center,ct))		
									displacement=max(displacements)
									if normalize_distance is True:
										displacement=displacement/calibrator
									velocity=displacement/((self.length-np.argmax(displacements))/self.fps)
									self.all_behavior_parameters[behavior_name]['velocity'][i][n]=velocity
								velocities_max=[]
								velocities_min=[]
								for v in self.all_behavior_parameters[behavior_name]['velocity'][i][n-self.length+1:n+1]:
									if v!=np.nan:
										velocities_max.append(v)
										velocities_min.append(v)
									else:
										velocities_max.append(-float('inf'))
										velocities_min.append(float('inf'))
								vmax=max(velocities_max)
								vmin=min(velocities_min)
								if vmax!=-float('inf') and vmin!=float('inf'):
									if np.argmax(velocities_max)!=np.argmin(velocities_min):
										t=abs(np.argmax(velocities_max)-np.argmin(velocities_min))/self.fps
										self.all_behavior_parameters[behavior_name]['acceleration'][i][n]=(vmax-vmin)/t
								self.all_behavior_parameters[behavior_name]['distance'][i]+=distance_traveled
								self.all_behavior_parameters[behavior_name]['speed'][i][n]=speed

							if '3 areal parameters' in parameter_to_analyze:
								mask=np.zeros_like(self.background)
								contour=self.animal_contours[i][n]
								if contour is not None:
									cv2.drawContours(mask,[contour],0,(255,255,255),-1)
									mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
									area_diffs=[]
									for ct in self.animal_contours[i][n-self.length+1:n+1]:
										if ct is not None:
											prev_mask=np.zeros_like(self.background)
											cv2.drawContours(prev_mask,[ct],0,(255,255,255),-1)
											prev_mask=cv2.cvtColor(prev_mask,cv2.COLOR_BGR2GRAY)
											xlf1,ybt1,w,h=cv2.boundingRect(contour)
											xrt1=xlf1+w
											ytp1=ybt1+h
											xlf2,ybt2,w,h=cv2.boundingRect(ct)
											xrt2=xlf2+w
											ytp2=ybt2+h
											xlf=min(xlf1,xlf2)
											xrt=max(xrt1,xrt2)
											ybt=min(ybt1,ybt2)
											ytp=max(ytp1,ytp2)
											curr_mask=mask[ybt:ytp,xlf:xrt]
											prev_mask=prev_mask[ybt:ytp,xlf:xrt]
											diff=cv2.bitwise_xor(prev_mask,curr_mask)
											#diff[diff!=0]=255
											area_diff=(np.sum(diff)/255)/(np.sum(prev_mask)/255)
											area_diffs.append(area_diff)
									if len(area_diffs)>0:
										magnitude_area=max(area_diffs)
										vigor_area=magnitude_area/((self.length-np.argmax(area_diffs))/self.fps)
										intensity_area=sum(area_diffs)/(self.length/self.fps)
										if magnitude_area>0:
											self.all_behavior_parameters[behavior_name]['magnitude_area'][i][n]=magnitude_area
										if vigor_area>0:
											self.all_behavior_parameters[behavior_name]['vigor_area'][i][n]=vigor_area
										if intensity_area>0:
											self.all_behavior_parameters[behavior_name]['intensity_area'][i][n]=intensity_area

					else:

						if '3 length parameters' in parameter_to_analyze:
							heights_diffs=[]
							for h in self.animal_heights[i][n-self.length+1:n+1]:
								if h is None or self.animal_heights[i][n] is None:
									height_diff=0.0
								else:
									height_diff=abs(h-self.animal_heights[i][n])/h
								heights_diffs.append(height_diff)
							magnitude_length=max(heights_diffs)
							vigor_length=magnitude_length/((self.length-np.argmax(heights_diffs))/self.fps)
							intensity_length=sum(heights_diffs)/(self.length/self.fps)
							if magnitude_length>0:
								self.all_behavior_parameters['magnitude_length'][i][n]=magnitude_length
							if vigor_length>0:
								self.all_behavior_parameters['vigor_length'][i][n]=vigor_length
							if intensity_length>0:
								self.all_behavior_parameters['intensity_length'][i][n]=intensity_length

						if '4 locomotion parameters' in parameter_to_analyze:
							distance_traveled=0.0
							d=n-self.length
							while d<n-1:
								start_center=self.animal_centers[i][d]
								end_center=self.animal_centers[i][d+1]
								if start_center is None or end_center is None:
									dt=0.0
								else:
									dt=math.dist(end_center,start_center)
								distance_traveled+=dt
								d+=1
							if normalize_distance is True:
								calibrator=math.sqrt(self.animal_area)
								distance_traveled=distance_traveled/calibrator
							speed=distance_traveled/(self.length/self.fps)
							end_center=self.animal_centers[i][n]
							if end_center is not None:
								displacements=[]
								for ct in self.animal_centers[i][n-self.length+1:n+1]:
									if ct is None:
										displacements.append(0)
									else:
										displacements.append(math.dist(end_center,ct))
								displacement=max(displacements)
								if normalize_distance is True:
									displacement=displacement/calibrator
								velocity=displacement/((self.length-np.argmax(displacements))/self.fps)
								self.all_behavior_parameters['velocity'][i][n]=velocity
							velocities_max=[]
							velocities_min=[]
							for v in self.all_behavior_parameters['velocity'][i][n-self.length+1:n+1]:
								if v!=np.nan:
									velocities_max.append(v)
									velocities_min.append(v)
								else:
									velocities_max.append(-float('inf'))
									velocities_min.append(float('inf'))
							vmax=max(velocities_max)
							vmin=min(velocities_min)
							if vmax!=-float('inf') and vmin!=float('inf'):
								if np.argmax(velocities_max)!=np.argmin(velocities_min):
									t=abs(np.argmax(velocities_max)-np.argmin(velocities_min))/self.fps
									self.all_behavior_parameters['acceleration'][i][n]=(vmax-vmin)/t
							self.all_behavior_parameters['distance'][i]+=distance_traveled
							self.all_behavior_parameters['speed'][i][n]=speed

						if '3 areal parameters' in parameter_to_analyze:
							mask=np.zeros_like(self.background)
							contour=self.animal_contours[i][n]
							if contour is not None:
								cv2.drawContours(mask,[contour],0,(255,255,255),-1)
								mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
								area_diffs=[]
								for ct in self.animal_contours[i][n-self.length+1:n+1]:
									if ct is not None:
										prev_mask=np.zeros_like(self.background)
										cv2.drawContours(prev_mask,[ct],0,(255,255,255),-1)
										prev_mask=cv2.cvtColor(prev_mask,cv2.COLOR_BGR2GRAY)
										xlf1,ybt1,w,h=cv2.boundingRect(contour)
										xrt1=xlf1+w
										ytp1=ybt1+h
										xlf2,ybt2,w,h=cv2.boundingRect(ct)
										xrt2=xlf2+w
										ytp2=ybt2+h
										xlf=min(xlf1,xlf2)
										xrt=max(xrt1,xrt2)
										ybt=min(ybt1,ybt2)
										ytp=max(ytp1,ytp2)
										curr_mask=mask[ybt:ytp,xlf:xrt]
										prev_mask=prev_mask[ybt:ytp,xlf:xrt]
										diff=cv2.bitwise_xor(prev_mask,curr_mask)
										#diff[diff!=0]=255
										area_diff=(np.sum(diff)/255)/(np.sum(prev_mask)/255)
										area_diffs.append(area_diff)
								if len(area_diffs)>0:
									magnitude_area=max(area_diffs)
									vigor_area=magnitude_area/((self.length-np.argmax(area_diffs))/self.fps)
									intensity_area=sum(area_diffs)/(self.length/self.fps)
									if magnitude_area>0:
										self.all_behavior_parameters['magnitude_area'][i][n]=magnitude_area
									if vigor_area>0:
										self.all_behavior_parameters['vigor_area'][i][n]=vigor_area
									if intensity_area>0:
										self.all_behavior_parameters['intensity_area'][i][n]=intensity_area

					n+=1

				if self.categorize_behavior is True:
				
					if 'duration' in parameter_to_analyze:
						for behavior_name in self.all_behavior_parameters:
							if self.all_behavior_parameters[behavior_name]['duration'][i]!=0.0:
								self.all_behavior_parameters[behavior_name]['duration'][i]+=round(self.length/self.fps,2)
							else:
								self.all_behavior_parameters[behavior_name]['duration'][i]='NA'

					if '4 locomotion parameters' in parameter_to_analyze:
						for behavior_name in self.all_behavior_parameters:
							if self.all_behavior_parameters[behavior_name]['distance'][i]==0.0:
								self.all_behavior_parameters[behavior_name]['distance'][i]='NA'


	def export_results(self,normalize_distance=True,parameter_to_analyze=[]):

		print('Quantifying behaviors...')
		print(datetime.datetime.now())

		self.analyze_parameters(normalize_distance=normalize_distance,parameter_to_analyze=parameter_to_analyze)

		print('Behavioral quantification completed!')

		print('Exporting results...')
		print(datetime.datetime.now())

		if self.categorize_behavior is True:
			events_df=pd.DataFrame.from_dict(self.event_probability,orient='index',columns=self.all_time)
			if len(self.all_time)<16000:
				events_df.to_excel(os.path.join(self.results_path,'all_event_probability.xlsx'),float_format='%.2f')
			else:
				events_df.to_csv(os.path.join(self.results_path,'all_event_probability.csv'),float_format='%.2f')

		all_parameters=[]

		if self.categorize_behavior is True:
			all_parameters.append('probability')
			
		if 'count' in parameter_to_analyze:
			all_parameters.append('count')
		if 'duration' in parameter_to_analyze:
			all_parameters.append('duration')
		if 'latency' in parameter_to_analyze:
			all_parameters.append('latency')
		if '3 length parameters' in parameter_to_analyze:
			all_parameters+=['intensity_length','magnitude_length','vigor_length']
		if '3 areal parameters' in parameter_to_analyze:
			all_parameters+=['intensity_area','magnitude_area','vigor_area']
		if '4 locomotion parameters' in parameter_to_analyze:
			all_parameters+=['acceleration','distance','speed','velocity']

		if self.categorize_behavior is True:

			for behavior_name in self.all_behavior_parameters:
				os.makedirs(os.path.join(self.results_path,behavior_name),exist_ok=True)

				summary=[]

				for parameter_name in all_parameters:
					if parameter_name in ['count','duration','distance','latency']:
						summary.append(pd.DataFrame.from_dict(self.all_behavior_parameters[behavior_name][parameter_name],orient='index',columns=[parameter_name]).reset_index(drop=True))
					else:
						individual_df=pd.DataFrame.from_dict(self.all_behavior_parameters[behavior_name][parameter_name],orient='index',columns=self.all_time)
						if parameter_name!='probability':
							summary.append(individual_df.mean(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_mean'}))
							summary.append(individual_df.max(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_max'}))
							summary.append(individual_df.min(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_min'}))
						if len(self.all_time)<16000:
							individual_df.to_excel(os.path.join(self.results_path,behavior_name,parameter_name+'.xlsx'),float_format='%.2f')
						else:
							individual_df.to_csv(os.path.join(self.results_path,behavior_name,parameter_name+'.csv'),float_format='%.2f')

				if len(summary)>=1:
					pd.concat(summary,axis=1).to_excel(os.path.join(self.results_path,behavior_name,'all_summary.xlsx'),float_format='%.2f')

		else:

			summary=[]

			for parameter_name in all_parameters:
				if parameter_name=='distance':
					summary.append(pd.DataFrame.from_dict(self.all_behavior_parameters[parameter_name],orient='index',columns=['distance']).reset_index(drop=True))
				else:
					individual_df=pd.DataFrame.from_dict(self.all_behavior_parameters[parameter_name],orient='index',columns=self.all_time)

					summary.append(individual_df.mean(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_mean'}))
					summary.append(individual_df.max(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_max'}))
					summary.append(individual_df.min(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_min'}))

					if len(self.all_time)<16000:
						individual_df.to_excel(os.path.join(self.results_path,parameter_name+'.xlsx'),float_format='%.2f')
					else:
						individual_df.to_csv(os.path.join(self.results_path,parameter_name+'.csv'),float_format='%.2f')

			if len(summary)>=1:
				pd.concat(summary,axis=1).to_excel(os.path.join(self.results_path,'all_summary.xlsx'),float_format='%.2f')			

		print('All results exported in: '+str(self.results_path))


	def generate_data(self,background_free=True,skip_redundant=1):
		
		print('Generating behavior examples...')
		print(datetime.datetime.now())

		background=self.background
		background_low=self.background_low
		background_high=self.background_high
		if self.animal_vs_bg==1:
			background=np.uint8(255-background)
			background_low=np.uint8(255-background_low)
			background_high=np.uint8(255-background_high)

		capture=cv2.VideoCapture(self.path_to_video)
		frame_count=frame_count_analyze=0
		temp_frames=deque(maxlen=self.length)
		os.makedirs(os.path.join(self.results_path,'examples'),exist_ok=True)

		start_t=round((self.t-self.length/self.fps),2)
		if start_t<0:
			start_t=0.00
		if self.duration==0:
			end_t=float('inf')
		else:
			end_t=start_t+self.duration

		while True:

			retval,frame=capture.read()
			time=round((frame_count+1)/self.fps,2)

			if time>=end_t or frame is None:
				break

			if time>=start_t:

				if self.framewidth is not None:
					frame=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)

				temp_frames.append(frame)

				(contours,centers,heights,inners,blobs)=contour_frame(frame,self.animal_number,background,background_low,background_high,self.delta,self.animal_area,animal_vs_bg=self.animal_vs_bg,include_bodyparts=self.include_bodyparts,animation_analyzer=False,kernel=self.kernel)

				if len(contours)>0:

					self.track_animal(frame_count_analyze,contours,centers,heights,inners=inners,blobs=None)

					if frame_count_analyze>=self.length and frame_count_analyze%skip_redundant==0:

						for n in self.animal_centers:

							h=w=0
							animation=[]
							for i,f in enumerate(temp_frames):
								contour=self.animal_contours[n][frame_count_analyze-self.length+1:frame_count_analyze+1][i]
								if contour is None:
									blob=np.zeros_like(f)
								else:
									blob=extract_blob_background(f,self.animal_contours[n][frame_count_analyze-self.length+1:frame_count_analyze+1],contour=contour,channel=3,background_free=background_free)
									h,w=blob.shape[:2]
								animation.append(blob)

							if h>0:

								if self.include_bodyparts is True:
									animation_name=os.path.splitext(self.basename)[0]+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'.avi'
									pattern_image_name=os.path.splitext(self.basename)[0]+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'.jpg'
									pattern_image=generate_patternimage(self.background,self.animal_contours[n][frame_count_analyze-self.length+1:frame_count_analyze+1],inners=self.animal_inners[n],std=self.std)
								else:
									animation_name=os.path.splitext(self.basename)[0]+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'.avi'
									pattern_image_name=os.path.splitext(self.basename)[0]+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'.jpg'
									pattern_image=generate_patternimage(self.background,self.animal_contours[n][frame_count_analyze-self.length+1:frame_count_analyze+1],inners=None,std=0)

								path_animation=os.path.join(self.results_path,'examples',animation_name)
								path_pattern_image=os.path.join(self.results_path,'examples',pattern_image_name)

								writer=cv2.VideoWriter(path_animation,cv2.VideoWriter_fourcc(*'MJPG'),self.fps/5,(w,h),True)
								for blob in animation:
									writer.write(cv2.resize(blob,(w,h),interpolation=cv2.INTER_AREA))
								writer.release()

								cv2.imwrite(path_pattern_image,pattern_image)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		print('Behavior example generation completed!')


	def generate_data_interact_basic(self,background_free=True,skip_redundant=1):

		print('Generating behavior examples...')
		print(datetime.datetime.now())

		background=self.background
		background_low=self.background_low
		background_high=self.background_high
		if self.animal_vs_bg==1:
			background=np.uint8(255-background)
			background_low=np.uint8(255-background_low)
			background_high=np.uint8(255-background_high)

		capture=cv2.VideoCapture(self.path_to_video)
		frame_count=frame_count_analyze=0
		temp_frames=deque(maxlen=self.length)
		temp_contours=deque(maxlen=self.length)
		temp_inners=deque(maxlen=self.length)
		animation=deque(maxlen=self.length)
		os.makedirs(os.path.join(self.results_path,'examples'),exist_ok=True)
		
		start_t=round((self.t-self.length/self.fps),2)
		if start_t<0:
			start_t=0.00
		if self.duration==0:
			end_t=float('inf')
		else:
			end_t=start_t+self.duration

		while True:

			retval,frame=capture.read()
			time=round((frame_count+1)/self.fps,2)

			if time>=end_t or frame is None:
				break

			if time>=start_t:

				if self.framewidth is not None:
					frame=cv2.resize(frame,(self.framewidth,self.frameheight),interpolation=cv2.INTER_AREA)

				temp_frames.append(frame)

				(contours,centers,heights,inners,blobs)=contour_frame(frame,self.animal_number,background,background_low,background_high,self.delta,self.animal_area,animal_vs_bg=self.animal_vs_bg,include_bodyparts=self.include_bodyparts,animation_analyzer=False,kernel=self.kernel)

				if len(contours)==0:

					temp_contours.append(None)
					temp_inners.append(None)
					animation.append(np.zeros_like(self.background))

				else:

					temp_contours.append(contours)
					temp_inners.append(inners)

					if frame_count_analyze>=self.length and frame_count_analyze%skip_redundant==0:

						(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,functools.reduce(operator.iconcat,temp_contours,[]))

						h=w=0
						for i,f in enumerate(temp_frames):
							if temp_contours[i] is None:
								blob=np.zeros_like(f)
							else:
								blob=extract_blob_all(f,y_bt,y_tp,x_lf,x_rt,contours=temp_contours[i],channel=3,background_free=background_free)
								h,w=blob.shape[:2]
							animation.append(blob)

						if h>0:

							if self.include_bodyparts is True:
								animation_name=os.path.splitext(self.basename)[0]+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'_itbs.avi'
								pattern_image_name=os.path.splitext(self.basename)[0]+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'_itbs.jpg'
								pattern_image=generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,temp_contours,temp_inners,std=self.std)
							else:
								animation_name=os.path.splitext(self.basename)[0]+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_itbs.avi'
								pattern_image_name=os.path.splitext(self.basename)[0]+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_itbs.jpg'
								pattern_image=generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,temp_contours,temp_inners,std=0)

							path_animation=os.path.join(self.results_path,'examples',animation_name)
							path_pattern_image=os.path.join(self.results_path,'examples',pattern_image_name)
						
							writer=cv2.VideoWriter(path_animation,cv2.VideoWriter_fourcc(*'MJPG'),self.fps/5,(w,h),True)
							for blob in animation:
								writer.write(cv2.resize(blob,(w,h),interpolation=cv2.INTER_AREA))
							writer.release()

							cv2.imwrite(path_pattern_image,pattern_image)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		print('Behavior example generation completed!')


