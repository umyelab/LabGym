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


# tracking animals and store all the parameters of all animals
class TrackAnimals():

	def __init__(self):

		# store the max counts to deregister the animal
		self.to_deregister=OrderedDict()
		# store contours of animal outlines
		self.contours=OrderedDict()
		# store animal centers
		self.centers=OrderedDict()
		# store the body angles of the animal
		self.angles=OrderedDict()
		# store the body heights of the animal
		self.heights=OrderedDict()
		# store the body widths of the animal
		self.widths=OrderedDict()
		# store addtitional factors
		self.factors1=OrderedDict()
		# # store addtitional factors
		self.factors2=OrderedDict()


	# initiate factor dict for an animal
	def register_animal(self,index,frame_index,fps,contour,center,angle,height,width,
		factor1=None,factor2=None):

		# initiate the dictionary of deregistered animal
		self.to_deregister[index]=0
		# initiate the dictionary of animal contours
		self.contours[index]=[]
		self.contours[index].append(contour)
		# initiate the dictionary of animal centers
		self.centers[index]=[]
		self.centers[index].append(center)
		# initiate the dictionary of animal angles
		self.angles[index]=[]
		self.angles[index].append(angle)
		# initiate the dictionary of animal heights
		self.heights[index]=[]
		self.heights[index].append(height)
		# initiate the dictionary of animal widths
		self.widths[index]=[]
		self.widths[index].append(width)
		# initiate the dictionary of animal factor1
		if factor1 is None:
			self.factors1=None
		else:
			self.factors1[index]=[]
			self.factors1[index].append(factor1)
		# initiate the dictionary of animal factor1
		if factor2 is None:
			self.factors2=None
		else:
			self.factors2[index]=[]
			self.factors2[index].append(factor2)


	# link the newly detected animals to exsting ones
	def link_animal(self,frame_index,fps,existing_centers,max_distance,contours,centers,
		angles,heights,widths,factors1=None,factors2=None,deregister=0):

		# deregister: if 0, link new animal to deregistered animal, otherwise never re-link if an animal is deregistered

		if deregister==0:
			max_distance=float('inf')

		# for storing the indices of used existing centers
		used_existing_indices=[]
		used_new_indices=[]

		# compute distance between existing centers and new input centers
		dt=distance.cdist(existing_centers,centers)

		# flatten to sort all distance between center pairs from min to max
		dt_sort_index=dt.flatten().argsort()

		# renew animal centers and add new data
		n=0
		while n<len(dt_sort_index):

			# distance between two centers should not be too far
			if dt.flatten()[dt_sort_index[n]]<max_distance:

				index_in_existing=int(dt_sort_index[n]/len(centers))
				index_in_new=int(dt_sort_index[n]%len(centers))

				# idx should not be used
				if index_in_existing not in used_existing_indices:
					if index_in_new not in used_new_indices:

						used_existing_indices.append(index_in_existing)
						used_new_indices.append(index_in_new)

						# clear deregistered center
						self.to_deregister[index_in_existing]=0
						# add new input contour
						self.contours[index_in_existing].append(contours[index_in_new])
						# add new center
						self.centers[index_in_existing].append(centers[index_in_new])
						# add angle
						self.angles[index_in_existing].append(angles[index_in_new])
						# add height
						self.heights[index_in_existing].append(heights[index_in_new])
						# add width
						self.widths[index_in_existing].append(widths[index_in_new])
						# add other factors
						if self.factors1 is not None:
							if factors1 is not None:
								self.factors1[index_in_existing].append(factors1[index_in_new])
						if self.factors2 is not None:
							if factors2 is not None:
								self.factors2[index_in_existing].append(factors2[index_in_new])

			n+=1

		return (used_existing_indices,used_new_indices)


	# perform tracking
	def track_animal(self,frame_index,fps,max_distance,contours,centers,angles,heights,widths,deregister=0,
		factors1=None,factors2=None):

		# deregister: if 0, link new animal to deregistered animal, otherwise never re-link if an animal is deregistered

		# list the existing centers
		existing_centers=[]
		for n in list(self.centers.keys()):
			existing_centers.append(self.centers[n][-1])

		(used_exi_indx,used_new_indx)=self.link_animal(frame_index,fps,existing_centers,max_distance,contours,
			centers,angles,heights,widths,factors1,factors2,deregister=deregister)

		# if there are remaining new animal to be registered
		if len(used_new_indx)<len(centers):

			remain_new_indx=list(set(list(range(0,len(centers))))-set(used_new_indx))

			contours_remain=[]
			centers_remain=[]
			angles_remain=[]
			heights_remain=[]
			widths_remain=[]
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
				widths_remain.append(widths[i])
				if self.factors1 is not None:
					if factors1 is not None:
						factors1_remain.append(factors1[i])
				if self.factors2 is not None:
					if factors2 is not None:
						factors2_remain.append(factors2[i])
			
			# register new animals
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
				self.register_animal(idx,frame_index,fps,contours_remain[n],centers_remain[n],
					angles_remain[n],heights_remain[n],widths_remain[n],f1,f2)
				n+=1

		# if there is existing animal to be deregistered
		if len(existing_centers)>len(used_exi_indx):

			for i in list(set(list(range(0,len(existing_centers))))-set(used_exi_indx)):

				# if lost track over 2 seconds
				if self.to_deregister[i]>2*fps:
					# deregister the animal
					self.centers[i].append((-10000,-10000))
				else:
					# temporarily keep the existing centers of this animal
					self.centers[i].append(existing_centers[i])
					self.to_deregister[i]+=1

				self.contours[i].append(self.contours[i][-1])
				self.angles[i].append(-10000)
				self.heights[i].append(-10000)
				self.widths[i].append(-10000)
				if self.factors1 is not None:
					if factors1 is not None:
						self.factors1[i].append(self.factors1[i][-1])
				if self.factors2 is not None:
					if factors1 is not None:
						self.factors2[i].append(self.factors2[i][-1])


	# reset the tracker for the next trakcing
	def clear_tracker(self):

		self.to_deregister=OrderedDict()
		self.time_points=OrderedDict()
		self.contours=OrderedDict()
		self.centers=OrderedDict()
		self.angles=OrderedDict()
		self.heights=OrderedDict()
		self.widths=OrderedDict()
		self.factors1=OrderedDict()
		self.factors2=OrderedDict()
		gc.collect()



