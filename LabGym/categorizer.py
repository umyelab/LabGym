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
matplotlib.use('Agg')
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
from tensorflow.keras.utils import plot_model,Sequence
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import itertools



class DatasetFromPath_AA(Sequence):

	'''
	Load batches of training examples (including animations) from path
	'''

	def __init__(self,path_to_examples,length=15,batch_size=32,dim_tconv=16,dim_conv=32,channel=1):

		self.path_to_examples=path_to_examples
		self.length=length
		self.batch_size=batch_size
		self.dim_tconv=dim_tconv
		self.dim_conv=dim_conv
		self.channel=channel
		self.pattern_image_paths,self.classmapping=self.load_info()


	def load_info(self):

		pattern_image_paths=[]
		classnames=[]

		for pattern_image in os.listdir(self.path_to_examples):
			if pattern_image.endswith('.jpg'):
				pattern_image_paths.append(os.path.join(self.path_to_examples,pattern_image))
				classname=pattern_image.split('.jpg')[0].split('_')[-1]
				if classname not in classnames:
					classnames.append(classname)

		classnames.sort()
		labels=np.array(classnames)
		lb=LabelBinarizer()
		labels=lb.fit_transform(labels)
		labels=[list(i) for i in labels]
		classmapping={name:labels[i] for i,name in enumerate(classnames)}

		return pattern_image_paths,classmapping


	def __len__(self):

		return int(np.floor(len(self.pattern_image_paths)/self.batch_size))


	def __getitem__(self,idx):

		batch=self.pattern_image_paths[idx*self.batch_size:(idx+1)*self.batch_size]
		animations=[]
		pattern_images=[]
		labels=[]

		for path_to_pattern_image in batch:

			animation=deque([np.zeros((self.dim_tconv,self.dim_tconv,self.channel),dtype='uint8')],maxlen=self.length)*self.length
			capture=cv2.VideoCapture(path_to_pattern_image.split('.jpg')[0]+'.avi')
			while True:
				retval,frame=capture.read()
				if frame is None:
					break
				if self.channel==1:
					frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
				frame=cv2.resize(frame,(self.dim_tconv,self.dim_tconv),interpolation=cv2.INTER_AREA)
				animation.append(img_to_array(frame))
			animations.append(np.array(animation))

			pattern_image=cv2.imread(path_to_pattern_image)
			pattern_image=cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA)
			pattern_images.append(img_to_array(pattern_image))

			labels.append(np.array(self.classmapping[path_to_pattern_image.split('.jpg')[0].split('_')[-1]]))

		animations=np.array(animations)
		animations=animations.astype('float32')/255.0
		pattern_images=np.array(pattern_images)
		pattern_images=pattern_images.astype('float32')/255.0
		labels=np.array(labels)

		return [animations,pattern_images],labels



class DatasetFromPath(Sequence):

	'''
	Load batches of training examples (not including animations) from path
	'''

	def __init__(self,path_to_examples,batch_size=32,dim_conv=32,channel=3):

		self.path_to_examples=path_to_examples
		self.batch_size=batch_size
		self.dim_conv=dim_conv
		self.channel=channel
		self.pattern_image_paths,self.classmapping=self.load_info()


	def load_info(self):

		pattern_image_paths=[]
		classnames=[]

		for pattern_image in os.listdir(self.path_to_examples):
			if pattern_image.endswith('.jpg'):
				pattern_image_paths.append(os.path.join(self.path_to_examples,pattern_image))
				classname=pattern_image.split('.jpg')[0].split('_')[-1]
				if classname not in classnames:
					classnames.append(classname)

		classnames.sort()
		labels=np.array(classnames)
		lb=LabelBinarizer()
		labels=lb.fit_transform(labels)
		labels=[list(i) for i in labels]
		classmapping={name:labels[i] for i,name in enumerate(classnames)}

		return pattern_image_paths,classmapping


	def __len__(self):

		return int(np.floor(len(self.pattern_image_paths)/self.batch_size))


	def __getitem__(self,idx):

		batch=self.pattern_image_paths[idx*self.batch_size:(idx+1)*self.batch_size]
		pattern_images=[]
		labels=[]

		for path_to_pattern_image in batch:

			pattern_image=cv2.imread(path_to_pattern_image)
			if self.channel==1:
				pattern_image=cv2.cvtColor(pattern_image,cv2.COLOR_BGR2GRAY)
			pattern_image=cv2.resize(pattern_image,(self.dim_conv,self.dim_conv),interpolation=cv2.INTER_AREA)
			pattern_images.append(img_to_array(pattern_image))

			labels.append(np.array(self.classmapping[path_to_pattern_image.split('.jpg')[0].split('_')[-1]]))

		pattern_images=np.array(pattern_images)
		pattern_images=pattern_images.astype('float32')/255.0
		labels=np.array(labels)

		return pattern_images,labels



class Categorizers():

	def __init__(self):

		self.extension_image=('.png','.PNG','.jpeg','.JPEG','.jpg','.JPG','.tiff','.TIFF','.bmp','.BMP') # the image formats that LabGym can accept
		self.extension_video=('.avi','.mpg','.wmv','.mp4','.mkv','.m4v','.mov') # the video formats that LabGym can accept
		self.classnames=None # the behavior category names in the trained Categorizer
		self.log=[]


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

					if imagedata:

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


	def build_data(self,path_to_animations,dim_tconv=0,dim_conv=64,channel=1,time_step=15,aug_methods=[],background_free=True,black_background=True,behavior_mode=0,out_path=None):

		# path_to_animations: the folder that stores all the prepared training examples
		# dim_tconv: the input dimension of Animation Analyzer
		# dim_conv: the input dimension of Pattern Recognizer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# aug_methods: the augmentation methods that are used in training
		# background_free: whether the background is included in animations
		# black_background: whether to set background black
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# out_path: if not None, will output all the augmented data to this path

		animations=deque()
		pattern_images=deque()
		labels=deque()
		amount=0

		if len(aug_methods)==0:

			methods=['orig']

		else:

			remove=[]

			all_methods=['orig','rot1','rot2','rot3','rot4','rot5','rot6','shrp','shrn','sclh','sclw','del1','del2']
			options=['rot7','flph','flpv','brih','bril','shrr','sclr','delr']
			for r in range(1,len(options)+1):
				all_methods.extend([''.join(c) for c in itertools.combinations(options,r)])

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

			methods=list(set(all_methods)-set(remove))

		for i in path_to_animations:

			name=os.path.splitext(os.path.basename(i))[0].split('_')[0]
			label=os.path.splitext(i)[0].split('_')[-1]
			path_to_pattern_image=os.path.splitext(i)[0]+'.jpg'
			
			random.shuffle(methods)

			for m in methods:

				if 'rot1' in m:
					angle=np.random.uniform(5,45)
				elif 'rot2' in m:
					angle=np.random.uniform(45,85)
				elif 'rot3' in m:
					angle=90.0
				elif 'rot4' in m:
					angle=np.random.uniform(95,135)
				elif 'rot5' in m:
					angle=np.random.uniform(135,175)
				elif 'rot6' in m:
					angle=180.0
				elif 'rot7' in m:
					angle=np.random.uniform(5,175)
				else:
					angle=None

				if 'flph' in m:
					code=1
				elif 'flpv' in m:
					code=0
				else:
					code=None

				if 'brih' in m:
					beta=np.random.uniform(10,50)
				elif 'bril' in m:
					beta=np.random.uniform(-50,10)
				else:
					beta=None

				if 'shrp' in m:
					shear=np.random.uniform(0.15,0.21)
				elif 'shrn' in m:
					shear=np.random.uniform(-0.21,-0.15)
				elif 'shrr' in m:
					shear=np.random.uniform(-0.21,0.21)
				else:
					shear=None

				if 'sclh' in m:
					width=0
					scale=np.random.uniform(0.6,0.9)
				elif 'sclw' in m:
					width=1
					scale=np.random.uniform(0.6,0.9)
				elif 'sclr' in m:
					width=random.randint(0,1)
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
				elif 'delr' in m:
					to_delete=[random.randint(0,time_step-1)]
				else:
					to_delete=None

				if dim_tconv!=0:

					capture=cv2.VideoCapture(i)
					if out_path is not None:
						fps=round(capture.get(cv2.CAP_PROP_FPS))
						w=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
						h=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
						writer=cv2.VideoWriter(os.path.join(out_path,name+'_'+m+'_'+label+'.avi'),cv2.VideoWriter_fourcc(*'MJPG'),int(fps),(w,h),True)
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

					capture.release()

					frames_length=len(frames)
					if frames_length<time_step:
						for diff in range(time_step-frames_length):
							frames.append(np.zeros_like(original_frame))
						print('Inconsistent duration of animation detected at: '+str(i)+'.')
						self.log.append('Inconsistent duration of animation detected at: '+str(i)+'.')
						print('Zero padding has been used, which may decrease the training accuracy.')
						self.log.append('Zero padding has been used, which may decrease the training accuracy.')

					for frame in frames:

						if to_delete is not None and n in to_delete:

							if black_background is False:
								frame=np.uint8(np.zeros_like(original_frame)+255)
							else:
								frame=np.zeros_like(original_frame)

						else:

							if code is not None:
								frame=cv2.flip(frame,code)

							if beta is not None:
								frame=frame.astype('float')
								if background_free:
									if black_background:
										frame[frame>30]+=beta
									else:
										frame[frame<225]+=beta
								else:
									frame+=beta
								frame=np.uint8(np.clip(frame,0,255))

							if angle is not None:
								frame=ndimage.rotate(frame,angle,reshape=False,prefilter=False)

							if shear is not None:
								tf=AffineTransform(shear=shear)
								frame=transform.warp(frame,tf,order=1,preserve_range=True,mode='constant')

							if scale is not None:
								frame_black=np.zeros_like(frame)
								if black_background is False:
									frame_black=np.uint8(frame_black+255)
								if width==0:
									frame_scl=cv2.resize(frame,(frame.shape[1],int(frame.shape[0]*scale)),interpolation=cv2.INTER_AREA)
								else:
									frame_scl=cv2.resize(frame,(int(frame.shape[1]*scale),frame.shape[0]),interpolation=cv2.INTER_AREA)
								frame_scl=img_to_array(frame_scl)
								x=(frame_black.shape[1]-frame_scl.shape[1])//2
								y=(frame_black.shape[0]-frame_scl.shape[0])//2
								frame_black[y:y+frame_scl.shape[0],x:x+frame_scl.shape[1]]=frame_scl
								frame=frame_black

						if out_path is None:
							if channel==1:
								frame=cv2.cvtColor(np.uint8(frame),cv2.COLOR_BGR2GRAY)
							frame=cv2.resize(frame,(dim_tconv,dim_tconv),interpolation=cv2.INTER_AREA)
							frame=img_to_array(frame)
							animation.append(frame)
						else:
							writer.write(np.uint8(frame))

						n+=1

					if out_path is None:
						animations.append(np.array(animation))
					else:
						writer.release()

				pattern_image=cv2.imread(path_to_pattern_image)

				if code is not None:
					pattern_image=cv2.flip(pattern_image,code)

				if behavior_mode==3:
					if beta is not None:
						pattern_image=pattern_image.astype('float')
						if background_free:
							if black_background:
								pattern_image[pattern_image>30]+=beta
							else:
								pattern_image[pattern_image<225]+=beta
						else:
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

				if out_path is None:

					if behavior_mode==3:
						if channel==1:
							pattern_image=cv2.cvtColor(np.uint8(pattern_image),cv2.COLOR_BGR2GRAY)

					pattern_image=cv2.resize(pattern_image,(dim_conv,dim_conv),interpolation=cv2.INTER_AREA)
					pattern_images.append(img_to_array(pattern_image))

					labels.append(label)

					amount+=1
					if amount%10000==0:
						print('The augmented example amount: '+str(amount))
						self.log.append('The augmented example amount: '+str(amount))
						print(datetime.datetime.now())
						self.log.append(str(datetime.datetime.now()))

				else:

					cv2.imwrite(os.path.join(out_path,name+'_'+m+'_'+label+'.jpg'),np.uint8(pattern_image))

		if out_path is None:

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

		if basic:

			x=ZeroPadding2D((1,1))(x)
			x=Conv2D(filters,(3,3),strides=(strides,strides))(x)

		else:

			x=Conv2D(filters,(1,1),strides=(strides,strides))(x)

		x=BatchNormalization()(x)
		x=Activation('relu')(x)

		x=ZeroPadding2D((1,1))(x)
		x=Conv2D(filters,(3,3),strides=(1,1))(x)
		x=BatchNormalization()(x)

		if basic:

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

		if basic:

			x=TimeDistributed(ZeroPadding2D((1,1)))(x)
			x=TimeDistributed(Conv2D(filters,(3,3),strides=(strides,strides)))(x)

		else:

			x=TimeDistributed(Conv2D(filters,(1,1),strides=(strides,strides)))(x)

		x=TimeDistributed(BatchNormalization())(x)
		x=TimeDistributed(Activation('relu'))(x)

		x=TimeDistributed(ZeroPadding2D((1,1)))(x)
		x=TimeDistributed(Conv2D(filters,(3,3),strides=(1,1)))(x)
		x=TimeDistributed(BatchNormalization())(x)

		if basic:

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


	def train_pattern_recognizer(self,data_path,model_path,out_path=None,dim=64,channel=3,time_step=15,level=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0,out_folder=None):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Pattern Recognizer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension
		# channel: the input color channel, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation / pattern image, also the length of a behavior episode
		# level: complexity level, determines how deep the neural network is
		# aug_methods: the augmentation methods that are used in training
		# augvalid: whether augment the validation data as well
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		# out_folder: if not None, will output all the augmented data to this folder

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)

		inputs=Input(shape=(dim,dim,channel))

		print('Training the Categorizer w/ only Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training the Categorizer w/ only Pattern Recognizer using the behavior examples in: '+str(data_path))

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
			self.log.append('Found behavior names: '+str(self.classnames))

			if out_folder is None:

				if include_bodyparts:
					inner_code=0
				else:
					inner_code=1

				if background_free:
					background_code=0
				else:
					background_code=1

				if black_background:
					black_code=0
				else:
					black_code=1

				if behavior_mode>=3:
					time_step=std=0
					inner_code=1

				parameters={'classnames':list(self.classnames),'dim_conv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':0,'level_conv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
				pd_parameters=pd.DataFrame.from_dict(parameters)
				pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

				(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples...')
				self.log.append('Perform augmentation for the behavior examples...')
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				_,trainX,trainY=self.build_data(train_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				trainY=lb.fit_transform(trainY)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				if augvalid:
					_,testX,testY=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				else:
					_,testX,testY=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				testY=lb.fit_transform(testY)

				with tf.device('CPU'):
					trainX=tf.convert_to_tensor(trainX)
					trainY=tf.convert_to_tensor(trainY)
					testX_tensor=tf.convert_to_tensor(testX)
					testY_tensor=tf.convert_to_tensor(testY)

				print('Training example shape : '+str(trainX.shape))
				self.log.append('Training example shape : '+str(trainX.shape))
				print('Training label shape : '+str(trainY.shape))
				self.log.append('Training label shape : '+str(trainY.shape))
				print('Validation example shape : '+str(testX.shape))
				self.log.append('Validation example shape : '+str(testX.shape))
				print('Validation label shape : '+str(testY.shape))
				self.log.append('Validation label shape : '+str(testY.shape))
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				if dim<=128:
					batch_size=32
				elif dim<=256:
					batch_size=16
				else:
					batch_size=8

				if level<5:
					model=self.simple_vgg(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
				else:
					model=self.simple_resnet(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
				if len(self.classnames)==2:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
				else:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

				cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
				es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
				rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

				H=model.fit(trainX,trainY,batch_size=batch_size,validation_data=(testX_tensor,testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

				model.save(model_path)
				print('Trained Categorizer saved in: '+str(model_path))
				self.log.append('Trained Categorizer saved in: '+str(model_path))

				predictions=model.predict(testX,batch_size=batch_size)

				if len(self.classnames)==2:
					predictions=[round(i[0]) for i in predictions]
					print(classification_report(testY,predictions,target_names=self.classnames))
					report=classification_report(testY,predictions,target_names=self.classnames,output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')
				
				plt.style.use('classic')
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
					if len(self.log)>0:
						with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
							training_log.write('\n'.join(str(i) for i in self.log))
				plt.close('all')

			else:

				(train_files,test_files,_,_)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				self.log.append('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				train_folder=os.path.join(out_folder,'train')
				os.makedirs(train_folder,exist_ok=True)
				_,_,_=self.build_data(train_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=train_folder)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				validation_folder=os.path.join(out_folder,'validation')
				os.makedirs(validation_folder,exist_ok=True)
				if augvalid:
					_,_,_=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)
				else:
					_,_,_=self.build_data(test_files,dim_tconv=0,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)

				self.train_pattern_recognizer_onfly(out_folder,model_path,out_path=out_path,dim=dim,channel=channel,time_step=time_step,level=level,include_bodyparts=include_bodyparts,std=std,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,social_distance=social_distance)


	def train_animation_analyzer(self,data_path,model_path,out_path=None,dim=64,channel=1,time_step=15,level=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0,out_folder=None):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension
		# channel: the input color channel, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# level: complexity level, determines how deep the neural network is
		# aug_methods: the augmentation methods that are used in training
		# augvalid: whether augment the validation data as well
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		# out_folder: if not None, will output all the augmented data to this folder

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)
		
		inputs=Input(shape=(time_step,dim,dim,channel))

		print('Training the Categorizer w/o Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training the Categorizer w/ only Pattern Recognizer using the behavior examples in: '+str(data_path))

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
			self.log.append('Found behavior names: '+str(self.classnames))

			if out_folder is None:

				if include_bodyparts:
					inner_code=0
				else:
					inner_code=1

				if background_free:
					background_code=0
				else:
					background_code=1

				if black_background:
					black_code=0
				else:
					black_code=1

				parameters={'classnames':list(self.classnames),'dim_tconv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':1,'level_tconv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
				pd_parameters=pd.DataFrame.from_dict(parameters)
				pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

				(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples...')
				self.log.append('Perform augmentation for the behavior examples...')
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				trainX,_,trainY=self.build_data(train_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				trainY=lb.fit_transform(trainY)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				if augvalid:
					testX,_,testY=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				else:
					testX,_,testY=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				testY=lb.fit_transform(testY)

				with tf.device('CPU'):
					trainX=tf.convert_to_tensor(trainX)
					trainY=tf.convert_to_tensor(trainY)
					testX_tensor=tf.convert_to_tensor(testX)
					testY_tensor=tf.convert_to_tensor(testY)

				print('Training example shape : '+str(trainX.shape))
				self.log.append('Training example shape : '+str(trainX.shape))
				print('Training label shape : '+str(trainY.shape))
				self.log.append('Training label shape : '+str(trainY.shape))
				print('Validation example shape : '+str(testX.shape))
				self.log.append('Validation example shape : '+str(testX.shape))
				print('Validation label shape : '+str(testY.shape))
				self.log.append('Validation label shape : '+str(testY.shape))
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				if dim<=16:
					batch_size=32
				elif dim<=64:
					batch_size=16
				elif dim<=128:
					batch_size=8
				else:
					batch_size=4

				if level<5:
					model=self.simple_tvgg(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)
				else:
					model=self.simple_tresnet(inputs,filters,classes=len(self.classnames),level=level,with_classifier=True)

				if len(self.classnames)==2:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
				else:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

				cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
				es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
				rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

				H=model.fit(trainX,trainY,batch_size=batch_size,validation_data=(testX_tensor,testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

				model.save(model_path)
				print('Trained Categorizer saved in: '+str(model_path))
				self.log.append('Trained Categorizer saved in: '+str(model_path))

				predictions=model.predict(testX,batch_size=batch_size)

				if len(self.classnames)==2:
					predictions=[round(i[0]) for i in predictions]
					print(classification_report(testY,predictions,target_names=self.classnames))
					report=classification_report(testY,predictions,target_names=self.classnames,output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')

				plt.style.use('classic')
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
					if len(self.log)>0:
						with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
							training_log.write('\n'.join(str(i) for i in self.log))
				plt.close('all')

			else:

				(train_files,test_files,_,_)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				self.log.append('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				train_folder=os.path.join(out_folder,'train')
				os.makedirs(train_folder,exist_ok=True)
				_,_,_=self.build_data(train_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=train_folder)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				validation_folder=os.path.join(out_folder,'validation')
				os.makedirs(validation_folder,exist_ok=True)
				if augvalid:
					_,_,_=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)
				else:
					_,_,_=self.build_data(test_files,dim_tconv=dim,dim_conv=dim,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)

				self.train_animation_analyzer_onfly(out_folder,model_path,out_path=out_path,dim=dim,channel=channel,time_step=time_step,level=level,include_bodyparts=include_bodyparts,std=std,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,social_distance=social_distance)


	def train_combnet(self,data_path,model_path,out_path=None,dim_tconv=32,dim_conv=64,channel=1,time_step=15,level_tconv=1,level_conv=2,aug_methods=[],augvalid=True,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0,out_folder=None):

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
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		# out_folder: if not None, will output all the augmented data to this folder

		print('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))

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
			self.log.append('Found behavior names: '+str(self.classnames))

			if out_folder is None:

				if include_bodyparts:
					inner_code=0
				else:
					inner_code=1

				if background_free:
					background_code=0
				else:
					background_code=1

				if black_background:
					black_code=0
				else:
					black_code=1

				parameters={'classnames':list(self.classnames),'dim_tconv':int(dim_tconv),'dim_conv':int(dim_conv),'channel':int(channel),'time_step':int(time_step),'network':2,'level_tconv':int(level_tconv),'level_conv':int(level_conv),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
				pd_parameters=pd.DataFrame.from_dict(parameters)
				pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

				(train_files,test_files,y1,y2)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples...')
				self.log.append('Perform augmentation for the behavior examples...')
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				train_animations,train_pattern_images,trainY=self.build_data(train_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				trainY=lb.fit_transform(trainY)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				if augvalid:
					test_animations,test_pattern_images,testY=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				else:
					test_animations,test_pattern_images,testY=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode)
				testY=lb.fit_transform(testY)

				with tf.device('CPU'):
					train_animations=tf.convert_to_tensor(train_animations)
					train_pattern_images=tf.convert_to_tensor(train_pattern_images)
					trainY=tf.convert_to_tensor(trainY)
					test_animations_tensor=tf.convert_to_tensor(test_animations)
					test_pattern_images_tensor=tf.convert_to_tensor(test_pattern_images)
					testY_tensor=tf.convert_to_tensor(testY)

				print('Training example shape : '+str(train_animations.shape)+', '+str(train_pattern_images.shape))
				self.log.append('Training example shape : '+str(train_animations.shape)+', '+str(train_pattern_images.shape))
				print('Training label shape : '+str(trainY.shape))
				self.log.append('Training label shape : '+str(trainY.shape))
				print('Validation example shape : '+str(test_animations.shape)+', '+str(test_pattern_images.shape))
				self.log.append('Validation example shape : '+str(test_animations.shape)+', '+str(test_pattern_images.shape))
				print('Validation label shape : '+str(testY.shape))
				self.log.append('Validation label shape : '+str(testY.shape))
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				if dim_tconv<=16:
					batch_size=32
				elif dim_tconv<=64:
					batch_size=16
				elif dim_tconv<=128:
					batch_size=8
				else:
					batch_size=4

				model=self.combined_network(time_step=time_step,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,classes=len(self.classnames),level_tconv=level_tconv,level_conv=level_conv)
				if len(self.classnames)==2:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
				else:
					model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

				cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
				es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
				rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

				H=model.fit([train_animations,train_pattern_images],trainY,batch_size=batch_size,validation_data=([test_animations_tensor,test_pattern_images_tensor],testY_tensor),epochs=1000000,callbacks=[cp,es,rl])

				model.save(model_path)
				print('Trained Categorizer saved in: '+str(model_path))
				self.log.append('Trained Categorizer saved in: '+str(model_path))

				predictions=model.predict([test_animations,test_pattern_images],batch_size=batch_size)

				if len(self.classnames)==2:
					predictions=[round(i[0]) for i in predictions]
					print(classification_report(testY,predictions,target_names=self.classnames))
					report=classification_report(testY,predictions,target_names=self.classnames,output_dict=True)
				else:
					print(classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames))
					report=classification_report(testY.argmax(axis=1),predictions.argmax(axis=1),target_names=self.classnames,output_dict=True)

				pd.DataFrame(report).transpose().to_csv(os.path.join(model_path,'training_metrics.csv'),float_format='%.2f')
				if out_path is not None:
					pd.DataFrame(report).transpose().to_excel(os.path.join(out_path,'training_metrics.xlsx'),float_format='%.2f')

				plt.style.use('classic')
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
					if len(self.log)>0:
						with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
							training_log.write('\n'.join(str(i) for i in self.log))
				plt.close('all')

			else:

				(train_files,test_files,_,_)=train_test_split(path_files,labels,test_size=0.2,stratify=labels)

				print('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				self.log.append('Perform augmentation for the behavior examples and export them to: '+str(out_folder))
				print('This might take hours or days, depending on the capacity of your computer.')
				print(datetime.datetime.now())
				self.log.append(str(datetime.datetime.now()))

				print('Start to augment training examples...')
				self.log.append('Start to augment training examples...')
				train_folder=os.path.join(out_folder,'train')
				os.makedirs(train_folder,exist_ok=True)
				_,_,_=self.build_data(train_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=train_folder)
				print('Start to augment validation examples...')
				self.log.append('Start to augment validation examples...')
				validation_folder=os.path.join(out_folder,'validation')
				os.makedirs(validation_folder,exist_ok=True)
				if augvalid:
					_,_,_=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=aug_methods,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)
				else:
					_,_,_=self.build_data(test_files,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,aug_methods=[],background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,out_path=validation_folder)

				self.train_combnet_onfly(out_folder,model_path,out_path=out_path,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,time_step=time_step,level_tconv=level_tconv,level_conv=level_conv,include_bodyparts=include_bodyparts,std=std,background_free=background_free,black_background=black_background,behavior_mode=behavior_mode,social_distance=social_distance)


	def train_pattern_recognizer_onfly(self,data_path,model_path,out_path=None,dim=32,channel=3,time_step=15,level=2,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Pattern Recognizer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension
		# channel: the input color channel, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation / pattern image, also the length of a behavior episode
		# level: complexity level, determines how deep the neural network is
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)

		inputs=Input(shape=(dim,dim,channel))

		print('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		print(datetime.datetime.now())
		self.log.append(str(datetime.datetime.now()))

		train_folder=os.path.join(data_path,'train')
		validation_folder=os.path.join(data_path,'validation')

		if os.path.isdir(train_folder) and os.path.isdir(validation_folder):

			if dim<=128:
				batch_size=32
			elif dim<=256:
				batch_size=16
			else:
				batch_size=8

			if behavior_mode==3:
				channel=channel
			else:
				channel=3

			train_data=DatasetFromPath(train_folder,batch_size=batch_size,dim_conv=dim,channel=channel)
			validation_data=DatasetFromPath(validation_folder,batch_size=batch_size,dim_conv=dim,channel=channel)


			if include_bodyparts:
				inner_code=0
			else:
				inner_code=1

			if background_free:
				background_code=0
			else:
				background_code=1

			if black_background:
				black_code=0
			else:
				black_code=1

			if behavior_mode>=3:
				time_step=std=0
				inner_code=1

			parameters={'classnames':list(train_data.classmapping.keys()),'dim_conv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':0,'level_conv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

			if level<5:
				model=self.simple_vgg(inputs,filters,classes=len(list(train_data.classmapping.keys())),level=level,with_classifier=True)
			else:
				model=self.simple_resnet(inputs,filters,classes=len(list(train_data.classmapping.keys())),level=level,with_classifier=True)
			if len(list(train_data.classmapping.keys()))==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

			H=model.fit(train_data,validation_data=(validation_data),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))
			self.log.append('Trained Categorizer saved in: '+str(model_path))
			print(datetime.datetime.now())
			self.log.append(str(datetime.datetime.now()))

			plt.style.use('classic')
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
				if len(self.log)>0:
					with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
						training_log.write('\n'.join(str(i) for i in self.log))
			plt.close('all')

		else:

			print('No train / validation folder!')


	def train_animation_analyzer_onfly(self,data_path,model_path,out_path=None,dim=32,channel=1,time_step=15,level=2,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim: the input dimension of Animation Analyzer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# level: complexity level of Animation Analyzer, determines how deep the neural network is
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		filters=8

		for i in range(round(dim/60)):
			filters=min(int(filters*2),64)

		inputs=Input(shape=(dim,dim,channel))

		print('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		print(datetime.datetime.now())
		self.log.append(str(datetime.datetime.now()))

		train_folder=os.path.join(data_path,'train')
		validation_folder=os.path.join(data_path,'validation')

		if os.path.isdir(train_folder) and os.path.isdir(validation_folder):

			if dim<=16:
				batch_size=32
			elif dim<=64:
				batch_size=16
			elif dim<=128:
				batch_size=8
			else:
				batch_size=4

			train_data=DatasetFromPath_AA(train_folder,length=time_step,batch_size=batch_size,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel)
			validation_data=DatasetFromPath_AA(validation_folder,length=time_step,batch_size=batch_size,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel)

			if include_bodyparts:
				inner_code=0
			else:
				inner_code=1

			if background_free:
				background_code=0
			else:
				background_code=1

			if black_background:
				black_code=0
			else:
				black_code=1

			parameters={'classnames':list(train_data.classmapping.keys()),'dim_tconv':int(dim),'channel':int(channel),'time_step':int(time_step),'network':1,'level_tconv':int(level),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)


			if level<5:
				model=self.simple_tvgg(inputs,filters,classes=len(list(train_data.classmapping.keys())),level=level,with_classifier=True)
			else:
				model=self.simple_tresnet(inputs,filters,classes=len(list(train_data.classmapping.keys())),level=level,with_classifier=True)
			if len(list(train_data.classmapping.keys()))==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

			H=model.fit(train_data,validation_data=(validation_data),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))
			self.log.append('Trained Categorizer saved in: '+str(model_path))
			print(datetime.datetime.now())
			self.log.append(str(datetime.datetime.now()))

			plt.style.use('classic')
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
				if len(self.log)>0:
					with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
						training_log.write('\n'.join(str(i) for i in self.log))
			plt.close('all')

		else:

			print('No train / validation folder!')


	def train_combnet_onfly(self,data_path,model_path,out_path=None,dim_tconv=32,dim_conv=64,channel=1,time_step=15,level_tconv=1,level_conv=2,include_bodyparts=True,std=0,background_free=True,black_background=True,behavior_mode=0,social_distance=0):

		# data_path: the folder that stores all the prepared training examples
		# model_path: the path to the trained Animation Analyzer
		# out_path: if not None, will store the training reports in this folder
		# dim_tconv: the input dimension of Animation Analyzer
		# dim_conv: the input dimension of Pattern Recognizer
		# channel: the input color channel of Animation Analyzer, 1 is gray scale, 3 is RGB
		# time_step: the duration of an animation, also the input length of Animation Analyzer
		# level_tconv: complexity level of Animation Analyzer, determines how deep the neural network is
		# level_conv: complexity level of Pattern Recognizer, determines how deep the neural network is
		# include_bodyparts: whether to include body parts in the pattern images
		# std: a value between 0 and 255, higher value, less body parts will be included in the pattern images
		# background_free: whether to include background in animations
		# black_background: whether to set background
		# behavior_mode:  0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		# social_distance: a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples

		print('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		self.log.append('Training Categorizer with both Animation Analyzer and Pattern Recognizer using the behavior examples in: '+str(data_path))
		print(datetime.datetime.now())
		self.log.append(str(datetime.datetime.now()))

		train_folder=os.path.join(data_path,'train')
		validation_folder=os.path.join(data_path,'validation')

		if os.path.isdir(train_folder) and os.path.isdir(validation_folder):

			if dim_tconv<=16:
				batch_size=32
			elif dim_tconv<=64:
				batch_size=16
			elif dim_tconv<=128:
				batch_size=8
			else:
				batch_size=4

			train_data=DatasetFromPath_AA(train_folder,length=time_step,batch_size=batch_size,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel)
			validation_data=DatasetFromPath_AA(validation_folder,length=time_step,batch_size=batch_size,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel)

			if include_bodyparts:
				inner_code=0
			else:
				inner_code=1

			if background_free:
				background_code=0
			else:
				background_code=1

			if black_background:
				black_code=0
			else:
				black_code=1

			parameters={'classnames':list(train_data.classmapping.keys()),'dim_tconv':int(dim_tconv),'dim_conv':int(dim_conv),'channel':int(channel),'time_step':int(time_step),'network':2,'level_tconv':int(level_tconv),'level_conv':int(level_conv),'inner_code':int(inner_code),'std':int(std),'background_free':int(background_code),'black_background':int(black_code),'behavior_kind':int(behavior_mode),'social_distance':int(social_distance)}
			pd_parameters=pd.DataFrame.from_dict(parameters)
			pd_parameters.to_csv(os.path.join(model_path,'model_parameters.txt'),index=False)

			model=self.combined_network(time_step=time_step,dim_tconv=dim_tconv,dim_conv=dim_conv,channel=channel,classes=len(list(train_data.classmapping.keys())),level_tconv=level_tconv,level_conv=level_conv)
			if len(list(train_data.classmapping.keys()))==2:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='binary_crossentropy',metrics=['accuracy'])
			else:
				model.compile(optimizer=SGD(learning_rate=1e-4,momentum=0.9),loss='categorical_crossentropy',metrics=['accuracy'])

			cp=ModelCheckpoint(model_path,monitor='val_loss',verbose=1,save_best_only=True,save_weights_only=False,mode='min',save_freq='epoch')
			es=EarlyStopping(monitor='val_loss',min_delta=0.001,mode='min',verbose=1,patience=6,restore_best_weights=True)
			rl=ReduceLROnPlateau(monitor='val_loss',min_delta=0.001,factor=0.2,patience=3,verbose=1,mode='min',min_lr=1e-7)

			H=model.fit(train_data,validation_data=(validation_data),epochs=1000000,callbacks=[cp,es,rl])

			model.save(model_path)
			print('Trained Categorizer saved in: '+str(model_path))
			self.log.append('Trained Categorizer saved in: '+str(model_path))
			print(datetime.datetime.now())
			self.log.append(str(datetime.datetime.now()))

			plt.style.use('classic')
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
				if len(self.log)>0:
					with open(os.path.join(out_path,'Training log.txt'),'w') as training_log:
						training_log.write('\n'.join(str(i) for i in self.log))
			plt.close('all')

		else:

			print('No train / validation folder!')


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
		if 'black_background' in parameters:
			if int(parameters['black_background'][0])==1:
				print('The background is white in the Categorizer.')
		classnames=list(parameters['classnames'])
		classnames=[str(i) for i in classnames]
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

			if len(classnames)==2:
				predictions=[round(i[0]) for i in predictions]
				print(classification_report(labels,predictions,target_names=classnames))
				report=classification_report(labels,predictions,target_names=classnames,output_dict=True)
			else:
				print(classification_report(labels,predictions.argmax(axis=1),target_names=classnames))
				report=classification_report(labels,predictions.argmax(axis=1),target_names=classnames,output_dict=True)

			if result_path is not None:
				pd.DataFrame(report).transpose().to_excel(os.path.join(result_path,'testing_reports.xlsx'),float_format='%.2f')

			print('Testing completed!')


