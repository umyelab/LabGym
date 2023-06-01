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
from .gui_categorizers import WindowLv1_GenerateExamples,WindowLv1_TrainCategorizers,WindowLv1_TestCategorizers
from .gui_detectors import WindowLv1_GenerateImages,WindowLv1_TrainDetectors,WindowLv1_TestDetectors
from .gui_preprocessor import WindowLv1_PreprossData
from .gui_analyzers import WindowLv1_AnalyzeBehaviors
from .gui_miners import WindowLv1_MineResults



current_version=1.9
current_version_check=19

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

		super(InitialWindow,self).__init__(parent=None,title=title,size=(750,500))
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
		userguide=wx.lib.agw.hyperlink.HyperLinkCtrl(panel,0,'User Guide',URL="https://github.com/yujiahu415/LabGym/blob/master/The%20full%20manual%20of%20LabGym_v1.9.pdf")
		links.Add(homepage,0,wx.LEFT|wx.EXPAND,10)
		links.Add(userguide,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(links,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,30,0)

		module_detectors=wx.BoxSizer(wx.HORIZONTAL)
		button_generateimages=wx.Button(panel,label='Generate Object Images',size=(200,40))
		button_generateimages.Bind(wx.EVT_BUTTON,self.generate_images)
		button_traindetectors=wx.Button(panel,label='Train Detectors',size=(200,40))
		button_traindetectors.Bind(wx.EVT_BUTTON,self.train_detectors)
		button_testdetectors=wx.Button(panel,label='Test Detectors',size=(200,40))
		button_testdetectors.Bind(wx.EVT_BUTTON,self.test_detectors)		
		module_detectors.Add(button_generateimages,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detectors.Add(button_traindetectors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detectors.Add(button_testdetectors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_detectors,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,10,0)

		module_categorizers=wx.BoxSizer(wx.HORIZONTAL)
		button_generateexamples=wx.Button(panel,label='Generate Behavior Examples',size=(200,40))
		button_generateexamples.Bind(wx.EVT_BUTTON,self.generate_examples)
		button_traincategorizers=wx.Button(panel,label='Train Categorizers',size=(200,40))
		button_traincategorizers.Bind(wx.EVT_BUTTON,self.train_categorizers)
		button_testcategorizers=wx.Button(panel,label='Test Categorizers',size=(200,40))
		button_testcategorizers.Bind(wx.EVT_BUTTON,self.test_categorizers)		
		module_categorizers.Add(button_generateexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizers.Add(button_traincategorizers,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizers.Add(button_testcategorizers,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_categorizers,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,10,0)

		module_analysis=wx.BoxSizer(wx.HORIZONTAL)
		button_preprocessdata=wx.Button(panel,label='Preprocess Data',size=(200,40))
		button_preprocessdata.Bind(wx.EVT_BUTTON,self.preprocess_data)
		button_analyzebehaviors=wx.Button(panel,label='Analyze Behaviors',size=(200,40))
		button_analyzebehaviors.Bind(wx.EVT_BUTTON,self.analyze_behaviors)
		button_mineresults=wx.Button(panel,label='Mine Analysis Results',size=(200,40))
		button_mineresults.Bind(wx.EVT_BUTTON,self.mine_results)
		module_analysis.Add(button_preprocessdata,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_analysis.Add(button_analyzebehaviors,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_analysis.Add(button_mineresults,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_analysis,0,wx.ALIGN_CENTER,50)
		boxsizer.Add(0,50,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def generate_images(self,event):

		WindowLv1_GenerateImages('Generate Object Images')


	def train_detectors(self,event):

		WindowLv1_TrainDetectors('Train Detectors')


	def test_detectors(self,event):

		WindowLv1_TestDetectors('Test Detectors')


	def generate_examples(self,event):

		WindowLv1_GenerateExamples('Generate Behavior Examples')


	def train_categorizers(self,event):

		WindowLv1_TrainCategorizers('Train Categorizers')


	def test_categorizers(self,event):

		WindowLv1_TestCategorizers('Test Categorizers')


	def preprocess_data(self,event):

		WindowLv1_PreprossData('Preprocess Data')


	def analyze_behaviors(self,event):

		WindowLv1_AnalyzeBehaviors('Analyze Behaviors')
		

	def mine_results(self,event):

		WindowLv1_MineResults('Mine Analysis Results')




def gui():

	the_absolute_current_path=str(Path(__file__).resolve().parent)

	app=wx.App()
	
	InitialWindow('LabGym version '+str(current_version))

	print('The user interface initialized!')
	
	app.MainLoop()




if __name__=='__main__':

	gui()








