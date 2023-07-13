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



import scipy
from scipy import stats
import scikit_posthocs as sp
import pandas as pd
import os
import openpyxl



class data_mining():

	def __init__(self, data_in, control_in = None, paired_in = False, result_path_in = None, pval_in = 0.05, file_names_in = None):

		self.data = data_in
		self.control = control_in
		self.paired = paired_in
		self.pval = pval_in
		self.writer = pd.ExcelWriter(os.path.join(result_path_in,'data_mining_results.xlsx'))
		self.file_names = file_names_in


	def normal(self, dataset):

		normal=True
		for i in dataset:
			if len(dataset)>=3:
				if stats.shapiro(i).pvalue < self.pval:
					normal=False
		return normal


	def two_groups(self):

		if self.control != None:
			self.data.insert(0, self.control)
		for behavior in self.data[0]:
			startrow = 0
			print(behavior)
			for parameter in self.data[0][behavior]:
				parameters = []
				pvalues = []
				setA = self.data[0][behavior][parameter].dropna()
				setB = self.data[1][behavior][parameter].dropna()
				dataset = [setA, setB]
				if (self.normal(dataset)):
					if self.paired:
						test = "paired t-test"
						result = stats.ttest_rel(setA, setB)
					else:
						test = "unpaired t-test"
						result = stats.ttest_ind(setA, setB)
				else:
					if self.paired:
						test = "Wilcoxon test"
						result = stats.wilcoxon(setA, setB)
					else:
						test = "Mann Whitney U test"
						result = stats.mannwhitneyu(setA, setB)
				if result.pvalue <= self.pval:
					print('\t', parameter)
					print('\t', "performing", test)
					print('\t'*2, "p-value: ", result.pvalue)
					parameters.append(parameter)
					pvalues.append(result.pvalue)

					stat_info = pd.DataFrame({"p-value":pvalues}, index=parameters) #parameter and associated p-value
					stat_info.to_excel(self.writer, sheet_name = behavior, startrow = startrow)

					significant_data = pd.DataFrame((setA, setB)).transpose() #print out the datasets with significant findings
					significant_data.columns = self.file_names
					significant_data.to_excel(self.writer, sheet_name = behavior, startrow = startrow, startcol = 3)

					sheet = self.writer.sheets[behavior]
					sheet.write_string(startrow, 0, test)
					startrow += significant_data.shape[0] + 2


	def multiple_groups(self):

		for behavior in self.data[0]:
			startrow = 0
			print(behavior)
			for parameter in self.data[0][behavior]:
				dataset = []
				parameters = []
				pvalues = []
				for i in range(len(self.data)):
					currentSet = self.data[i][behavior][parameter].dropna()
					dataset.append(currentSet)
				if self.control != None:
					currentSet = self.control[behavior][parameter].dropna()
					dataset.insert(0, currentSet)
				if self.normal(dataset):
					test = "ANOVA"
					result = stats.f_oneway(*dataset)
				else:
					if self.paired:
						test = "Friedman"
						result = stats.friedmanchisquare(*dataset)
					else:
						test = "Kruskal Wallis"
						result = stats.kruskal(*dataset)
				if result.pvalue <= self.pval:
					pvalues = []
					parameters = []
					posthoc = None
					posthoc_name = None
					print('\t', parameter)
					print('\t', "performing", test)
					print('\t'*2, "p-value: ", result.pvalue)

					pvalues.append(result.pvalue)
					parameters.append(parameter)

					stat_info = pd.DataFrame({"p-value":pvalues}, index=parameters) #parameter and associated p-value
					stat_info.to_excel(self.writer, sheet_name = behavior, startrow = startrow)

					significant_data = pd.DataFrame(dataset).transpose() #print out the datasets with significant findings
					significant_data.columns = self.file_names
					significant_data.to_excel(self.writer, sheet_name = behavior, startrow = startrow, startcol = 8)

					if test == "ANOVA":
						if self.control==None:
							tukey = stats.tukey_hsd(*dataset)
							print(tukey)

							posthoc_name = "Tukey"
							posthoc = pd.DataFrame(tukey)
						else:
							dataset_exp=dataset[1:]
							dunnett = stats.dunnett(*dataset_exp,control=self.control)
							dunnett.columns = self.file_names[1:]
							dunnett.index = self.file_names[1:]
							print('\t'*2, "Dunnett's post-hoc results:")
							print("\t"*2+dunnett.to_string().replace("\n","\n\t\t"))

							posthoc_name = "Dunnett"
							posthoc = pd.DataFrame(dunnett)
					else:
						dunn = sp.posthoc_dunn(dataset) 
						dunn.columns = self.file_names
						dunn.index = self.file_names
						print('\t'*2, "Dunn's post-hoc results:")
						print("\t"*2+dunn.to_string().replace("\n","\n\t\t"))

						posthoc_name = "Dunn"
						posthoc = pd.DataFrame(dunn)

					posthoc.to_excel(self.writer, sheet_name = behavior, startrow = startrow, startcol = 3)
					sheet = self.writer.sheets[behavior]
					sheet.write_string(startrow, 0, test)
					sheet.write_string(startrow, 3, posthoc_name+"'s post-hoc")
					startrow += significant_data.shape[0] + 2


	def statistical_analysis(self):

		if (len(self.data)==2 and self.control == None) or (len(self.data)==1 and self.control != None): #tests for two groups only
			self.two_groups()
		else: #tests for 3+ groups
			self.multiple_groups()
		self.writer.close()
		print('Data mining for statistical analysis completed!')


