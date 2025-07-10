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

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
import logging
logger =  logging.getLogger(__name__)
logger.debug('loading %s', __file__)


import os
import gc
import cv2
import numpy as np
import datetime
from skimage import exposure
logger.debug('importing tensorflow.keras.preprocessing.image (starting...)')
from tensorflow.keras.preprocessing.image import img_to_array
logger.debug('importing tensorflow.keras.preprocessing.image (done)')
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.colorbar import ColorbarBase
from PIL import Image,ImageEnhance
import pandas as pd
import seaborn as sb
import functools
import operator
import math
import shutil


def extract_background(frames,stable_illumination=True,animal_vs_bg=0):

	'''
	This function is used in 'background subtraction based detection method', 
	which extract the static background of a video.

	animal_vs_bg: 0--animals brighter than the background
				  1--animals darker than the background
				  2--hard to tell
	'''

	len_frames=len(frames)
	
	if len_frames<=3:

		background=None

	else:

		frames=np.array(frames,dtype='float32')

		if animal_vs_bg==2:

			if len_frames>101:

				frames_mean=[]
				check_frames=[]
				mean_overall=frames.mean(0)
				n=0

				while n<len_frames-101:
					frames_temp=frames[n:n+100]
					mean=frames_temp.mean(0)
					frames_mean.append(mean)	
					check_frames.append(abs(mean-mean_overall)+frames_temp.std(0))
					n+=30

				frames_mean=np.array(frames_mean,dtype='float32')
				check_frames=np.array(check_frames,dtype='float32')
				background=np.uint8(np.take_along_axis(frames_mean,np.argsort(check_frames,axis=0),axis=0)[0])

				del frames_mean
				del check_frames
				del frames_temp
				gc.collect()

			else:

				background=np.uint8(np.median(frames,axis=0))	

		else:

			if stable_illumination:

				if animal_vs_bg==1:
					background=np.uint8(frames.max(0))
				else:
					background=np.uint8(frames.min(0))

			else:

				if len_frames>101:

					frames_mean=[]
					check_frames=[]
					n=0

					while n<len_frames-101:
						frames_temp=frames[n:n+100]
						mean=frames_temp.mean(0)
						frames_mean.append(mean)
						if animal_vs_bg==1:
							frames_temp_inv=255-frames_temp
							check_frames.append(frames_temp_inv.mean(0)+frames_temp_inv.std(0))
						else:
							check_frames.append(mean+frames_temp.std(0))
						n+=30

					frames_mean=np.array(frames_mean,dtype='float32')
					check_frames=np.array(check_frames,dtype='float32')
					background=np.uint8(np.take_along_axis(frames_mean,np.argsort(check_frames,axis=0),axis=0)[0])

					del frames_mean
					del check_frames
					del frames_temp
					gc.collect()

				else:

					if animal_vs_bg==1:
						background=np.uint8(frames.max(0))
					else:
						background=np.uint8(frames.min(0))
	
	return background


def estimate_constants(path_to_video,delta,animal_number,framewidth=None,frameheight=None,stable_illumination=True,ex_start=0,ex_end=None,t=None,duration=10,animal_vs_bg=0,path_background=None,kernel=3):

	'''
	This function is in 'background subtraction based detection method',
	which determines the time windows for background extraction and 
	estimating animal size, as well as finding the stimulation start time.

	delta: a float number that detemines fold changes of illumination when it's considered as stimulation start time point
	ex_start and ex_end: determines the time window (in second) for extracting background
	path_to_background: the path to the extracted background, which can be reused for background subtraction
	kernel: determines how fine the erosion or dilation operation is
	'''

	capture=cv2.VideoCapture(path_to_video)
	fps=round(capture.get(cv2.CAP_PROP_FPS))
	capture.release()
	frame_initial=None
	stim_t=None

	if path_background is None:

		print('Extracting the static background...')

		capture=cv2.VideoCapture(path_to_video)

		if ex_start>=capture.get(cv2.CAP_PROP_FRAME_COUNT)/fps:
			print('The beginning time for background extraction is later than the end of the video!')
			print('Will use the 1st second of the video as the beginning time for background extraction!')
			ex_start=0
		if ex_start==ex_end:
			ex_end=ex_start+1

		frames=deque(maxlen=1000)
		frames_low=deque(maxlen=1000)
		frames_high=deque(maxlen=1000)
		backgrounds=deque(maxlen=1000)
		backgrounds_low=deque(maxlen=1000)
		backgrounds_high=deque(maxlen=1000)
		frame_number=1
		frame_count=1
		frame_low_count=1
		frame_high_count=1

		while True:

			retval,frame=capture.read()

			if frame is None:
				break

			if ex_end is not None:
				if frame_number>=ex_end*fps:
					break

			if frame_initial is None:
				frame_initial=frame
				if framewidth is not None:
					frame_initial=cv2.resize(frame,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

			if frame_number>=ex_start*fps:

				if framewidth is not None:
					frame=cv2.resize(frame,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

				if np.mean(frame)<np.mean(frame_initial)/delta:
					if stim_t is None:
						stim_t=frame_number/fps
					frames_low.append(frame)
					frame_low_count+=1
				elif np.mean(frame)>delta*np.mean(frame_initial):
					if stim_t is None:
						stim_t=frame_number/fps
					frames_high.append(frame)
					frame_high_count+=1
				else:
					frames.append(frame)
					frame_count+=1

			if frame_count==1001:
				frame_count=1
				background=extract_background(frames,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				backgrounds.append(background)

			if frame_low_count==1001:
				frame_low_count=1
				background_low=extract_background(frames_low,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				backgrounds_low.append(background_low)

			if frame_high_count==1001:
				frame_high_count=1
				background_high=extract_background(frames_high,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				backgrounds_high.append(background_high)

			frame_number+=1

		capture.release()

		if len(backgrounds)>0:
			if frame_count>600:
				background=extract_background(frames,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				del frames
				gc.collect()
				backgrounds.append(background)
			if len(backgrounds)==1:
				background=backgrounds[0]
			else:
				backgrounds=np.array(backgrounds,dtype='float32')
				if animal_vs_bg==1:
					background=np.uint8(backgrounds.max(0))
				elif animal_vs_bg==2:
					background=np.uint8(np.median(backgrounds,axis=0))
				else:
					background=np.uint8(backgrounds.min(0))
				del backgrounds
				gc.collect()
		else:
			background=extract_background(frames,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
			del frames
			gc.collect()

		if len(backgrounds_low)>0:
			if frame_low_count>600:
				background_low=extract_background(frames_low,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				del frames_low
				gc.collect()
				backgrounds_low.append(background_low)
			if len(backgrounds_low)==1:
				background_low=backgrounds_low[0]
			else:
				backgrounds_low=np.array(backgrounds_low,dtype='float32')
				if animal_vs_bg==1:
					background_low=np.uint8(backgrounds_low.max(0))
				elif animal_vs_bg==2:
					background_low=np.uint8(np.median(backgrounds_low,axis=0))
				else:
					background_low=np.uint8(backgrounds_low.min(0))
				del backgrounds_low
				gc.collect()
		else:
			background_low=extract_background(frames_low,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
			del frames_low
			gc.collect()

		if len(backgrounds_high)>0:
			if frame_high_count>600:
				background_high=extract_background(frames_high,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
				del frames_high
				gc.collect()
				backgrounds_high.append(background_high)
			if len(backgrounds_high)==1:
				background_high=backgrounds_high[0]
			else:
				backgrounds_high=np.array(backgrounds_high,dtype='float32')
				if animal_vs_bg==1:
					background_high=np.uint8(backgrounds_high.max(0))
				elif animal_vs_bg==2:
					background_high=np.uint8(np.median(backgrounds_high,axis=0))
				else:
					background_high=np.uint8(backgrounds_high.min(0))
				del backgrounds_high
				gc.collect()
		else:
			background_high=extract_background(frames_high,stable_illumination=stable_illumination,animal_vs_bg=animal_vs_bg)
			del frames_high
			gc.collect()

		if background is None:
			background=frame_initial
		if background_low is None:
			background_low=background
		if background_high is None:
			background_high=background

		print('Background extraction completed!')

	else:

		background=cv2.imread(os.path.join(path_background,'background.jpg'))
		background_low=cv2.imread(os.path.join(path_background,'background_low.jpg'))
		background_high=cv2.imread(os.path.join(path_background,'background_high.jpg'))
		if framewidth is not None:
			background=cv2.resize(background,(framewidth,frameheight),interpolation=cv2.INTER_AREA)
			background_low=cv2.resize(background_low,(framewidth,frameheight),interpolation=cv2.INTER_AREA)
			background_high=cv2.resize(background_high,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

		frame_initial=background

	print('Estimating the animal size...')
	print(datetime.datetime.now())

	if delta<10000:
		
		if ex_start!=0 or path_background is not None:

			capture=cv2.VideoCapture(path_to_video)
			frame_count=1

			while True:

				retval,frame=capture.read()

				if frame is None:
					break

				if framewidth is not None:
					frame=cv2.resize(frame,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

				if frame_initial is None:
					frame_initial=frame
				else:
					if np.mean(frame)<np.mean(frame_initial)/delta:
						stim_t=frame_count/fps
						break
					if np.mean(frame)>delta*np.mean(frame_initial):
						stim_t=frame_count/fps
						break
						
				frame_count+=1

			capture.release()

	if t is None:
		if stim_t is None:
			es_start=0
		else:
			es_start=stim_t
	else:
		es_start=t

	if duration>30 or duration<=0:
		duration=30
	es_end=es_start+duration

	capture=cv2.VideoCapture(path_to_video)
	total_contour_area=[]
	frame_count=1
	min_area=(background.shape[1]/100)*(background.shape[0]/100)
	max_area=(background.shape[1]*background.shape[0])*3/4

	if animal_vs_bg==1:
		background_estimation=np.uint8(255-background)
		background_low_estimation=np.uint8(255-background_low)
		background_high_estimation=np.uint8(255-background_high)
	else:
		background_estimation=background
		background_low_estimation=background_low
		background_high_estimation=background_high

	while True:

		retval,frame=capture.read()

		if frame_initial is None:
			frame_initial=frame

		if frame is None:
			break

		if es_end is not None:
			if frame_count>=es_end*fps:
				break

		if frame_count>=es_start*fps:

			if framewidth is not None:
				frame=cv2.resize(frame,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

			if animal_vs_bg==1:
				frame=np.uint8(255-frame)

			contour_area=0

			if np.mean(frame)<np.mean(frame_initial)/delta:
				if animal_vs_bg==2:
					foreground=cv2.absdiff(frame,background_low_estimation)
				else:
					foreground=cv2.subtract(frame,background_low_estimation)
			elif np.mean(frame)>delta*np.mean(frame_initial):
				if animal_vs_bg==2:
					foreground=cv2.absdiff(frame,background_high_estimation)
				else:
					foreground=cv2.subtract(frame,background_high_estimation)
			else:
				if animal_vs_bg==2:
					foreground=cv2.absdiff(frame,background_estimation)
				else:
					foreground=cv2.subtract(frame,background_estimation)

			foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
			thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
			thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))

			if animal_vs_bg==2:
				kernel_erode=max(kernel-4,1)
				thred=cv2.erode(thred,np.ones((kernel_erode,kernel_erode),np.uint8))
			contours,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

			for i in contours:
				if min_area<cv2.contourArea(i)<max_area:
					contour_area+=cv2.contourArea(i)
			total_contour_area.append(contour_area)

		frame_count+=1

	capture.release()

	print('Estimation completed!')

	if len(total_contour_area)>0:
		if animal_number==0:
			print('Animal number is 0. Please enter the correct animal number!')
			animal_area=1
		else:
			animal_area=(sum(total_contour_area)/len(total_contour_area))/animal_number
	else:
		print('No animal detected!')
		animal_area=1

	print('Single animal size: '+str(animal_area))

	if stim_t is None:
		stim_t=2

	return (background,background_low,background_high,stim_t,animal_area)


def crop_frame(frame,contours):

	'''
	This function is used to crop a frame to fit
	the border of a list of contours.
	'''

	lfbt=np.array([contours[i].min(0) for i in range(len(contours)) if contours[i] is not None]).min(0)[0]
	x_lf=lfbt[0]
	y_bt=lfbt[1]
	rttp=np.array([contours[i].max(0) for i in range(len(contours)) if contours[i] is not None]).max(0)[0]
	x_rt=rttp[0]
	y_tp=rttp[1]

	w=x_rt-x_lf+1
	h=y_tp-y_bt+1

	difference=int(abs(w-h)/2)+1

	if w>h:
		y_bt=max(y_bt-difference-1,0)
		y_tp=min(y_tp+difference+1,frame.shape[0])
		x_lf=max(x_lf-1,0)
		x_rt=min(x_rt+1,frame.shape[1])
	if w<h:
		y_bt=max(y_bt-1,0)
		y_tp=min(y_tp+1,frame.shape[0])
		x_lf=max(x_lf-difference-1,0)
		x_rt=min(x_rt+difference+1,frame.shape[1])

	return (y_bt,y_tp,x_lf,x_rt)


def extract_blob_background(frame,contours,contour=None,channel=1,background_free=False,black_background=True):

	'''
	This function is used to keep the pixels for the area
	inside a contour, and crop the frame to fit a list of 
	contours. It can also include background pixels.

	channel: 1--gray scale blob
			 3--RGB scale blob
	black_background: whether to set background black
	'''

	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,contours)
	if background_free:
		mask=np.zeros_like(frame)
		cv2.drawContours(mask,[contour],0,(255,255,255),-1)
		masked_frame=frame*(mask/255.0)
		if black_background is False:
			masked_frame[mask==0]=255
	else:
		masked_frame=frame
	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))

	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def extract_blob_all(frame,y_bt,y_tp,x_lf,x_rt,contours=None,channel=1,background_free=False,black_background=True):

	'''
	This function is used to keep the pixels for the area
	inside a list of contours, and crop the frame to fit 
	the y_bt,y_tp,x_lf,x_rt coordinates.

	channel: 1--gray scale blob
			 3--RGB scale blob
	black_background: whether to set background black
	'''

	if background_free:
		mask=np.zeros_like(frame)
		cv2.drawContours(mask,contours,-1,(255,255,255),-1)
		masked_frame=frame*(mask/255.0)
		if black_background is False:
			masked_frame[mask==0]=255
	else:
		masked_frame=frame
	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))

	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def get_inner(masked_frame_gray,contour):

	'''
	This function is used to get the inner contours, which is used
	when body parts are inlcuded in the pattern images.
	'''

	blur=cv2.GaussianBlur(masked_frame_gray,(3,3),0)
	edges=cv2.Canny(blur,20,75,apertureSize=3,L2gradient=True)
	cnts,_=cv2.findContours(edges,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)

	if len(cnts)>3:
		inner=sorted(cnts,key=cv2.contourArea,reverse=True)[2:]
	else:
		inner=[contour,contour]

	return inner


def contour_frame(frame,animal_number,background,background_low,background_high,delta,contour_area,animal_vs_bg=0,include_bodyparts=False,animation_analyzer=False,channel=1,kernel=5,black_background=True):

	'''
	This function is used in 'background subtraction based detection method',
	which gets contours parameters in a frame based on extracted background.

	delta: a float number that detemines fold changes of illumination when it's considered as stimulation start time point
	contour_area: an estimated area of a single animal / object, which is used to filter out unwanted contours
	animal_vs_bg: 0--animals brighter than the background
				  1--animals darker than the background
				  2--hard to tell
	channel: 1--gray scale blob
			 3--RGB scale blob
	kernel: determines how fine the erosion or dilation operation is
	black_background: whether to set background black
	'''

	if animal_vs_bg==1:
		frame_dt=np.uint8(255-frame)
	else:
		frame_dt=frame

	if np.mean(frame_dt)<np.mean(background)/delta:
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame_dt,background_low)
		else:
			foreground=cv2.subtract(frame_dt,background_low)
	elif np.mean(frame_dt)>delta*np.mean(background):
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame_dt,background_high)
		else:
			foreground=cv2.subtract(frame_dt,background_high)
	else:
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame_dt,background)
		else:
			foreground=cv2.subtract(frame_dt,background)
			
	foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
	thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
	thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
	if animal_vs_bg==2:
		kernel_erode=max(kernel-4,1)
		thred=cv2.erode(thred,np.ones((kernel_erode,kernel_erode),np.uint8))
	cnts,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

	contours=[]
	centers=[]
	heights=[]
	inners=[]

	if animal_number>1:
		for i in cnts:
			if contour_area*0.2<cv2.contourArea(i)<contour_area*1.5:
				contours.append(i)
		if len(contours)>0:
			contours=sorted(contours,key=cv2.contourArea)[-animal_number:]
	else:
		if len(cnts)>0:
			contours=[sorted(cnts,key=cv2.contourArea,reverse=True)[0]]

	if len(contours)>0:
		for i in contours:
			centers.append((int(cv2.moments(i)['m10']/cv2.moments(i)['m00']),int(cv2.moments(i)['m01']/cv2.moments(i)['m00'])))
			(_,_),(w,h),_=cv2.minAreaRect(i)
			heights.append(max(w,h))
			if include_bodyparts:
				mask=np.zeros_like(frame)
				cv2.drawContours(mask,[i],0,(255,255,255),-1)
				mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
				masked_frame=frame_dt*(mask/255)
				gray=cv2.cvtColor(np.uint8(masked_frame),cv2.COLOR_BGR2GRAY)
				inners.append(get_inner(gray,i))

	return (contours,centers,heights,inners)


def generate_patternimage(frame,outlines,inners=None,std=0):

	'''
	This function is used to generate pattern images 
	in 'non-interactive' behavior mode.

	inners: the inner contours when body parts are inlcuded in the pattern images
	std: a integer between 0 and 255, higher std, less inners are included in the pattern images
	'''

	if inners is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)
		backgrounds_std=[]

	background_outlines=np.zeros_like(frame)

	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,outlines)

	length=len(outlines)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outline in enumerate(outlines):

		if outline is not None:
				
			if inners is not None:
				background_std=np.zeros_like(frame)
				cv2.drawContours(background_std,inners[n],-1,(255,255,255),-1)
				backgrounds_std.append(background_std)

			if n<length/4:
				d=n*int((255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,d,0),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,d,0),p_size)	
			elif n<length/2:
				d=int((n-length/4)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,255,d),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,255,d),p_size)
			elif n<3*length/4:
				d=int((n-length/2)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,255-d,255),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,255-d,255),p_size)
			else:
				d=int((n-3*length/4)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255-d,0,255),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255-d,0,255),p_size)

			if inners is not None:
				cv2.drawContours(background_outers,[outline],0,(255,255,255),int(2*p_size))

	outlines_image=background_outlines[y_bt:y_tp,x_lf:x_rt]

	if inners is not None:
		inners_image=background_inners[y_bt:y_tp,x_lf:x_rt]
		outers_image=background_outers[y_bt:y_tp,x_lf:x_rt]
		inners_image=cv2.subtract(inners_image,outers_image)
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)
		inners_image[std_image<std]=0
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,outlines_list,inners_list,std=0):

	'''
	This function is used to generate pattern images 
	in 'interactive basic' behavior mode.

	y_bt...x_rt: the coordinates that determine the border of the pattern images
	inners_list: the list of inner contours when body parts are inlcuded in the pattern images
	std: a integer between 0 and 255, higher std, less inners are included in the pattern images
	'''

	if inners_list is None:
		inners_length=0
		std=0
	else:
		inners_length=len(inners_list[0])

	if inners_list is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)
		backgrounds_std=[]

	background_outlines=np.zeros_like(frame)

	length=len(outlines_list)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outlines in enumerate(outlines_list):

		if inners_list is not None:
			background_std=np.zeros_like(frame)
			if inners_length>0:
				for inners in inners_list[n]:
					cv2.drawContours(background_std,inners,-1,(255,255,255),-1)
			backgrounds_std.append(background_std)

		if n<length/4:
			d=n*int((255*4/length))
			cv2.drawContours(background_outlines,outlines,-1,(255,d,0),p_size)
			if inners_length>0:
				for inners in inners_list[n]:
					cv2.drawContours(background_inners,inners,-1,(255,d,0),p_size)	
		elif n<length/2:
			d=int((n-length/4)*(255*4/length))
			cv2.drawContours(background_outlines,outlines,-1,(255,255,d),p_size)
			if inners_length>0:
				for inners in inners_list[n]:
					cv2.drawContours(background_inners,inners,-1,(255,255,d),p_size)
		elif n<3*length/4:
			d=int((n-length/2)*(255*4/length))
			cv2.drawContours(background_outlines,outlines,-1,(255,255-d,255),p_size)
			if inners_length>0:
				for inners in inners_list[n]:
					cv2.drawContours(background_inners,inners,-1,(255,255-d,255),p_size)
		else:
			d=int((n-3*length/4)*(255*4/length))
			cv2.drawContours(background_outlines,outlines,-1,(255-d,0,255),p_size)
			if inners_length>0:
				for inners in inners_list[n]:
					cv2.drawContours(background_inners,inners,-1,(255-d,0,255),p_size)

		if inners_list is not None:
			cv2.drawContours(background_outers,outlines,-1,(255,255,255),int(2*p_size))

	outlines_image=background_outlines[y_bt:y_tp,x_lf:x_rt]

	if inners_list is not None:
		inners_image=background_inners[y_bt:y_tp,x_lf:x_rt]
		outers_image=background_outers[y_bt:y_tp,x_lf:x_rt]
		inners_image=cv2.subtract(inners_image,outers_image)
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)
		inners_image[std_image<std]=0

	if inners_list is not None:
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def generate_patternimage_interact(frame,outlines,other_outlines,inners=None,other_inners=None,std=0):

	'''
	This function is used to generate pattern images 
	in 'interactive advanced' behavior mode.

	other_outlines: the contours of animals / objects that are not the 'main character'
	other_inners: the inner contours of animals / objects that are not the 'main character' when body parts are inlcuded
	std: a integer between 0 and 255, higher std, less inners are included in the pattern images
	'''

	total_outlines=functools.reduce(operator.iconcat,[ol for ol in other_outlines if ol is not None],[])
	total_outlines+=outlines
	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,total_outlines)

	if inners is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)
		backgrounds_std=[]

	background_outlines=np.zeros_like(frame)

	length=len(outlines)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outline in enumerate(outlines):

		other_outline=other_outlines[n]
		if len(other_outline)>0:
			if other_outline[0] is not None:
				cv2.drawContours(background_outlines,other_outline,-1,(150,150,150),p_size)

		if outline is not None:

			if inners is not None:
				background_std=np.zeros_like(frame)
				inner=inners[n]
				other_inner=functools.reduce(operator.iconcat,[ir for ir in other_inners[n] if ir is not None],[])
				if other_inner is not None:
					cv2.drawContours(background_inners,other_inner,-1,(150,150,150),p_size)
				if inner is not None:
					cv2.drawContours(background_std,inner,-1,(255,255,255),-1)
				if other_inner is not None:
					cv2.drawContours(background_std,other_inner,-1,(255,255,255),-1)
				backgrounds_std.append(background_std)
			else:
				inner=None

			if n<length/4:
				d=n*int((255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,d,0),p_size)
				if inner is not None:
					cv2.drawContours(background_inners,inner,-1,(255,d,0),p_size)
			elif n<length/2:
				d=int((n-length/4)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,255,d),p_size)
				if inner is not None:
					cv2.drawContours(background_inners,inner,-1,(255,255,d),p_size)
			elif n<3*length/4:
				d=int((n-length/2)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255,255-d,255),p_size)
				if inner is not None:
					cv2.drawContours(background_inners,inner,-1,(255,255-d,255),p_size)
			else:
				d=int((n-3*length/4)*(255*4/length))
				cv2.drawContours(background_outlines,[outline],0,(255-d,0,255),p_size)
				if inner is not None:
					cv2.drawContours(background_inners,inner,-1,(255-d,0,255),p_size)

			if inners is not None:
				cv2.drawContours(background_outers,[outline],0,(255,255,255),int(2*p_size))
				if len(other_outline)>0:
					if other_outline[0] is not None:
						cv2.drawContours(background_outers,other_outline,-1,(150,150,150),int(2*p_size))

	outlines_image=background_outlines[y_bt:y_tp,x_lf:x_rt]

	if inners is not None:
		inners_image=background_inners[y_bt:y_tp,x_lf:x_rt]
		outers_image=background_outers[y_bt:y_tp,x_lf:x_rt]
		inners_image=cv2.subtract(inners_image,outers_image)
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)
		inners_image[std_image<std]=0
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def plot_events(result_path,event_probability,time_points,names_and_colors,behavior_to_include,width=0,height=0):

	'''
	This function is used to plot a raster plot for behavior events and probability
	over time based on the 'event_probability' and 'time_points'.
	
	names_and_colors: the behavior names and their representative colors
	width and height: the size of the plot, when ==0, the size is defined automatically
	'''

	print('Exporting the raster plot for this analysis batch...')
	print(datetime.datetime.now())

	if width==0 or height==0:
		time_length=len(time_points)
		if time_length>30000:
			width=round(time_length/3000)+1
			x_intvl=3000
		elif time_length>3000:
			width=round(time_length/300)+1
			x_intvl=300
		else:
			width=round(time_length/30)+1
			x_intvl=30
		height=round(len(event_probability)/4)+1
		if height<3:
			height=3
		figure,ax=plt.subplots(figsize=(width,height))
		if height<=5:
			figure.subplots_adjust(bottom=0.25)
	
	for behavior_name in behavior_to_include:

		all_data=[]
		masks=[]

		for i in event_probability:
			data=[]
			mask=[]
			for n in range(len(event_probability[i])):
				if event_probability[i][n][0]==behavior_name:
					data.append(event_probability[i][n][1])
					mask.append(0)
				else:
					data.append(-1)
					mask.append(True)
			all_data.append(data)
			masks.append(mask)

		all_data=np.array(all_data)
		masks=np.array(masks)
		dataframe=pd.DataFrame(all_data,columns=[float('{:.1f}'.format(i)) for i in time_points])

		heatmap=sb.heatmap(dataframe,mask=masks,xticklabels=x_intvl,cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),cbar=False,vmin=0,vmax=1)
		heatmap.set_xticklabels(heatmap.get_xticklabels(),rotation=90) 
		# if don't want the ticks
		# ax.tick_params(axis='both',which='both',length=0)
	
	plt.savefig(os.path.join(result_path,'behaviors_plot.png'))

	for behavior_name in behavior_to_include: 

		colorbar_fig=plt.figure(figsize=(5,1))
		ax=colorbar_fig.add_axes([0,1,1,1])
		colorbar=ColorbarBase(ax,orientation='horizontal',cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),norm=Normalize(vmin=0,vmax=1),ticks=[])
		colorbar.outline.set_linewidth(0)
			
		plt.savefig(os.path.join(result_path,behavior_name+'_colorbar.png'),bbox_inches='tight')
		plt.close()

	plt.close('all')

	print('The raster plot stored in: '+str(result_path))


def extract_frames(path_to_video,out_path,framewidth=None,start_t=0,duration=0,skip_redundant=1000):

	'''
	This function is used to extract frames from a video.
	
	skip_redundant: the interval between two consecutively extracted frames
	'''

	capture=cv2.VideoCapture(path_to_video)
	fps=round(capture.get(cv2.CAP_PROP_FPS))
	full_duration=capture.get(cv2.CAP_PROP_FRAME_COUNT)/fps
	video_name=os.path.splitext(os.path.basename(path_to_video))[0]

	if start_t>=full_duration:
		print('The beginning time is later than the end of the video!')
		print('Will use the beginning of the video as the beginning time!')
		start_t=0
	if duration<=0:
		duration=full_duration
	end_t=start_t+duration
		
	frame_count=1
	frame_count_generate=0

	while True:

		retval,frame=capture.read()
		t=(frame_count)/fps

		if frame is None:
			break

		if t>=end_t:
			break

		if t>=start_t:
			
			if frame_count_generate%skip_redundant==0:

				if framewidth is not None:
					frameheight=int(frame.shape[0]*framewidth/frame.shape[1])
					frame=cv2.resize(frame,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

				cv2.imwrite(os.path.join(out_path,video_name+'_'+str(frame_count_generate)+'.jpg'),frame)

			frame_count_generate+=1

		frame_count+=1

	capture.release()

	print('The image examples stored in: '+out_path)


def preprocess_video(
	path_to_video,
	out_folder,
	framewidth,
	trim_video=False,
	time_windows=[[0,10]],
	enhance_brightness=False,
	enhance_contrast=False,
	brightness=1.0,
	contrast=1.0,
	crop_frame=False,
	left=0,
	right=0,
	top=0,
	bottom=0,
	fps_new=None,
	):

	'''
	This function is used to preprocess a video.
	
	time_windows: if trim_video is True, the time_windows will form a new, trimmed video
	contrast: only valide if enhance_contrast is True
	left...bottom: the edges defining the cropped frame if crop_frame is True
	'''

	capture=cv2.VideoCapture(path_to_video)
	name=os.path.basename(path_to_video).split('.')[0]
	fps=round(capture.get(cv2.CAP_PROP_FPS))
	num_frames=int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
	width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
	height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

	if framewidth is not None:
		w_resize=int(framewidth)
		h_resize=int(framewidth*height/width)

	if crop_frame:
		if framewidth is not None:
			w=int(min(right,w_resize)-left)
			h=int(min(bottom,h_resize)-top)
		else:
			w=int(min(right,width)-left)
			h=int(min(bottom,height)-top)
	else:
		if framewidth is not None:
			w=w_resize
			h=h_resize
		else:
			w=width
			h=height

	added_name=''
	if trim_video:
		for start,end in time_windows:
			added_name+='_'+str(start)+'-'+str(end)

	dropped_frames=[]
	if fps_new is not None:
		if fps_new>=fps:
			logger.warning('The target fps is equal or greater than the original fps, which is: %r.\nWill keep the original fps.', fps)
			fps_new=fps
		else:
			drop_interval=fps/(fps-fps_new)
			if num_frames>1:
				num_dropped_frames=int(num_frames*(1-fps_new/fps))
				dropped_frames=[round(drop_interval*i) for i in range(num_dropped_frames)]
	else:
		fps_new=fps

	writer=cv2.VideoWriter(os.path.join(out_folder,name+added_name+'_processed.avi'),cv2.VideoWriter_fourcc(*'MJPG'),int(fps_new),(w,h),True)
	frame_count=0

	while True:

		ret,frame=capture.read()

		if frame is None:
			break

		frame_count+=1

		if frame_count-1 in dropped_frames:
			continue

		if framewidth is not None:
			frame=cv2.resize(frame,(w_resize,h_resize),interpolation=cv2.INTER_AREA)

		if crop_frame:
			if framewidth is not None:
				frame=frame[top:min(bottom,h_resize),left:min(right,w_resize),:]
			else:
				frame=frame[top:min(bottom,height),left:min(right,width),:]

		if enhance_brightness:
			frame=frame*brightness
			frame[frame>255]=255
			frame=np.uint8(frame)

		if enhance_contrast:
			frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
			frame=Image.fromarray(frame)
			frame=ImageEnhance.Contrast(frame).enhance(contrast)
			frame=cv2.cvtColor(np.array(frame),cv2.COLOR_RGB2BGR)

		if trim_video:
			t=frame_count/fps
			if t>float(time_windows[-1][-1]):
				break
			for i in time_windows:
				if float(i[0])<=t<=float(i[1]):
					writer.write(frame)
		else:
			writer.write(frame)

	writer.release()
	capture.release()

	logger.info('The processed video(s) stored in: %r', out_folder)


def parse_all_events_file(path_to_events):

	'''
	This function is used to parse an all_events.xlsx file and convert it into 
	a dict 'event_probability', a list 'time_points', and a list 'behavior_names'.

	path_to_events: The path to the 'all_events.xlsx' file

	event_probability is a dictionary with the keys as the ID of each animal / object 
	and the values are lists of lists, where each sub-list has a length of 2 and is 
	in one of the following formats:

		- ['NA', -1]
		- [behavior, probability], where behavior is the name of the behavior 
		and probability is a float between 0 and 1.

	time_points is a list of floats containing the time points of the analysis duration.
	'''

	df=pd.read_excel(path_to_events)

	event_probability={}
	time_points=[]
	behavior_names=[]

	for col_name,col in df.items():

		if col_name=='time/ID':

			time_points=[float(i) for i in col]

		else:

			idx=int(col_name)
			event_probability[idx]=[['NA',-1]]*len(time_points)
			for n,i in enumerate(col):
				event=eval(i)
				behavior=event[0]
				if behavior!='NA':
					if behavior not in behavior_names:
						behavior_names.append(behavior)
					event_probability[idx][n]=event

	behavior_names.sort()

	return (event_probability,time_points,behavior_names)


def calculate_distances(path_to_folder,filename,behavior_to_include,out_path):

	'''
	This function is used to calculate the shortes distance and the total 
	traveling dsitance and their ratio among the locations of the animals 
	when a selected behavior occurs for the first time.

	For example, an animal explores locations A, B, and C in sequence.
	This function will calculate the shortes distance that connects 
	locations A, B, and C, in the exploration sequence of the aninmal.
	It will also calculate the traveling distance of the actual route of 
	the animal.
	
	path_to_folder: The path to the folder that stores the 'all_event_probability.xlsx',
	'all_centers.xlsx', and 'Annotated video.avi'.
	filename: the name of the path_to_folder
	behavior_to_include: the behaviors used in calculation
	'''

	animals=[]
	all_centers=[]
	all_event_probability=[]

	for i in os.listdir(path_to_folder):
		if i.endswith('_centers.xlsx') or i.endswith('_centers.xls') or i.endswith('_centers.XLSX') or i.endswith('_centers.XLS'):
			all_centers.append(i)
		if i.endswith('_event_probability.xlsx') or i.endswith('_event_probability.xls') or i.endswith('_event_probability.XLSX') or i.endswith('_event_probability.XLS'):
			all_event_probability.append(i)

	if len(all_centers)>1:
		for i in all_centers:
			animals.append(i.split('_')[0])
	else:
		if len(all_centers[0].split('_'))>2:
			animals.append(all_centers[0].split('_')[0])
		else:
			animals=['']

	for a,animal in enumerate(animals):

		all_centers_df=pd.read_excel(os.path.join(path_to_folder,all_centers[a]))
		all_events_probability_df=pd.read_excel(os.path.join(path_to_folder,all_event_probability[a]))

		centers={}
		behavior_names={}
		included_behaviors={}
		start_centers={}
		start_indices={}
		frame_count=0
		frame_index=None

		for col_name,col in all_centers_df.items():

			if col_name=='time/ID':
				time_points=[float(i) for i in col]
			else:
				idx=int(col_name)
				centers[idx]=[]
				behavior_names[idx]=[]
				included_behaviors[idx]=[]
				start_centers[idx]={}
				start_indices[idx]={}
				for i in col:
					try:
						value=eval(i)
					except:
						value=None
					centers[idx].append(value)

		for col_name,col in all_events_probability_df.items():

			if col_name!='time/ID':
				idx=int(col_name)
				for n,i in enumerate(col):
					event=eval(i)
					behavior=event[0]
					if behavior!='NA':
						if frame_index is None:
							if behavior in behavior_to_include:
								frame_index=n
						if behavior not in behavior_names[idx]:
							behavior_names[idx].append(behavior)
							start_centers[idx][behavior]=centers[idx][n]
							start_indices[idx][behavior]=n

				if len(behavior_names[idx])<len(behavior_to_include):
					included_behaviors[idx]=behavior_names[idx]
				else:
					included_behaviors[idx]=behavior_to_include

		capture=cv2.VideoCapture(os.path.join(path_to_folder,'Annotated video.avi'))
		while True:
			ret,frame=capture.read()
			if frame_count>frame_index:
				break
			if frame is None:
				break
			frame_count+=1
		capture.release()

		shortest_distances={}
		traveling_distances={}
		durations={}
		speeds={}
		velocities={}
		distance_ratios={}
		diff=int(255/len(behavior_to_include))+25
		diff_animal=int(255/len(centers))+25

		for idx in start_centers:

			shortest_distance=0.0
			traveling_distance=0.0
			centers_for_calculation=[]
			indices_for_calculation=[]

			for behavior in start_centers[idx]:
				if behavior in included_behaviors[idx]:
					centers_for_calculation.append(start_centers[idx][behavior])
					indices_for_calculation.append(start_indices[idx][behavior])

			n=0
			centers_traveled=centers[idx][indices_for_calculation[0]:indices_for_calculation[-1]+1]
			while n<len(centers_traveled)-1:
				if centers_traveled[n] is not None:
					if centers_traveled[n+1] is not None:
						cv2.line(frame,centers_traveled[n],centers_traveled[n+1],(255,0,max(0,255-int(idx*diff_animal))),2)
						traveling_distance+=math.dist(centers_traveled[n],centers_traveled[n+1])
					else:
						cv2.circle(frame,(centers_traveled[n]),2,(255,0,max(0,255-int(idx*diff_animal))),-1)
				n+=1

			n=0
			while n<len(centers_for_calculation):
				if n!=len(centers_for_calculation)-1:
					shortest_distance+=math.dist(centers_for_calculation[n],centers_for_calculation[n+1])
					cv2.circle(frame,(centers_for_calculation[n]),4,(max(0,255-int(n*diff)),max(0,255-int(n*diff)),0),-1)
					cv2.line(frame,centers_for_calculation[n],centers_for_calculation[n+1],(max(0,255-int(n*diff)),max(0,255-int(n*diff))),4)
				n+=1

			shortest_distances[idx]=shortest_distance
			traveling_distances[idx]=traveling_distance
			duration=time_points[indices_for_calculation[-1]]-time_points[indices_for_calculation[0]]
			durations[idx]=duration
			speeds[idx]=traveling_distance/duration
			velocities[idx]=shortest_distance/duration
			distance_ratios[idx]=shortest_distance/traveling_distance

		out_spreadsheet=[]
		out_spreadsheet.append(pd.DataFrame.from_dict(shortest_distances,orient='index',columns=['shortest_distances']).reset_index(drop=True))
		out_spreadsheet.append(pd.DataFrame.from_dict(traveling_distances,orient='index',columns=['traveling_distances']).reset_index(drop=True))
		out_spreadsheet.append(pd.DataFrame.from_dict(durations,orient='index',columns=['durations']).reset_index(drop=True))
		out_spreadsheet.append(pd.DataFrame.from_dict(speeds,orient='index',columns=['speeds']).reset_index(drop=True))
		out_spreadsheet.append(pd.DataFrame.from_dict(velocities,orient='index',columns=['velocities']).reset_index(drop=True))
		out_spreadsheet.append(pd.DataFrame.from_dict(distance_ratios,orient='index',columns=['distance_ratios']).reset_index(drop=True))
		if animals[0]=='':
			pd.concat(out_spreadsheet,axis=1).to_excel(os.path.join(out_path,filename+'_distance_calculation.xlsx'),float_format='%.2f',index_label='ID/parameter')
			cv2.imwrite(os.path.join(out_path,filename+'_shortest_distance.jpg'),frame)
		else:
			pd.concat(out_spreadsheet,axis=1).to_excel(os.path.join(out_path,filename+'_'+animal+'_distance_calculation.xlsx'),float_format='%.2f',index_label='ID/parameter')
			cv2.imwrite(os.path.join(out_path,filename+'_'+animal+'_shortest_distance.jpg'),frame)

	print('Distances calculation completed!')


def sort_examples_from_csv(path_to_examples,out_path):

	'''
	This function is used to sort behavior examples generated by LabGym according to
	the manual labeling from other sources. It inputs the unsorted behavior examples
	generated by LabGym and a .csv file that stores the frame-wise behavior labels, 
	and sort the unsorted examples into different behavior categories (labels) that
	can be used to train a Categorizer in LabGym.
	
	path_to_examples: The folder that stores all unsorted examples generated by LabGym. 
	The .csv file should also be in this folder.
	out_path: the folder to store the sorted behavior examples
	'''

	path_to_csv=None
	path_to_animations=[]

	for i in os.listdir(path_to_examples):
		if i.endswith('.csv'):
			path_to_csv=os.path.join(path_to_examples,i)
		if i.endswith('.avi'):
			path_to_animations.append(os.path.join(path_to_examples,i))

	if path_to_csv is None or len(path_to_animations)==0:

		print('No .csv file or behavior example!')

	else:

		annotation=pd.read_csv(path_to_csv)
		for i in list(annotation.columns):
			if i!='Unnamed: 0':
				os.makedirs(os.path.join(out_path,i),exist_ok=True)

		for path_to_animation in path_to_animations:
			basename=os.path.basename(path_to_animation)
			path_to_pattern_image=os.path.splitext(path_to_animation)[0]+'.jpg'
			frame_index=int(basename.split('_len')[0].split('_')[-1])
			row_in_annotation=annotation.loc[frame_index]
			for behavior_name,score in row_in_annotation.items():
				if str(behavior_name)!='Unnamed: 0':
					if score==1 and os.path.exists(path_to_animation) and os.path.exists(path_to_pattern_image):
						shutil.move(path_to_animation,os.path.join(out_path,str(behavior_name),basename))
						shutil.move(path_to_pattern_image,os.path.join(out_path,str(behavior_name),os.path.splitext(basename)[0]+'.jpg'))

	print('Sorting completed!')


