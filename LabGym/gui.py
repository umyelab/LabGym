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



import wx
import wx.lib.agw.hyperlink as hl
import json
from urllib import request
from pathlib import Path
from .gui_categorizers import WindowLv2_GenerateExamples,WindowLv2_TrainCategorizers
from .gui_detectors import WindowLv2_GenerateImages,WindowLv2_TrainDetectors
from .gui_preprocessors import WindowLv2_ProcessVideos,WindowLv2_SortBehaviors
from .gui_analyzers import WindowLv2_AnalyzeBehaviors,WindowLv2_MineResults



current_version=2.0
current_version_check=20.1

try:

	latest_version=list(json.loads(request.urlopen('https://pypi.python.org/pypi/LabGym/json').read())['releases'].keys())[-1]
	latest_version_str=list(latest_version)
	latest_version_str.remove('.')
	latest_version_check=latest_version_str[0]
	for i in latest_version_str[1:]:
		latest_version_check+=i
	latest_version_check=float(latest_version_check)
	if latest_version_check>current_version_check:
		print('A newer version '+'('+str(latest_version)+')'+' of LabGym is available. You may upgrade it by "python3 -m pip install --upgrade LabGym".\nFor the details of new changes, check: "https://github.com/umyelab/LabGym".')

except:
	
	pass



class InitialWindow(wx.Frame):

	def __init__(self,title):

		super(InitialWindow,self).__init__(parent=None,title=title,size=(750,440))
		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		self.text_welcome=wx.StaticText(panel,label='Welcome to LabGym!',style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(0,60,0)
		boxsizer.Add(self.text_welcome,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,60,0)
		self.text_developers=wx.StaticText(panel,label='Developed by Yujia Hu, Kelly Goss, Isabelle Baker\n\nBing Ye Lab, Life Sciences Institute, University of Michigan',style=wx.ALIGN_CENTER|wx.ST_ELLIPSIZE_END)
		boxsizer.Add(self.text_developers,0,wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		boxsizer.Add(0,60,0)
		
		links=wx.BoxSizer(wx.HORIZONTAL)
		homepage=wx.lib.agw.hyperlink.HyperLinkCtrl(panel,0,'Home Page',URL='https://github.com/umyelab/LabGym')
		userguide=wx.lib.agw.hyperlink.HyperLinkCtrl(panel,0,'Extended Guide',URL='https://github.com/yujiahu415/LabGym/blob/master/LabGym%20user%20guide_v2.0.pdf')
		links.Add(homepage,0,wx.LEFT|wx.EXPAND,10)
		links.Add(userguide,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(links,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		module_modules=wx.BoxSizer(wx.HORIZONTAL)
		button_preprocess=wx.Button(panel,label='Preprocessing Module',size=(200,40))
		button_preprocess.Bind(wx.EVT_BUTTON,self.window_preprocess)
		wx.Button.SetToolTip(button_preprocess,'Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.')
		button_train=wx.Button(panel,label='Training Module',size=(200,40))
		button_train.Bind(wx.EVT_BUTTON,self.window_train)
		wx.Button.SetToolTip(button_train,'Teach LabGym to recognize the animals / objects of your interest and identify their behaviors that are defined by you.')
		button_analyze=wx.Button(panel,label='Analysis Module',size=(200,40))
		button_analyze.Bind(wx.EVT_BUTTON,self.window_analyze)
		wx.Button.SetToolTip(button_analyze,'Use LabGym to track the animals / objects of your interest, quantify their behaviors, and let LabGym show you the significant findings.')
		module_modules.Add(button_preprocess,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_modules.Add(button_train,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_modules.Add(button_analyze,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_modules,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def window_preprocess(self,event):

		WindowLv1_ProcessModule('Preprocessing Module')


	def window_train(self,event):

		WindowLv1_TrainingModule('Training Module')


	def window_analyze(self,event):

		WindowLv1_AnalysisModule('Analysis Module')



class WindowLv1_ProcessModule(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_ProcessModule,self).__init__(parent=None,title=title,size=(500,150))
		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,40,0)

		button_processvideos=wx.Button(panel,label='Preprocess Videos',size=(300,40))
		button_processvideos.Bind(wx.EVT_BUTTON,self.process_videos)
		wx.Button.SetToolTip(button_processvideos,'Enhance video contrast / crop frames to exclude unnecessary region / trim videos to only keep necessary time windows.')
		boxsizer.Add(button_processvideos,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def process_videos(self,event):

		WindowLv2_ProcessVideos('Preprocess Videos')



class WindowLv1_TrainingModule(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_TrainingModule,self).__init__(parent=None,title=title,size=(500,480))
		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,60,0)

		button_generateimages=wx.Button(panel,label='Generate Image Examples',size=(300,40))
		button_generateimages.Bind(wx.EVT_BUTTON,self.generate_images)
		wx.Button.SetToolTip(button_generateimages,'Extract frames from videos for annotating animals / objects in them so that they can be used to train a Detector to detect animals / objects of your interest.')
		boxsizer.Add(button_generateimages,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		link_annotate=wx.lib.agw.hyperlink.HyperLinkCtrl(panel,0,'\nAnnotate images with Roboflow\n',URL='https://roboflow.com')
		boxsizer.Add(link_annotate,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_traindetectors=wx.Button(panel,label='Train Detectors',size=(300,40))
		button_traindetectors.Bind(wx.EVT_BUTTON,self.train_detectors)
		wx.Button.SetToolTip(button_traindetectors,'There are two detection methods in LabGym, the Detector-based method is more versatile (useful in any recording conditions and complex social behaviors) but slower than the other background subtraction-based method (requires static background and stable illumination in videos).')
		boxsizer.Add(button_traindetectors,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,50,0)

		button_generatebehaviorexamples=wx.Button(panel,label='Generate Behavior Examples',size=(300,40))
		button_generatebehaviorexamples.Bind(wx.EVT_BUTTON,self.generate_behaviorexamples)
		wx.Button.SetToolTip(button_generatebehaviorexamples,'Generate behavior examples for sorting them so that they can be used to teach a Categorizer to recognize behaviors defined by you.')
		boxsizer.Add(button_generatebehaviorexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_sortbehaviorexamples=wx.Button(panel,label='Sort Behavior Examples',size=(300,40))
		button_sortbehaviorexamples.Bind(wx.EVT_BUTTON,self.sort_behaviorexamples)
		wx.Button.SetToolTip(button_sortbehaviorexamples,'Set shortcut keys for behavior categories to help sorting the behavior examples in an easier way.')
		boxsizer.Add(button_sortbehaviorexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,5,0)

		button_traincategorizers=wx.Button(panel,label='Train Categorizers',size=(300,40))
		button_traincategorizers.Bind(wx.EVT_BUTTON,self.train_categorizers)
		wx.Button.SetToolTip(button_traincategorizers,'Customize a Categorizer and use the sorted behavior examples to train it so that it can recognize the behaviors of your interest during analysis.')
		boxsizer.Add(button_traincategorizers,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,50,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def generate_images(self,event):

		WindowLv2_GenerateImages('Generate Image Examples')


	def train_detectors(self,event):

		WindowLv2_TrainDetectors('Train Detectors')


	def generate_behaviorexamples(self,event):

		WindowLv2_GenerateExamples('Generate Behavior Examples')


	def sort_behaviorexamples(self,event):

		WindowLv2_SortBehaviors('Sort Behavior Examples')


	def train_categorizers(self,event):

		WindowLv2_TrainCategorizers('Train Categorizers')



class WindowLv1_AnalysisModule(wx.Frame):

	def __init__(self,title):

		super(WindowLv1_AnalysisModule,self).__init__(parent=None,title=title,size=(500,220))
		self.dispaly_window()


	def dispaly_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		boxsizer.Add(0,40,0)

		button_analyzebehaviors=wx.Button(panel,label='Analyze Behaviors',size=(300,40))
		button_analyzebehaviors.Bind(wx.EVT_BUTTON,self.analyze_behaviors)
		wx.Button.SetToolTip(button_analyzebehaviors,'Automatically track animals / objects of your interest, identify and quantify their behaviors in videos.')
		boxsizer.Add(button_analyzebehaviors,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_mineresults=wx.Button(panel,label='Mine Results',size=(300,40))
		button_mineresults.Bind(wx.EVT_BUTTON,self.mine_results)
		wx.Button.SetToolTip(button_mineresults,'Automatically mine the analysis results to display the data details that show statistically significant differences among groups of your selection.')
		boxsizer.Add(button_mineresults,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def analyze_behaviors(self,event):

		WindowLv2_AnalyzeBehaviors('Analyze Behaviors')


	def mine_results(self,event):

		WindowLv2_MineResults('Mine Results')



def gui():

	the_absolute_current_path=str(Path(__file__).resolve().parent)

	app=wx.App()
	
	InitialWindow('LabGym version '+str(current_version))

	print('The user interface initialized!')
	
	app.MainLoop()



if __name__=='__main__':

	gui()








