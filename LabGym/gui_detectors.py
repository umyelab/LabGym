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



from .tools import extract_frames
from pathlib import Path
import wx
import os
import json
import shutil
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



the_absolute_current_path=str(Path(__file__).resolve().parent)



class WindowLv2_GenerateImages(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_GenerateImages,self).__init__(parent=None,title=title,size=(1000,330))
		self.path_to_videos=None
		self.result_path=None
		self.framewidth=None
		self.t=0
		self.duration=0
		self.skip_redundant=1000

		self.dispaly_window()

	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s) to generate\nimage examples',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		wx.Button.SetToolTip(button_inputvideos,'Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.')
		self.text_inputvideos=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store the\ngenerated image examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'The generated image examples (extracted frames) will be stored in this folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startgenerate=wx.BoxSizer(wx.HORIZONTAL)
		button_startgenerate=wx.Button(panel,label='Specify when generating image examples\nshould begin (unit: second)',size=(300,40))
		button_startgenerate.Bind(wx.EVT_BUTTON,self.specify_timing)
		wx.Button.SetToolTip(button_startgenerate,'Enter a beginning time point for all videos')
		self.text_startgenerate=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startgenerate.Add(button_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startgenerate.Add(self.text_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify how long generating examples\nshould last (unit: second)',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		wx.Button.SetToolTip(button_duration,'This duration will be used for all the videos.')
		self.text_duration=wx.StaticText(panel,label='Default: from the specified beginning time to the end of a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_skipredundant=wx.BoxSizer(wx.HORIZONTAL)
		button_skipredundant=wx.Button(panel,label='Specify how many frames to skip when\ngenerating two consecutive images',size=(300,40))
		button_skipredundant.Bind(wx.EVT_BUTTON,self.specify_redundant)
		wx.Button.SetToolTip(button_skipredundant,'To increase the efficiency of training a Detector, you need to make the training images as diverse (look different) as possible. You can do this by setting an interval between the two consecutively extracted images.')
		self.text_skipredundant=wx.StaticText(panel,label='Default: generate an image example every 1000 frames.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_skipredundant.Add(button_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_skipredundant.Add(self.text_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		generate=wx.BoxSizer(wx.HORIZONTAL)
		button_generate=wx.Button(panel,label='Start to generate image examples',size=(300,40))
		button_generate.Bind(wx.EVT_BUTTON,self.generate_images)
		wx.Button.SetToolTip(button_generate,'Press the button to start generating image examples.')
		generate.Add(button_generate,0,wx.LEFT,50)
		boxsizer.Add(0,5,0)
		boxsizer.Add(generate,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_videos(self,event):

		wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'
		dialog=wx.FileDialog(self,'Select video(s)','','',wildcard,style=wx.FD_MULTIPLE)

		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			path=os.path.dirname(self.path_to_videos[0])
			dialog2=wx.MessageDialog(self,'Proportional resize the video frames?\nSelect "No" if dont know what it is.','(Optional) resize the frames?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				dialog3=wx.NumberEntryDialog(self,'Enter the desired frame width','The unit is pixel:','Desired frame width',480,1,10000)
				if dialog3.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog3.GetValue())
					if self.framewidth<10:
						self.framewidth=10
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (proportionally resize framewidth to '+str(self.framewidth)+').')
				else:
					self.framewidth=None
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
				dialog3.Destroy()
			else:
				self.framewidth=None
				self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' video(s) in: '+path+' (original framesize).')
			dialog2.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Generate image examples in: '+self.result_path+'.')
		dialog.Destroy()


	def specify_timing(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter beginning time to generate examples','The unit is second:','Beginning time to generate examples',0,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.t=float(dialog.GetValue())
			if self.t<0:
				self.t=0
			self.text_startgenerate.SetLabel('Start to generate image examples at the: '+str(self.t)+' second.')
		dialog.Destroy()


	def input_duration(self,event):

		dialog=wx.NumberEntryDialog(self,'Enter the duration for generating examples','The unit is second:','Duration for generating examples',0,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.duration=int(dialog.GetValue())
			if self.duration!=0:
				self.text_duration.SetLabel('The generation of image examples lasts for '+str(self.duration)+' seconds.')
		dialog.Destroy()


	def specify_redundant(self,event):

		dialog=wx.NumberEntryDialog(self,'How many frames to skip?','Enter a number:','Interval for generating examples',15,0,100000000000000)
		if dialog.ShowModal()==wx.ID_OK:
			self.skip_redundant=int(dialog.GetValue())
			self.text_skipredundant.SetLabel('Generate an image example every '+str(self.skip_redundant)+' frames.')
		else:
			self.skip_redundant=1000
			self.text_skipredundant.SetLabel('Generate an image example every 10000 frames.')
		dialog.Destroy()


	def generate_images(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=True

			dialog=wx.MessageDialog(self,'Start to generate image examples?','Start to generate examples?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				do_nothing=False
			else:
				do_nothing=True
			dialog.Destroy()

			if do_nothing is False:
				print('Generating image examples...')
				for i in self.path_to_videos:
					extract_frames(i,self.result_path,framewidth=self.framewidth,start_t=self.t,duration=self.duration,skip_redundant=self.skip_redundant)
				print('Image example generation completed!')



class WindowLv2_TrainDetectors(wx.Frame):

	def __init__(self,title):

		super(WindowLv2_TrainDetectors,self).__init__(parent=None,title=title,size=(1000,280))
		self.path_to_trainingimages=None
		self.path_to_annotation=None
		self.inference_size=320
		self.iteration_num=200
		self.detector_path=os.path.join(the_absolute_current_path,'detectors')
		self.path_to_detector=None

		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_selectimages=wx.BoxSizer(wx.HORIZONTAL)
		button_selectimages=wx.Button(panel,label='Select the folder containing\nall the training images',size=(300,40))
		button_selectimages.Bind(wx.EVT_BUTTON,self.select_images)
		wx.Button.SetToolTip(button_selectimages,'The folder that stores all the training images.')
		self.text_selectimages=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectimages.Add(button_selectimages,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectimages.Add(self.text_selectimages,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_selectimages,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectannotation=wx.BoxSizer(wx.HORIZONTAL)
		button_selectannotation=wx.Button(panel,label='Select the *.json\nannotation file',size=(300,40))
		button_selectannotation.Bind(wx.EVT_BUTTON,self.select_annotation)
		wx.Button.SetToolTip(button_selectannotation,'The .json file that stores the annotation for the training images. Make sure it is in “COCO instance segmentation” format.')
		self.text_selectannotation=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectannotation.Add(button_selectannotation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectannotation.Add(self.text_selectannotation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectannotation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inferencingsize=wx.BoxSizer(wx.HORIZONTAL)
		button_inferencingsize=wx.Button(panel,label='Specify the inferencing framesize\nfor the Detector to train',size=(300,40))
		button_inferencingsize.Bind(wx.EVT_BUTTON,self.input_inferencingsize)
		wx.Button.SetToolTip(button_inferencingsize,'This number should be divisible by 32. It determines the speed-accuracy trade-off of Detector performance. Larger size means higher accuracy but slower speed. See Extended Guide for recommendation.')
		self.text_inferencingsize=wx.StaticText(panel,label='Default: 320.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inferencingsize.Add(button_inferencingsize,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inferencingsize.Add(self.text_inferencingsize,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inferencingsize,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_iterations=wx.BoxSizer(wx.HORIZONTAL)
		button_iterations=wx.Button(panel,label='Specify the iteration number\nfor the Detector training',size=(300,40))
		button_iterations.Bind(wx.EVT_BUTTON,self.input_iterations)
		wx.Button.SetToolTip(button_iterations,'The number of training loops. More iterations typically yield better accuracy but too many may cause overfitting. A number between 100 ~ 500 is good for most scenarios. Instead of increasing iterations, you may rather increase the diversity and amount of training images.')
		self.text_iterations=wx.StaticText(panel,label='Default: 200.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_iterations.Add(button_iterations,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_iterations.Add(self.text_iterations,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_iterations,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		trainanddelete=wx.BoxSizer(wx.HORIZONTAL)
		button_train=wx.Button(panel,label='Train the Detector',size=(300,40))
		button_train.Bind(wx.EVT_BUTTON,self.train_detector)
		wx.Button.SetToolTip(button_train,'You need to name the Detector to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.')
		button_delete=wx.Button(panel,label='Delete a Detector',size=(300,40))
		button_delete.Bind(wx.EVT_BUTTON,self.remove_detector)
		wx.Button.SetToolTip(button_delete,'Permanently delete a Detector. The deletion CANNOT be restored.')
		trainanddelete.Add(button_train,0,wx.RIGHT,50)
		trainanddelete.Add(button_delete,0,wx.LEFT,50)
		boxsizer.Add(0,5,0)
		boxsizer.Add(trainanddelete,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_images(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_trainingimages=dialog.GetPath()
			self.text_selectimages.SetLabel('Path to training images: '+self.path_to_trainingimages+'.')
		dialog.Destroy()


	def select_annotation(self,event):

		wildcard='Annotation File (*.json)|*.json'
		dialog=wx.FileDialog(self, 'Select the annotation file (.json)','',wildcard=wildcard,style=wx.FD_OPEN)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_annotation=dialog.GetPath()
			f=open(self.path_to_annotation)
			info=json.load(f)
			classnames=[]
			for i in info['categories']:
				if i['id']>0:
					classnames.append(i['name'])
			self.text_selectannotation.SetLabel('Animal/object categories in annotation file: '+str(classnames)+'.')
		dialog.Destroy()


	def input_inferencingsize(self,event):

		dialog=wx.NumberEntryDialog(self,'Input the inferencing frame size\nof the Detector to train','Enter a number:','Divisible by 32',480,1,2048)
		if dialog.ShowModal()==wx.ID_OK:
			self.inference_size=int(dialog.GetValue())
			self.text_inferencingsize.SetLabel('Input inferencing frame size: '+str(self.inference_size)+'.')
		dialog.Destroy()
		

	def input_iterations(self,event):

		dialog=wx.NumberEntryDialog(self,'Input the iteration number\nfor the Detector training','Enter a number:','Iterations',200,1,2000)
		if dialog.ShowModal()==wx.ID_OK:
			self.iteration_num=int(dialog.GetValue())
			self.text_iterations.SetLabel('Input iteration number: '+str(self.iteration_num)+'.')
		dialog.Destroy()


	def train_detector(self,event):

		if self.path_to_trainingimages is None or self.path_to_annotation is None:

			wx.MessageBox('No training images / annotation file selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=False

			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter a name for the Detector to train','Detector name')
				if dialog.ShowModal()==wx.ID_OK:
					if dialog.GetValue()!='':
						self.path_to_detector=os.path.join(self.detector_path,dialog.GetValue())
						if not os.path.isdir(self.path_to_detector):
							stop=True
						else:
							wx.MessageBox('The name already exists.','Error',wx.OK|wx.ICON_ERROR)
				else:
					do_nothing=True
					stop=True
				dialog.Destroy()

			if do_nothing is False:

				if torch.cuda.is_available():
					device='cuda'
				else:
					device='cpu'

				if str('LabGym_detector_train') in DatasetCatalog.list():
					DatasetCatalog.remove('LabGym_detector_train')
					MetadataCatalog.remove('LabGym_detector_train')
				register_coco_instances('LabGym_detector_train',{},self.path_to_annotation,self.path_to_trainingimages)
				datasetcat=DatasetCatalog.get('LabGym_detector_train')
				metadatacat=MetadataCatalog.get('LabGym_detector_train')
				classnames=metadatacat.thing_classes

				model_parameters_dict={}
				model_parameters_dict['animal_names']=[]
				annotation_data=json.load(open(self.path_to_annotation))
				for i in annotation_data['categories']:
					if i['id']>0:
						model_parameters_dict['animal_names'].append(i['name'])
				print('Animal names in annotation file: '+str(model_parameters_dict['animal_names']))

				cfg=get_cfg()
				cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
				cfg.OUTPUT_DIR=self.path_to_detector
				cfg.DATASETS.TRAIN=('LabGym_detector_train',)
				cfg.DATASETS.TEST=()
				cfg.DATALOADER.NUM_WORKERS=4
				cfg.MODEL.WEIGHTS=model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
				cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE=128
				cfg.MODEL.ROI_HEADS.NUM_CLASSES=int(len(classnames))
				cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST=0.5
				cfg.SOLVER.MAX_ITER=int(self.iteration_num)
				cfg.SOLVER.BASE_LR=0.001
				cfg.SOLVER.WARMUP_ITERS=int(self.iteration_num*0.1)
				cfg.SOLVER.STEPS=(int(self.iteration_num*0.4),int(self.iteration_num*0.8))
				cfg.SOLVER.GAMMA=0.5
				cfg.SOLVER.IMS_PER_BATCH=4
				cfg.MODEL.DEVICE=device
				cfg.INPUT.MIN_SIZE_TEST=int(self.inference_size)
				cfg.INPUT.MAX_SIZE_TEST=int(self.inference_size)
				cfg.INPUT.MIN_SIZE_TRAIN=(int(self.inference_size),)
				cfg.INPUT.MAX_SIZE_TRAIN=int(self.inference_size)
				os.makedirs(cfg.OUTPUT_DIR)
				trainer=DefaultTrainer(cfg)
				trainer.resume_or_load(False)
				trainer.train()

				model_parameters=os.path.join(cfg.OUTPUT_DIR,'model_parameters.txt')
				
				model_parameters_dict['animal_mapping']={}
				model_parameters_dict['inferencing_framesize']=int(self.inference_size)

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


	def remove_detector(self,event):

		detectors=[i for i in os.listdir(self.detector_path) if os.path.isdir(os.path.join(self.detector_path,i))]
		if '__pycache__' in detectors:
			detectors.remove('__pycache__')
		if '__init__' in detectors:
			detectors.remove('__init__')
		if '__init__.py' in detectors:
			detectors.remove('__init__.py')
		detectors.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Detector to delete',caption='Delete a Detector',choices=detectors)
		if dialog.ShowModal()==wx.ID_OK:
			detector=dialog.GetStringSelection()
			dialog2=wx.MessageDialog(self,'Delete '+str(detector)+'?','CANNOT be restored!',wx.YES_NO|wx.ICON_QUESTION)
			if dialog2.ShowModal()==wx.ID_YES:
				shutil.rmtree(os.path.join(self.detector_path,detector))
			dialog2.Destroy()
		dialog.Destroy()


