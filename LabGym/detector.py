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
import cv2
import json
import torch
try:
	from detectron2 import model_zoo
	from detectron2.checkpoint import DetectionCheckpointer
	from detectron2.config import get_cfg
	from detectron2.data import MetadataCatalog,DatasetCatalog,build_detection_test_loader
	from detectron2.data.datasets import register_coco_instances
	from detectron2.engine import DefaultTrainer,DefaultPredictor
	from detectron2.utils.visualizer import Visualizer
	from detectron2.evaluation import COCOEvaluator,inference_on_dataset
	from detectron2.modeling import build_model
except:
	print('You need to install Detectron2 to use the Detector module in LabGym.')
	print('See installation instructions on LabGym GitHub page or here:')
	print('https://labgym.readthedocs.io/en/latest/installation/index.html')



class Detector():

	def __init__(self):

		self.device='cuda' if torch.cuda.is_available() else 'cpu' # whether the GPU is available, if so, use GPU
		self.animal_mapping=None # the animal categories and names in a Detector
		self.current_detector=None # the current Detector used for inference


	def train(self,path_to_annotation,path_to_trainingimages,path_to_detector,iteration_num,inference_size):

		# path_to_annotation: the path to the .json file that stores the annotations in coco format
		# path_to_trainingimages: the folder that stores all the training images
		# iteration_num: the number of training iterations
		# inference_size: the Detector inferencing frame size

		if str('LabGym_detector_train') in DatasetCatalog.list():
			DatasetCatalog.remove('LabGym_detector_train')
			MetadataCatalog.remove('LabGym_detector_train')

		register_coco_instances('LabGym_detector_train',{},path_to_annotation,path_to_trainingimages)

		datasetcat=DatasetCatalog.get('LabGym_detector_train')
		metadatacat=MetadataCatalog.get('LabGym_detector_train')

		classnames=metadatacat.thing_classes

		model_parameters_dict={}
		model_parameters_dict['animal_names']=[]

		annotation_data=json.load(open(path_to_annotation))

		for i in annotation_data['categories']:
			if i['id']>0:
				model_parameters_dict['animal_names'].append(i['name'])

		print('Animal names in annotation file: '+str(model_parameters_dict['animal_names']))

		cfg=get_cfg()
		cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
		cfg.OUTPUT_DIR=path_to_detector
		cfg.DATASETS.TRAIN=('LabGym_detector_train',)
		cfg.DATASETS.TEST=()
		cfg.DATALOADER.NUM_WORKERS=4
		cfg.MODEL.WEIGHTS=model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
		cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE=128
		cfg.MODEL.ROI_HEADS.NUM_CLASSES=int(len(classnames))
		cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST=0.5
		cfg.SOLVER.MAX_ITER=int(iteration_num)
		cfg.SOLVER.BASE_LR=0.001
		cfg.SOLVER.WARMUP_ITERS=int(iteration_num*0.1)
		cfg.SOLVER.STEPS=(int(iteration_num*0.4),int(iteration_num*0.8))
		cfg.SOLVER.GAMMA=0.5
		cfg.SOLVER.IMS_PER_BATCH=4
		cfg.MODEL.DEVICE=self.device
		cfg.INPUT.MIN_SIZE_TEST=int(inference_size)
		cfg.INPUT.MAX_SIZE_TEST=int(inference_size)
		cfg.INPUT.MIN_SIZE_TRAIN=(int(inference_size),)
		cfg.INPUT.MAX_SIZE_TRAIN=int(inference_size)
		os.makedirs(cfg.OUTPUT_DIR)

		trainer=DefaultTrainer(cfg)
		trainer.resume_or_load(False)
		trainer.train()

		model_parameters=os.path.join(cfg.OUTPUT_DIR,'model_parameters.txt')
		
		model_parameters_dict['animal_mapping']={}
		model_parameters_dict['inferencing_framesize']=int(inference_size)

		for i in range(len(classnames)):
			model_parameters_dict['animal_mapping'][i]=classnames[i]

		with open(model_parameters,'w') as f:
			f.write(json.dumps(model_parameters_dict))

		predictor=DefaultPredictor(cfg)
		model=predictor.model

		DetectionCheckpointer(model).resume_or_load(os.path.join(cfg.OUTPUT_DIR,'model_final.pth'))
		model.eval()

		config=os.path.join(cfg.OUTPUT_DIR,'config.yaml')

		with open(config,'w') as f:
			f.write(cfg.dump())

		print('Detector training completed!')


	def test(self,path_to_annotation,path_to_testingimages,path_to_detector,output_path):

		# path_to_annotation: the path to the .json file that stores the annotations in coco format
		# path_to_testingimages: the folder that stores all the ground-truth testing images
		# output_path: the folder that stores the testing images with annotations

		if str('LabGym_detector_test') in DatasetCatalog.list():
			DatasetCatalog.remove('LabGym_detector_test')
			MetadataCatalog.remove('LabGym_detector_test')

		register_coco_instances('LabGym_detector_test',{},path_to_annotation,path_to_testingimages)

		datasetcat=DatasetCatalog.get('LabGym_detector_test')
		metadatacat=MetadataCatalog.get('LabGym_detector_test')

		animalmapping=os.path.join(path_to_detector,'model_parameters.txt')

		with open(animalmapping) as f:
			model_parameters=f.read()

		animal_names=json.loads(model_parameters)['animal_names']
		dt_infersize=int(json.loads(model_parameters)['inferencing_framesize'])

		print('The total categories of animals in this Detector: '+str(animal_names))
		print('The inferencing framesize of this Detector: '+str(dt_infersize))

		cfg=get_cfg()
		cfg.merge_from_file(os.path.join(path_to_detector,'config.yaml'))
		cfg.MODEL.WEIGHTS=os.path.join(path_to_detector,'model_final.pth')
		cfg.MODEL.DEVICE=self.device

		predictor=DefaultPredictor(cfg)

		for d in datasetcat:
			im=cv2.imread(d['file_name'])
			outputs=predictor(im)
			v=Visualizer(im[:,:,::-1],MetadataCatalog.get('LabGym_detector_test'),scale=1.2)
			out=v.draw_instance_predictions(outputs['instances'].to('cpu'))
			cv2.imwrite(os.path.join(output_path,os.path.basename(d['file_name'])),out.get_image()[:,:,::-1])

		evaluator=COCOEvaluator('LabGym_detector_test',cfg,False,output_dir=output_path)
		val_loader=build_detection_test_loader(cfg,'LabGym_detector_test')

		inference_on_dataset(predictor.model,val_loader,evaluator)

		mAP=evaluator._results['bbox']['AP']

		print(f'The mean average precision (mAP) of the Detector is: {mAP:.4f}%.')
		print('Detector testing completed!')


	def load(self,path_to_detector,animal_kinds):

		# animal_kinds: the catgories of animals / objects to be analyzed

		config=os.path.join(path_to_detector,'config.yaml')
		detector_model=os.path.join(path_to_detector,'model_final.pth')
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
		cfg.MODEL.DEVICE=self.device
		self.current_detector=build_model(cfg)
		DetectionCheckpointer(self.current_detector).load(detector_model)
		self.current_detector.eval()


	def inference(self,inputs):

		# inputs: images that the current Detector runs on

		with torch.no_grad():
			outputs=self.current_detector(inputs)

		return outputs


