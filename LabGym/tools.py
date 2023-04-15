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
import moviepy.editor as mv
import scipy.ndimage as ndimage
from skimage import exposure
import math
from tensorflow.keras.preprocessing.image import img_to_array
from collections import OrderedDict,deque
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.colorbar import ColorbarBase
import pandas as pd
import seaborn as sb



def extract_background(frames,minimum=0,invert=0):

	# frame_initial: the first frame
	# minimum: 0: use minimum, otherwise use stable value detector for background extraction
	# invert: 0: animals brighter than the background; 1: invert the pixel value (for animals darker than the background); 2: use absdiff

	len_frames=len(frames)
	
	if len_frames<=3:
		background=None
	else:
		frames=np.array(frames,dtype='float32')
		if invert==2:
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
			if minimum==0:
				if invert==1:
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
						if invert==1:
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
					if invert==1:
						background=np.uint8(frames.max(0))
					else:
						background=np.uint8(frames.min(0))
	
	return background


def estimate_constants(path_to_video,delta,animal_number,framewidth=None,minimum=0,ex_start=0,ex_end=None,t=None,duration=10,invert=0,path_background=None):

	# delta: an estimated fold change of the light intensity (normally about 1.2)
	# framewidth: width dimension to resize
	# ex_start: the start time point for background extraction
	# ex_end: the end time point for background extraction, if None, use the entire video
	# t: analysis start time
	# path_background: if not None, load backgrounds (need to put the background images under the name 'background.jpg', 'background_low.jpg' and 'background_high.jpg' in the 'path_background' path)

	fps=mv.VideoFileClip(path_to_video).fps
	frame_initial=None
	stim_t=None
	kernel=5

	if path_background is None:

		print('Extracting the static background...')

		if ex_start>=mv.VideoFileClip(path_to_video).duration:
			print('The beginning time for background extraction is later than the end of the video!')
			print('Will use the 1st second of the video as the beginning time for background extraction!')
			ex_start=0
		if ex_start==ex_end:
			ex_end=ex_start+1

		capture=cv2.VideoCapture(path_to_video)
		
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
					frame_initial=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

			if frame_number>=ex_start*fps:

				if framewidth is not None:
					frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

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
				background=extract_background(frames,minimum=minimum,invert=invert)
				backgrounds.append(background)

			if frame_low_count==1001:
				frame_low_count=1
				background_low=extract_background(frames_low,minimum=minimum,invert=invert)
				backgrounds_low.append(background_low)

			if frame_high_count==1001:
				frame_high_count=1
				background_high=extract_background(frames_high,minimum=minimum,invert=invert)
				backgrounds_high.append(background_high)

			frame_number+=1

		capture.release()

		if len(backgrounds)>0:
			if frame_count>600:
				background=extract_background(frames,minimum=minimum,invert=invert)
				del frames
				gc.collect()
				backgrounds.append(background)
			if len(backgrounds)==1:
				background=backgrounds[0]
			else:
				backgrounds=np.array(backgrounds,dtype='float32')
				if invert==1:
					background=np.uint8(backgrounds.max(0))
				elif invert==2:
					background=np.uint8(np.median(backgrounds,axis=0))
				else:
					background=np.uint8(backgrounds.min(0))
				del backgrounds
				gc.collect()
		else:
			background=extract_background(frames,minimum=minimum,invert=invert)
			del frames
			gc.collect()
		

		if len(backgrounds_low)>0:
			if frame_low_count>600:
				background_low=extract_background(frames_low,minimum=minimum,invert=invert)
				del frames_low
				gc.collect()
				backgrounds_low.append(background_low)
			if len(backgrounds_low)==1:
				background_low=backgrounds_low[0]
			else:
				backgrounds_low=np.array(backgrounds_low,dtype='float32')
				if invert==1:
					background_low=np.uint8(backgrounds_low.max(0))
				elif invert==2:
					background_low=np.uint8(np.median(backgrounds_low,axis=0))
				else:
					background_low=np.uint8(backgrounds_low.min(0))
				del backgrounds_low
				gc.collect()
		else:
			background_low=extract_background(frames_low,minimum=minimum,invert=invert)
			del frames_low
			gc.collect()

		if len(backgrounds_high)>0:
			if frame_high_count>600:
				background_high=extract_background(frames_high,minimum=minimum,invert=invert)
				del frames_high
				gc.collect()
				backgrounds_high.append(background_high)
			if len(backgrounds_high)==1:
				background_high=backgrounds_high[0]
			else:
				backgrounds_high=np.array(backgrounds_high,dtype='float32')
				if invert==1:
					background_high=np.uint8(backgrounds_high.max(0))
				elif invert==2:
					background_high=np.uint8(np.median(backgrounds_high,axis=0))
				else:
					background_high=np.uint8(backgrounds_high.min(0))
				del backgrounds_high
				gc.collect()
		else:
			background_high=extract_background(frames_high,minimum=minimum,invert=invert)
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
			frameheight=int(background.shape[0]*framewidth/background.shape[1])
			background=cv2.resize(background,(framewidth,frameheight),interpolation=cv2.INTER_AREA)
			background_low=cv2.resize(background_low,(framewidth,frameheight),interpolation=cv2.INTER_AREA)
			background_high=cv2.resize(background_high,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

		frame_initial=background

	if min(frame_initial.shape[0],frame_initial.shape[1])/animal_number<250:
		kernel=3
	elif min(frame_initial.shape[0],frame_initial.shape[1])/animal_number<500:
		kernel=5
	elif min(frame_initial.shape[0],frame_initial.shape[1])/animal_number<1000:
		kernel=7
	elif min(frame_initial.shape[0],frame_initial.shape[1])/animal_number<1500:
		kernel=9
	else:
		kernel=11

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
					frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

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

	if invert==1:
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
				frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

			if invert==1:
				frame=np.uint8(255-frame)

			contour_area=0

			if np.mean(frame)<np.mean(frame_initial)/delta:
				if invert==2:
					foreground=cv2.absdiff(frame,background_low_estimation)
				else:
					foreground=cv2.subtract(frame,background_low_estimation)
			elif np.mean(frame)>delta*np.mean(frame_initial):
				if invert==2:
					foreground=cv2.absdiff(frame,background_high_estimation)
				else:
					foreground=cv2.subtract(frame,background_high_estimation)
			else:
				if invert==2:
					foreground=cv2.absdiff(frame,background_estimation)
				else:
					foreground=cv2.subtract(frame,background_estimation)
			foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
			thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
			thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
			if invert==2:
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

	return (background,background_low,background_high,stim_t,animal_area,kernel)


def crop_frame(frame,animal_contours):

	mask=np.zeros_like(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))

	for i in animal_contours:
		cv2.drawContours(mask,[i],0,(255,255,255),-1)
		
	mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
	cnts,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
	cnts=sorted(cnts,key=cv2.contourArea,reverse=True)
	x,y,w,h=cv2.boundingRect(cnts[0])

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

	return (y_bt,y_tp,x_lf,x_rt)


def extract_blob(frame,animal_contour,y_bt=0,y_tp=0,x_lf=0,x_rt=0,analyze=0,background_free=0,channel=1):

	# analyze: if not 0, generate data
	# background_free: 0: do not include background in animations
	# channel: 1: gray scale

	if background_free==0:

		mask=np.zeros_like(frame)
		cv2.drawContours(mask,[animal_contour],0,(255,255,255),-1)
		mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))

		if analyze==0:
			x,y,w,h=cv2.boundingRect(animal_contour)
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

	else:
		
		masked_frame=frame

	blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
	blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
	
	if channel==1:
		blob=cv2.cvtColor(blob,cv2.COLOR_BGR2GRAY)
		blob=img_to_array(blob)

	return blob


def contour_frame(frame,animal_number,background,background_low,background_high,delta,contour_area,invert=0,inner_code=1,kernel=5):

	# delta: the light intensity increase when apply optogenetic stimulation
	# contour_area: estimated area of an individual contour	
	# inner_code: 0: include inner contours of animal body parts in pattern images
	# kernel: the kernel size for morphological changes
	
	if invert==1:
		frame=np.uint8(255-frame)

	if np.mean(frame)<np.mean(background)/delta:
		if invert==2:
			foreground=cv2.absdiff(frame,background_low)
		else:
			foreground=cv2.subtract(frame,background_low)
	elif np.mean(frame)>delta*np.mean(background):
		if invert==2:
			foreground=cv2.absdiff(frame,background_high)
		else:
			foreground=cv2.subtract(frame,background_high)
	else:
		if invert==2:
			foreground=cv2.absdiff(frame,background)
		else:
			foreground=cv2.subtract(frame,background)
	foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
	thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
	thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
	if invert==2:
		kernel_erode=max(kernel-4,1)
		thred=cv2.erode(thred,np.ones((kernel_erode,kernel_erode),np.uint8))
	cnts,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

	contours=[]
	
	if animal_number>1:
		for i in cnts:
			if contour_area*0.2<cv2.contourArea(i)<contour_area*1.2:
				contours.append(i)
	else:
		contours=[sorted(cnts,key=cv2.contourArea,reverse=True)[0]]

	if inner_code==0:
		inners=[]
		n=0
		while n<len(contours):
			mask=np.zeros_like(frame)
			cv2.drawContours(mask,[contours[n]],0,(255,255,255),-1)
			mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
			masked_frame=frame*(mask/255)
			gray=cv2.cvtColor(np.uint8(masked_frame),cv2.COLOR_BGR2GRAY)
			blur=cv2.GaussianBlur(gray,(3,3),0)
			edges=cv2.Canny(blur,20,75,apertureSize=3,L2gradient=True)
			cnts,_=cv2.findContours(edges,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
			if len(cnts)>3:
				inners.append(sorted(cnts,key=cv2.contourArea,reverse=True)[2:])
			else:
				inners.append([contours[n],contours[n]])
			n+=1
	else:
		inners=None

	return (contours,inners)


def get_parameters(frame,contours):

	new_contours=[]
	centers=[]
	angles=[]
	heights=[]

	n=0
	
	while n<len(contours):

		new_contours.append(contours[n])

		cx=int(cv2.moments(contours[n])['m10']/cv2.moments(contours[n])['m00'])
		cy=int(cv2.moments(contours[n])['m01']/cv2.moments(contours[n])['m00'])

		centers.append((cx,cy))

		[vx,vy,x,y]=cv2.fitLine(contours[n],cv2.DIST_L2,0,0.01,0.01)
		angle=math.degrees(np.arctan(-float(vy)/vx))

		angles.append(angle)

		(_,_),(w,h),_=cv2.minAreaRect(contours[n])
		height=max(w,h)

		heights.append(height)

		n+=1

	return (new_contours,centers,angles,heights)


def concatenate_blobs(frame,outlines,y_bt,y_tp,x_lf,x_rt,inners=None,std=0):

	if inners is None:
		std=0

	background_outlines=np.zeros_like(frame)

	if inners is not None:
		background_inners=np.zeros_like(frame)
		background_outers=np.zeros_like(frame)

	if std>0:
		backgrounds_std=[]

	if len(outlines)==0:

		print('No animal detected!')
		return (background_outlines,(0,0,0,0))

	else:

		p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

		n=0

		while n<len(outlines):

			if std>0:
				background_std=np.zeros_like(frame)
				cv2.drawContours(background_std,inners[n],-1,(255,255,255),-1)
				backgrounds_std.append(background_std)

			if n<len(outlines)/4:
				d=n*int((255*4/len(outlines)))
				cv2.drawContours(background_outlines,[outlines[n]],0,(255,d,0),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,d,0),p_size)	
			elif n<len(outlines)/2:
				d=int((n-len(outlines)/4)*(255*4/len(outlines)))
				cv2.drawContours(background_outlines,[outlines[n]],0,(255,255,d),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,255,d),p_size)
			elif n<3*len(outlines)/4:
				d=int((n-len(outlines)/2)*(255*4/len(outlines)))
				cv2.drawContours(background_outlines,[outlines[n]],0,(255,255-d,255),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255,255-d,255),p_size)
			else:
				d=int((n-3*len(outlines)/4)*(255*4/len(outlines)))
				cv2.drawContours(background_outlines,[outlines[n]],0,(255-d,0,255),p_size)
				if inners is not None:
					cv2.drawContours(background_inners,inners[n],-1,(255-d,0,255),p_size)

			if inners is not None:
				cv2.drawContours(background_outers,[outlines[n]],0,(255,255,255),int(2*p_size))

			n+=1

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


def plot_evnets(result_path,event_probability,time_points,names_and_colors,to_include,width=0,height=0):

	# names_and_colors: the behavior names and their representing colors
	# to_include: the behaviors selected for annotation
	# width/height: size for the raster plot figure

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
		height=round(len(list(event_probability.keys()))/4)+1
		if height<3:
			height=3
		figure,ax=plt.subplots(figsize=(width,height))
		if height<=5:
			figure.subplots_adjust(bottom=0.25)
	
	for behavior_name in to_include:

		all_data=[]
		masks=[]

		for i in list(event_probability.keys()):
			data=[]
			mask=[]
			n=0
			while n<len(event_probability[i]):
				if event_probability[i][n][0]==behavior_name:
					data.append(event_probability[i][n][1])
					mask.append(0)
				else:
					data.append(-1)
					mask.append(True)
				n+=1

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

	for behavior_name in to_include: 

		colorbar_fig=plt.figure(figsize=(5,1))
		ax=colorbar_fig.add_axes([0,1,1,1])
		colorbar=ColorbarBase(ax,orientation='horizontal',cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),norm=Normalize(vmin=0,vmax=1),ticks=[])
		colorbar.outline.set_linewidth(0)
			
		plt.savefig(os.path.join(result_path,behavior_name+'_colorbar.png'),bbox_inches='tight')

	plt.close('all')

	print('The raster plot stored in: '+str(result_path))


def extract_frames(path_to_video,out_path,framewidth=None,start_t=0,duration=0,skip_redundant=1000):

	fps=mv.VideoFileClip(path_to_video).fps
	video_name=os.path.splitext(os.path.basename(path_to_video))[0]
	example_path=os.path.join(out_path,video_name)

	if not os.path.isdir(example_path):
		os.mkdir(example_path)
		print('Folder created: '+str(example_path))
	else:
		print('Folder already exists: '+str(example_path))

	if start_t>=mv.VideoFileClip(path_to_video).duration:
		print('The beginning time is later than the end of the video!')
		print('Will use the beginning of the video as the beginning time!')
		start_t=0
	if duration<=0:
		duration=mv.VideoFileClip(path_to_video).duration
	end_t=start_t+duration

	capture=cv2.VideoCapture(path_to_video)
		
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
					frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),interpolation=cv2.INTER_AREA)

				cv2.imwrite(os.path.join(example_path,video_name+'_'+str(frame_count_generate)+'.jpg'),frame)

			frame_count_generate+=1

		frame_count+=1

	capture.release()


