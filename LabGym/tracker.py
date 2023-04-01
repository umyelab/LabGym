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



import numpy as np
import math
import gc
from scipy.spatial import distance
from collections import OrderedDict


class TrackAnimals():

	def __init__(self):

		# store the max counts to deregister the animal
		self.to_deregister=OrderedDict()
		self.contours=OrderedDict()
		self.centers=OrderedDict()
		self.angles=OrderedDict()
		self.heights=OrderedDict()
		# store addtitional factors
		self.factors1=OrderedDict()
		self.factors2=OrderedDict()


	def register_animal(self,index,contour,center,angle,height,factor1=None,factor2=None):

		self.to_deregister[index]=0
		self.contours[index]=[]
		self.contours[index].append(contour)
		self.centers[index]=[]
		self.centers[index].append(center)
		self.angles[index]=[]
		self.angles[index].append(angle)
		self.heights[index]=[]
		self.heights[index].append(height)
		if factor1 is None:
			self.factors1=None
		else:
			self.factors1[index]=[]
			self.factors1[index].append(factor1)
		if factor2 is None:
			self.factors2=None
		else:
			self.factors2[index]=[]
			self.factors2[index].append(factor2)


	def link_animal(self,existing_centers,max_distance,contours,centers,angles,heights,factors1=None,factors2=None,deregister=0):

		# deregister: 0: link new animal to deregistered animal, otherwise never re-link if an animal is deregistered

		if deregister==0:
			max_distance=float('inf')

		used_existing_indices=[]
		used_new_indices=[]

		dt=distance.cdist(existing_centers,centers)

		dt_sort_index=dt.flatten().argsort()

		n=0
		while n<len(dt_sort_index):

			if dt.flatten()[dt_sort_index[n]]<max_distance:

				index_in_existing=int(dt_sort_index[n]/len(centers))
				index_in_new=int(dt_sort_index[n]%len(centers))

				if index_in_existing not in used_existing_indices:
					if index_in_new not in used_new_indices:

						used_existing_indices.append(index_in_existing)
						used_new_indices.append(index_in_new)

						self.to_deregister[index_in_existing]=0
						self.contours[index_in_existing].append(contours[index_in_new])
						self.centers[index_in_existing].append(centers[index_in_new])
						self.angles[index_in_existing].append(angles[index_in_new])
						self.heights[index_in_existing].append(heights[index_in_new])
						if self.factors1 is not None:
							if factors1 is not None:
								self.factors1[index_in_existing].append(factors1[index_in_new])
						if self.factors2 is not None:
							if factors2 is not None:
								self.factors2[index_in_existing].append(factors2[index_in_new])

			n+=1

		return (used_existing_indices,used_new_indices)


	def track_animal(self,fps,max_distance,contours,centers,angles,heights,deregister=0,factors1=None,factors2=None):

		existing_centers=[]
		for n in list(self.centers.keys()):
			existing_centers.append(self.centers[n][-1])

		(used_exi_indx,used_new_indx)=self.link_animal(existing_centers,max_distance,contours,centers,angles,heights,factors1,factors2,deregister=deregister)

		if len(used_new_indx)<len(centers):

			remain_new_indx=list(set(list(range(0,len(centers))))-set(used_new_indx))

			contours_remain=[]
			centers_remain=[]
			angles_remain=[]
			heights_remain=[]
			factors1_remain=None
			factors2_remain=None

			if self.factors1 is not None:
				if factors1 is not None:
					factors1_remain=[]
			if self.factors2 is not None:
				if factors2 is not None:
					factors2_remain=[]

			for i in remain_new_indx:
				contours_remain.append(contours[i])
				centers_remain.append(centers[i])
				angles_remain.append(angles[i])
				heights_remain.append(heights[i])
				if self.factors1 is not None:
					if factors1 is not None:
						factors1_remain.append(factors1[i])
				if self.factors2 is not None:
					if factors2 is not None:
						factors2_remain.append(factors2[i])
			
			n=0
			while n<len(centers_remain):
				idx=len(self.centers)
				f1=f2=None
				if self.factors1 is not None:
					if factors1 is not None:
						f1=factors1_remain[n]
				if self.factors2 is not None:
					if factors2 is not None:
						f2=factors2_remain[n]
				self.register_animal(idx,contours_remain[n],centers_remain[n],angles_remain[n],heights_remain[n],f1,f2)
				n+=1

		if len(existing_centers)>len(used_exi_indx):

			for i in list(set(list(range(0,len(existing_centers))))-set(used_exi_indx)):

				if self.to_deregister[i]>2*fps:
					self.centers[i].append((-10000,-10000))
				else:
					self.centers[i].append(existing_centers[i])
					self.to_deregister[i]+=1

				self.contours[i].append(self.contours[i][-1])
				self.angles[i].append(-10000)
				self.heights[i].append(-10000)
				if self.factors1 is not None:
					if factors1 is not None:
						self.factors1[i].append(self.factors1[i][-1])
				if self.factors2 is not None:
					if factors1 is not None:
						self.factors2[i].append(self.factors2[i][-1])


	def clear_tracker(self):

		self.to_deregister=OrderedDict()
		self.contours=OrderedDict()
		self.centers=OrderedDict()
		self.angles=OrderedDict()
		self.heights=OrderedDict()
		self.factors1=OrderedDict()
		self.factors2=OrderedDict()
		gc.collect()


