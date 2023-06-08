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



from .detectanimals import DetectAnimals
import os
import json
import torch
try:
	from detectron2 import model_zoo
	from detectron2.checkpoint import DetectionCheckpointer
	from detectron2.config import get_cfg
	from detectron2.data import MetadataCatalog,DatasetCatalog
	from detectron2.data.datasets import register_coco_instances
	from detectron2.engine import DefaultTrainer,DefaultPredictor
except:
	print('You need to install Detectron2 to use the Detector module in LabGym:')
	print('https://detectron2.readthedocs.io/en/latest/tutorials/install.html')



class TrainTestDetectors():

	def __init__(self):
		pass


	def train_the_detector(self,path_to_detector,path_to_trainingimages,path_to_annotation,inference_size=640,iteration_num=500):

		if torch.cuda.is_available():
			device='cuda'
		else:
			device='cpu'

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
		cfg.MODEL.DEVICE=device
		cfg.INPUT.MIN_SIZE_TEST=int(inference_size)
		cfg.INPUT.MAX_SIZE_TEST=int(inference_size)
		cfg.INPUT.MIN_SIZE_TRAIN=(int(inference_size),)
		cfg.INPUT.MAX_SIZE_TRAIN=int(inference_size)
		os.makedirs(cfg.OUTPUT_DIR,exist_ok=True)
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

		print("Detector training completed!")


	def test_the_detector(self,path_to_detector,path_to_video,out_path,duration=10,animal_number=1):

		DA=DetectAnimals(path_to_detector)
		DA.run_test(path_to_video,out_path,duration=duration,animal_number=animal_number)


