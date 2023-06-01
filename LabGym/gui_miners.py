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
import os
import pandas as pd
from .minedata import data_mining
from collections import OrderedDict

		

class WindowLv1_MineResults(wx.Frame):
	def __init__(self, title):
		super(WindowLv1_MineResults,self).__init__(parent=None,title=title,size=(1000,250))
		self.file_path = None
		self.result_path = None
		self.dataset = None
		self.paired = False
		self.control = None
		self.pval = 0.05
		self.file_names = []
		self.control_file_name = None
		self.display_window()


	def display_window(self):

		panel=wx.Panel(self)
		boxsizer=wx.BoxSizer(wx.VERTICAL)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that stores\nthe data files',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.select_filepath)
		self.text_inputfolder=wx.StaticText(panel,label='Files for the same experimental group should be stored in the same subfolder.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_selectcontrol=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcontrol=wx.Button(panel,label='Select the\ncontrol group',size=(300,40))
		button_selectcontrol.Bind(wx.EVT_BUTTON, self.select_control)
		self.text_selectcontrol=wx.StaticText(panel,label='Only select a control group if you are comparing it to at least 2 other groups.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcontrol.Add(button_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcontrol.Add(self.text_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_selectcontrol,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe data mining results',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_result_path)
		self.text_outputfolder=wx.StaticText(panel,label='The folder that stores all the results of data mining.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)


		button_minedata=wx.Button(panel,label='Start to mine data',size=(300,40))
		button_minedata.Bind(wx.EVT_BUTTON,self.mine_data)
		boxsizer.Add(button_minedata,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_filepath(self, event): #select folder containing Excel files of data

		dialog=wx.MessageDialog(self, 'Is the data paired?','Paired data?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.paired=True
		else:
			self.paired=False
		dialog.Destroy()

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			if self.paired is True:
				self.text_inputfolder.SetLabel('Paired input data is in: '+self.file_path+'.')
			else:
				self.text_inputfolder.SetLabel('Unpaired input data is in: '+self.file_path+'.')
		dialog.Destroy()


	def select_control(self, event):

		dialog = wx.SingleChoiceDialog(self, 'Select the folder for the control group', 
									   'Ignore if you wish to compare all groups',
									   choices=[i for i in os.listdir(self.file_path) if os.path.isdir(os.path.join(self.file_path,i))],
									   style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			control_path=dialog.GetStringSelection()
			self.text_selectcontrol.SetLabel("The control group is '"+control_path+"'.")
			self.control = self.read_folder(os.path.join(self.file_path, control_path))
			self.control_file_name = os.path.split(control_path)[1]
		else:
			self.control = None
			self.text_selectcontrol.SetLabel("No control group.")
		dialog.Destroy()
		
		 
	def select_result_path(self, event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Mining results are in: '+self.result_path+'.')
		dialog.Destroy()


	def read_folder(self, folder): #helper function to read in each subfolder
		folder = folder.replace('\\','/') + '/'
		filelist=[]
		for path, subdirs, files in os.walk(folder):
			for file in files:
				if (file.endswith('summary.xlsx') or file.endswith('summary.xls') or file.endswith('summary.XLS')):
					filelist.append(os.path.join(path, file))
		if len(filelist) == 0: #folder does not have the proper excel files
			return

		number_of_files=len(filelist)
		df = OrderedDict()
		for i in range(number_of_files):
		    try:
		    	dataset = pd.read_excel(r''+filelist[i])
		    	dataset = dataset.drop(columns=['Unnamed: 0.1', 'Unnamed: 0', 'ID'])
		    	behavior = filelist[i].split(folder)[1].split('_')[0]
		    	df[behavior] = dataset
		    except:
		    	continue
		        #print('Empty Excel File!')
		return df


	def read_all_folders(self): #read in data from all folders
		data = []
		for file in os.listdir(self.file_path):
			subfolder = os.path.join(self.file_path, file)
			if os.path.isdir(subfolder):
				folder_data = self.read_folder(subfolder)
				if folder_data != None:
					data.append(folder_data)
					self.file_names.append(os.path.split(subfolder)[1])
				else:
					print("Improper file / file structure in:"+subfolder+'.')
		self.dataset = data

	def control_organization(self):
		if self.control == None: #if no control group is specified, do nothing
			return
		del_idx = self.file_names.index(self.control_file_name)
		self.dataset.pop(del_idx)
		self.file_names.insert(0, self.file_names.pop(del_idx))

	
	def mine_data(self, event):

		if self.file_path is None or self.result_path is None:
			wx.MessageBox('No input / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.TextEntryDialog(self,'Enter a p-value to determine statistical significance','Default p-value is 0.05',"0.05")
			if dialog.ShowModal()==wx.ID_OK:
				self.pval=float(dialog.GetValue())
			dialog.Destroy()

			print("Start to mine analysis results...")

			self.read_all_folders()
			self.control_organization()
			DM = data_mining(self.dataset, self.control, self.paired, self.result_path, self.pval, self.file_names)
			DM.statistical_analysis()


