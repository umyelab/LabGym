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



import os
import gc
import cv2
import numpy as np
import datetime
import scipy.ndimage as ndimage
from skimage import exposure
from tensorflow.keras.preprocessing.image import img_to_array
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.colorbar import ColorbarBase
import pandas as pd
import seaborn as sb
import functools
import operator



def extract_background(frames,stable_illumination=True,animal_vs_bg=0):

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
			if stable_illumination is True:
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


def extract_blob(frame,contour,channel=1):

	mask=np.zeros_like(frame)

	cv2.drawContours(mask,[contour],0,(255,255,255),-1)
	mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))

	x,y,w,h=cv2.boundingRect(contour)
	difference=int(abs(w-h)/2)+1

	if w>h:
		y_bt=max(y-difference-1,0)
		y_tp=min(y+h+difference+1,frame.shape[0])
		x_lf=max(x-1,0)
		x_rt=min(x+w+1,frame.shape[1])
	else:
		y_bt=max(y-1,0)
		y_tp=min(y+h+1,frame.shape[0])
		x_lf=max(x-difference-1,0)
		x_rt=min(x+w+difference+1,frame.shape[1])

	masked_frame=frame*(mask/255.0)
	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))

	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def extract_blob_background(frame,contours,contour=None,channel=1,background_free=False):

	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,contours)
	if background_free is True:
		mask=np.zeros_like(frame)
		cv2.drawContours(mask,[contour],0,(255,255,255),-1)
		masked_frame=frame*(mask/255.0)
	else:
		masked_frame=frame
	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))

	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def extract_blob_all(frame,y_bt,y_tp,x_lf,x_rt,contours=None,channel=1,background_free=False):

	if background_free is True:
		mask=np.zeros_like(frame)
		cv2.drawContours(mask,contours,-1,(255,255,255),-1)
		masked_frame=frame*(mask/255.0)
	else:
		masked_frame=frame
	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))

	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def get_inner(masked_frame_gray,contour):

	blur=cv2.GaussianBlur(masked_frame_gray,(3,3),0)
	edges=cv2.Canny(blur,20,75,apertureSize=3,L2gradient=True)
	cnts,_=cv2.findContours(edges,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)

	if len(cnts)>3:
		inner=sorted(cnts,key=cv2.contourArea,reverse=True)[2:]
	else:
		inner=[contour,contour]

	return inner


def contour_frame(frame,animal_number,background,background_low,background_high,delta,contour_area,animal_vs_bg=0,include_bodyparts=False,animation_analyzer=False,channel=1,kernel=5):

	if animal_vs_bg==1:
		frame=np.uint8(255-frame)

	if np.mean(frame)<np.mean(background)/delta:
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame,background_low)
		else:
			foreground=cv2.subtract(frame,background_low)
	elif np.mean(frame)>delta*np.mean(background):
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame,background_high)
		else:
			foreground=cv2.subtract(frame,background_high)
	else:
		if animal_vs_bg==2:
			foreground=cv2.absdiff(frame,background)
		else:
			foreground=cv2.subtract(frame,background)
			
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
	blobs=[]

	if animal_number>1:
		for i in cnts:
			if contour_area*0.2<cv2.contourArea(i)<contour_area*1.5:
				contours.append(i)
		contours=sorted(contours,key=cv2.contourArea)[-animal_number:]
	else:
		contours=[sorted(cnts,key=cv2.contourArea,reverse=True)[0]]

	if len(contours)>0:
		for i in contours:
			centers.append((int(cv2.moments(i)['m10']/cv2.moments(i)['m00']),int(cv2.moments(i)['m01']/cv2.moments(i)['m00'])))
			(_,_),(w,h),_=cv2.minAreaRect(i)
			heights.append(max(w,h))
			if include_bodyparts is True:
				mask=np.zeros_like(frame)
				cv2.drawContours(mask,[i],0,(255,255,255),-1)
				mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
				masked_frame=frame*(mask/255)
				gray=cv2.cvtColor(np.uint8(masked_frame),cv2.COLOR_BGR2GRAY)
				inners.append(get_inner(gray,i))
			if animation_analyzer is True:
				blobs.append(extract_blob(frame,i,channel=channel))

	return (contours,centers,heights,inners,blobs)


def generate_patternimage(frame,outlines,inners=None,std=0):

	if inners is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)

	background_outlines=np.zeros_like(frame)

	if std>0:
		backgrounds_std=[]

	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,outlines)

	length=len(outlines)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outline in enumerate(outlines):

		if outline is not None:

			if std>0:
				background_std=np.zeros_like(frame)
				if inners is not None:
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

	if std>0:
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)

		inners_image[std_image<std]=0

	if inners is not None:
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def generate_patternimage_all(frame,y_bt,y_tp,x_lf,x_rt,outlines_list,inners_list,std=0):

	inners_length=len(inners_list[0])

	if inners_length>0:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)

	background_outlines=np.zeros_like(frame)

	if std>0:
		backgrounds_std=[]

	length=len(outlines_list)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outlines in enumerate(outlines_list):

		if std>0:
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

		if inners_length>0:
			cv2.drawContours(background_outers,outlines,-1,(255,255,255),int(2*p_size))

	outlines_image=background_outlines[y_bt:y_tp,x_lf:x_rt]

	if inners_length>0:
		inners_image=background_inners[y_bt:y_tp,x_lf:x_rt]
		outers_image=background_outers[y_bt:y_tp,x_lf:x_rt]
		inners_image=cv2.subtract(inners_image,outers_image)

	if std>0:
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)

		inners_image[std_image<std]=0

	if inners_length>0:
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def generate_patternimage_interact(frame,outlines,other_outlines,inners=None,other_inners=None,std=0):

	total_outlines=functools.reduce(operator.iconcat,other_outlines,[])
	total_outlines+=outlines
	(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,total_outlines)

	if inners is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)

	background_outlines=np.zeros_like(frame)

	if std>0:
		backgrounds_std=[]

	length=len(outlines)
	p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

	for n,outline in enumerate(outlines):

		other_outline=other_outlines[n]
		if len(other_outline)>0:
			if other_outline[0] is not None:
				cv2.drawContours(background_outlines,other_outline,-1,(150,150,150),p_size)

		if outline is not None:

			if inners is not None:
				inner=inners[n]
				other_inner=functools.reduce(operator.iconcat,other_inners[n],[])
				if other_inner is not None:
					cv2.drawContours(background_inners,other_inner,-1,(150,150,150),p_size)
				if std>0:
					background_std=np.zeros_like(frame)
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
				if other_outline[0] is not None:
					cv2.drawContours(background_outers,other_outline,-1,(150,150,150),int(2*p_size))

	outlines_image=background_outlines[y_bt:y_tp,x_lf:x_rt]

	if inners is not None:
		inners_image=background_inners[y_bt:y_tp,x_lf:x_rt]
		outers_image=background_outers[y_bt:y_tp,x_lf:x_rt]
		inners_image=cv2.subtract(inners_image,outers_image)

	if std>0:
		backgrounds_std=np.array(backgrounds_std,dtype='float32')
		std_images=backgrounds_std[:,y_bt:y_tp,x_lf:x_rt]
		std_image=std_images.std(0)

		inners_image[std_image<std]=0

	if inners is not None:
		pattern_image=cv2.add(inners_image,outlines_image)
	else:
		pattern_image=outlines_image

	return pattern_image


def plot_evnets(result_path,event_probability,time_points,names_and_colors,behavior_to_annotate,width=0,height=0):

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
	
	for behavior_name in behavior_to_annotate:

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
		# no ticks
		#ax.tick_params(axis='both',which='both',length=0)
	
	plt.savefig(os.path.join(result_path,'behaviors_plot.png'))

	for behavior_name in behavior_to_annotate: 

		colorbar_fig=plt.figure(figsize=(5,1))
		ax=colorbar_fig.add_axes([0,1,1,1])
		colorbar=ColorbarBase(ax,orientation='horizontal',cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),norm=Normalize(vmin=0,vmax=1),ticks=[])
		colorbar.outline.set_linewidth(0)
			
		plt.savefig(os.path.join(result_path,behavior_name+'_colorbar.png'),bbox_inches='tight')
		plt.close()

	plt.close('all')

	print('The raster plot stored in: '+str(result_path))


def extract_frames(path_to_video,out_path,framewidth=None,start_t=0,duration=0,skip_redundant=1000):

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


def preprocess_video(path_to_video,out_folder,trim_video=False,time_windows=[[0,10]],enhance_contrast=True,contrast=1.0,crop_frame=True,left=0,right=0,top=0,bottom=0):

	capture=cv2.VideoCapture(path_to_video)
	name=os.path.basename(path_to_video).split('.')[0]
	writer=None
	fps=round(capture.get(cv2.CAP_PROP_FPS))
	frame_count=1

	while True:

		ret,frame=capture.read()
		if frame is None:
			break

		t=frame_count/fps

		if crop_frame is True:
			frame=frame[top:bottom,left:right,:]

		if enhance_contrast is True:
			frame=frame*contrast
			frame[frame>255]=255
			frame=np.uint8(frame)

		(h,w)=frame.shape[:2]

		if trim_video is True:
			added_name=''
			for i in time_windows:
				added_name+='_'+str(i[0])+'-'+str(i[1])
			if writer is None:
				writer=cv2.VideoWriter(os.path.join(out_folder,name+added_name+'_processed.avi'),cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h),True)
			for i in time_windows:
				if float(i[0])<=t<=float(i[1]):
					writer.write(np.uint8(frame))
		else:
			if writer is None:
				writer=cv2.VideoWriter(os.path.join(out_folder,name+'_processed.avi'),cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h),True)
			writer.write(np.uint8(frame))

		frame_count+=1

	writer.release()
	capture.release()

	print('The processed video(s) stored in: '+out_folder)


