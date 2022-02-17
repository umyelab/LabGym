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
from collections import OrderedDict
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.colorbar import ColorbarBase
import pandas as pd
import seaborn as sb



# extract static background
def extract_background(frames,minimum=0,invert=0):

	# frame_min: the first frame
	# minimum: if 0, use minimum, otherwise use stable value detector for background extraction
	# invert: if 0, animals brighter than the background
	#         if 1, invert the pixel value (for animals darker than the background)
	#         if 2, use absdiff

	if len(frames)>10:
		frames=frames[4:-4]
	len_frames=len(frames)
	
	if len_frames<=1:
		background=None
	else:
		frames=np.array(frames,dtype='float32')
		if invert==2:
			background=np.uint8(frames.mean(0))
		else:
			if minimum==0:
				if invert==1:
					background=np.uint8(frames.max(0))
				else:
					background=np.uint8(frames.min(0))
			else:
				if len_frames>105:
					frames_mean=[]
					check_frames=[]
					n=0
					while n<len_frames-101:
						frames_mean.append(frames[n:n+100].mean(0))
						if invert==1:
							frames_inv=255-frames
							check_frames.append(frames_inv[n:n+100].mean(0)+frames_inv[n:n+100].std(0))
						else:
							check_frames.append(frames[n:n+100].mean(0)+frames[n:n+100].std(0))
						n+=30
					frames_mean=np.array(frames_mean,dtype='float32')
					check_frames=np.array(check_frames,dtype='float32')
					background=np.uint8(np.take_along_axis(frames_mean,np.argsort(check_frames,axis=0),axis=0)[0])
					del frames_mean
					del check_frames
					gc.collect()
				else:
					if invert==1:
						background=np.uint8(frames.max(0))
					else:
						background=np.uint8(frames.min(0))
	
	return background


# estimate some constants that can be used in anlysis, need to import background extraction
def estimate_constants(path_to_video,delta,animal_number,framewidth=None,method=0,minimum=0,ex_start=0,ex_end=None,
	es_start=0,es_end=None,invert=0,path_background=None):

	# delta: an estimated fold change of the light intensity (normally about 1.2)
	# framewidth: width dimension to resize
	# method: threshold animal by:
	#       0--subtracting static background
	#       1--basic threshold
	#       2--edge detection
	# minimum: if 0, use minimum, otherwise use stable value detector for background extraction
	# ex_start: the start time point for background extraction
	# ex_end: the end time point for background extraction, if None, use the entire video
	# es_start: the start time point for estimation of animal contour area
	# es_end: the end time point for estimation of animal contour area, if None, use the entire video
	# invert: if 0, animals brighter than the background
	#         if 1, invert the pixel value (for animals darker than the background)
	#         if 2, use both
	# path_background: if not None, load backgrounds (need to put the background images under the name
	#                  'background.jpg' and 'stim_background.jpg' in the 'path_background' path)

	fps=mv.VideoFileClip(path_to_video).fps
	frame_min=None
	stim_t=2

	# if using background subtraction
	if method==0:

		if path_background is None:

			print('Extracting static background...')

			if ex_start>=mv.VideoFileClip(path_to_video).duration:
				print('The beginning time for background extraction exceeds the duration of the video!')
				print('Will use the beginning of the video as the beginning time for background extraction!')
				ex_start=0
			if ex_start==ex_end:
				ex_end=ex_start+1

			if es_start>=mv.VideoFileClip(path_to_video).duration:
				print('The beginning time for estimating animal contours exceeds the duration of the video!')
				print('Will use the beginning of the video as the beginning time for estimation!')
				es_start=0
			if es_start==es_end:
				es_end=es_start+1

			capture=cv2.VideoCapture(path_to_video)
		
			# initiate all parameters
			frames=[]
			stim_frames=[]
			frame_count=1
			backgrounds=[]
			stim_backgrounds=[]

			# store frames
			while True:

				retval,frame=capture.read()
				if frame is None:
					break

				if ex_end is not None:
					if frame_count>=ex_end*fps:
						break

				if frame_count>=ex_start*fps:
					if framewidth is not None:
						frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),
							interpolation=cv2.INTER_AREA)
					if frame_min is None:
						frame_min=frame
						frames.append(frame)
					else:
						if np.mean(frame)>delta*np.mean(frame_min):
							stim_t=frame_count/fps
							stim_frames.append(frame)
						else:
							frames.append(frame)

				frame_count+=1

				if len(frames)==1500:
					background=extract_background(frames,minimum=minimum,invert=invert)
					del frames
					gc.collect()
					frames=[]
					backgrounds.append(background)

					if len(backgrounds)==1500:
						backgrounds=np.array(backgrounds,dtype='float32')
						if invert==1:
							background=np.uint8(backgrounds.max(0))
						else:
							background=np.uint8(backgrounds.min(0))
						del backgrounds
						gc.collect()
						backgrounds=[]
						backgrounds.append(background)

				if len(stim_frames)==1500:
					stim_background=extract_background(stim_frames,minimum=minimum,invert=invert)
					del stim_frames
					gc.collect()
					stim_frames=[]
					stim_backgrounds.append(stim_background)

					if len(stim_backgrounds)==1500:
						stim_backgrounds=np.array(stim_backgrounds,dtype='float32')
						if invert==1:
							stim_background=np.uint8(stim_backgrounds.max(0))
						else:
							stim_background=np.uint8(stim_backgrounds.min(0))
						del stim_backgrounds
						gc.collect()
						stim_backgrounds=[]
						stim_backgrounds.append(stim_background)

			capture.release()

			if len(backgrounds)>0:
				if len(frames)>1000:
					background=extract_background(frames,minimum=minimum,invert=invert)
					backgrounds.append(background)
				if len(backgrounds)==1:
					background=backgrounds[0]
				else:
					backgrounds=np.array(backgrounds,dtype='float32')
					if invert==1:
						background=np.uint8(backgrounds.max(0))
					else:
						background=np.uint8(backgrounds.min(0))
			else:
				background=extract_background(frames,minimum=minimum,invert=invert)

			if len(stim_backgrounds)>0:
				if len(stim_frames)>1000:
					stim_background=extract_background(stim_frames,minimum=minimum,invert=invert)
					stim_backgrounds.append(stim_background)
				if len(stim_backgrounds)==1:
					stim_background=stim_backgrounds[0]
				else:
					stim_backgrounds=np.array(stim_backgrounds,dtype='float32')
					if invert==1:
						stim_background=np.uint8(stim_backgrounds.max(0))
					else:
						stim_background=np.uint8(stim_backgrounds.min(0))
			else:
				stim_background=extract_background(stim_frames,minimum=minimum,invert=invert)

			if background is None:
				background=frame_min
			if stim_background is None:
				stim_background=background

			print('Background extraction completed!')

		else:

			background=cv2.imread(os.path.join(path_background,'background.jpg'))
			stim_background=cv2.imread(os.path.join(path_background,'stim_background.jpg'))
			if framewidth is not None:
				frameheight=int(background.shape[0]*framewidth/background.shape[1])
				background=cv2.resize(background,(framewidth,frameheight),interpolation=cv2.INTER_AREA)
				stim_background=cv2.resize(stim_background,(framewidth,frameheight),interpolation=cv2.INTER_AREA)

	print('Estimating animal size...')
	print(datetime.datetime.now())

	if delta<10000:
		
		# if no background extraction or manually set the start time for background extraction, re-compute stim_t
		if method!=0 or ex_start!=0 or path_background is not None:

			capture=cv2.VideoCapture(path_to_video)
			frame_count=1

			while True:

				retval,frame=capture.read()
				if frame is None:
					break

				if framewidth is not None:
					frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),
						interpolation=cv2.INTER_AREA)

				if frame_min is None:
					frame_min=frame
				else:
					if np.mean(frame)>delta*np.mean(frame_min):
						stim_t=frame_count/fps
						break

				frame_count+=1

			capture.release()

	if method!=0:
		background=stim_background=frame_min

	# estimate animal contour area
	capture=cv2.VideoCapture(path_to_video)
	total_contour_area=[]
	frame_count=1
	min_area=(background.shape[1]/200)*(background.shape[0]/200)
	max_area=(background.shape[1]*background.shape[0])*2/3

	if invert==1:
		background_estimation=np.uint8(255-background)
	else:
		background_estimation=background

	while True:
		retval,frame=capture.read()
		if frame_min is None:
			frame_min=frame
		if frame is None:
			break
		if es_end is not None:
			if frame_count>=es_end*fps:
				break

		if frame_count>=es_start*fps:

			if framewidth is not None:
				frame=cv2.resize(frame,(framewidth,int(frame.shape[0]*framewidth/frame.shape[1])),
					interpolation=cv2.INTER_AREA)

			if invert==1:
				frame=np.uint8(255-frame)

			contour_area=0

			# exlude stimulation frames and find contours
			if np.mean(frame)<delta*np.mean(frame_min):
				if method==0:
					if invert==2:
						foreground=cv2.absdiff(frame,background_estimation)
					else:
						foreground=cv2.subtract(frame,background_estimation)
					foreground=cv2.morphologyEx(foreground,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
					foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
					thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
				elif method==1:
					contrast=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
					contrast=cv2.morphologyEx(cv2.cvtColor(contrast,cv2.COLOR_BGR2GRAY),
						cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
					thred=cv2.adaptiveThreshold(contrast,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,-2)
				elif method==2:
					contrast=cv2.cvtColor(np.uint8(exposure.rescale_intensity(frame,out_range=(0,255))),
						cv2.COLOR_BGR2GRAY)
					thred=cv2.Canny(cv2.GaussianBlur(contrast,(3,3),0),40,120,apertureSize=3,L2gradient=True)
					thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
				contours,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

				# if using edge detection
				if method==2:
					cts=contours
					contours=[]
					gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
					bg=np.zeros_like(gray)
					for i in cts:
						cv2.drawContours(bg,[i],0,(255,255,255),-1)
					cnts,_=cv2.findContours(bg,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
					for i in cnts:
						contours.append(i)

				# add contour areas of individual animals
				for i in contours:
					if min_area<cv2.contourArea(i)<max_area:
						contour_area+=cv2.contourArea(i)
				# add to total contour area
				total_contour_area.append(contour_area)

		frame_count+=1

	capture.release()

	print('Estimation completed!')

	if len(total_contour_area)>0:
		if animal_number==0:
			print('Animal number is 0. Please check animal number!')
			animal_area=1
		else:
			animal_area=(sum(total_contour_area)/len(total_contour_area))/animal_number
	else:
		print('No object!')
		animal_area=1

	print('Single animal size: '+str(animal_area))

	return (background,stim_background,stim_t,animal_area)


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


# extract a blob for an animal
def extract_blob(frame,animal_contour,y_bt=0,y_tp=0,x_lf=0,x_rt=0,analyze=0,background_free=0,channel=1):

	# analyze: if not 0, generate data
	# background_free: if 0, do not include background in animations
	# channel: if 1, gray scale

	if background_free==0:

		mask=np.zeros_like(frame)
		cv2.drawContours(mask,[animal_contour],0,(255,255,255),-1)
		mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))

		if analyze==0:
			x,y,w,h=cv2.boundingRect(animal_contour)
			difference=int(abs(w-h)/2)+1
			# form a square blob
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


# find the contours in each frame
def contour_frame(frame,animal_number,entangle_number,background,stim_background,delta,contour_area,
	method=1,invert=0,inner_code=1):

	# entangle_number: the number of animal allowed to be entangled
	# delta: the light intensity increase when apply optogenetic stimulation
	# contour_area: estimated area of an individual contour	
	# method: threshold contour by:
	#         0--subtracting static background
	#         1--basic threshold
	#         2--edge detection
	# invert: if 0, animals brighter than the background
	#         if 1, invert the pixel value (for animals darker than the background)
	#         if 2, use absdiff
	# inner_code: if 0, include inner contours of animal body parts in pattern images, else not
	
	if invert==1:
		frame=np.uint8(255-frame)

	if method==0:
		if np.mean(frame)>delta*np.mean(background):
			if invert==2:
				foreground=cv2.absdiff(frame,stim_background)
			else:
				foreground=cv2.subtract(frame,stim_background)
		else:
			if invert==2:
				foreground=cv2.absdiff(frame,background)
			else:
				foreground=cv2.subtract(frame,background)
		foreground=cv2.morphologyEx(foreground,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
		foreground=cv2.cvtColor(foreground,cv2.COLOR_BGR2GRAY)
		thred=cv2.threshold(foreground,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
		
	elif method==1:
		contrast=cv2.cvtColor(np.uint8(exposure.rescale_intensity(frame,out_range=(0,255))),cv2.COLOR_BGR2GRAY)
		contrast=cv2.morphologyEx(contrast,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
		thred=cv2.adaptiveThreshold(contrast,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,-2)

	elif method==2:
		contrast=cv2.cvtColor(np.uint8(exposure.rescale_intensity(frame,out_range=(0,255))),cv2.COLOR_BGR2GRAY)
		thred=cv2.Canny(cv2.GaussianBlur(contrast,(3,3),0),40,120,apertureSize=3,L2gradient=True)
		thred=cv2.morphologyEx(thred,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))

	cnts,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

	# exclude too large or too small contours
	contours=[]
	
	for i in cnts:
		if animal_number>1:
			if contour_area*0.5<cv2.contourArea(i)<contour_area*(entangle_number+0.8):
				contours.append(i)
		else:
			if contour_area*0.2<cv2.contourArea(i)<contour_area*2.5:
				contours.append(i)

	# if using edge detection
	if method==2:
		cts=contours
		contours=[]
		gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
		bg=np.zeros_like(gray)
		for i in cts:
			cv2.drawContours(bg,[i],0,(255,255,255),-1)
		cnts,_=cv2.findContours(bg,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
		for i in cnts:
			contours.append(i)

	# if 0, include inner contours of animal body parts in pattern images
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


# extract some common contour parameters for analysis
def get_parameters(frame,contours):

	# store centers, angles, heights, widths
	new_contours=[]
	centers=[]
	angles=[]
	heights=[]
	widths=[]

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
		width=min(w,h)

		heights.append(height)
		widths.append(width)

		n+=1

	return (new_contours,centers,angles,heights,widths)


# concatenate sets of contours (body parts and outlines, color indicating their sequence) into a square blob
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

		print('No contours!')
		return (background_outlines,(0,0,0,0))

	else:

		# determine the pixel size for drawing the contours
		p_size=int(max(abs(y_bt-y_tp),abs(x_lf-x_rt))/150+1)

		n=0

		while n<len(outlines):

			# evaluate the std between frames
			if std>0:
				background_std=np.zeros_like(frame)
				cv2.drawContours(background_std,inners[n],-1,(255,255,255),-1)
				backgrounds_std.append(background_std)

			# use different colors to indicate the sequence of contours
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


# plot behaviral event and probability as raster plot
def plot_evnets(result_path,event_probability,time_points,names_and_colors,to_include,width=0,height=0):

	# names_and_colors: the behavior names and their representing colors
	# to_include: the behaviors selected for annotation
	# width/height: size for the raster plot figure

	print('Exporting raster plot for behaviors...')
	print(datetime.datetime.now())

	# define width and height of the figure
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
	
	# plot all selected behavioral events
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
		dataframe=pd.DataFrame(all_data,columns=time_points)

		heatmap=sb.heatmap(dataframe,mask=masks,xticklabels=x_intvl,
			cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),cbar=False,
			vmin=0,vmax=1)
		heatmap.set_xticklabels(heatmap.get_xticklabels(),rotation=90) 
		# no ticks
		#ax.tick_params(axis='both',which='both',length=0)
	
	plt.savefig(os.path.join(result_path,'behaviors_plot.png'))

	# plot all colorbars
	for behavior_name in to_include: 

		colorbar_fig=plt.figure(figsize=(5,1))
		ax=colorbar_fig.add_axes([0,1,1,1])
		colorbar=ColorbarBase(ax,orientation='horizontal',
			cmap=LinearSegmentedColormap.from_list('',names_and_colors[behavior_name]),
			norm=Normalize(vmin=0,vmax=1),ticks=[])
		colorbar.outline.set_linewidth(0)
			
		plt.savefig(os.path.join(result_path,behavior_name+'_colorbar.png'),bbox_inches='tight')

	print('Behavioral events stored in: '+str(result_path))





