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
import matplotlib
matplotlib.use("Agg")
import os
import cv2
import datetime
import numpy as np
import matplotlib.pyplot as plt
import random
from collections import deque
from skimage import exposure,transform
from skimage.transform import AffineTransform
import scipy.ndimage as ndimage
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array,load_img
from tensorflow.keras.layers import Input,TimeDistributed,BatchNormalization,MaxPooling2D,Activation,ZeroPadding2D,Add
from tensorflow.keras.layers import Conv2D,Dropout,Flatten,Dense,LSTM,concatenate,AveragePooling2D,GlobalMaxPooling2D
from tensorflow.keras.models import Model,Sequential,load_model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.callbacks import ModelCheckpoint,EarlyStopping,ReduceLROnPlateau
from tensorflow.keras.utils import plot_model
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd



class Categorizers():

	def __init__(self):

		self.extension_image=('.png','.PNG','.jpeg','.JPEG','.jpg','.JPG','.tiff','.TIFF','.bmp','.BMP') # the image formats that LabGym can accept
		self.extension_video=('.avi','.mpg','.wmv','.mp4','.mkv','.m4v','.mov') # the video formats that LabGym can accept
		self.classnames=None # the behavior category names in the trained Categorizer


	def rename_label(self,file_path,new_path,resize=None):

		# file_path: the folder that stores the sorted, unprepared examples
		# new_path: the folder that stores all prepared examples, which can be directly used for training a Categorizer
		# resize: if not None, resize the frames in animations / pattern images to the target size

		folder_list=[i for i in os.listdir(file_path) if os.path.isdir(os.path.join(file_path,i))]

		if len(folder_list)<2:

			print('You need at least 2 categories of behaviors!')
			print('Preparation aborted!')

		else:

			print('Behavior names are: '+str(folder_list))
			previous_lenth=None
			imagedata=False

			for folder in folder_list:

				name_list=[i for i in os.listdir(os.path.join(file_path,folder)) if i.endswith('.avi')]

				if len(name_list)==0:
					name_list=[i for i in os.listdir(os.path.join(file_path,folder)) if i.endswith('.jpg')]
					imagedata=True
			
				for i in name_list:

					if imagedata is True:

						image=os.path.join(file_path,folder,i)
						new_image=os.path.join(new_path,str(name_list.index(i))+'_'+folder+'.jpg')
						image=cv2.imread(image)
						if resize is not None:
							image=cv2.resize(image,(resize,resize),interpolation=cv2.INTER_AREA)
						cv2.imwrite(new_image,image)

					else:

						animation=os.path.join(file_path,folder,i)
						pattern_image=os.path.join(file_path,folder,os.path.splitext(i)[0]+'.jpg')
						current_length=0

						new_animation=os.path.join(new_path,str(name_list.index(i))+'_'+folder+'.avi')
						new_pattern_image=os.path.join(new_path,str(name_list.index(i))+'_'+folder+'.jpg')
						writer=None
						capture=cv2.VideoCapture(animation)
						fps=round(capture.get(cv2.CAP_PROP_FPS))
						while True:
							retval,frame=capture.read()
							current_length+=1
							if frame is None:
								break
							if resize is not None:
								frame=cv2.resize(frame,(resize,resize),interpolation=cv2.INTER_AREA)
							if writer is None:
								(h,w)=frame.shape[:2]
								writer=cv2.VideoWriter(new_animation,cv2.VideoWriter_fourcc(*'MJPG'),fps,(w,h),True)
							writer.write(frame)
						capture.release()
						writer.release()
						pattern_image=cv2.imread(pattern_image)
						if resize is not None:
							pattern_image=cv2.resize(pattern_image,(resize,resize),interpolation=cv2.INTER_AREA)
						cv2.imwrite(new_pattern_image,pattern_image)
						if previous_lenth is None:
							previous_lenth=current_length
						else:
							if previous_lenth!=current_length:
								previous_lenth=current_length
								print('Inconsistent duration of animation detected at: '+str(i)+'. Check the duration of animations!')

			print('All prepared training examples stored in: '+str(new_path))


	def build_data(self,path_to_animations,dim_tconv=0,dim_conv=64,channel=1,time_step=15,aug_methods=[],background_free=True,behavior_mode=0):

		# path_to_animations: the folder that stores all the prepared training examples
		# dim_tconv: the input dimension of Animation Analyzer
		# dim_conv: the input dimension of Pattern Recognizer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# aug_methods: the augmentation methods that are used in training
		# background_free: whether the background is included in animations
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images

		animations=deque()
		pattern_images=deque()
		labels=deque()
		amount=0

		if len(aug_methods)==0:

			methods=['orig']

		else:

			remove=[]

			all_methods=['orig','del1','del2','rot1','rot2','rot3','rot4','flph','flpv','brih','bril','shrp','shrn','sclh','sclw','rot1_brih','rot1_bril','rot4_brih','rot4_bril','flph_brih','flph_bril','flpv_brih','flpv_bril',
			'del2_rot5_brii','del2_rot6_brii','del2_rot5_brid','del2_rot6_brid','del2_flph_brii','del2_flph_brid','del2_flpv_brii','del2_flpv_brid','flph_rot5_brii','flph_rot6_brii','flph_rot5_brid','flph_rot6_brid',
			'flpv_rot5_brii','flpv_rot6_brii','flpv_rot5_brid','flpv_rot6_brid','flph_shrp_brii','flph_shrn_brii','flph_shrp_brid','flph_shrn_brid','flpv_shrp_brii','flpv_shrn_brii','flpv_shrp_brid','flpv_shrn_brid']

			for i in all_methods:
				if 'random rotation' not in aug_methods:
					if 'rot' in i:
						remove.append(i)
				if 'horizontal flipping' not in aug_methods:
					if 'flph' in i:
						remove.append(i)
				if 'vertical flipping' not in aug_methods:
					if 'flpv' in i:
						remove.append(i)
				if 'random brightening' not in aug_methods:
					if 'brih' in i:
						remove.append(i)
				if 'random dimming' not in aug_methods:
					if 'bril' in i:
						remove.append(i)
				if 'random shearing' not in aug_methods:
					if 'shr' in i:
						remove.append(i)
				if 'random rescaling' not in aug_methods:
					if 'scl' in i:
						remove.append(i)
				if 'random deletion' not in aug_methods:
					if 'del' in i:
						remove.append(i)
				if 'exclude original' in aug_methods:
					remove.append('orig')

			methods=list(set(all_methods)-set(remove))

		for i in path_to_animations:

			name=os.path.splitext(os.path.basename(i))[0].split('_')[0]
			label=os.path.splitext(i)[0].split('_')[-1]
			path_to_pattern_image=os.path.splitext(i)[0]+'.jpg'
			
			random.shuffle(methods)

			for m in methods:

				if 'rot1' in m:
					angle=np.random.uniform(10,50)
				elif 'rot2' in m:
					angle=np.random.uniform(50,90)
				elif 'rot3' in m:
					angle=np.random.uniform(90,130)
				elif 'rot4' in m:
					angle=np.random.uniform(130,170)
				elif 'rot5' in m:
					angle=np.random.uniform(30,80)
				elif 'rot6' in m:
					angle=np.random.uniform(100,150)
				else:
					angle=None

				if 'flph' in m:
					code=1
				elif 'flpv' in m:
					code=0
				else:
					code=None

				if 'brih' in m:
					beta=np.random.uniform(30,80)
				elif 'brii' in m:
					beta=np.random.uniform(10,45)
				elif 'bril' in m:
					beta=np.random.uniform(-80,-30)
				elif 'brid' in m:
					beta=np.random.uniform(-45,10)
				else:
					beta=None

				if 'shrp' in m:
					shear=np.random.uniform(0.15,0.21)
				elif 'shrn' in m:
					shear=np.random.uniform(-0.21,-0.15)
				else:
					shear=None

				if 'sclh' in m:
					width=0
					scale=np.random.uniform(0.6,0.9)
				elif 'sclw' in m:
					width=1
					scale=np.random.uniform(0.6,0.9)
				else:
					scale=None

				if 'del1' in m:
					if time_step>=30:
						idx1=random.randint(0,round(time_step/3))
						idx2=random.randint(round(time_step/3)+1,round(time_step*2/3))
						to_delete=[idx1,idx2]
					else:
						to_delete=[random.randint(0,round(time_step/3))]
				elif 'del2' in m:
					to_delete=[random.randint(0,round(time_step/2)+1)]
				else:
					to_delete=None

				if dim_tconv!=0:

					capture=cv2.VideoCapture(i)
					animation=deque()
					frames=deque(maxlen=time_step)
					original_frame=None
					n=0

					while True:
						retval,frame=capture.read()
						if original_frame is None:
							original_frame=frame
						if frame is None:
							break
						frames.append(frame)

					frames_length=len(frames)
					if frames_length<time_step:
						for diff in range(time_step-frames_length):
							frames.append(np.zeros_like(original_frame))
						print('Inconsistent duration of animation detected at: '+str(i)+'.')
						print('Zero padding has been used, which may decrease the training accuracy.')

					for frame in frames:

						if to_delete is not None and n in to_delete:

							blob=np.zeros_like(original_frame)

						else:

							frame_contrast=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))

							if background_free is True:
								frame_gray=cv2.cvtColor(frame_contrast,cv2.COLOR_BGR2GRAY)
								thred=cv2.threshold(frame_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
								cnts,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
								if len(cnts)==0:
									blob=np.zeros_like(frame)
								else:
									if behavior_mode==0:
										contour=sorted(cnts,key=cv2.contourArea,reverse=True)[0]
										blob=extract_blob(frame,contour,channel=3)
									else:
										(y_bt,y_tp,x_lf,x_rt)=crop_frame(frame,cnts)
										blob=frame_contrast[y_bt:y_tp,x_lf:x_rt]
							else:
								blob=frame_contrast

							if code is not None:
								blob=cv2.flip(blob,code)

							if beta is not None:
								blob=blob.astype('float')
								if background_free is True:
									blob[blob>30]+=beta
								else:
									blob+=beta
								blob=np.uint8(np.clip(blob,0,255))

							if angle is not None:
								blob=ndimage.rotate(blob,angle,reshape=False,prefilter=False)

							if shear is not None:
								tf=AffineTransform(shear=shear)
								blob=transform.warp(blob,tf,order=1,preserve_range=True,mode='constant')

							if scale is not None:
								blob_black=np.zeros_like(blob)
								if width==0:
									blob_scl=cv2.resize(blob,(blob.shape[1],int(blob.shape[0]*scale)),interpolation=cv2.INTER_AREA)
								else:
									blob_scl=cv2.resize(blob,(int(blob.shape[1]*scale),blob.shape[0]),interpolation=cv2.INTER_AREA)
								blob_scl=img_to_array(blob_scl)
								x=(blob_black.shape[1]-blob_scl.shape[1])//2
								y=(blob_black.shape[0]-blob_scl.shape[0])//2
								blob_black[y:y+blob_scl.shape[0],x:x+blob_scl.shape[1]]=blob_scl
								blob=blob_black

						if channel==1:
							blob=cv2.cvtColor(np.uint8(blob),cv2.COLOR_BGR2GRAY)

						blob=cv2.resize(blob,(dim_tconv,dim_tconv),interpolation=cv2.INTER_AREA)
						blob=img_to_array(blob)
						animation.append(blob)

						n+=1

					capture.release()

					animations.append(np.array(animation))

				pattern_image=cv2.imread(path_to_pattern_image)

				if code is not None:
					pattern_image=cv2.flip(pattern_image,code)

				if behavior_mode==3:
					if beta is not None:
						if background_free is True:
							pattern_image_gray=cv2.cvtColor(pattern_image,cv2.COLOR_BGR2GRAY)
							thred=cv2.threshold(pattern_image_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
							cnts,_=cv2.findContours(thred,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
							if len(cnts)==0:
								pattern_image=np.zeros_like(pattern_image)
							else:
								contour=sorted(cnts,key=cv2.contourArea,reverse=True)[0]
								pattern_image=extract_blob(pattern_image,contour,channel=3)
							pattern_image=pattern_image.astype('float')
							pattern_image[pattern_image>30]+=beta
						else:
							pattern_image=pattern_image.astype('float')
							pattern_image+=beta
						pattern_image=np.uint8(np.clip(pattern_image,0,255))

				if angle is not None:
					pattern_image=ndimage.rotate(pattern_image,angle,reshape=False,prefilter=False)

				if shear is not None:
					tf=AffineTransform(shear=shear)
					pattern_image=transform.warp(pattern_image,tf,order=1,preserve_range=True,mode='constant')

				if scale is not None:
					pattern_image_black=np.zeros_like(pattern_image)
					if width==0:
						pattern_image_scl=cv2.resize(pattern_image,(pattern_image.shape[1],int(pattern_image.shape[0]*scale)),interpolation=cv2.INTER_AREA)
					else:
						pattern_image_scl=cv2.resize(pattern_image,(int(pattern_image.shape[1]*scale),pattern_image.shape[0]),interpolation=cv2.INTER_AREA)
					x=(pattern_image_black.shape[1]-pattern_image_scl.shape[1])//2
					y=(pattern_image_black.shape[0]-pattern_image_scl.shape[0])//2
					pattern_image_black[y:y+pattern_image_scl.shape[0],
					x:x+pattern_image_scl.shape[1],:]=pattern_image_scl
					pattern_image=pattern_image_black

				if behavior_mode==3:
					if channel==1:
						pattern_image=cv2.cvtColor(np.uint8(pattern_image),cv2.COLOR_BGR2GRAY)

				pattern_image=cv2.resize(pattern_image,(dim_conv,dim_conv),interpolation=cv2.INTER_AREA)
				pattern_images.append(img_to_array(pattern_image))

				labels.append(label)

				amount+=1
				if amount%10000==0:
					print('The augmented example amount: '+str(amount))
					print(datetime.datetime.now())

		if dim_tconv!=0:
			animations=np.array(animations,dtype='float32')/255.0
		pattern_images=np.array(pattern_images,dtype='float32')/255.0
		labels=np.array(labels)

		return animations,pattern_images,labels


	def simple_vgg(self,inputs,filters,classes=3,level=2,with_classifier=False):

		# inputs: the input tensor (w,h,c) of the neural network
		# filters: the number of nodes (neurons) in each layer
		# classes: the behavior category names (if with_classifier is True)
		# level: complexity level, determines how deep the neural network is
		# with_classifier: if True, the neural network can output classification probabilities

		if level<2:
			layers=[2]
		elif level<3:
			layers=[2,3]
		elif level<4:
			layers=[2,3,4]
		else:
			layers=[2,3,4,4]

		for i in layers:
			for n in range(i):
				if n==0:
					if layers.index(i)==0:
						x=Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu')(inputs)
						x=BatchNormalization()(x)
					else:
						x=Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu')(x)
						x=BatchNormalization()(x)
				else:
					x=Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu')(x)
					x=BatchNormalization()(x)
			x=MaxPooling2D(pool_size=(2,2))(x)
			filters=int(filters*2)

		x=Flatten()(x)

		if with_classifier is False:

			return x

		else:

			x=Dense(int(filters/2),activation='relu')(x)
			x=BatchNormalization()(x)
			x=Dropout(0.5)(x)
			if classes==2:
				x=Dense(1,activation='sigmoid')(x)
			else:
				x=Dense(classes,activation='softmax')(x)

			model=Model(inputs=inputs,outputs=x)
			#plot_model(model,'model.png',show_shapes=True)

			return model


	def simple_tvgg(self,inputs,filters,classes=3,level=2,with_classifier=False):

		# inputs: the input tensor (t,w,h,c) of the neural network
		# filters: the number of nodes (neurons) in each layer
		# classes: the behavior category names (if with_classifier is True)
		# level: complexity level, determines how deep the neural network is
		# with_classifier: if True, the neural network can output classification probabilities

		if level<2:
			layers=[2]
		elif level<3:
			layers=[2,3]
		elif level<4:
			layers=[2,3,4]
		else:
			layers=[2,3,4,4]

		for i in layers:
			for n in range(i):
				if n==0:
					if layers.index(i)==0:
						x=TimeDistributed(Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu'))(inputs)
						x=TimeDistributed(BatchNormalization())(x)
					else:
						x=TimeDistributed(Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu'))(x)
						x=TimeDistributed(BatchNormalization())(x)
				else:
					x=TimeDistributed(Conv2D(filters,kernel_size=(3,3),padding='same',activation='relu'))(x)
					x=TimeDistributed(BatchNormalization())(x)
			x=TimeDistributed(MaxPooling2D(pool_size=(2,2)))(x)
			filters=int(filters*2)

		x=TimeDistributed(Flatten())(x)
		x=LSTM(int(filters/2),return_sequences=False,return_state=False)(x)

		if with_classifier is False:

			return x

		else:

			x=Dense(int(filters/2),activation='relu')(x)
			x=BatchNormalization()(x)
			x=Dropout(0.5)(x)
			if classes==2:
				x=Dense(1,activation='sigmoid')(x)
			else:
				x=Dense(classes,activation='softmax')(x)

			model=Model(inputs=inputs,outputs=x)
			#plot_model(model,'model.png',show_shapes=True)

			return model


	def res_block(self,x,filters,strides=2,block=False,basic=True):

		# x: the output from the last layer
		# filters: the number of nodes (neurons) in each layer
		# strides: the strides in each layer
		# block: whether it's a block or shortcut
		# basic: whether it uses additional zeropadding and normalization

		shortcut=x

		if basic is True:

			x=ZeroPadding2D((1,1))(x)
			x=Conv2D(filters,(3,3),strides=(strides,strides))(x)

		else:

			x=Conv2D(filters,(1,1),strides=(strides,strides))(x)

		x=BatchNormalization()(x)
		x=Activation('relu')(x)

		x=ZeroPadding2D((1,1))(x)
		x=Conv2D(filters,(3,3),strides=(1,1))(x)
		x=BatchNormalization()(x)

		if basic is True:

			if block is False:
				shortcut=Conv2D(filters,(1,1),strides=(strides,strides))(shortcut)
				shortcut=BatchNormalization()(shortcut)

		else:

			x=Activation('relu')(x)
		
			x=Conv2D(int(filters*4),(1,1),strides=(1,1))(x)
			x=BatchNormalization()(x)

			if block is False:
				shortcut=Conv2D(filters*4,(1,1),strides=(strides,strides))(shortcut)
				shortcut=BatchNormalization()(shortcut)

		x=Add()([x,shortcut])
		x=Activation('relu')(x)

		return x


	def tres_block(self,x,filters,strides=2,block=False,basic=True):

		# x: the output from the last layer
		# filters: the number of nodes (neurons) in each layer
		# strides: the strides in each layer
		# block: whether it's a block or shortcut
		# basic: whether it uses additional zeropadding and normalization

		shortcut=x

		if basic is True:

			x=TimeDistributed(ZeroPadding2D((1,1)))(x)
			x=TimeDistributed(Conv2D(filters,(3,3),strides=(strides,strides)))(x)

		else:

			x=TimeDistributed(Conv2D(filters,(1,1),strides=(strides,strides)))(x)

		x=TimeDistributed(BatchNormalization())(x)
		x=TimeDistributed(Activation('relu'))(x)

		x=TimeDistributed(ZeroPadding2D((1,1)))(x)
		x=TimeDistributed(Conv2D(filters,(3,3),strides=(1,1)))(x)
		x=TimeDistributed(BatchNormalization())(x)

		if basic is True:

			if block is False:
				shortcut=TimeDistributed(Conv2D(filters,(1,1),strides=(strides,strides)))(shortcut)
				shortcut=TimeDistributed(BatchNormalization())(shortcut)

		else:

			x=TimeDistributed(Activation('relu'))(x)
		
			x=TimeDistributed(Conv2D(int(filters*4),(1,1),strides=(1,1)))(x)
			x=TimeDistributed(BatchNormalization())(x)

			if block is False:
				shortcut=TimeDistributed(Conv2D(int(filters*4),(1,1),strides=(strides,strides)))(shortcut)
				shortcut=TimeDistributed(BatchNormalization())(shortcut)

		x=Add()([x,shortcut])
		x=TimeDistributed(Activation('relu'))(x)

		return x


	def simple_resnet(self,inputs,filters,classes=3,level=5,with_classifier=False):

		# inputs: the input tensor (w,h,c) of the neural network
		# filters: the number of nodes (neurons) in each layer
		# classes: the behavior category names (if with_classifier is True)
		# level: complexity level, determines how deep the neural network is
		# with_classifier: if True, the neural network can output classification probabilities

		x=ZeroPadding2D((3,3))(inputs)
		x=Conv2D(filters,(5,5),strides=(2,2))(x)
		x=BatchNormalization()(x)
		x=Activation('relu')(x)
		x=MaxPooling2D((3,3),strides=(2,2))(x)

		if level<6:
			layers=[2,2,2,2]
			basic=True
		elif level<7:
			layers=[3,4,6,3]
			basic=True
		else:
			layers=[3,4,6,3]
			basic=False

		for i in layers:
			for n in range(i):
				if n==0:
					if layers.index(i)==0:
						x=self.res_block(x,filters,strides=1,block=False,basic=basic)
					else:
						x=self.res_block(x,filters,strides=2,block=False,basic=basic)
				else:
					x=self.res_block(x,filters,strides=1,block=True,basic=basic)
			filters=int(filters*2)

		x=AveragePooling2D((2,2))(x)
		x=Flatten()(x)

		if with_classifier is False:

			return x

		else:

			x=Dropout(0.5)(x)
			if classes==2:
				x=Dense(1,activation='sigmoid')(x)
			else:
				x=Dense(classes,activation='softmax')(x)

			model=Model(inputs=inputs,outputs=x)

			return model


	def simple_tresnet(self,inputs,filters,classes=3,level=5,with_classifier=False):

		# inputs: the input tensor (t,w,h,c) of the neural network
		# filters: the number of nodes (neurons) in each layer
		# classes: the behavior category names (if with_classifier is True)
		# level: complexity level, determines how deep the neural network is
		# with_classifier: if True, the neural network can output classification probabilities

		x=TimeDistributed(ZeroPadding2D((3,3)))(inputs)
		x=TimeDistributed(Conv2D(filters,(5,5),strides=(2,2)))(x)
		x=TimeDistributed(BatchNormalization())(x)
		x=TimeDistributed(Activation('relu'))(x)
		x=TimeDistributed(MaxPooling2D((3,3),strides=(2,2)))(x)

		if level<6:
			layers=[2,2,2,2]
			basic=True
		elif level<7:
			layers=[3,4,6,3]
			basic=True
		else:
			layers=[3,4,6,3]
			basic=False

		for i in layers:
			for n in range(i):
				if n==0:
					if layers.index(i)==0:
						x=self.tres_block(x,filters,strides=1,block=False,basic=basic)
					else:
						x=self.tres_block(x,filters,strides=2,block=False,basic=basic)
				else:
					x=self.tres_block(x,filters,strides=1,block=True,basic=basic)
			filters=int(filters*2)

		x=TimeDistributed(AveragePooling2D((2,2)))(x)
		x=TimeDistributed(Flatten())(x)

		if level==5:
			x=LSTM(1024,return_sequences=False,return_state=False)(x)
		elif level==6:
			x=LSTM(2048,return_sequences=False,return_state=False)(x)
		else:
			x=LSTM(4096,return_sequences=False,return_state=False)(x)
			
		if with_classifier is False:

			return x

		else:

			if level==5:
				x=Dense(1024,activation='relu')(x)
			elif level==6:
				x=Dense(2048,activation='relu')(x)
			else:
				x=Dense(4096,activation='relu')(x)
				
			x=Dropout(0.5)(x)
			if classes==2:
				x=Dense(1,activation='sigmoid')(x)
			else:
				x=Dense(classes,activation='softmax')(x)

			model=Model(inputs=inputs,outputs=x)

			return model


	def combined_network(self,time_step=15,dim_tconv=32,dim_conv=64,channel=1,classes=9,level_tconv=1,level_conv=2):

		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# dim_tconv: the input dimension of Animation Analyzer
		# dim_conv: the input dimension of Pattern Recognizer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# classes: the behavior category names
		# level_tconv: complexity level of Animation Analyzer, determines how deep the neural network is
		# level_conv: complexity level of Pattern Recognizer, determines how deep the neural network is

		animation_inputs=Input(shape=(time_step,dim_tconv,dim_tconv,channel))
		pattern_image_inputs=Input(shape=(dim_conv,dim_conv,3))

		filters_tconv=8
		filters_conv=8

		for i in range(round(dim_tconv/60)):
			filters_tconv=min(int(filters_tconv*2),64)
		
		for i in range(round(dim_conv/60)):
			filters_conv=min(int(filters_conv*2),64)

		if level_tconv<5:
			animation_feature=self.simple_tvgg(animation_inputs,filters_tconv,level=level_tconv,with_classifier=False)
		else:
			animation_feature=self.simple_tresnet(animation_inputs,filters_tconv,level=level_tconv,with_classifier=False)
		
		if level_conv<5:
			pattern_image_feature=self.simple_vgg(pattern_image_inputs,filters_conv,level=level_conv,with_classifier=False)
		else:
			pattern_image_feature=self.simple_resnet(pattern_image_inputs,filters_conv,level=level_conv,with_classifier=False)

		merged_features=concatenate([animation_feature,pattern_image_feature])

		nodes=32
		for i in range(max(level_tconv,level_conv)):
			nodes=int(nodes*2)
		outputs=Dense(nodes,activation='relu')(merged_features)
		outputs=BatchNormalization()(outputs)
		outputs=Dropout(0.5)(outputs)
		if classes==2:
			predictions=Dense(1,activation='sigmoid')(outputs)
		else:
			predictions=Dense(classes,activation='softmax')(outputs)

		model=Model(inputs=[animation_inputs,pattern_image_inputs],outputs=predictions)

		return model


	def train_pattern_recognizer(self,data_path,model_path,out_path=None,dim=64,channel=3,time_step=15,level=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension
		# channel: the input color channel, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation / pattern image, also the length of a behavior episode
		# level: complexity level, determines how deep the neural network is
		# aug_methods: the augmentation methods that are used in training
		# augvalid: whether augment the validation data as well
		# whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)

		inputs=Input(shape=(dim,dim,channel))

		print('Training the Categorizer w/ only Pattern Recognizer using the behavior examples in: '+str(data_path))

		files=[i for i in os.listdir(data_path) if i.endswith(self.extension_image)]

		path_files=[]
		labels=[]

		for i in files:
			path_file=os.path.join(data_path,i)
			path_files.append(path_file)
			labels.append(os.path.splitext(i)[0].split('_')[-1])

		labels=np.array(labels)
		lb=LabelBinarizer()
		labels=lb.fit_transform(labels)
		self.classnames=lb.classes_

		if len(list(self.classnames))<2:

			print('You need at least 2 categories of behaviors!')
			print('Training aborted!')

		else:

			print('Found behavior names: '+str(self.classnames))

			if include_bodyparts is True:
				inner_code=0
			else:
				inner_code=1

			if background_free is True:
				background_code=0
			else:
				background_code=1

			if behavior_mode>=3:
				time_step=std=0
				inner_code=1

			parameters={'classnames':list(self.classnames),'dim_conv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':0,'level_conv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

			(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

			print('Perform augmentation for the behavior examples...')
			print('This might take hours or days, depending on the capacity of your computer.')
			print(datetime.datetime.now())

			print('Start to augment training examples...')
			_,trainX,trainY=self.build_data(train_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			trainY=lb.fit_transform(trainY)
			print('Start to augment validation examples...')
			if augvalid is True:
				_,testX,testY=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			else:
				_,testX,testY=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,behavior_mode=behavior_mode)
			testY=lb.fit_transform(testY)

			with tf.device('CPU'):
				trainX=tf.convert_to_tensor(trainX)
				trainY=tf.convert_to_tensor(trainY)
				testX_tensor=tf.convert_to_tensor(testX)
				testY_tensor=tf.convert_to_tensor(testY)

			print('Training example shape : '+str(trainX.shape))
			print('Training label shape : '+str(trainY.shape))
			print('Validation example shape : '+str(testX.shape))
			print('Validation label shape : '+str(testY.shape))
			print(datetime.datetime.now())

			if trainX.shape[0]<5000:
				batch_size=8
			elif trainX.shape[0]<50000:
				batch_size=16
			else:
				batch_size=32

			if level<5:
				model=self.simple_vgg(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
			else:
				model=self.simple_resnet(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
			if len(self.classnames)==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=4,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=2,verbose=1,mode='min',min_learning_rate=1e-7)

			H=model.fit(trainX,trainY,batch_size=batch_size,validation_data=(testX_tensor,testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))

			try:
			
				predictions=model.predict(testX,batch_size=batch_size)

				if len(self.classnames)==2:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]]))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]],output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')
				
				plt.style.use('seaborn-bright')
				plt.figure()
				plt.plot(H.history['loss'],label='train_loss')
				plt.plot(H.history['val_loss'],label='val_loss')
				plt.plot(H.history['accuracy'],label='train_accuracy')
				plt.plot(H.history['val_accuracy'],label='val_accuracy')
				plt.title('Loss and Accuracy')
				plt.xlabel('Epoch')
				plt.ylabel('Loss/Accuracy')
				plt.legend(loc='center right')
				plt.savefig(os.path.join(model_path,'training_history.png'))
				if out_path is not None:
					plt.savefig(os.path.join(out_path,'training_history.png'))
					print('Training reports saved in: '+str(out_path))
				plt.close('all')

			except:

				pass


	def train_animation_analyzer(self,data_path,model_path,out_path=None,dim=64,channel=1,time_step=15,level=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension
		# channel: the input color channel, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# level: complexity level, determines how deep the neural network is
		# aug_methods: the augmentation methods that are used in training
		# augvalid: whether augment the validation data as well
		# whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)
		
		inputs=Input(shape=(time_step,dim,dim,channel))

		print('Training the Categorizer w/o Pattern Recognizer using the behavior examples in: '+str(data_path))

		files=[i for i in os.listdir(data_path) if i.endswith(self.extension_video)]

		path_files=[]
		labels=[]

		for i in files:
			path_file=os.path.join(data_path,i)
			path_files.append(path_file)
			labels.append(os.path.splitext(i)[0].split('_')[-1])

		labels=np.array(labels)
		lb=LabelBinarizer()
		labels=lb.fit_transform(labels)
		self.classnames=lb.classes_

		if len(list(self.classnames))<2:

			print('You need at least 2 categories of behaviors!')
			print('Training aborted!')

		else:

			print('Found behavior names: '+str(self.classnames))

			if include_bodyparts is True:
				inner_code=0
			else:
				inner_code=1

			if background_free is True:
				background_code=0
			else:
				background_code=1

			parameters={'classnames':list(self.classnames),'dim_tconv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':1,'level_tconv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

			(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

			print('Perform augmentation for the behavior examples...')
			print('This might take hours or days, depending on the capacity of your computer.')
			print(datetime.datetime.now())

			print('Start to augment training examples...')
			trainX,_,trainY=self.build_data(train_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			trainY=lb.fit_transform(trainY)
			print('Start to augment validation examples...')
			if augvalid is True:
				testX,_,testY=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			else:
				testX,_,testY=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,behavior_mode=behavior_mode)
			testY=lb.fit_transform(testY)

			with tf.device('CPU'):
				trainX=tf.convert_to_tensor(trainX)
				trainY=tf.convert_to_tensor(trainY)
				testX_tensor=tf.convert_to_tensor(testX)
				testY_tensor=tf.convert_to_tensor(testY)

			print('Training example shape : '+str(trainX.shape))
			print('Training label shape : '+str(trainY.shape))
			print('Validation example shape : '+str(testX.shape))
			print('Validation label shape : '+str(testY.shape))
			print(datetime.datetime.now())

			if trainX.shape[0]<5000:
				batch_size=8
			elif trainX.shape[0]<50000:
				batch_size=16
			else:
				batch_size=32

			if level<5:
				model=self.simple_tvgg(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
			else:
				model=self.simple_tresnet(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)

			if len(self.classnames)==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=4,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=2,verbose=1,mode='min',min_learning_rate=1e-7)

			H=model.fit(trainX,trainY,batch_size=batch_size,validation_data=(testX_tensor,testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))

			try:
			
				predictions=model.predict(testX,batch_size=batch_size)

				if len(self.classnames)==2:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]]))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]],output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')

				plt.style.use('seaborn-bright')
				plt.figure()
				plt.plot(H.history['loss'],label='train_loss')
				plt.plot(H.history['val_loss'],label='val_loss')
				plt.plot(H.history['accuracy'],label='train_accuracy')
				plt.plot(H.history['val_accuracy'],label='val_accuracy')
				plt.title('Loss and Accuracy')
				plt.xlabel('Epoch')
				plt.ylabel('Loss/Accuracy')
				plt.legend(loc='center right')
				plt.savefig(os.path.join(model_path,'training_history.png'))
				if out_path is not None:
					plt.savefig(os.path.join(out_path,'training_history.png'))
					print('Training reports saved in: '+str(out_path))
				plt.close('all')

			except:

				pass


	def train_combnet(self,data_path,model_path,out_path=None,dim_tconv=32,dim_conv=64,channel=1,time_step=15,level_tconv=1,level_conv=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim_tconv: the input dimension of Animation Analyzer
		# dim_conv: the input dimension of Pattern Recognizer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# level_tconv: complexity level of Animation Analyzer, determines how deep the neural network is
		# level_conv: complexity level of Pattern Recognizer, determines how deep the neural network is
		# aug_methods: the augmentation methods that are used in training
		# augvalid: whether augment the validation data as well
		# whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		print('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))

		files=[i for i in os.listdir(data_path) if i.endswith(self.extension_video)]

		path_files=[]
		labels=[]

		for i in files:
			path_file=os.path.join(data_path,i)
			path_files.append(path_file)
			labels.append(os.path.splitext(i)[0].split('_')[-1])

		labels=np.array(labels)
		lb=LabelBinarizer()
		labels=lb.fit_transform(labels)
		self.classnames=lb.classes_

		if len(list(self.classnames))<2:

			print('You need at least 2 categories of behaviors!')
			print('Training aborted!')

		else:

			print('Found behavior names: '+str(self.classnames))

			if include_bodyparts is True:
				inner_code=0
			else:
				inner_code=1

			if background_free is True:
				background_code=0
			else:
				background_code=1

			parameters={'classnames':list(self.classnames),'dim_tconv':int(dim_tconv),'dim_conv':int(dim_conv),'channel':int(channel),'time_step':int(time_step),'network':2,'level_tconv':int(level_tconv),'level_conv':int(level_conv),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

			(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

			print('Perform augmentation for the behavior examples...')
			print('This might take hours or days, depending on the capacity of your computer.')
			print(datetime.datetime.now())

			print('Start to augment training examples...')
			train_animations,train_pattern_images,trainY=self.build_data(train_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			trainY=lb.fit_transform(trainY)
			print('Start to augment validation examples...')
			if augvalid is True:
				test_animations,test_pattern_images,testY=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,behavior_mode=behavior_mode)
			else:
				test_animations,test_pattern_images,testY=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,behavior_mode=behavior_mode)
			testY=lb.fit_transform(testY)

			with tf.device('CPU'):
				train_animations=tf.convert_to_tensor(train_animations)
				train_pattern_images=tf.convert_to_tensor(train_pattern_images)
				trainY=tf.convert_to_tensor(trainY)
				test_animations_tensor=tf.convert_to_tensor(test_animations)
				test_pattern_images_tensor=tf.convert_to_tensor(test_pattern_images)
				testY_tensor=tf.convert_to_tensor(testY)

			print('Training example shape : '+str(train_animations.shape)+', '+str(train_pattern_images.shape))
			print('Training label shape : '+str(trainY.shape))
			print('Validation example shape : '+str(test_animations.shape)+', '+str(test_pattern_images.shape))
			print('Validation label shape : '+str(testY.shape))
			print(datetime.datetime.now())

			if train_animations.shape[0]<5000:
				batch_size=8
			elif train_animations.shape[0]<50000:
				batch_size=16
			else:
				batch_size=32

			model=self.combined_network(time_step=time_step,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,classes=len(self.classnames),level_tconv=level_tconv,level_conv=level_conv)
			if len(self.classnames)==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=4,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=2,verbose=1,mode='min',min_learning_rate=1e-7)

			H=model.fit([train_animations,train_pattern_images],trainY,batch_size=batch_size,validation_data=([test_animations_tensor,test_pattern_images_tensor],testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))

			try:

				predictions=model.predict([test_animations,test_pattern_images],batch_size=batch_size)

				if len(self.classnames)==2:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]]))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=[self.classnames[0]],output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')

				plt.style.use('seaborn-bright')
				plt.figure()
				plt.plot(H.history['loss'],label='train_loss')
				plt.plot(H.history['val_loss'],label='val_loss')
				plt.plot(H.history['accuracy'],label='train_accuracy')
				plt.plot(H.history['val_accuracy'],label='val_accuracy')
				plt.title('Loss and Accuracy')
				plt.xlabel('Epoch')
				plt.ylabel('Loss/Accuracy')
				plt.legend(loc='center right')
				plt.savefig(os.path.join(model_path,'training_history.png'))
				if out_path is not None:
					plt.savefig(os.path.join(out_path,'training_history.png'))
					print('Training reports saved in: '+str(out_path))
				plt.close('all')

			except:

				pass


	def test_categorizer(self,groundtruth_path,model_path,result_path=None):

		# groundtruth_path: the folder that stores all the groundtruth behavior examples, each subfolder should be a behavior category, all categories must match those in the Categorizer
		# model_path: path to the Categorizer
		# result_path: if not None, will store the testing reports in this folder

		print('Testing the selected Categorizer...')

		animations=deque()
		pattern_images=deque()
		labels=deque()

		parameters=pd.read_csv(os.path.join(model_path,'model_parameters.txt'))

		if 'dim_conv' in list(parameters.keys()):
			dim_conv=int(parameters['dim_conv'][0])
		if 'dim_tconv' in list(parameters.keys()):
			dim_tconv=int(parameters['dim_tconv'][0])
		if 'level_conv' in list(parameters.keys()):
			level_conv=int(parameters['level_conv'][0])
		if 'dim_tconv' in list(parameters.keys()):
			level_tconv=int(parameters['level_tconv'][0])
		if 'channel' in list(parameters.keys()):
			channel=int(parameters['channel'][0])
		if 'behavior_kind' in list(parameters.keys()):
			behavior_mode=int(parameters['behavior_kind'][0])
		else:
			behavior_mode=0
		if behavior_mode==0:
			print('The behavior mode of the Categorizer: Non-interactive.')
		elif behavior_mode==1:
			print('The behavior mode of the Categorizer: Interactive basic.')
		elif behavior_mode==2:
			print('The behavior mode of the Categorizer: Interactive advanced (Social distance '+str(parameters['social_distance'][0])+').')
		else:
			print('The behavior mode of the Categorizer: Static images (non-interactive).')
		network=int(parameters['network'][0])
		if network==0:
			if behavior_mode==3:
				print('The type of the Categorizer: Pattern Recognizer (Lv '+str(level_conv)+'; Shape '+str(dim_conv)+' X '+str(dim_conv)+' X '+str(channel)+').')
			else:
				print('The type of the Categorizer: Pattern Recognizer (Lv '+str(level_conv)+'; Shape '+str(dim_conv)+' X '+str(dim_conv)+' X 3).')
		if network==1:
			print('The type of the Categorizer: Animation Analyzer (Lv '+str(level_tconv)+'; Shape '+str(dim_tconv)+' X '+str(channel)+').')		
		if network==2:
			print('The type of the Categorizer: Animation Analyzer (Lv '+str(level_tconv)+'; Shape '+str(dim_tconv)+' X '+str(dim_tconv)+' X '+str(channel)+') + Pattern Recognizer (Lv '+str(level_conv)+'; Shape '+str(dim_conv)+' X '+str(dim_conv)+' X 3).')
		length=int(parameters['time_step'][0])
		print('The length of a behavior example in the Categorizer: '+str(length)+' frames.')
		if int(parameters['inner_code'][0])==0:
			print('The Categorizer includes body parts in analysis with STD = '+str(parameters['std'][0])+'.')
		else:
			print('The Categorizer does not include body parts in analysis.')
		if int(parameters['background_free'][0])==0:
			print('The Categorizer does not include background in analysis.')
		else:
			print('The Categorizer includes background in analysis.')
		classnames=list(parameters['classnames'])
		print('Behavior names in the Categorizer: '+str(classnames))
		behaviornames=[i for i in os.listdir(groundtruth_path) if os.path.isdir(os.path.join(groundtruth_path,i))]
		incorrect_behaviors=list(set(behaviornames)-set(classnames))
		incorrect_classes=list(set(classnames)-set(behaviornames))
		if len(incorrect_behaviors)>0:
			print('Mismatched behavior names in testing examples: '+str(incorrect_behaviors))
		if len(incorrect_classes)>0:
			print('Unused behavior names in the Categorizer: '+str(incorrect_classes))

		if len(incorrect_behaviors)==0 and len(incorrect_classes)==0:

			for behavior in behaviornames:

				if network!=0:
					filenames=[i for i in os.listdir(os.path.join(groundtruth_path,behavior)) if i.endswith('.avi')]
				else:
					filenames=[i for i in os.listdir(os.path.join(groundtruth_path,behavior)) if i.endswith('.jpg')]

				for i in filenames:

					if network!=0:

						path_to_animation=os.path.join(groundtruth_path,behavior,i)

						capture=cv2.VideoCapture(path_to_animation)
						animation=deque()
						frames=deque(maxlen=length)

						while True:
							retval,frame=capture.read()
							if frame is None:
								break
							frames.append(frame)

						capture.release()

						for frame in frames:
							frame=np.uint8(exposure.rescale_intensity(frame,out_range=(0,255)))
							if channel==1:
								frame=cv2.cvtColor(np.uint8(frame),cv2.COLOR_BGR2GRAY)
							frame=cv2.resize(frame,(dim_tconv,dim_tconv),interpolation=cv2.INTER_AREA)
							frame=img_to_array(frame)
							animation.append(frame)

						animations.append(np.array(animation))

					if network!=1:

						path_to_pattern_image=os.path.splitext(os.path.join(groundtruth_path,behavior,i))[0]+'.jpg'
						pattern_image=cv2.imread(path_to_pattern_image)
						if behavior_mode==3:
							if channel==1:
								pattern_image=cv2.cvtColor(pattern_image,cv2.COLOR_BGR2GRAY)
						pattern_image=cv2.resize(pattern_image,(dim_conv,dim_conv),interpolation=cv2.INTER_AREA)
						pattern_images.append(img_to_array(pattern_image))

					labels.append(classnames.index(behavior))

			if network!=0:
				animations=np.array(animations,dtype='float32')/255.0
			pattern_images=np.array(pattern_images,dtype='float32')/255.0

			labels=np.array(labels)

			model=load_model(model_path)

			if network==0:
				predictions=model.predict(pattern_images,batch_size=32)
			elif network==1:
				predictions=model.predict(animations,batch_size=32)
			else:
				predictions=model.predict([animations,pattern_images],batch_size=32)

			print(classification_report(labels,predictions.argmax(axis=1),target_names=classnames))
			report=classification_report(labels,predictions.argmax(axis=1),target_names=classnames,output_dict=True)

			if result_path is not None:
				pd.DataFrame(report).transpose().to_excel(os.path.join(result_path,'testing_reports.xlsx'),float_format='%.2f')

			print('Testing completed!')


