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
import json
import torch
import datetime
import numpy as np
import math
from scipy.spatial import distance
from collections import deque
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import pandas as pd
import seaborn as sb
from skimage import exposure
import functools
import operator
try:
	from detectron2.config import get_cfg
	from detectron2.modeling import build_model
	from detectron2.checkpoint import DetectionCheckpointer
except:
	print('You need to install Detectron2 to use the Detector module in LabGym:')
	print('https://detectron2.readthedocs.io/en/latest/tutorials/install.html')



class AnalyzeAnimalDetector():

	def __init__(self):

		self.behavior_kind=0
		self.detector=None
		self.animal_mapping=None
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
		self.animal_number=None
		self.animal_kinds=None
		self.t=0
		self.duration=5
		self.length=None
		self.background=None
		self.skipped_frames=[]
		self.all_time=[]
		self.total_analysis_framecount=None
		self.animal_area={}
		self.to_deregister={}
		self.count_to_deregister=None
		self.register_counts={}
		self.animal_contours={}
		self.animal_other_contours={}
		self.animal_centers={}
		self.animal_existingcenters={}
		self.animal_heights={}
		self.animal_inners={}
		self.animal_other_inners={}
		self.animal_blobs={}
		self.animations={}
		self.pattern_images={}
		self.event_probability={}
		self.all_behavior_parameters={}
		self.animal_present={}
		self.temp_frames=None
		self.social_distance=0


	def prepare_analysis(self,
		path_to_detector,
		path_to_video,
		results_path,
		animal_number,
		animal_kinds, # the catgories of animals / objects to be analyzed
		behavior_kind, # 0: non-interactive; 1: interactive basic; 2: interactive advance
		names_and_colors=None, # the behavior names and their representing colors
		framewidth=None, # the width of the frame to resize
		dim_tconv=8, # input dim of Animation Analyzer
		dim_conv=8, # input dim of Pattern Recognizer
		channel=1, # color of Animation Analyzer
		include_bodyparts=False, # whether to include body parts in pattern images
		std=0, # for excluding static pixels in pattern images
		categorize_behavior=True, # whether to categorize behaviors or just track animals without behavioral categorization
		animation_analyzer=True, # whether to include Animation Analyzer
		t=0, # start time point
		duration=5, # the duration for example generation / analysis
		length=15, # the duration (number of frames) of a behavior example (a behavior episode)
		social_distance=0 # the distance to determine which two animals / objects form a interactive pair / group
		):
		
		print('Preparation started...')
		print(datetime.datetime.now())

		config=os.path.join(path_to_detector,'config.yaml')
		detector=os.path.join(path_to_detector,'model_final.pth')
		animalmapping=os.path.join(path_to_detector,'model_parameters.txt')
		with open(animalmapping) as f:
			model_parameters=f.read()
		self.animal_mapping=json.loads(model_parameters)['animal_mapping']
		animal_names=json.loads(model_parameters)['animal_names']
		dt_infersize=int(json.loads(model_parameters)['inferencing_framesize'])
		print('The total categories of animals / objects in this Detector: '+str(animal_names))
		print('The animals / objects of interest in this Detector: '+str(animal_kinds))
		print('The inferencing framesize of this Detector: '+str(dt_infersize))
		cfg=get_cfg()
		cfg.merge_from_file(config)
		cfg.MODEL.DEVICE='cuda' if torch.cuda.is_available() else 'cpu'
		self.detector=build_model(cfg)
		DetectionCheckpointer(self.detector).load(detector)
		self.detector.eval()

		self.path_to_video=path_to_video
		self.basename=os.path.basename(self.path_to_video)
		self.framewidth=framewidth
		self.results_path=os.path.join(results_path,os.path.splitext(self.basename)[0])
		self.animal_number=animal_number
		self.animal_kinds=animal_kinds
		self.behavior_kind=behavior_kind
		self.dim_tconv=dim_tconv
		self.dim_conv=dim_conv
		self.channel=channel
		self.include_bodyparts=include_bodyparts
		self.std=std
		self.categorize_behavior=categorize_behavior
		self.animation_analyzer=animation_analyzer
		self.t=t
		self.duration=duration
		self.length=length
		self.social_distance=social_distance
		if self.social_distance==0:
			self.social_distance=float('inf')
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
		self.temp_frames=deque(maxlen=self.length)
		framesize=min(self.background.shape[0],self.background.shape[1])

		total_number=0
		for animal_name in self.animal_kinds:
			total_number+=self.animal_number[animal_name]
			if self.categorize_behavior is True:
				self.event_probability[animal_name]={}
				self.all_behavior_parameters[animal_name]={}
				for behavior_name in names_and_colors:
					self.all_behavior_parameters[animal_name][behavior_name]={}
					self.all_behavior_parameters[animal_name][behavior_name]['color']=names_and_colors[behavior_name]
					for parameter_name in ['acceleration','count','distance','duration','intensity_area','intensity_length','latency','magnitude_area','magnitude_length','probability','speed','velocity','vigor_area','vigor_length']:
						self.all_behavior_parameters[animal_name][behavior_name][parameter_name]={}
			else:
				self.dim_conv=8
				self.animation_analyzer=False
				self.all_behavior_parameters[animal_name]={}
				for parameter_name in ['acceleration','distance','intensity_area','intensity_length','magnitude_area','magnitude_length','speed','velocity','vigor_area','vigor_length']:
					self.all_behavior_parameters[animal_name][parameter_name]={}
			self.animal_area[animal_name]=None
			self.to_deregister[animal_name]={}
			self.register_counts[animal_name]={}
			self.animal_contours[animal_name]={}
			if self.behavior_kind==2:
				self.animal_other_contours[animal_name]={}
			self.animal_centers[animal_name]={}
			self.animal_existingcenters[animal_name]={}
			self.animal_heights[animal_name]={}
			self.pattern_images[animal_name]={}
			if self.include_bodyparts is True:
				self.animal_inners[animal_name]={}
				if self.behavior_kind==2:
					self.animal_other_inners[animal_name]={}
			if self.animation_analyzer is True:
				self.animal_blobs[animal_name]={}
				self.animations[animal_name]={}
			for i in range(self.animal_number[animal_name]):
				self.to_deregister[animal_name][i]=0
				self.register_counts[animal_name][i]=None
				self.animal_contours[animal_name][i]=[None]*self.total_analysis_framecount
				if self.behavior_kind==2:
					self.animal_other_contours[animal_name][i]=deque(maxlen=self.length)
				self.animal_centers[animal_name][i]=[None]*self.total_analysis_framecount
				self.animal_existingcenters[animal_name][i]=(-10000,-10000)
				self.animal_heights[animal_name][i]=[None]*self.total_analysis_framecount
				if self.include_bodyparts is True:
					self.animal_inners[animal_name][i]=deque(maxlen=self.length)
					if self.behavior_kind==2:
						self.animal_other_inners[animal_name][i]=deque(maxlen=self.length)
				if self.animation_analyzer is True:
					self.animal_blobs[animal_name][i]=deque([np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')],maxlen=self.length)*self.length
					self.animations[animal_name][i]=[np.zeros((self.length,self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')]*self.total_analysis_framecount
				self.pattern_images[animal_name][i]=[np.zeros((self.dim_conv,self.dim_conv,3),dtype='uint8')]*self.total_analysis_framecount
			self.animal_present[animal_name]=0

		if framesize/total_number<250:
			self.kernel=3
		elif framesize/total_number<500:
			self.kernel=5
		elif framesize/total_number<1000:
			self.kernel=7
		elif framesize/total_number<1500:
			self.kernel=9
		else:
			self.kernel=11

		print('Prepration completed!')


	def track_animal(self,frame_count_analyze,animal_name,contours,centers,heights,inners=None,blobs=None):

		unused_existing_indices=list(self.animal_existingcenters[animal_name])
		existing_centers=list(self.animal_existingcenters[animal_name].values())
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
					if self.register_counts[animal_name][index_in_existing] is None:
						self.register_counts[animal_name][index_in_existing]=frame_count_analyze
					self.to_deregister[animal_name][index_in_existing]=0
					self.animal_contours[animal_name][index_in_existing][frame_count_analyze]=contours[index_in_new]
					center=centers[index_in_new]
					self.animal_centers[animal_name][index_in_existing][frame_count_analyze]=center
					self.animal_existingcenters[animal_name][index_in_existing]=center
					self.animal_heights[animal_name][index_in_existing][frame_count_analyze]=heights[index_in_new]
					if self.animation_analyzer is True:
						blob=img_to_array(cv2.resize(blobs[index_in_new],(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA))
						self.animal_blobs[animal_name][index_in_existing].append(blob)
						self.animations[animal_name][index_in_existing][frame_count_analyze]=np.array(self.animal_blobs[animal_name][index_in_existing])
					if self.include_bodyparts is True:
						self.animal_inners[animal_name][index_in_existing].append(inners[index_in_new])
						pattern_image=generate_patternimage(self.background,self.animal_contours[animal_name][index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],inners=self.animal_inners[animal_name][index_in_existing],std=self.std)
					else:
						pattern_image=generate_patternimage(self.background,self.animal_contours[animal_name][index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],inners=None,std=0)
					pattern_image=cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA)
					self.pattern_images[animal_name][index_in_existing][frame_count_analyze]=np.array(pattern_image)

		if len(unused_existing_indices)>0:
			for i in unused_existing_indices:
				if self.to_deregister[animal_name][i]<=self.count_to_deregister:
					self.to_deregister[animal_name][i]+=1
				else:
					self.animal_existingcenters[animal_name][i]=(-10000,-10000)
				if self.animation_analyzer is True:
					self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
				if self.include_bodyparts is True:
					self.animal_inners[animal_name][i].append(None)


	def track_animal_interact(self,frame_count_analyze,contours,other_contours,centers,heights,inners=None,other_inners=None,blobs=None):

		n=0

		for animal_name in self.animal_number:

			if self.animal_present[animal_name]>0:

				animal_length=n+self.animal_present[animal_name]
				animal_centers=centers[n:animal_length]
				animal_contours=contours[n:animal_length]
				animal_other_contours=other_contours[n:animal_length]
				animal_heights=heights[n:animal_length]
				if self.include_bodyparts is True:
					animal_inners=inners[n:animal_length]
					animal_other_inners=other_inners[n:animal_length]
				if self.animation_analyzer is True:
					animal_blobs=blobs[n:animal_length]

				unused_existing_indices=list(self.animal_existingcenters[animal_name])
				existing_centers=list(self.animal_existingcenters[animal_name].values())
				unused_new_indices=list(range(len(animal_centers)))
				dt_flattened=distance.cdist(existing_centers,animal_centers).flatten()
				dt_sort_index=dt_flattened.argsort()
				length=len(animal_centers)

				for idx in dt_sort_index:
					index_in_existing=int(idx/length)
					index_in_new=int(idx%length)
					if index_in_existing in unused_existing_indices:
						if index_in_new in unused_new_indices:
							unused_existing_indices.remove(index_in_existing)
							unused_new_indices.remove(index_in_new)
							if self.register_counts[animal_name][index_in_existing] is None:
								self.register_counts[animal_name][index_in_existing]=frame_count_analyze
							self.to_deregister[animal_name][index_in_existing]=0
							contour=animal_contours[index_in_new]
							self.animal_contours[animal_name][index_in_existing][frame_count_analyze]=contour
							center=animal_centers[index_in_new]
							self.animal_centers[animal_name][index_in_existing][frame_count_analyze]=center
							self.animal_existingcenters[animal_name][index_in_existing]=center
							self.animal_heights[animal_name][index_in_existing][frame_count_analyze]=animal_heights[index_in_new]
							self.animal_other_contours[animal_name][index_in_existing].append(animal_other_contours[index_in_new])
							if self.animation_analyzer is True:
								blob=img_to_array(cv2.resize(animal_blobs[index_in_new],(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA))
								self.animal_blobs[animal_name][index_in_existing].append(blob)
								self.animations[animal_name][index_in_existing][frame_count_analyze]=np.array(self.animal_blobs[animal_name][index_in_existing])
							if self.include_bodyparts is True:
								self.animal_inners[animal_name][index_in_existing].append(animal_inners[index_in_new])
								self.animal_other_inners[animal_name][index_in_existing].append(animal_other_inners[index_in_new])
								pattern_image=generate_patternimage_interact(self.background,self.animal_contours[animal_name][index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],self.animal_other_contours[animal_name][index_in_existing],inners=self.animal_inners[animal_name][index_in_existing],other_inners=self.animal_other_inners[animal_name][index_in_existing],std=self.std)
							else:
								pattern_image=generate_patternimage_interact(self.background,self.animal_contours[animal_name][index_in_existing][max(0,(frame_count_analyze-self.length+1)):frame_count_analyze+1],self.animal_other_contours[animal_name][index_in_existing],inners=None,other_inners=None,std=0)
							pattern_image=cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA)
							self.pattern_images[animal_name][index_in_existing][frame_count_analyze]=np.array(pattern_image)

				if len(unused_existing_indices)>0:
					for i in unused_existing_indices:
						if self.to_deregister[animal_name][i]<=self.count_to_deregister:
							self.to_deregister[animal_name][i]+=1
						else:
							self.animal_existingcenters[animal_name][i]=(-10000,-10000)
						self.animal_other_contours[animal_name][i].append([None])
						if self.animation_analyzer is True:
							self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
						if self.include_bodyparts is True:
							self.animal_inners[animal_name][i].append(None)
							self.animal_other_inners[animal_name][i].append([None])

				n+=self.animal_present[animal_name]


	def detect_track_individuals(self,frames,batch_size,frame_count_analyze,background_free=True,animation=None):

		tensor_frames=[torch.as_tensor(frame.astype("float32").transpose(2,0,1)) for frame in frames]
		inputs=[{"image":tensor_frame} for tensor_frame in tensor_frames]

		with torch.no_grad():
			outputs=self.detector(inputs)

		for batch_count,output in enumerate(outputs):

			frame=frames[batch_count]
			self.temp_frames.append(frame)
			instances=outputs[batch_count]['instances'].to('cpu')
			masks=instances.pred_masks.numpy().astype(np.uint8)
			classes=instances.pred_classes.numpy()
			scores=instances.scores.numpy()

			if len(masks)==0:

				self.skipped_frames.append(frame_count_analyze+1-batch_size+batch_count)

				for animal_name in self.animal_kinds:
					for i in self.animal_centers[animal_name]:
						if self.animation_analyzer is True:
							self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
						if self.include_bodyparts is True:
							self.animal_inners[animal_name][i].append(None)

			else:

				mask_area=np.sum(np.array(masks),axis=(1,2))
				exclusion_mask=np.zeros(len(masks),dtype=bool)
				exclusion_mask[np.where((np.sum(np.logical_and(masks[:,None],masks),axis=(2,3))/mask_area[:,None]>0.8) & (mask_area[:,None]<mask_area[None,:]))[0]]=True
				masks=[m for m,exclude in zip(masks,exclusion_mask) if not exclude]
				classes=[c for c,exclude in zip(classes,exclusion_mask) if not exclude]
				classes=[self.animal_mapping[str(x)] for x in classes]
				scores=[s for s,exclude in zip(scores,exclusion_mask) if not exclude]

				for animal_name in self.animal_kinds:

					contours=[]
					centers=[]
					goodcontours=[]
					goodmasks=[]
					heights=[]
					inners=[]
					blobs=[]

					animal_number=int(self.animal_number[animal_name])
					animal_masks=[masks[a] for a,name in enumerate(classes) if name==animal_name]
					animal_scores=[scores[a] for a,name in enumerate(classes) if name==animal_name]

					if len(animal_masks)==0:

						for i in self.animal_centers[animal_name]:
							if self.animation_analyzer is True:
								self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
							if self.include_bodyparts is True:
								self.animal_inners[animal_name][i].append(None)

					else:

						if len(animal_scores)>animal_number*2:
							sorted_scores_indices=np.argsort(animal_scores)[-int(animal_number*2):]
							animal_masks=[animal_masks[x] for x in sorted_scores_indices]
						for mask in animal_masks:
							mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((self.kernel,self.kernel),np.uint8))
							goodmasks.append(mask)
							cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
							goodcontours.append(sorted(cnts,key=cv2.contourArea,reverse=True)[0])
						areas=[cv2.contourArea(ct) for ct in goodcontours]
						sorted_area_indices=np.argsort(np.array(areas))[-animal_number:]
						areas_sorted=sorted(areas)[-animal_number:]
						area=sum(areas_sorted)/len(areas_sorted)
						if self.animal_area[animal_name] is None:
							self.animal_area[animal_name]=area
						else:
							self.animal_area[animal_name]=(self.animal_area[animal_name]+area)/2
						for x in sorted_area_indices:
							mask=goodmasks[x]
							cnt=goodcontours[x]
							contours.append(cnt)
							centers.append((int(cv2.moments(cnt)['m10']/cv2.moments(cnt)['m00']),int(cv2.moments(cnt)['m01']/cv2.moments(cnt)['m00'])))  
							(_,_),(w,h),_=cv2.minAreaRect(cnt)
							heights.append(max(w,h))
							if self.include_bodyparts is True:
								masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
								inners.append(get_inner(masked_frame,cnt))
							if self.animation_analyzer is True:
								masked_frame=frame*cv2.cvtColor(mask,cv2.COLOR_GRAY2BGR)
								x,y,w,h=cv2.boundingRect(cnt)
								difference=int(abs(w-h)/2)+1
								if w>h:
									y_bt=max(y-difference-1,0)
									y_tp=min(y+h+difference+1,self.background.shape[0])
									x_lf=max(x-1,0)
									x_rt=min(x+w+1,self.background.shape[1])
								else:
									y_bt=max(y-1,0)
									y_tp=min(y+h+1,self.background.shape[0])
									x_lf=max(x-difference-1,0)
									x_rt=min(x+w+difference+1,self.background.shape[1])
								blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
								blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
								if self.channel==1:
									blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
									blob=img_to_array(blob)
								blobs.append(blob)

						self.track_animal(frame_count_analyze+1-batch_size+batch_count,animal_name,contours,centers,heights,inners=inners,blobs=blobs)
						
						if self.animation_analyzer is True:
							if background_free is False:
								for i in self.animal_centers[animal_name]:
									for n,f in enumerate(self.temp_frames):
										if self.animal_contours[animal_name][i][max(0,frame_count_analyze+1-batch_size+batch_count-self.length+1):frame_count_analyze+1-batch_size+batch_count+1][n] is None:
											blob=np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')
										else:
											blob=extract_blob_background(f,self.animal_contours[animal_name][i][max(0,frame_count_analyze+1-batch_size+batch_count-self.length+1):frame_count_analyze+1-batch_size+batch_count+1],contour=None,channel=self.channel,background_free=False)
											blob=cv2.resize(blob,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA)
										animation.append(img_to_array(blob))
									self.animations[animal_name][i][frame_count_analyze+1-batch_size+batch_count]=np.array(animation)


	def detect_track_interact(self,frames,batch_size,frame_count_analyze,background_free=True):

		tensor_frames=[torch.as_tensor(frame.astype("float32").transpose(2,0,1)) for frame in frames]
		inputs=[{"image":tensor_frame} for tensor_frame in tensor_frames]

		with torch.no_grad():
			outputs=self.detector(inputs)

		for batch_count,output in enumerate(outputs):

			frame=frames[batch_count]
			instances=outputs[batch_count]['instances'].to('cpu')
			masks=instances.pred_masks.numpy().astype(np.uint8)
			classes=instances.pred_classes.numpy()
			scores=instances.scores.numpy()

			if len(masks)==0:

				self.skipped_frames.append(frame_count_analyze+1-batch_size+batch_count)

				for animal_name in self.animal_kinds:
					self.animal_present[animal_name]=0
					for i in self.animal_centers[animal_name]:
						self.animal_other_contours[animal_name][i].append([None])
						if self.animation_analyzer is True:
							self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
						if self.include_bodyparts is True:
							self.animal_inners[animal_name][i].append(None)
							self.animal_other_inners[animal_name][i].append([None])

			else:

				mask_area=np.sum(np.array(masks),axis=(1,2))
				exclusion_mask=np.zeros(len(masks),dtype=bool)
				exclusion_mask[np.where((np.sum(np.logical_and(masks[:,None],masks),axis=(2,3))/mask_area[:,None]>0.8) & (mask_area[:,None]<mask_area[None,:]))[0]]=True
				masks=[m for m,exclude in zip(masks,exclusion_mask) if not exclude]
				classes=[c for c,exclude in zip(classes,exclusion_mask) if not exclude]
				classes=[self.animal_mapping[str(x)] for x in classes]
				scores=[s for s,exclude in zip(scores,exclusion_mask) if not exclude]

				all_centers=[]
				all_masks=[]
				all_contours=[]
				all_inners=[]
				all_heights=[]
				all_blobs=[]
				average_area=[]

				for animal_name in self.animal_kinds:

					goodmasks=[]
					goodcontours=[]
					animal_number=int(self.animal_number[animal_name])
					animal_masks=[masks[a] for a,name in enumerate(classes) if name==animal_name]
					animal_scores=[scores[a] for a,name in enumerate(classes) if name==animal_name]

					if len(animal_masks)==0:
						self.animal_present[animal_name]=0
						for i in self.animal_centers[animal_name]:
							self.animal_other_contours[animal_name][i].append([None])
							if self.animation_analyzer is True:
								self.animal_blobs[animal_name][i].append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))
							if self.include_bodyparts is True:
								self.animal_inners[animal_name][i].append(None)
								self.animal_other_inners[animal_name][i].append([None])
					else:
						if len(animal_scores)>animal_number*2:
							sorted_scores_indices=np.argsort(animal_scores)[-int(animal_number*2):]
							animal_masks=[animal_masks[x] for x in sorted_scores_indices]
						for mask in animal_masks:
							mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((self.kernel,self.kernel),np.uint8))
							goodmasks.append(mask)
							cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
							goodcontours.append(sorted(cnts,key=cv2.contourArea,reverse=True)[0])
						areas=[cv2.contourArea(ct) for ct in goodcontours]
						sorted_area_indices=np.argsort(np.array(areas))[-animal_number:]
						self.animal_present[animal_name]=len(sorted_area_indices)
						areas_sorted=sorted(areas)[-animal_number:]
						area=sum(areas_sorted)/len(areas_sorted)
						if self.animal_area[animal_name] is None:
							self.animal_area[animal_name]=area
						else:
							self.animal_area[animal_name]=(self.animal_area[animal_name]+area)/2
						average_area.append(self.animal_area[animal_name])
						for x in sorted_area_indices:
							mask=goodmasks[x]
							all_masks.append(mask)
							cnt=goodcontours[x]
							all_contours.append(cnt)
							all_centers.append((int(cv2.moments(cnt)['m10']/cv2.moments(cnt)['m00']),int(cv2.moments(cnt)['m01']/cv2.moments(cnt)['m00'])))  
							(_,_),(w,h),_=cv2.minAreaRect(cnt)
							all_heights.append(max(w,h))
							if self.include_bodyparts is True:
								masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
								all_inners.append(get_inner(masked_frame,cnt))

				if len(all_centers)>1:

					centers_array=np.array(all_centers)
					distances_squared=np.sum((centers_array[:,None]-centers_array)**2,axis=2)
					determine=np.logical_and(distances_squared>0,distances_squared<(math.sqrt(sum(average_area)/len(average_area))*self.social_distance)**2)
					other_contours=[[all_contours[x] for x,determ in enumerate(determine[y]) if determ] for y,c in enumerate(all_centers)]
					if self.include_bodyparts is True:
						other_inners=[[all_inners[x] for x,determ in enumerate(determine[y]) if determ] for y,c in enumerate(all_centers)]
					else:
						other_inners=None
					if self.animation_analyzer is True:
						other_masks=[np.bitwise_or.reduce(np.stack(np.array(all_masks)[determine[x]])) if len(c)>0 else None for x,c in enumerate(other_contours)]
						for i,other_mask in enumerate(other_masks):
							contour=all_contours[i]
							total_contours=other_contours[i]
							total_contours.append(contour)
							(y_bt,y_tp,x_lf,x_rt)=crop_frame(self.background,total_contours)
							if background_free is True:
								blob=frame*cv2.cvtColor(all_masks[i],cv2.COLOR_GRAY2BGR)
								if other_mask is not None:
									other_blob=cv2.cvtColor(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*other_mask,cv2.COLOR_GRAY2BGR)
									blob=cv2.add(blob,other_blob)
									blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
							else:
								blob=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
							cv2.drawContours(blob,[contour],0,(255,0,255),2)
							all_blobs.append(blob[y_bt:y_tp,x_lf:x_rt])

					self.track_animal_interact(frame_count_analyze+1-batch_size+batch_count,all_contours,other_contours,all_centers,all_heights,inners=all_inners,other_inners=other_inners,blobs=all_blobs)

				else:

					if len(all_centers)>0:
						other_contours=[[None]]
						if self.include_bodyparts is True:
							other_inners=[[None]]
						else:
							other_inners=None
						if background_free is True:
							blob=frame*cv2.cvtColor(all_masks[0],cv2.COLOR_GRAY2BGR)
							blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
						else:
							blob=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
						contour=all_contours[0]
						cv2.drawContours(blob,[contour],0,(255,0,255),2)
						x,y,w,h=cv2.boundingRect(contour)
						difference=int(abs(w-h)/2)+1
						if w>h:
							y_bt=max(y-difference-1,0)
							y_tp=min(y+h+difference+1,self.background.shape[0])
							x_lf=max(x-1,0)
							x_rt=min(x+w+1,self.background.shape[1])
						else:
							y_bt=max(y-1,0)
							y_tp=min(y+h+1,self.background.shape[0])
							x_lf=max(x-difference-1,0)
							x_rt=min(x+w+difference+1,self.background.shape[1])
						blob=blob[y_bt:y_tp,x_lf:x_rt]
						all_blobs.append(blob)

						self.track_animal_interact(frame_count_analyze+1-batch_size+batch_count,all_contours,other_contours,all_centers,all_heights,inners=all_inners,other_inners=other_inners,blobs=all_blobs)


	def acquire_information(self,batch_size=1,background_free=True):

		print('Acquiring information in each frame...')
		print(datetime.datetime.now())

		capture=cv2.VideoCapture(self.path_to_video)
		batch=[]
		batch_count=frame_count=frame_count_analyze=0
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

				batch.append(frame)
				batch_count+=1

				if batch_count==batch_size:
					batch_count=0
					if self.behavior_kind==2:
						self.detect_track_interact(batch,batch_size,frame_count_analyze,background_free=background_free)
					else:
						self.detect_track_individuals(batch,batch_size,frame_count_analyze,background_free=background_free,animation=animation)
					batch=[]

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		for animal_name in self.animal_kinds:
			print('The area of '+str(animal_name)+' is: '+str(self.animal_area[animal_name])+'.')

		print('Information acquisition completed!')


	def acquire_information_interact_basic(self,batch_size=1,background_free=True):

		print('Acquiring information in each frame...')
		print(datetime.datetime.now())

		name=self.animal_kinds[0]
		self.register_counts={}
		self.register_counts[name]=None
		if self.animation_analyzer is True:
			self.animations={}
			self.animations[name]={}
			self.animations[name][0]=[np.zeros((self.length,self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')]*self.total_analysis_framecount
		self.pattern_images={}
		self.pattern_images[name]={}
		self.pattern_images[name][0]=[np.zeros((self.dim_conv,self.dim_conv,3),dtype='uint8')]*self.total_analysis_framecount
		self.animal_contours={}
		self.animal_contours[name]={}
		self.animal_contours[name][0]=[None]*self.total_analysis_framecount
		self.animal_centers[name]={}
		self.animal_centers[name][0]=[None]*self.total_analysis_framecount

		capture=cv2.VideoCapture(self.path_to_video)
		batch=[]
		batch_count=frame_count=frame_count_analyze=0
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

				batch.append(frame)
				batch_count+=1

				if batch_count==batch_size:

					batch_count=0

					tensor_frames=[torch.as_tensor(frame.astype("float32").transpose(2,0,1)) for frame in batch]
					inputs=[{"image":tensor_frame} for tensor_frame in tensor_frames]

					with torch.no_grad():
						outputs=self.detector(inputs)

					for batch_count,output in enumerate(outputs):

						frame=batch[batch_count]
						self.temp_frames.append(frame)
						instances=outputs[batch_count]['instances'].to('cpu')
						masks=instances.pred_masks.numpy().astype(np.uint8)
						classes=instances.pred_classes.numpy()
						scores=instances.scores.numpy()

						if len(masks)==0:

							self.skipped_frames.append(frame_count_analyze+1-batch_size+batch_count)

							temp_contours.append(None)
							temp_inners.append(None)
							animation.append(np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8'))

						else:

							self.register_counts[name][0]=frame_count_analyze+1-batch_size+batch_count

							mask_area=np.sum(np.array(masks),axis=(1,2))
							exclusion_mask=np.zeros(len(masks),dtype=bool)
							exclusion_mask[np.where((np.sum(np.logical_and(masks[:,None],masks),axis=(2,3))/mask_area[:,None]>0.8) & (mask_area[:,None]<mask_area[None,:]))[0]]=True
							masks=[m for m,exclude in zip(masks,exclusion_mask) if not exclude]
							classes=[c for c,exclude in zip(classes,exclusion_mask) if not exclude]
							classes=[self.animal_mapping[str(x)] for x in classes]
							scores=[s for s,exclude in zip(scores,exclusion_mask) if not exclude]

							contours=[]
							inners=[]

							for animal_name in self.animal_kinds:
								goodcontours=[]
								goodmasks=[]
								animal_number=int(self.animal_number[animal_name])
								animal_masks=[masks[a] for a,n in enumerate(classes) if n==animal_name]
								animal_scores=[scores[a] for a,n in enumerate(classes) if n==animal_name]
								if len(animal_masks)>0:
									if len(animal_scores)>animal_number*2:
										sorted_scores_indices=np.argsort(animal_scores)[-int(animal_number*2):]
										animal_masks=[animal_masks[x] for x in sorted_scores_indices]
									for mask in animal_masks:
										mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((self.kernel,self.kernel),np.uint8))
										cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
										goodcontours.append(sorted(cnts,key=cv2.contourArea,reverse=True)[0])
										goodmasks.append(mask)
									areas=[cv2.contourArea(ct) for ct in goodcontours]
									sorted_area_indices=np.argsort(np.array(areas))[-animal_number:]
									for x in sorted_area_indices:
										cnt=goodcontours[x]
										mask=goodmasks[x]
										contours.append(cnt)
										if self.include_bodyparts is True:
											masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
											inners.append(get_inner(masked_frame,cnt))

							self.animal_contours[name][0][frame_count_analyze+1-batch_size+batch_count]=contours

							temp_contours.append(contours)
							temp_inners.append(inners)
							(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,functools.reduce(operator.iconcat,temp_contours,[]))

							self.animal_centers[name][0][frame_count_analyze+1-batch_size+batch_count]=(x_lf+20,y_bt+10)

							pattern_image=generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,temp_contours,temp_inners,std=self.std)
							self.pattern_images[name][0][frame_count_analyze+1-batch_size+batch_count]=np.array(cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA))
							if self.animation_analyzer is True:
								for i,f in enumerate(self.temp_frames):
									if self.animal_contours[name][0][max(0,frame_count_analyze+1-batch_size+batch_count-self.length+1):frame_count_analyze+1-batch_size+batch_count+1][i] is None:
										blob=np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')
									else:
										blob=extract_blob_all(f,y_bt,y_tp,x_lf,x_rt,contours=temp_contours[i],channel=self.channel,background_free=background_free)
										blob=cv2.resize(blob,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA)
									animation.append(img_to_array(blob))
									self.animations[name][0][frame_count_analyze+1-batch_size+batch_count]=np.array(animation)
					
					batch=[]

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		length=len(self.all_time)
		self.animations[name][0]=self.animations[name][0][:length]
		self.pattern_images[name][0]=self.pattern_images[name][0][:length]
		self.animal_contours[name][0]=self.animal_contours[name][0][:length]
		self.animal_centers[name][0]=self.animal_centers[name][0][:length]
		
		print('Information acquisition completed!')


	def craft_data(self):

		print('Crafting data...')
		print(datetime.datetime.now())

		for animal_name in self.animal_kinds:

			lengths=[]
			length=len(self.all_time)
			to_delete=[]
			IDs=list(self.animal_centers[animal_name].keys())

			for i in IDs:
				check=0
				for x in self.animal_heights[animal_name][i]:
					if x is not None:
						check+=1
				lengths.append(check)
				if self.register_counts[animal_name][i] is None:
					to_delete.append(i)

			if len(IDs)==len(to_delete):
				to_delete.remove(np.argsort(lengths)[-1])
			
			for i in IDs:
				if i in to_delete:
					del self.to_deregister[animal_name][i]
					del self.register_counts[animal_name][i]
					del self.animal_centers[animal_name][i]
					del self.animal_existingcenters[animal_name][i]
					del self.animal_contours[animal_name][i]
					if self.behavior_kind==2:
						del self.animal_other_contours[animal_name][i]
					del self.animal_heights[animal_name][i]
					if self.include_bodyparts is True:
						del self.animal_inners[animal_name][i]
						if self.behavior_kind==2:
							del self.animal_other_inners[animal_name][i]
					if self.animation_analyzer is True:
						del self.animal_blobs[animal_name][i]
						del self.animations[animal_name][i]
					del self.pattern_images[animal_name][i]

			for i in self.animal_centers[animal_name]:
				self.animal_centers[animal_name][i]=self.animal_centers[animal_name][i][:length]
				self.animal_contours[animal_name][i]=self.animal_contours[animal_name][i][:length]
				self.animal_heights[animal_name][i]=self.animal_heights[animal_name][i][:length]
				if self.animation_analyzer is True:
					self.animations[animal_name][i]=self.animations[animal_name][i][:length]
				self.pattern_images[animal_name][i]=self.pattern_images[animal_name][i][:length]

		print('Data crafting completed!')


	def categorize_behaviors(self,path_to_categorizer,uncertain=0):

		print('Categorizing behaviors...')
		print(datetime.datetime.now())

		categorizer=load_model(path_to_categorizer)

		if self.behavior_kind==1:
			self.animal_kinds=[self.animal_kinds[0]]

		for animal_name in self.animal_kinds:

			IDs=list(self.pattern_images[animal_name].keys())

			if self.animation_analyzer is True:
				animations=self.animations[animal_name][IDs[0]]
			pattern_images=self.pattern_images[animal_name][IDs[0]]

			if len(self.pattern_images[animal_name])>1:
				for n in IDs[1:]:
					if self.animation_analyzer is True:
						animations+=self.animations[animal_name][n]
					pattern_images+=self.pattern_images[animal_name][n]

			del self.animations[animal_name]
			del self.pattern_images[animal_name]
			gc.collect()

			if self.animation_analyzer is True:
				inputs=[np.array(animations,dtype='float32')/255.0,np.array(pattern_images,dtype='float32')/255.0]
			else:
				inputs=np.array(pattern_images,dtype='float32')/255.0

			predictions=categorizer.predict(inputs,batch_size=32)

			for behavior_name in self.all_behavior_parameters[animal_name]:
				for i in IDs:
					self.all_behavior_parameters[animal_name][behavior_name]['probability'][i]=[np.nan]*len(self.all_time)
					self.event_probability[animal_name][i]=[['NA',-1]]*len(self.all_time)

			idx=0
			for n in IDs:
				i=self.length+self.register_counts[animal_name][n]
				idx+=i
				while i<len(self.animal_contours[animal_name][n]):
					if self.animal_contours[animal_name][n][i] is not None:
						check=0
						for c in self.animal_contours[animal_name][n][i-self.length+1:i+1]:
							if c is None:
								check+=1
						if check<=self.length/2:
							prediction=predictions[idx]
							behavior_names=list(self.all_behavior_parameters[animal_name].keys())
							for name_index,behavior_name in enumerate(behavior_names):
								if len(behavior_names)==2:
									if name_index==0:
										probability=1-prediction[0]
									else:
										probability=prediction[0]
								else:
									probability=prediction[name_index]
								self.all_behavior_parameters[animal_name][behavior_name]['probability'][n][i]=probability
							if len(behavior_names)==2:
								if prediction[0]>0.5:
									if prediction[0]-(1-prediction[0])>uncertain:
										self.event_probability[animal_name][n][i]=[behavior_names[1],prediction[0]]
								if prediction[0]<0.5:
									if (1-prediction[0])-prediction[0]>uncertain:
										self.event_probability[animal_name][n][i]=[behavior_names[0],1-prediction[0]]
							else:
								if sorted(prediction)[-1]-sorted(prediction)[-2]>uncertain:
									self.event_probability[animal_name][n][i]=[behavior_names[np.argmax(prediction)],max(prediction)]

					idx+=1
					i+=1

			del predictions
			gc.collect()

		print('Behavioral categorization completed!')


	def correct_identity(self,specific_behaviors):

		print('Initiating behavior-guided identity correction...')
		print(datetime.datetime.now())

		for animal_name in self.animal_kinds:

			for i in self.animal_centers[animal_name]:
				for idx,x in enumerate(self.animal_contours[animal_name][i]):
					if idx>=self.length-1 and x is not None:
						behavior_name=self.event_probability[animal_name][i][idx][0]
						if behavior_name in specific_behaviors[animal_name]:
							if specific_behaviors[animal_name][behavior_name] is None:
								specific_behaviors[animal_name][behavior_name]=i
							else:
								ID=specific_behaviors[animal_name][behavior_name]
								if ID!=i:
									temp=self.register_counts[animal_name][ID]
									self.register_counts[animal_name][ID]=self.register_counts[animal_name][i]
									self.register_counts[animal_name][i]=temp
									temp=self.animal_centers[animal_name][ID][idx]
									self.animal_centers[animal_name][ID][idx]=self.animal_centers[animal_name][i][idx]
									self.animal_centers[animal_name][i][idx]=temp
									temp=self.animal_contours[animal_name][ID][idx]
									self.animal_contours[animal_name][ID][idx]=self.animal_contours[animal_name][i][idx]
									self.animal_contours[animal_name][i][idx]=temp
									temp=self.animal_heights[animal_name][ID][idx]
									self.animal_heights[animal_name][ID][idx]=self.animal_heights[animal_name][i][idx]
									self.animal_heights[animal_name][i][idx]=temp
									temp=self.event_probability[animal_name][ID][idx]
									self.event_probability[animal_name][ID][idx]=self.event_probability[animal_name][i][idx]
									self.event_probability[animal_name][i][idx]=temp
									temp=self.all_behavior_parameters[animal_name][behavior_name]['probability'][ID][idx]
									self.all_behavior_parameters[animal_name][behavior_name]['probability'][ID][idx]=self.all_behavior_parameters[animal_name][behavior_name]['probability'][i][idx]
									self.all_behavior_parameters[animal_name][behavior_name]['probability'][i][idx]=temp

		print('Identity correction completed!')


	def annotate_video(self,behavior_to_annotate=None,show_legend=True):

		print('Annotating video...')
		print(datetime.datetime.now())

		text_scl=max(min(self.background.shape[0],self.background.shape[1])/960,0.5)
		text_tk=max(1,int(min(self.background.shape[0],self.background.shape[1])/960))

		if self.categorize_behavior is True:
			colors={}
			for behavior_name in self.all_behavior_parameters[self.animal_kinds[0]]:
				if self.all_behavior_parameters[self.animal_kinds[0]][behavior_name]['color'][1][0]!='#':
					colors[behavior_name]=(255,255,255)
				else:
					hex_color=self.all_behavior_parameters[self.animal_kinds[0]][behavior_name]['color'][1].lstrip('#')
					color=tuple(int(hex_color[i:i+2],16) for i in (0,2,4))
					colors[behavior_name]=color[::-1]
			
			if len(behavior_to_annotate)!=len(self.all_behavior_parameters[self.animal_kinds[0]]):
				for behavior_name in self.all_behavior_parameters[self.animal_kinds[0]]:
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
		frame_count=frame_count_analyze=0

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

					for animal_name in self.animal_kinds:

						for i in self.animal_contours[animal_name]:

							if frame_count_analyze<len(self.animal_contours[animal_name][i]):

								if self.animal_contours[animal_name][i][frame_count_analyze] is not None:

									cx=self.animal_centers[animal_name][i][frame_count_analyze][0]
									cy=self.animal_centers[animal_name][i][frame_count_analyze][1]

									if self.behavior_kind!=1:
										cv2.circle(frame,(cx,cy),int(text_tk*3),(255,0,0),-1)

									if self.categorize_behavior is True:
										if self.behavior_kind!=1:
											cv2.putText(frame,animal_name+' '+str(i),(cx-10,cy-25),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)	
										if self.event_probability[animal_name][i][frame_count_analyze][0]=='NA':
											if self.behavior_kind==1:
												cv2.drawContours(frame,self.animal_contours[animal_name][i][frame_count_analyze],-1,(255,255,255),1)
											else:
												cv2.drawContours(frame,[self.animal_contours[animal_name][i][frame_count_analyze]],0,(255,255,255),1)
											cv2.putText(frame,'NA',(cx-10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
										else:
											name=self.event_probability[animal_name][i][frame_count_analyze][0]
											probability=str(round(self.event_probability[animal_name][i][frame_count_analyze][1]*100))+'%'
											if name in colors:
												color=colors[self.event_probability[animal_name][i][frame_count_analyze][0]]
												if self.behavior_kind==1:
													cv2.drawContours(frame,self.animal_contours[animal_name][i][frame_count_analyze],-1,color,1)
												else:
													cv2.drawContours(frame,[self.animal_contours[animal_name][i][frame_count_analyze]],0,color,1)
												cv2.putText(frame,name+' '+probability,(cx-10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,color,text_tk)
											else:
												if self.behavior_kind==1:
													cv2.drawContours(frame,self.animal_contours[animal_name][i][frame_count_analyze],-1,(255,255,255),1)
												else:
													cv2.drawContours(frame,[self.animal_contours[animal_name][i][frame_count_analyze]],0,(255,255,255),1)
												cv2.putText(frame,'NA',(cx-10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
									else:
										cv2.putText(frame,animal_name+' '+str(i),(cx-10,cy-10),cv2.FONT_HERSHEY_SIMPLEX,text_scl,(255,255,255),text_tk)
										cv2.drawContours(frame,[self.animal_contours[animal_name][i][frame_count_analyze]],0,(255,255,255),1)

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
			for animal_name in self.animal_kinds:
				for behavior_name in self.all_behavior_parameters[animal_name]:
					for i in self.event_probability[animal_name]:
						if 'count' in parameter_to_analyze:
							self.all_behavior_parameters[animal_name][behavior_name]['count'][i]=0
						if 'duration' in parameter_to_analyze:
							self.all_behavior_parameters[animal_name][behavior_name]['duration'][i]=0.0
						if '4 locomotion parameters' in parameter_to_analyze:
							self.all_behavior_parameters[animal_name][behavior_name]['distance'][i]=0.0
						if 'latency' in parameter_to_analyze:
							self.all_behavior_parameters[animal_name][behavior_name]['latency'][i]='NA'
					for parameter_name in all_parameters:
						for i in self.event_probability[animal_name]:
							self.all_behavior_parameters[animal_name][behavior_name][parameter_name][i]=[np.nan]*len(self.all_time)
		else:
			for animal_name in self.animal_kinds:
				for i in self.animal_contours[animal_name]:
					if '4 locomotion parameters' in parameter_to_analyze:
						self.all_behavior_parameters[animal_name]['distance'][i]=0.0
					for parameter_name in all_parameters:
						self.all_behavior_parameters[animal_name][parameter_name][i]=[np.nan]*len(self.all_time)
				
		if len(parameter_to_analyze)>0:

			for animal_name in self.animal_kinds:

				for i in self.animal_contours[animal_name]:

					n=self.length+self.register_counts[animal_name][i]

					while n<len(self.animal_contours[animal_name][i]):

						if self.categorize_behavior is True:

							behavior_name=self.event_probability[animal_name][i][n][0]

							if behavior_name!='NA':

								if 'count' in parameter_to_analyze:
									if behavior_name!=self.event_probability[animal_name][i][n-1][0]:
										self.all_behavior_parameters[animal_name][behavior_name]['count'][i]+=1
										
								if 'duration' in parameter_to_analyze:
									self.all_behavior_parameters[animal_name][behavior_name]['duration'][i]+=round(1/self.fps,2)

								if 'latency' in parameter_to_analyze:
									if self.all_behavior_parameters[animal_name][behavior_name]['latency'][i]=='NA':
										self.all_behavior_parameters[animal_name][behavior_name]['latency'][i]=self.all_time[n]

								if '3 length parameters' in parameter_to_analyze:
									heights_diffs=[]
									for h in self.animal_heights[animal_name][i][n-self.length+1:n+1]:
										if h is None or self.animal_heights[animal_name][i][n] is None:
											height_diff=0.0
										else:
											height_diff=abs(h-self.animal_heights[animal_name][i][n])/h	
										heights_diffs.append(height_diff)
									magnitude_length=max(heights_diffs)
									vigor_length=magnitude_length/((self.length-np.argmax(heights_diffs))/self.fps)
									intensity_length=sum(heights_diffs)/(self.length/self.fps)
									if magnitude_length>0:
										self.all_behavior_parameters[animal_name][behavior_name]['magnitude_length'][i][n]=magnitude_length
									if vigor_length>0:
										self.all_behavior_parameters[animal_name][behavior_name]['vigor_length'][i][n]=vigor_length
									if intensity_length>0:
										self.all_behavior_parameters[animal_name][behavior_name]['intensity_length'][i][n]=intensity_length

								if '4 locomotion parameters' in parameter_to_analyze:
									distance_traveled=0.0
									d=n-self.length
									while d<n-1:
										start_center=self.animal_centers[animal_name][i][d]
										end_center=self.animal_centers[animal_name][i][d+1]
										if start_center is None or end_center is None:
											dt=0.0
										else:
											dt=math.dist(end_center,start_center)
										distance_traveled+=dt
										d+=1
									if normalize_distance is True:
										calibrator=math.sqrt(self.animal_area[animal_name])
										distance_traveled=distance_traveled/calibrator
									speed=distance_traveled/(self.length/self.fps)
									end_center=self.animal_centers[animal_name][i][n]
									if end_center is not None:
										displacements=[]
										for ct in self.animal_centers[animal_name][i][n-self.length+1:n+1]:
											if ct is None:
												displacements.append(0)
											else:
												displacements.append(math.dist(end_center,ct))		
										displacement=max(displacements)
										if normalize_distance is True:
											displacement=displacement/calibrator
										velocity=displacement/((self.length-np.argmax(displacements))/self.fps)
										self.all_behavior_parameters[animal_name][behavior_name]['velocity'][i][n]=velocity
									velocities_max=[]
									velocities_min=[]
									for v in self.all_behavior_parameters[animal_name][behavior_name]['velocity'][i][n-self.length+1:n+1]:
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
											self.all_behavior_parameters[animal_name][behavior_name]['acceleration'][i][n]=(vmax-vmin)/t
									self.all_behavior_parameters[animal_name][behavior_name]['distance'][i]+=distance_traveled
									self.all_behavior_parameters[animal_name][behavior_name]['speed'][i][n]=speed

								if '3 areal parameters' in parameter_to_analyze:
									mask=np.zeros_like(self.background)
									contour=self.animal_contours[animal_name][i][n]
									if contour is not None:
										cv2.drawContours(mask,[contour],0,(255,255,255),-1)
										mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
										area_diffs=[]
										for ct in self.animal_contours[animal_name][i][n-self.length+1:n+1]:
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
												self.all_behavior_parameters[animal_name][behavior_name]['magnitude_area'][i][n]=magnitude_area
											if vigor_area>0:
												self.all_behavior_parameters[animal_name][behavior_name]['vigor_area'][i][n]=vigor_area
											if intensity_area>0:
												self.all_behavior_parameters[animal_name][behavior_name]['intensity_area'][i][n]=intensity_area

						else:

							if '3 length parameters' in parameter_to_analyze:
								heights_diffs=[]
								for h in self.animal_heights[animal_name][i][n-self.length+1:n+1]:
									if h is None or self.animal_heights[animal_name][i][n] is None:
										height_diff=0.0
									else:
										height_diff=abs(h-self.animal_heights[animal_name][i][n])/h
									heights_diffs.append(height_diff)
								magnitude_length=max(heights_diffs)
								vigor_length=magnitude_length/((self.length-np.argmax(heights_diffs))/self.fps)
								intensity_length=sum(heights_diffs)/(self.length/self.fps)
								if magnitude_length>0:
									self.all_behavior_parameters[animal_name]['magnitude_length'][i][n]=magnitude_length
								if vigor_length>0:
									self.all_behavior_parameters[animal_name]['vigor_length'][i][n]=vigor_length
								if intensity_length>0:
									self.all_behavior_parameters[animal_name]['intensity_length'][i][n]=intensity_length

							if '4 locomotion parameters' in parameter_to_analyze:
								distance_traveled=0.0
								d=n-self.length
								while d<n-1:
									start_center=self.animal_centers[animal_name][i][d]
									end_center=self.animal_centers[animal_name][i][d+1]
									if start_center is None or end_center is None:
										dt=0.0
									else:
										dt=math.dist(end_center,start_center)
									distance_traveled+=dt
									d+=1
								if normalize_distance is True:
									calibrator=math.sqrt(self.animal_area[animal_name])
									distance_traveled=distance_traveled/calibrator
								speed=distance_traveled/(self.length/self.fps)
								end_center=self.animal_centers[animal_name][i][n]
								if end_center is not None:
									displacements=[]
									for ct in self.animal_centers[animal_name][i][n-self.length+1:n+1]:
										if ct is None:
											displacements.append(0)
										else:
											displacements.append(math.dist(end_center,ct))
									displacement=max(displacements)
									if normalize_distance is True:
										displacement=displacement/calibrator
									velocity=displacement/((self.length-np.argmax(displacements))/self.fps)
									self.all_behavior_parameters[animal_name]['velocity'][i][n]=velocity
								velocities_max=[]
								velocities_min=[]
								for v in self.all_behavior_parameters[animal_name]['velocity'][i][n-self.length+1:n+1]:
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
										self.all_behavior_parameters[animal_name]['acceleration'][i][n]=(vmax-vmin)/t
								self.all_behavior_parameters[animal_name]['distance'][i]+=distance_traveled
								self.all_behavior_parameters[animal_name]['speed'][i][n]=speed

							if '3 areal parameters' in parameter_to_analyze:
								mask=np.zeros_like(self.background)
								contour=self.animal_contours[animal_name][i][n]
								if contour is not None:
									cv2.drawContours(mask,[contour],0,(255,255,255),-1)
									mask=cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
									area_diffs=[]
									for ct in self.animal_contours[animal_name][i][n-self.length+1:n+1]:
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
											self.all_behavior_parameters[animal_name]['magnitude_area'][i][n]=magnitude_area
										if vigor_area>0:
											self.all_behavior_parameters[animal_name]['vigor_area'][i][n]=vigor_area
										if intensity_area>0:
											self.all_behavior_parameters[animal_name]['intensity_area'][i][n]=intensity_area

						n+=1

					if self.categorize_behavior is True:
					
						if 'duration' in parameter_to_analyze:
							for behavior_name in self.all_behavior_parameters[animal_name]:
								if self.all_behavior_parameters[animal_name][behavior_name]['duration'][i]!=0.0:
									self.all_behavior_parameters[animal_name][behavior_name]['duration'][i]+=round(self.length/self.fps,2)
								else:
									self.all_behavior_parameters[animal_name][behavior_name]['duration'][i]='NA'

						if '4 locomotion parameters' in parameter_to_analyze:
							for behavior_name in self.all_behavior_parameters[animal_name]:
								if self.all_behavior_parameters[animal_name][behavior_name]['distance'][i]==0.0:
									self.all_behavior_parameters[animal_name][behavior_name]['distance'][i]='NA'


	def export_results(self,normalize_distance=True,parameter_to_analyze=[]):

		print('Quantifying behaviors...')
		print(datetime.datetime.now())

		self.analyze_parameters(normalize_distance=normalize_distance,parameter_to_analyze=parameter_to_analyze)

		print('Behavioral quantification Completed!')

		print('Exporting results...')
		print(datetime.datetime.now())

		for animal_name in self.animal_kinds:

			if self.categorize_behavior is True:
				events_df=pd.DataFrame.from_dict(self.event_probability[animal_name],orient='index',columns=self.all_time)
				if len(self.all_time)<16000:
					events_df.to_excel(os.path.join(self.results_path,animal_name+'_all_event_probability.xlsx'),float_format='%.2f')
				else:
					events_df.to_csv(os.path.join(self.results_path,animal_name+'all_event_probability.csv'),float_format='%.2f')

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

				for behavior_name in self.all_behavior_parameters[animal_name]:
					os.makedirs(os.path.join(self.results_path,behavior_name),exist_ok=True)

					summary=[]

					for parameter_name in all_parameters:
						if parameter_name in ['count','duration','distance','latency']:
							summary.append(pd.DataFrame.from_dict(self.all_behavior_parameters[animal_name][behavior_name][parameter_name],orient='index',columns=[parameter_name]).reset_index(drop=True))
						else:
							individual_df=pd.DataFrame.from_dict(self.all_behavior_parameters[animal_name][behavior_name][parameter_name],orient='index',columns=self.all_time)
							if parameter_name!='probability':
								summary.append(individual_df.mean(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_mean'}))
								summary.append(individual_df.max(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_max'}))
								summary.append(individual_df.min(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_min'}))
							if len(self.all_time)<16000:
								individual_df.to_excel(os.path.join(self.results_path,behavior_name,animal_name+'_'+parameter_name+'.xlsx'),float_format='%.2f')
							else:
								individual_df.to_csv(os.path.join(self.results_path,behavior_name,animal_name+'_'+parameter_name+'.csv'),float_format='%.2f')

					if len(summary)>=1:
						pd.concat(summary,axis=1).to_excel(os.path.join(self.results_path,behavior_name,animal_name+'_all_summary.xlsx'),float_format='%.2f')

			else:

				summary=[]

				for parameter_name in all_parameters:
					if parameter_name=='distance':
						summary.append(pd.DataFrame.from_dict(self.all_behavior_parameters[animal_name][parameter_name],orient='index',columns=['distance']).reset_index(drop=True))
					else:
						individual_df=pd.DataFrame.from_dict(self.all_behavior_parameters[animal_name][parameter_name],orient='index',columns=self.all_time)

						summary.append(individual_df.mean(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_mean'}))
						summary.append(individual_df.max(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_max'}))
						summary.append(individual_df.min(axis=1,skipna=True).to_frame().reset_index(drop=True).rename(columns={0:parameter_name+'_min'}))

						if len(self.all_time)<16000:
							individual_df.to_excel(os.path.join(self.results_path,animal_name+'_'+parameter_name+'.xlsx'),float_format='%.2f')
						else:
							individual_df.to_csv(os.path.join(self.results_path,animal_name+'_'+parameter_name+'.csv'),float_format='%.2f')

				if len(summary)>=1:
					pd.concat(summary,axis=1).to_excel(os.path.join(self.results_path,animal_name+'_all_summary.xlsx'),float_format='%.2f')			

		print('All results exported in: '+str(self.results_path))


	def generate_data(self,background_free=True,skip_redundant=1):
		
		print('Generating behavior examples...')
		print(datetime.datetime.now())

		capture=cv2.VideoCapture(self.path_to_video)
		frame_count=frame_count_analyze=0
		animation=deque(maxlen=self.length)

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

				self.detect_track_individuals([frame],1,frame_count_analyze,background_free=background_free,animation=animation)

				for animal_name in self.animal_kinds:
						
					if frame_count_analyze>=self.length and frame_count_analyze%skip_redundant==0:

						for n in self.animal_centers[animal_name]:

							h=w=0

							for i,f in enumerate(self.temp_frames):
								contour=self.animal_contours[animal_name][n][frame_count_analyze-self.length+1:frame_count_analyze+1][i]
								if contour is None:
									blob=np.zeros_like(self.background)
								else:
									blob=extract_blob_background(f,self.animal_contours[animal_name][n][frame_count_analyze-self.length+1:frame_count_analyze+1],contour=contour,channel=3,background_free=background_free)
									h,w=blob.shape[:2]
								animation.append(blob)

							if h>0:

								if self.include_bodyparts is True:
									animation_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'.avi'
									pattern_image_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_std'+str(self.std)+'.jpg'
									pattern_image=generate_patternimage(self.background,self.animal_contours[animal_name][n][frame_count_analyze-self.length+1:frame_count_analyze+1],inners=self.animal_inners[animal_name][n],std=self.std)
								else:
									animation_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'.avi'
									pattern_image_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'.jpg'
									pattern_image=generate_patternimage(self.background,self.animal_contours[animal_name][n][frame_count_analyze-self.length+1:frame_count_analyze+1],inners=None,std=0)

								path_animation=os.path.join(self.results_path,animation_name)
								path_pattern_image=os.path.join(self.results_path,pattern_image_name)

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

		frame_count=frame_count_analyze=0
		temp_contours=deque(maxlen=self.length)
		temp_inners=deque(maxlen=self.length)
		animation=deque(maxlen=self.length)
		capture=cv2.VideoCapture(self.path_to_video)

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

				self.temp_frames.append(frame)
				tensor_frame=torch.as_tensor(frame.astype("float32").transpose(2,0,1))
				with torch.no_grad():
					output=self.detector([{"image":tensor_frame}])
				instances=output[0]['instances'].to('cpu')
				masks=instances.pred_masks.numpy().astype(np.uint8)
				classes=instances.pred_classes.numpy()
				scores=instances.scores.numpy()

				if len(masks)==0:

					temp_contours.append(None)
					temp_inners.append(None)
					animation.append(np.zeros_like(self.background))

				else:

					mask_area=np.sum(np.array(masks),axis=(1,2))
					exclusion_mask=np.zeros(len(masks),dtype=bool)
					exclusion_mask[np.where((np.sum(np.logical_and(masks[:,None],masks),axis=(2,3))/mask_area[:,None]>0.8) & (mask_area[:,None]<mask_area[None,:]))[0]]=True
					masks=[m for m,exclude in zip(masks,exclusion_mask) if not exclude]
					classes=[c for c,exclude in zip(classes,exclusion_mask) if not exclude]
					classes=[self.animal_mapping[str(x)] for x in classes]
					scores=[s for s,exclude in zip(scores,exclusion_mask) if not exclude]

					contours=[]
					inners=[]

					for animal_name in self.animal_kinds:
						goodcontours=[]
						goodmasks=[]
						animal_number=int(self.animal_number[animal_name])
						animal_masks=[masks[a] for a,name in enumerate(classes) if name==animal_name]
						animal_scores=[scores[a] for a,name in enumerate(classes) if name==animal_name]
						if len(animal_masks)>0:
							if len(animal_scores)>animal_number*2:
								sorted_scores_indices=np.argsort(animal_scores)[-int(animal_number*2):]
								animal_masks=[animal_masks[x] for x in sorted_scores_indices]
							for mask in animal_masks:
								mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((self.kernel,self.kernel),np.uint8))
								cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
								goodcontours.append(sorted(cnts,key=cv2.contourArea,reverse=True)[0])
								goodmasks.append(mask)
							areas=[cv2.contourArea(ct) for ct in goodcontours]
							sorted_area_indices=np.argsort(np.array(areas))[-animal_number:]
							for x in sorted_area_indices:
								cnt=goodcontours[x]
								mask=goodmasks[x]
								contours.append(cnt)
								if self.include_bodyparts is True:
									masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
									inners.append(get_inner(masked_frame,cnt))

					temp_contours.append(contours)
					temp_inners.append(inners)

					if frame_count_analyze>=self.length and frame_count_analyze%skip_redundant==0:

						(y_bt,y_tp,x_lf,x_rt)=crop_frame(self.background,functools.reduce(operator.iconcat,temp_contours,[]))

						h=w=0

						for i,f in enumerate(self.temp_frames):
							if temp_contours[i] is None:
								blob=np.zeros_like(self.background)
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

							path_animation=os.path.join(self.results_path,animation_name)
							path_pattern_image=os.path.join(self.results_path,pattern_image_name)

							writer=cv2.VideoWriter(path_animation,cv2.VideoWriter_fourcc(*'MJPG'),self.fps/5,(w,h),True)
							for blob in animation:
								writer.write(cv2.resize(blob,(w,h),interpolation=cv2.INTER_AREA))
							writer.release()

							cv2.imwrite(path_pattern_image,pattern_image)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		print('Behavior example generation completed!')


	def generate_data_interact_advance(self,background_free=True,skip_redundant=1):

		print('Generating behavior examples...')
		print(datetime.datetime.now())

		capture=cv2.VideoCapture(self.path_to_video)
		frame_count=frame_count_analyze=0
		animation=deque(maxlen=self.length)
		for animal_name in self.animal_kinds:
			self.animal_blobs[animal_name]={}
			for i in range(self.animal_number[animal_name]):
				self.to_deregister[animal_name][i]=0
				self.animal_contours[animal_name][i]=deque(maxlen=self.length)
				self.animal_other_contours[animal_name][i]=deque(maxlen=self.length)
				self.animal_centers[animal_name][i]=deque(maxlen=self.length)
				self.animal_existingcenters[animal_name][i]=(-10000,-10000)
				self.animal_blobs[animal_name][i]=deque(maxlen=self.length)
				if self.include_bodyparts is True:
					self.animal_inners[animal_name][i]=deque(maxlen=self.length)
					self.animal_other_inners[animal_name][i]=deque(maxlen=self.length)

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

				tensor_frame=torch.as_tensor(frame.astype("float32").transpose(2,0,1))
				with torch.no_grad():
					output=self.detector([{"image":tensor_frame}])
				instances=output[0]['instances'].to('cpu')
				masks=instances.pred_masks.numpy().astype(np.uint8)
				classes=instances.pred_classes.numpy()
				scores=instances.scores.numpy()

				if len(masks)==0:

					for animal_name in self.animal_kinds:
						self.animal_present[animal_name]=0
						for i in self.animal_centers[animal_name]:
							self.animal_contours[animal_name][i].append(None)
							self.animal_other_contours[animal_name][i].append([None])
							self.animal_centers[animal_name][i].append(None)
							self.animal_blobs[animal_name][i].append(None)
							if self.include_bodyparts is True:
								self.animal_inners[animal_name][i].append(None)
								self.animal_other_inners[animal_name][i].append([None])

				else:

					mask_area=np.sum(np.array(masks),axis=(1,2))
					exclusion_mask=np.zeros(len(masks),dtype=bool)
					exclusion_mask[np.where((np.sum(np.logical_and(masks[:,None],masks),axis=(2,3))/mask_area[:,None]>0.8) & (mask_area[:,None]<mask_area[None,:]))[0]]=True
					masks=[m for m,exclude in zip(masks,exclusion_mask) if not exclude]
					classes=[c for c,exclude in zip(classes,exclusion_mask) if not exclude]
					classes=[self.animal_mapping[str(x)] for x in classes]
					scores=[s for s,exclude in zip(scores,exclusion_mask) if not exclude]

					all_centers=[]
					all_masks=[]
					all_contours=[]
					all_inners=[]
					all_blobs=[]
					average_area=[]

					for animal_name in self.animal_kinds:

						goodmasks=[]
						goodcontours=[]
						animal_number=int(self.animal_number[animal_name])
						animal_masks=[masks[a] for a,name in enumerate(classes) if name==animal_name]
						animal_scores=[scores[a] for a,name in enumerate(classes) if name==animal_name]
						
						if len(animal_masks)==0:
							self.animal_present[animal_name]=0
							for i in self.animal_centers[animal_name]:
								self.animal_contours[animal_name][i].append(None)
								self.animal_other_contours[animal_name][i].append([None])
								self.animal_centers[animal_name][i].append(None)
								self.animal_blobs[animal_name][i].append(None)
								if self.include_bodyparts is True:
									self.animal_inners[animal_name][i].append(None)
									self.animal_other_inners[animal_name][i].append([None])
						else:
							if len(animal_scores)>animal_number*2:
								sorted_scores_indices=np.argsort(animal_scores)[-int(animal_number*2):]
								animal_masks=[animal_masks[x] for x in sorted_scores_indices]
							for mask in animal_masks:
								mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((self.kernel,self.kernel),np.uint8))
								goodmasks.append(mask)
								cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
								goodcontours.append(sorted(cnts,key=cv2.contourArea,reverse=True)[0])
							areas=[cv2.contourArea(ct) for ct in goodcontours]
							sorted_area_indices=np.argsort(np.array(areas))[-animal_number:]
							self.animal_present[animal_name]=len(sorted_area_indices)
							areas_sorted=sorted(areas)[-animal_number:]
							area=sum(areas_sorted)/len(areas_sorted)
							if self.animal_area[animal_name] is None:
								self.animal_area[animal_name]=area
							else:
								self.animal_area[animal_name]=(self.animal_area[animal_name]+area)/2
							average_area.append(self.animal_area[animal_name])
							for x in sorted_area_indices:
								mask=goodmasks[x]
								all_masks.append(mask)
								cnt=goodcontours[x]
								all_contours.append(cnt)
								all_centers.append((int(cv2.moments(cnt)['m10']/cv2.moments(cnt)['m00']),int(cv2.moments(cnt)['m01']/cv2.moments(cnt)['m00'])))
								if self.include_bodyparts is True:
									masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
									all_inners.append(get_inner(masked_frame,cnt))

					if len(all_centers)>1:

						centers_array=np.array(all_centers)
						distances_squared=np.sum((centers_array[:,None]-centers_array)**2,axis=2)
						determine=np.logical_and(distances_squared>0,distances_squared<(math.sqrt(sum(average_area)/len(average_area))*self.social_distance)**2)
						other_contours=[[all_contours[x] for x,determ in enumerate(determine[y]) if determ] for y,c in enumerate(all_centers)]
						if self.include_bodyparts is True:
							other_inners=[[all_inners[x] for x,determ in enumerate(determine[y]) if determ] for y,c in enumerate(all_centers)]
						other_masks=[np.bitwise_or.reduce(np.stack(np.array(all_masks)[determine[x]])) if len(c)>0 else None for x,c in enumerate(other_contours)]
						for i,other_mask in enumerate(other_masks):
							if background_free is True:
								blob=frame*cv2.cvtColor(all_masks[i],cv2.COLOR_GRAY2BGR)
								if other_mask is not None:
									other_blob=cv2.cvtColor(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*other_mask,cv2.COLOR_GRAY2BGR)
									blob=cv2.add(blob,other_blob)
									blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
							else:
								blob=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
							cv2.drawContours(blob,[all_contours[i]],0,(255,0,255),2)
							all_blobs.append(blob)

					else:

						if len(all_centers)>0:
							other_contours=[[None]]
							if self.include_bodyparts is True:
								other_inners=[[None]]
							if background_free is True:
								blob=frame*cv2.cvtColor(all_masks[0],cv2.COLOR_GRAY2BGR)
								blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
							else:
								blob=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
							cv2.drawContours(blob,[all_contours[0]],0,(255,0,255),2)
							all_blobs.append(blob)

					n=0

					for animal_name in self.animal_number:

						if self.animal_present[animal_name]>0:

							animal_length=n+self.animal_present[animal_name]

							animal_centers=all_centers[n:animal_length]
							animal_contours=all_contours[n:animal_length]
							animal_other_contours=other_contours[n:animal_length]
							animal_blobs=all_blobs[n:animal_length]
							if self.include_bodyparts is True:
								animal_inners=all_inners[n:animal_length]
								animal_other_inners=other_inners[n:animal_length]

							unused_existing_indices=list(self.animal_existingcenters[animal_name])
							existing_centers=list(self.animal_existingcenters[animal_name].values())
							unused_new_indices=list(range(len(animal_centers)))
							dt_flattened=distance.cdist(existing_centers,animal_centers).flatten()
							dt_sort_index=dt_flattened.argsort()
							length=len(animal_centers)

							for idx in dt_sort_index:
								index_in_existing=int(idx/length)
								index_in_new=int(idx%length)
								if index_in_existing in unused_existing_indices:
									if index_in_new in unused_new_indices:
										unused_existing_indices.remove(index_in_existing)
										unused_new_indices.remove(index_in_new)
										self.to_deregister[animal_name][index_in_existing]=0
										contour=animal_contours[index_in_new]
										self.animal_contours[animal_name][index_in_existing].append(contour)
										center=animal_centers[index_in_new]
										self.animal_centers[animal_name][index_in_existing].append(center)
										self.animal_existingcenters[animal_name][index_in_existing]=center
										self.animal_other_contours[animal_name][index_in_existing].append(animal_other_contours[index_in_new])

										self.animal_blobs[animal_name][index_in_existing].append(animal_blobs[index_in_new])
										if self.include_bodyparts is True:
											self.animal_inners[animal_name][index_in_existing].append(animal_inners[index_in_new])
											self.animal_other_inners[animal_name][index_in_existing].append(animal_other_inners[index_in_new])

							if len(unused_existing_indices)>0:
								for i in unused_existing_indices:
									if self.to_deregister[animal_name][i]<=self.count_to_deregister:
										self.to_deregister[animal_name][i]+=1
									else:
										self.animal_existingcenters[animal_name][i]=(-10000,-10000)
									self.animal_contours[animal_name][i].append(None)
									self.animal_other_contours[animal_name][i].append([None])
									self.animal_centers[animal_name][i].append(None)
									self.animal_blobs[animal_name][i].append(None)
									if self.include_bodyparts is True:
										self.animal_inners[animal_name][i].append(None)
										self.animal_other_inners[animal_name][i].append([None])

							n+=self.animal_present[animal_name]


				if frame_count_analyze>=self.length and frame_count_analyze%skip_redundant==0:

					for animal_name in self.animal_kinds:

						if self.animal_present[animal_name]>0:

							for n in self.animal_centers[animal_name]:

								total_contours=functools.reduce(operator.iconcat,self.animal_other_contours[animal_name][n],[])
								total_contours+=self.animal_contours[animal_name][n]
								total_contours=[i for i in total_contours if i is not None]

								if len(total_contours)>0:

									(y_bt,y_tp,x_lf,x_rt)=crop_frame(self.background,total_contours)

									h=w=0

									for i,b in enumerate(self.animal_blobs[animal_name][n]):
										if b is None:
											blob=np.zeros_like(self.background)
										else:
											blob=b[y_bt:y_tp,x_lf:x_rt]
											h,w=blob.shape[:2]
										animation.append(blob)

									if h>0:

										if self.social_distance==float('inf'):
											scdt=str(0)
										else:
											scdt=str(self.social_distance)

										if self.include_bodyparts is True:
											animation_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_scdt'+scdt+'_std'+str(self.std)+'_itadv.avi'
											pattern_image_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_scdt'+scdt+'_std'+str(self.std)+'_itadv.jpg'
											pattern_image=pattern_image=generate_patternimage_interact(self.background,self.animal_contours[animal_name][n],self.animal_other_contours[animal_name][n],inners=self.animal_inners[animal_name][n],other_inners=self.animal_other_inners[animal_name][n],std=self.std)
										else:
											animation_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_scdt'+scdt+'_itadv.avi'
											pattern_image_name=os.path.splitext(self.basename)[0]+'_'+animal_name+'_'+str(n)+'_'+str(frame_count_analyze)+'_len'+str(self.length)+'_scdt'+scdt+'_itadv.jpg'
											pattern_image=pattern_image=generate_patternimage_interact(self.background,self.animal_contours[animal_name][n],self.animal_other_contours[animal_name][n],inners=None,other_inners=None,std=0)

										path_animation=os.path.join(self.results_path,animation_name)
										path_pattern_image=os.path.join(self.results_path,pattern_image_name)

										writer=cv2.VideoWriter(path_animation,cv2.VideoWriter_fourcc(*'MJPG'),self.fps/5,(w,h),True)
										for blob in animation:
											writer.write(cv2.resize(blob,(w,h),interpolation=cv2.INTER_AREA))
										writer.release()

										cv2.imwrite(path_pattern_image,pattern_image)

				frame_count_analyze+=1

			frame_count+=1

		capture.release()

		print('Behavior example generation completed!')




