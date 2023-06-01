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
import cv2
import json
import torch
import numpy as np
import datetime
from skimage import exposure
from detectron2.config import get_cfg
from detectron2.modeling import build_model
from detectron2.checkpoint import DetectionCheckpointer
from tensorflow.keras.preprocessing.image import img_to_array



class DetectAnimals():

	def __init__(self,path_to_detector):

		self.detector=None
		self.animal_names=None
		self.animal_mapping=None
		self.inferencing_framesize=None
		self.load_detector(path_to_detector)


	def load_detector(self,path_to_detector):

		config=os.path.join(path_to_detector,'config.yaml')
		detector=os.path.join(path_to_detector,'model_final.pth')
		animalmapping=os.path.join(path_to_detector,'model_parameters.txt')

		with open(animalmapping) as f:
			model_parameters=f.read()
		self.animal_names=json.loads(model_parameters)['animal_names']
		self.animal_mapping=json.loads(model_parameters)['animal_mapping']
		self.inferencing_framesize=int(json.loads(model_parameters)['inferencing_framesize'])
		print('The animals / objects in this Detector: '+str(self.animal_names))
		print('The inferencing framesize of this Detector: '+str(self.inferencing_framesize))

		cfg=get_cfg()
		cfg.merge_from_file(config)
		cfg.MODEL.DEVICE='cuda' if torch.cuda.is_available() else 'cpu'
		self.detector=build_model(cfg)
		DetectionCheckpointer(self.detector).load(detector)
		self.detector.eval()


	def detect_animals(self,frame,animal_number=1,kernel=3,include_bodyparts=False,animation_analyzer=False,channel=1):

		contours={}
		centers={}
		heights={}
		inners={}
		blobs={}
		area={}
		goodcontours={}
		goodmasks={}

		for animal_name in self.animal_names:
			contours[animal_name]=[]
			centers[animal_name]=[]
			heights[animal_name]=[]
			inners[animal_name]=[]
			blobs[animal_name]=[]
			goodcontours[animal_name]=[]
			goodmasks[animal_name]=[]

		tensor_frame=torch.as_tensor(frame.astype("float32").transpose(2,0,1))

		with torch.no_grad():
			output=self.detector([{"image":tensor_frame}])

		instances=output[0]['instances'].to('cpu')

		masks=instances.pred_masks.numpy().astype(np.uint8)
		classes=instances.pred_classes.numpy()
		scores=instances.scores.numpy()

		mask_area=[np.sum(mask) for mask in masks]
		exclusion_mask=np.zeros(len(masks),dtype=bool)

		for i,mask_i in enumerate(masks):
			size_i=mask_area[i]
			for j,mask_j in enumerate(masks):
				if i==j:
					continue
				intersection=np.logical_and(mask_i,mask_j)
				intersection_area=np.sum(intersection)
				iou=intersection_area/size_i
				if iou>0.8 and mask_area[j]>size_i:
					exclusion_mask[i]=True
					break

		masks=[masks[i] for i,exclude in enumerate(exclusion_mask) if not exclude]
		classes=[classes[i] for i,exclude in enumerate(exclusion_mask) if not exclude]
		scores=[scores[i] for i,exclude in enumerate(exclusion_mask) if not exclude]

		if len(scores)>animal_number*3:
			sorted_scores_indices=np.argsort(scores)[-int(animal_number*3):]
			masks=[masks[i] for i in sorted_scores_indices]
			classes=[classes[i] for i in sorted_scores_indices]

		for i,mask in enumerate(masks):
			animal_name=self.animal_mapping[str(classes[i])]
			mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
			cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
			cnt=sorted(cnts,key=cv2.contourArea,reverse=True)[0]
			goodcontours[animal_name].append(cnt)
			goodmasks[animal_name].append(mask)

		for animal_name in list(contours.keys()):

			if len(goodcontours[animal_name])>0:
				areas=[cv2.contourArea(ct) for ct in goodcontours[animal_name]]
				areas_sorted=sorted(areas)
				areas=np.array(areas)
				sorted_area_indices=np.argsort(areas)[-animal_number:]
				areas_sorted=areas_sorted[-animal_number:]
				area[animal_name]=sum(areas_sorted)/len(areas_sorted)

				for i in sorted_area_indices:
					cnt=goodcontours[animal_name][i]
					mask=goodmasks[animal_name][i]
					contours[animal_name].append(cnt)
					centers[animal_name].append((int(cv2.moments(cnt)['m10']/cv2.moments(cnt)['m00']),int(cv2.moments(cnt)['m01']/cv2.moments(cnt)['m00'])))  
					(_,_),(w,h),_=cv2.minAreaRect(cnt)
					heights[animal_name].append(max(w,h))
					if include_bodyparts is True:
						masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
						inners[animal_name].append(get_inner(masked_frame,cnt))
					if animation_analyzer is True:
						masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
						x,y,w,h=cv2.boundingRect(cnt)
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
						blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
						blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
						if channel==1:
							blob=img_to_array(blob)
						else:
							blob=cv2.cvtColor(blob,cv2.COLOR_GRAY2BGR)
						blobs[animal_name].append(blob)

		return contours,centers,heights,inners,blobs,area


	def detect_animals_batch(self,frames,animal_number=1,kernel=3,include_bodyparts=False,animation_analyzer=False,channel=1):

		contours_dict={}
		centers_dict={}
		heights_dict={}
		inners_dict={}
		blobs_dict={}
		area_dict={}

		tensor_frames=[torch.as_tensor(frame.astype("float32").transpose(2,0,1)) for frame in frames]
		inputs=[{"image":tensor_frame} for tensor_frame in tensor_frames]

		with torch.no_grad():
			outputs=self.detector(inputs)

		for i,output in enumerate(outputs):

			instances=outputs[i]['instances'].to('cpu')
			masks=instances.pred_masks.numpy().astype(np.uint8)
			classes=instances.pred_classes.numpy()
			scores=instances.scores.numpy()

			contours={}
			centers={}
			heights={}
			inners={}
			blobs={}
			area={}
			goodcontours={}
			goodmasks={}

			for animal_name in self.animal_names:
				contours[animal_name]=[]
				centers[animal_name]=[]
				heights[animal_name]=[]
				inners[animal_name]=[]
				blobs[animal_name]=[]
				goodcontours[animal_name]=[]
				goodmasks[animal_name]=[]

			mask_area=[np.sum(mask) for mask in masks]
			exclusion_mask=np.zeros(len(masks),dtype=bool)

			for n,mask_n in enumerate(masks):
				size_n=mask_area[n]
				for m,mask_m in enumerate(masks):
					if n==m:
						continue
					intersection=np.logical_and(mask_n,mask_m)
					intersection_area=np.sum(intersection)
					iou=intersection_area/size_n
					if iou>0.8 and mask_area[m]>size_n:
						exclusion_mask[n]=True
						break

			masks=[masks[x] for x,exclude in enumerate(exclusion_mask) if not exclude]
			classes=[classes[x] for x,exclude in enumerate(exclusion_mask) if not exclude]
			scores=[scores[x] for x,exclude in enumerate(exclusion_mask) if not exclude]

			if len(scores)>animal_number*3:
				sorted_scores_indices=np.argsort(scores)[-int(animal_number*3):]
				masks=[masks[x] for x in sorted_scores_indices]
				classes=[classes[x] for x in sorted_scores_indices]

			for j,mask in enumerate(masks):
				animal_name=self.animal_mapping[str(classes[j])]
				mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((kernel,kernel),np.uint8))
				cnts,_=cv2.findContours((mask*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
				cnt=sorted(cnts,key=cv2.contourArea,reverse=True)[0]
				goodcontours[animal_name].append(cnt)
				goodmasks[animal_name].append(mask)

			for animal_name in list(contours.keys()):
				if len(goodcontours[animal_name])>0:
					areas=[cv2.contourArea(ct) for ct in goodcontours[animal_name]]
					areas_sorted=sorted(areas)
					areas=np.array(areas)
					sorted_area_indices=np.argsort(areas)[-animal_number:]
					areas_sorted=areas_sorted[-animal_number:]
					area[animal_name]=sum(areas_sorted)/len(areas_sorted)

					for x in sorted_area_indices:
						cnt=goodcontours[animal_name][x]
						mask=goodmasks[animal_name][x]
						contours[animal_name].append(cnt)
						centers[animal_name].append((int(cv2.moments(cnt)['m10']/cv2.moments(cnt)['m00']),int(cv2.moments(cnt)['m01']/cv2.moments(cnt)['m00'])))  
						(_,_),(w,h),_=cv2.minAreaRect(cnt)
						heights[animal_name].append(max(w,h))
						if include_bodyparts is True:
							masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
							inners[animal_name].append(get_inner(masked_frame,cnt))
						if animation_analyzer is True:
							masked_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)*mask
							x,y,w,h=cv2.boundingRect(cnt)
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
							blob=masked_frame[y_bt:y_tp,x_lf:x_rt]
							blob=np.uint8(exposure.rescale_intensity(blob,out_range=(0,255)))
							if channel==1:
								blob=img_to_array(blob)
							else:
								blob=cv2.cvtColor(blob,cv2.COLOR_GRAY2BGR)
							blobs[animal_name].append(blob)

			contours_dict[i]=contours
			centers_dict[i]=centers
			heights_dict[i]=heights
			inners_dict[i]=inners
			blobs_dict[i]=blobs
			area_dict[i]=area

		return contours_dict,centers_dict,heights_dict,inners_dict,blobs_dict,area_dict


	def test_detector(self,path_to_video,out_path,duration=0,animal_number=1):

		print(datetime.datetime.now())

		capture=cv2.VideoCapture(path_to_video)
		fps=round(capture.get(cv2.CAP_PROP_FPS))
		width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
		height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

		writer=cv2.VideoWriter(os.path.join(out_path,'Annotated_testing_video.avi'),cv2.VideoWriter_fourcc(*'MJPG'),fps,(width,height))

		frame_count=0
		end_count=duration*fps

		while True:

			ret,frame=capture.read()
			if not ret:
				break
			if end_count>0:
				if frame_count>=end_count:
					break
			if (frame_count+1)%500==0:
				print(str(frame_count+1)+' frames analyzed...')
				print(datetime.datetime.now())

			contours_all,centers_all,_,_,_,_=self.detect_animals(frame,animal_number=animal_number,kernel=3,include_bodyparts=False,animation_analyzer=False,channel=3)

			for animal_name in list(contours_all.keys()):
				if len(contours_all[animal_name])>0:
					for i,contour in enumerate(contours_all[animal_name]):
						frame=cv2.drawContours(frame,[contour],0,(255,255,255),2)
						cv2.putText(frame,str(animal_name),(centers_all[animal_name][i][0]-10,centers_all[animal_name][i][1]-10),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1)

			writer.write(frame)
			frame_count+=1

		capture.release()
		writer.release()

		print('Testing completed!')
		print(datetime.datetime.now())



