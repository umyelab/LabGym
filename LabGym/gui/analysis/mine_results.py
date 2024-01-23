"""
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
"""

import os

import pandas as pd
import wx

from LabGym.minedata import data_mining


class MineResults(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="Mine Results", size=(1000, 240))
        self.file_path = None
        self.result_path = None
        self.dataset = None
        self.paired = False
        self.control = None
        self.pval = 0.05
        self.file_names = None
        self.control_file_name = None

        self.display_window()

    def display_window(self):
        panel = wx.Panel(self)
        boxsizer = wx.BoxSizer(wx.VERTICAL)

        module_inputfolder = wx.BoxSizer(wx.HORIZONTAL)
        button_inputfolder = wx.Button(
            panel, label="Select the folder that stores\nthe data files", size=(300, 40)
        )
        button_inputfolder.Bind(wx.EVT_BUTTON, self.select_filepath)
        wx.Button.SetToolTip(
            button_inputfolder,
            "Put all folders that store analysis results (each folder contains one raster plot) for control / experimental groups into this folder.",
        )
        self.text_inputfolder = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_inputfolder.Add(
            button_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_inputfolder.Add(
            self.text_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(0, 10, 0)
        boxsizer.Add(module_inputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_selectcontrol = wx.BoxSizer(wx.HORIZONTAL)
        button_selectcontrol = wx.Button(
            panel, label="Select the\ncontrol group", size=(300, 40)
        )
        button_selectcontrol.Bind(wx.EVT_BUTTON, self.select_control)
        wx.Button.SetToolTip(
            button_selectcontrol,
            "For multiple-group comparison, you can select one group as control for post-hoc comparison. If no control is selected, post-hoc comparison will be performed between each pair of the two groups.",
        )
        self.text_selectcontrol = wx.StaticText(
            panel,
            label="Default: no control group.",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        module_selectcontrol.Add(
            button_selectcontrol, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_selectcontrol.Add(
            self.text_selectcontrol, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_selectcontrol, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        module_outputfolder = wx.BoxSizer(wx.HORIZONTAL)
        button_outputfolder = wx.Button(
            panel,
            label="Select the folder to store\nthe data mining results",
            size=(300, 40),
        )
        button_outputfolder.Bind(wx.EVT_BUTTON, self.select_result_path)
        wx.Button.SetToolTip(
            button_outputfolder,
            "A spreadsheet containing all data mining results will be stored in this folder.",
        )
        self.text_outputfolder = wx.StaticText(
            panel, label="None.", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )
        module_outputfolder.Add(
            button_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        module_outputfolder.Add(
            self.text_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10
        )
        boxsizer.Add(module_outputfolder, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        boxsizer.Add(0, 5, 0)

        button_minedata = wx.Button(panel, label="Start to mine data", size=(300, 40))
        button_minedata.Bind(wx.EVT_BUTTON, self.mine_data)
        wx.Button.SetToolTip(
            button_minedata,
            "Parametric / non-parametric tests will be automatically selected according to the data distribution, to compare the mean / median of different groups. See Extended Guide for details.",
        )
        boxsizer.Add(0, 5, 0)
        boxsizer.Add(button_minedata, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        boxsizer.Add(0, 10, 0)

        panel.SetSizer(boxsizer)

        self.Centre()
        self.Show(True)

    def select_filepath(self, event):
        dialog = wx.MessageDialog(
            self, "Is the data paired?", "Paired data?", wx.YES_NO | wx.ICON_QUESTION
        )
        if dialog.ShowModal() == wx.ID_YES:
            self.paired = True
        else:
            self.paired = False
        dialog.Destroy()

        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.file_path = dialog.GetPath()
            if self.paired is True:
                self.text_inputfolder.SetLabel(
                    "Paired input data is in: " + self.file_path + "."
                )
            else:
                self.text_inputfolder.SetLabel(
                    "Unpaired input data is in: " + self.file_path + "."
                )
        dialog.Destroy()

    def select_control(self, event):
        dialog = wx.SingleChoiceDialog(
            self,
            "Select the folder for the control group.",
            "Ignore if you wish to compare all groups",
            choices=[
                i
                for i in os.listdir(self.file_path)
                if os.path.isdir(os.path.join(self.file_path, i))
            ],
            style=wx.DD_DEFAULT_STYLE,
        )
        if dialog.ShowModal() == wx.ID_OK:
            control_path = dialog.GetStringSelection()
            self.text_selectcontrol.SetLabel(
                "The control group is: " + control_path + "."
            )
            self.control = self.read_folder(os.path.join(self.file_path, control_path))
            self.control_file_name = os.path.split(control_path)[1]
        else:
            self.control = None
            self.text_selectcontrol.SetLabel("No control group.")
        dialog.Destroy()

    def select_result_path(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                "Mining results are in: " + self.result_path + "."
            )
        dialog.Destroy()

    def read_folder(self, folder):
        folder = folder.replace("\\", "/")
        filelist = {}
        df = {}
        for i in os.listdir(folder):
            if (
                i.endswith("_summary.xlsx")
                or i.endswith("_summary.xls")
                or i.endswith("_summary.XLS")
            ):
                behavior_name = i.split("_")[-2]
                filelist[behavior_name] = os.path.join(folder, i)
        if len(filelist) == 0:
            print('No "_summary.xlsx" excel file found!')
        else:
            for behavior_name in filelist:
                dataset = pd.read_excel(r"" + filelist[behavior_name])
                dataset = dataset.drop(columns=["ID/parameter"])
                df[behavior_name] = dataset
        return df

    def read_all_folders(self):
        data = []
        filenames = []
        for file in os.listdir(self.file_path):
            subfolder = os.path.join(self.file_path, file)
            if os.path.isdir(subfolder):
                folder_data = self.read_folder(subfolder)
                if len(folder_data) > 0:
                    data.append(folder_data)
                    filenames.append(os.path.split(subfolder)[1])
                else:
                    print("Improper file / file structure in: " + subfolder + ".")
        self.dataset = data
        self.file_names = filenames

    def control_organization(self):
        if self.control == None:
            return
        del_idx = self.file_names.index(self.control_file_name)
        self.dataset.pop(del_idx)
        self.file_names.insert(0, self.file_names.pop(del_idx))

    def mine_data(self, event):
        if self.file_path is None or self.result_path is None:
            wx.MessageBox(
                "No input / output folder selected.", "Error", wx.OK | wx.ICON_ERROR
            )

        else:
            dialog = wx.TextEntryDialog(
                self,
                "Enter a p-value to determine statistical significance",
                "Default p-value is 0.05",
                "0.05",
            )
            if dialog.ShowModal() == wx.ID_OK:
                self.pval = float(dialog.GetValue())
            dialog.Destroy()

            print("Start to mine analysis results...")

            self.read_all_folders()
            self.control_organization()
            DM = data_mining(
                self.dataset,
                self.control,
                self.paired,
                self.result_path,
                self.pval,
                self.file_names,
            )
            DM.statistical_analysis()
