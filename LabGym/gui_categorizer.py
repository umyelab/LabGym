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


# Standard library imports.
import json
import logging
import os
import re
import sys
import subprocess

# from pathlib import Path
import shutil

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Related third party imports.
import cv2
import numpy as np
import wx
import wx.richtext
import wx.lib.buttons as wxbuttons
import wx.grid
import wx.html

# Local application/library specific imports.
from .categorizer import Categorizers, CategorizerClassMismatchError
from LabGym import config
from .tools import sort_examples_from_csv
from .gui_utils import (
	add_or_select_notebook_page,
	add_info_button,
	create_hyperlink,
	INFO_COLOUR_S3,
	count_prepared_examples,
	count_sorted_examples,
	counts_enable_diagnostics,
)


# Confusion-matrix correct-cell colors: dark -> approved max green #2E7D32.
CM_CORRECT_RGB_MIN = (20, 40, 20)
CM_CORRECT_RGB_MAX = (46, 125, 50)  # #2E7D32


def import_generate_examples_analyzer(kind):
	"""
	Import AnalyzeAnimal ('animal') or AnalyzeAnimalDetector ('detector').

	Returns the class, or None after logging and a MessageBox when the import
	raises ImportError or OSError (for example a missing native library).
	Unknown kind values raise ValueError without attempting an import.
	"""
	if kind not in ('animal', 'detector'):
		raise ValueError(
			"import_generate_examples_analyzer kind must be 'animal' or 'detector', "
			f'got {kind!r}'
		)
	try:
		if kind == 'animal':
			from .analyzebehavior import AnalyzeAnimal
			return AnalyzeAnimal
		if kind == 'detector':
			from .analyzebehavior_dt import AnalyzeAnimalDetector
			return AnalyzeAnimalDetector
	except (ImportError, OSError):
		logger.exception(
			'Failed to import Generate Examples analyzer components (kind=%r)',
			kind,
		)
		wx.MessageBox(
			'LabGym could not load the analysis components required for this Generate '
			'Examples workflow. Verify that the LabGym environment and its required '
			'dependencies are installed correctly, then try again.',
			'Analysis dependency unavailable',
			wx.OK | wx.ICON_ERROR,
		)
		return None


def cm_correct_cell_rgb(accuracy):
	"""Return RGB for a correct (diagonal) CM cell given row accuracy in [0, 1]."""
	accuracy = max(0.0, min(1.0, float(accuracy)))
	r0, g0, b0 = CM_CORRECT_RGB_MIN
	r1, g1, b1 = CM_CORRECT_RGB_MAX
	return (
		int(round(r0 + (r1 - r0) * accuracy)),
		int(round(g0 + (g1 - g0) * accuracy)),
		int(round(b0 + (b1 - b0) * accuracy)),
	)


def triage_assignment_counts(h1_count, h2_count, h3_count):
	"""Return True when at least one triage hypothesis has an assignment."""
	return (h1_count + h2_count + h3_count) > 0


def reportlab_importable():
	"""Return (ok, error_message_or_None) for PDF dependency availability."""
	try:
		import reportlab  # noqa: F401
		from reportlab.lib.pagesizes import letter  # noqa: F401
		from reportlab.platypus import SimpleDocTemplate  # noqa: F401
		return True, None
	except ImportError as e:
		return False, str(e)


DIAGNOSTIC_BUTTON_LABELS = (
	'Overview',
	'Major Confusions',
	'Minor Confusions',
	'Successes',
	'Build Triage Plan',
)


def insufficient_support_threshold(total_support):
	"""Minimum observed support required for automated major/minor ranking."""
	return max(20, float(total_support) * 0.01)


def collect_insufficient_support_entries(classnames, report):
	"""Return low-support class entries, including classes with zero support."""
	total_support = sum(
		float(report.get(name, {}).get('support', 0)) for name in classnames
	)
	min_support = int(insufficient_support_threshold(total_support))
	entries = []
	for true_class in classnames:
		support = float(report.get(true_class, {}).get('support', 0))
		if support < min_support:
			entries.append({
				'class': true_class,
				'support': int(support),
				'min_support': min_support,
			})
	return entries


def fit_dialog_client_size(
	nominal_w,
	nominal_h,
	work_w,
	work_h,
	margin=40,
	max_frac=0.92,
):
	"""Clamp a nominal dialog client size to a usable work area."""
	work_w = max(1, int(work_w))
	work_h = max(1, int(work_h))
	margin = max(0, int(margin))
	max_frac = max(0.1, min(1.0, float(max_frac)))
	cap_w = min(work_w - 2 * margin, int(work_w * max_frac))
	cap_h = min(work_h - 2 * margin, int(work_h * max_frac))
	cap_w = max(1, cap_w)
	cap_h = max(1, cap_h)
	return min(int(nominal_w), cap_w), min(int(nominal_h), cap_h)


def next_versioned_pdf_path(directory, base='categorizer_diagnostics'):
	"""Return the next non-overwriting `{base}_vN.pdf` path in directory."""
	pattern = re.compile(r'^' + re.escape(base) + r'_v(\d+)\.pdf$')
	max_n = 0
	try:
		names = os.listdir(directory)
	except OSError:
		names = []
	for name in names:
		path = os.path.join(directory, name)
		if not os.path.isfile(path):
			continue
		matched = pattern.match(name)
		if matched:
			max_n = max(max_n, int(matched.group(1)))
	return os.path.join(directory, f'{base}_v{max_n + 1}.pdf')


_WIN_INVALID_CHARS = set('<>:"|?*')
_WIN_RESERVED = {
	'CON', 'PRN', 'AUX', 'NUL',
	*(f'COM{i}' for i in range(1, 10)),
	*(f'LPT{i}' for i in range(1, 10)),
}
_TRAILING_TRIAGE_VERSION = re.compile(r'_triage_v\d+$', re.IGNORECASE)


def sanitize_triage_package_base(source_name):
	"""Return a portable basename stem for `<stem>_triage_vN` packages."""
	import unicodedata

	text = unicodedata.normalize('NFC', str(source_name or ''))
	chars = []
	for ch in text:
		category = unicodedata.category(ch)
		if category.startswith('C'):
			continue
		if ch.isalnum() or ch in '-_':
			chars.append(ch)
		elif ch.isspace() or ch in '/\\' or ch in _WIN_INVALID_CHARS:
			chars.append('_')
		else:
			chars.append('_')
	base = ''.join(chars)
	while '__' in base:
		base = base.replace('__', '_')
	base = base.strip(' ._')
	base = _TRAILING_TRIAGE_VERSION.sub('', base)
	base = base.strip(' ._')
	if len(base) > 80:
		base = base[:80].rstrip(' ._')
	if not base:
		base = 'sorted_test_examples'
	if base.upper() in _WIN_RESERVED:
		base = f'{base}_data'
	return base


def next_versioned_triage_package_name(parent_dir, source_name):
	"""Return next `<sanitized>_triage_vN` sibling directory basename."""
	base = sanitize_triage_package_base(source_name)
	pattern = re.compile(r'^' + re.escape(base) + r'_triage_v(\d+)$')
	max_n = 0
	try:
		names = os.listdir(parent_dir)
	except OSError:
		names = []
	for name in names:
		path = os.path.join(parent_dir, name)
		if not os.path.isdir(path):
			continue
		matched = pattern.match(name)
		if matched:
			max_n = max(max_n, int(matched.group(1)))
	return f'{base}_triage_v{max_n + 1}'


def validate_triage_package_name(name):
	"""Return (ok, error_message_or_None) for a user-edited package basename."""
	if name is None:
		return False, 'Package name cannot be empty.'
	raw = str(name)
	if raw.strip() == '':
		return False, 'Package name cannot be empty.'
	if raw != raw.strip():
		return False, 'Package name cannot start or end with spaces.'
	if raw in ('.', '..'):
		return False, 'Package name cannot be "." or "..".'
	if os.path.isabs(raw) or raw.startswith('~'):
		return False, 'Package name must be a folder name, not an absolute path.'
	if '/' in raw or '\\' in raw:
		return False, 'Package name cannot contain path separators.'
	if any(ord(ch) < 32 for ch in raw):
		return False, 'Package name cannot contain control characters.'
	if any(ch in _WIN_INVALID_CHARS for ch in raw):
		return False, 'Package name contains characters that are invalid on Windows.'
	if raw.endswith('.') or raw.endswith(' '):
		return False, 'Package name cannot end with a period or space.'
	stem = raw.split('.')[0].upper()
	if stem in _WIN_RESERVED:
		return False, f'"{raw}" is a reserved device name on Windows.'
	return True, None


def collect_h1_filename_collisions(source_root, h1_pairs):
	"""
	Return sorted collision records for H1 merges against source_root.

	Each record: {'pair': (true, pred), 'filenames': [sorted basenames]}
	Also return missing class folders as sorted (kind, class_name) tuples where
	kind is 'source' or 'target'.
	"""
	collisions = []
	missing = []
	seen_pairs = []
	for true_class, pred_class in h1_pairs:
		pair = (true_class, pred_class)
		if pair in seen_pairs:
			continue
		seen_pairs.append(pair)
		src_dir = os.path.join(source_root, true_class)
		tgt_dir = os.path.join(source_root, pred_class)
		if not os.path.isdir(src_dir):
			missing.append(('source', true_class))
			continue
		if not os.path.isdir(tgt_dir):
			missing.append(('target', pred_class))
			continue
		try:
			src_names = set(os.listdir(src_dir))
			tgt_names = set(os.listdir(tgt_dir))
		except OSError:
			missing.append(('source', true_class))
			continue
		overlap = sorted(src_names & tgt_names)
		if overlap:
			collisions.append({'pair': pair, 'filenames': overlap})
	collisions.sort(key=lambda rec: (rec['pair'][0], rec['pair'][1]))
	missing = sorted(set(missing))
	return collisions, missing


class PanelLv2_GenerateExamples(wx.Panel):

	'''
	The 'Generate Behavior Examples' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		# Get all of the values needed from config.get_config().
		self.config = config.get_config('detectors', 'models')

		self.behavior_mode=0 # 0: non-interactive behavior; 1: interact basic; 2: interact advanced; 3: static images
		self.use_detector=False # whether the Detector is used
		self.detector_path=None # the 'LabGym/detectors' folder, which stores all the trained Detectors
		self.path_to_detector=None # path to the Detector
		self.detection_threshold=0 # only for 'static images' behavior mode
		self.animal_kinds=[] # the total categories of animals / objects in a Detector
		self.background_path=None # if not None, load background images from path in 'background subtraction' detection method
		self.path_to_videos=None # path to a batch of videos for generating behavior examples
		self.result_path=None # the folder for storing the unsorted behavior examples
		self.framewidth=None # if not None, will resize the video frame keeping the original w:h ratio
		self.delta=10000 # the fold changes in illumination that determines the optogenetic stimulation onset
		self.decode_animalnumber=False # whether to decode animal numbers from '_nn_' in video file names
		self.animal_number=None # the number of animals / objects in a video
		self.autofind_t=False # whether to find stimulation onset automatically (only for optogenetics)
		self.decode_t=False # whether to decode start_t from '_bt_' in video file names
		self.t=0 # the start_t for generating behavior examples
		self.duration=0 # the duration for generating behavior examples
		self.decode_extraction=False # whether to decode time windows for background extraction from '_xst_' and '_xet_' in video file names
		self.ex_start=0 # start time for background extraction
		self.ex_end=None # end time for background extraction
		self.animal_vs_bg=0 # 0: animals birghter than the background; 1: animals darker than the background; 2: hard to tell
		self.stable_illumination=True # whether the illumination in videos is stable
		self.length=15 # the duration / length for a behavior example, is also the input time step for Animation Analyzer
		self.skip_redundant=1 # the interval (in frames) of two consecutively generated behavior example pairs
		self.include_bodyparts=False # whether to include body parts in the pattern images
		self.std=0 # a value between 0 and 255, higher value, less body parts will be included in the pattern images
		self.background_free=True # whether to include background in animations
		self.black_background=True # whether to set background black
		self.social_distance=0 # a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		self.color_costar=False # in 'interactive advanced' mode, whether to make the supporting roles RGB scale in animations

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_specifymode=wx.BoxSizer(wx.HORIZONTAL)
		button_specifymode=wx.Button(panel,label='Specify the mode of behavior\nexamples to generate',size=(300,40))
		button_specifymode.Bind(wx.EVT_BUTTON,self.specify_mode)
		wx.Button.SetToolTip(button_specifymode,'"Non-interactive" is for behaviors of each individual; "Interactive basic" is for interactive behaviors of all animals but not distinguishing each individual; "Interactive advanced" is slower in analysis than "basic" but distinguishes individuals during close body contact. "Static images" is for analyzing images not videos. See Extended Guide for details.')
		self.text_specifymode=wx.StaticText(panel,label='Default: Non-interactive: behaviors of each individuals (each example contains one animal / object)',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_specifymode.Add(button_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_specifymode.Add(self.text_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_specifymode,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inputvideos=wx.BoxSizer(wx.HORIZONTAL)
		button_inputvideos=wx.Button(panel,label='Select the video(s) / image(s) to\ngenerate behavior examples',size=(300,40))
		button_inputvideos.Bind(wx.EVT_BUTTON,self.select_videos)
		wx.Button.SetToolTip(button_inputvideos,'Select one or more videos / images. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) or image formats (jpg, jpeg, png, tiff, bmp) are supported except wmv format.')
		self.text_inputvideos=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputvideos.Add(button_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputvideos.Add(self.text_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inputvideos,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store the\ngenerated behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video and stores the generated behavior examples. For "Static images" mode, all generated behavior examples will be in this folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_detection=wx.BoxSizer(wx.HORIZONTAL)
		button_detection=wx.Button(panel,label='Specify the method to\ndetect animals or objects',size=(300,40))
		button_detection.Bind(wx.EVT_BUTTON,self.select_method)
		wx.Button.SetToolTip(button_detection,'Background subtraction-based method is accurate and fast but needs static background and stable illumination in videos; Detectors-based method is accurate and versatile in any recording settings but is slow. See Extended Guide for details.')
		self.text_detection=wx.StaticText(panel,label='Default: Background subtraction-based method.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_detection.Add(button_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_detection.Add(self.text_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_detection,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_startgenerate=wx.BoxSizer(wx.HORIZONTAL)
		button_startgenerate=wx.Button(panel,label='Specify when generating behavior examples\nshould begin (unit: second)',size=(300,40))
		button_startgenerate.Bind(wx.EVT_BUTTON,self.specify_timing)
		wx.Button.SetToolTip(button_startgenerate,'Enter a beginning time point for all videos or use "Decode from filenames" to let LabGym decode the different beginning time for different videos. See Extended Guide for details.')
		self.text_startgenerate=wx.StaticText(panel,label='Default: at the beginning of the video(s).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_startgenerate.Add(button_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_startgenerate.Add(self.text_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_startgenerate,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_duration=wx.BoxSizer(wx.HORIZONTAL)
		button_duration=wx.Button(panel,label='Specify how long generating examples\nshould last (unit: second)',size=(300,40))
		button_duration.Bind(wx.EVT_BUTTON,self.input_duration)
		wx.Button.SetToolTip(button_duration,'The duration is the same for all the videos in one batch.')
		self.text_duration=wx.StaticText(panel,label='Default: from the specified beginning time to the end of a video.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_duration.Add(button_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_duration.Add(self.text_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_duration,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_animalnumber=wx.BoxSizer(wx.HORIZONTAL)
		button_animalnumber=wx.Button(panel,label='Specify the number of animals\nin a video',size=(300,40))
		button_animalnumber.Bind(wx.EVT_BUTTON,self.specify_animalnumber)
		wx.Button.SetToolTip(button_animalnumber,'Enter a number for all videos or use "Decode from filenames" to let LabGym decode the different animal number for different videos. See Extended Guide for details.')
		self.text_animalnumber=wx.StaticText(panel,label='Default: 1.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_animalnumber.Add(button_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_animalnumber.Add(self.text_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_animalnumber,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_length)
		wx.Button.SetToolTip(button_length,'The duration (the number of frames, an integer) of each behavior example, which should approximate the length of a behavior episode. This duration needs to be the same across all the behavior examples for training one Categorizer. See Extended Guide for details.')
		self.text_length=wx.StaticText(panel,label='Default: 15 frames.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_skipredundant=wx.BoxSizer(wx.HORIZONTAL)
		button_skipredundant=wx.Button(panel,label='Specify how many frames to skip when\ngenerating two consecutive behavior examples',size=(300,40))
		button_skipredundant.Bind(wx.EVT_BUTTON,self.specify_redundant)
		wx.Button.SetToolTip(button_skipredundant,'If two consecutively generated examples have many overlapping frames, they look similar, which makes training inefficient and sorting laborious. Specifying an interval (skipped frames) between two examples can address this. See Extended Guide for details.')
		self.text_skipredundant=wx.StaticText(panel,label='Default: no frame to skip (generate a behavior example every frame).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_skipredundant.Add(button_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_skipredundant.Add(self.text_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_skipredundant,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_generate=wx.Button(panel,label='Start to generate behavior examples',size=(300,40))
		button_generate.Bind(wx.EVT_BUTTON,self.generate_data)
		wx.Button.SetToolTip(button_generate,'Need to specify whether to include background and body parts in the generated behavior examples. See Extended Guide for details.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_generate,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def specify_mode(self,event):

		behavior_modes=['Non-interactive: behaviors of each individual (each example contains one animal / object)','Interactive basic: behaviors of all (each example contains all animals / objects)','Interactive advanced: behaviors of each individual and social groups (each example contains either one or multiple animals / objects)','Static images (non-interactive): behaviors of each individual in static images (each image contains one animal / object)']
		dialog=wx.SingleChoiceDialog(self,message='Specify the mode of behavior examples to generate',caption='Behavior-example mode',choices=behavior_modes)
		if dialog.ShowModal()==wx.ID_OK:
			behavior_mode=dialog.GetStringSelection()
			if behavior_mode=='Non-interactive: behaviors of each individual (each example contains one animal / object)':
				self.behavior_mode=0
			elif behavior_mode=='Interactive basic: behaviors of all (each example contains all animals / objects)':
				self.behavior_mode=1
			elif behavior_mode=='Interactive advanced: behaviors of each individual and social groups (each example contains either one or multiple animals / objects)':
				self.behavior_mode=2
				dialog1=wx.NumberEntryDialog(self,'Interactions happen within the interaction distance.','(See Extended Guide for details)\nHow many folds of square root of the animals area\nis the interaction distance (0=infinity far):','interaction distance (Enter an integer)',0,0,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.social_distance=int(dialog1.GetValue())
				else:
					self.social_distance=0
				dialog1.Destroy()
				dialog1=wx.MessageDialog(self,'Make both main and supporting characters RGB scale?\nSelect "No" if dont know what it is.','(Optional) RGB supporting characters?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.color_costar=True
				else:
					self.color_costar=False
				dialog1.Destroy()
				self.text_detection.SetLabel('Only Detector-based detection method is available for the selected behavior mode.')
			else:
				self.behavior_mode=3
				self.text_detection.SetLabel('Only Detector-based detection method is available for the selected behavior mode.')
				self.text_startgenerate.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_duration.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_animalnumber.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_length.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
				self.text_skipredundant.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
		else:
			self.behavior_mode=0
			behavior_mode='Non-interactive: behaviors of each individual (each example contains one animal / object)'
		if self.behavior_mode==2:
			self.text_specifymode.SetLabel('Behavior mode: '+behavior_mode+' with interaction distance: '+str(self.social_distance)+' folds of the animal diameter.')
		else:
			self.text_specifymode.SetLabel('Behavior mode: '+behavior_mode+'.')
		dialog.Destroy()


	def select_videos(self,event):

		if self.behavior_mode>=3:
			wildcard='Image files(*.jpg;*.jpeg;*.png;*.tiff;*.bmp)|*.jpg;*.JPG;*.jpeg;*.JPEG;*.png;*.PNG;*.tiff;*.TIFF;*.bmp;*.BMP'
		else:
			wildcard='Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov'

		dialog=wx.FileDialog(self,'Select video(s) / image(s)','','',wildcard,style=wx.FD_MULTIPLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_videos=dialog.GetPaths()
			self.path_to_videos.sort()
			path=os.path.dirname(self.path_to_videos[0])
			dialog1=wx.MessageDialog(self,'Proportional resize the video frames / images?\nSelect "No" if dont know what it is.','(Optional) resize the frames / images?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog1.ShowModal()==wx.ID_YES:
				dialog2=wx.NumberEntryDialog(self,'Enter the desired frame / image width','The unit is pixel:','Desired frame / image width',480,1,10000)
				if dialog2.ShowModal()==wx.ID_OK:
					self.framewidth=int(dialog2.GetValue())
					if self.framewidth<10:
						self.framewidth=10
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (proportionally resize frame / image width to '+str(self.framewidth)+').')
				else:
					self.framewidth=None
					self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (original frame / image size).')
				dialog2.Destroy()
			else:
				self.framewidth=None
				self.text_inputvideos.SetLabel('Selected '+str(len(self.path_to_videos))+' file(s) in: '+path+' (original frame / image size).')
			dialog1.Destroy()

		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Generate behavior examples in: '+self.result_path+'.')
		dialog.Destroy()


	def select_method(self,event):

		if self.behavior_mode<=1:
			methods=['Subtract background (fast but requires static background & stable illumination)','Use trained Detectors (versatile but slow)']
		else:
			methods=['Use trained Detectors (versatile but slow)']

		dialog=wx.SingleChoiceDialog(self,message='How to detect the animals?',caption='Detection methods',choices=methods)
		if dialog.ShowModal()==wx.ID_OK:
			method=dialog.GetStringSelection()

			if method=='Subtract background (fast but requires static background & stable illumination)':

				self.use_detector=False

				contrasts=['Animal brighter than background','Animal darker than background','Hard to tell']
				dialog1=wx.SingleChoiceDialog(self,message='Select the scenario that fits your videos best',caption='Which fits best?',choices=contrasts)
				if dialog1.ShowModal()==wx.ID_OK:
					contrast=dialog1.GetStringSelection()
					if contrast=='Animal brighter than background':
						self.animal_vs_bg=0
					elif contrast=='Animal darker than background':
						self.animal_vs_bg=1
					else:
						self.animal_vs_bg=2
					dialog2=wx.MessageDialog(self,'Load an existing background from a folder?\nSelect "No" if dont know what it is.','(Optional) load existing background?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog2.ShowModal()==wx.ID_YES:
						dialog3=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
						if dialog3.ShowModal()==wx.ID_OK:
							self.background_path=dialog3.GetPath()
						dialog3.Destroy()
					else:
						self.background_path=None
						if self.animal_vs_bg!=2:
							dialog3=wx.MessageDialog(self,'Unstable illumination in the video?\nSelect "Yes" if dont know what it is.','(Optional) unstable illumination?',wx.YES_NO|wx.ICON_QUESTION)
							if dialog3.ShowModal()==wx.ID_YES:
								self.stable_illumination=False
							else:
								self.stable_illumination=True
							dialog3.Destroy()
					dialog2.Destroy()
					if self.background_path is None:
						ex_methods=['Use the entire duration (default but NOT recommended)','Decode from filenames: "_xst_" and "_xet_"','Enter two time points']
						dialog2=wx.SingleChoiceDialog(self,message='Specify the time window for background extraction',caption='Time window for background extraction',choices=ex_methods)
						if dialog2.ShowModal()==wx.ID_OK:
							ex_method=dialog2.GetStringSelection()
							if ex_method=='Use the entire duration (default but NOT recommended)':
								self.decode_extraction=False
								if self.animal_vs_bg==0:
									self.text_detection.SetLabel('Background subtraction: animal brighter, using the entire duration.')
								elif self.animal_vs_bg==1:
									self.text_detection.SetLabel('Background subtraction: animal darker, using the entire duration.')
								else:
									self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using the entire duration.')
							elif ex_method=='Decode from filenames: "_xst_" and "_xet_"':
								self.decode_extraction=True
								if self.animal_vs_bg==0:
									self.text_detection.SetLabel('Background subtraction: animal brighter, using time window decoded from filenames "_xst_" and "_xet_".')
								elif self.animal_vs_bg==1:
									self.text_detection.SetLabel('Background subtraction: animal darker, using time window decoded from filenames "_xst_" and "_xet_".')
								else:
									self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window decoded from filenames "_xst_" and "_xet_".')
							else:
								self.decode_extraction=False
								dialog3=wx.NumberEntryDialog(self,'Enter the start time','The unit is second:','Start time for background extraction',0,0,100000000000000)
								if dialog3.ShowModal()==wx.ID_OK:
									self.ex_start=int(dialog3.GetValue())
								dialog3.Destroy()
								dialog3=wx.NumberEntryDialog(self,'Enter the end time','The unit is second:','End time for background extraction',0,0,100000000000000)
								if dialog3.ShowModal()==wx.ID_OK:
									self.ex_end=int(dialog3.GetValue())
									if self.ex_end==0:
										self.ex_end=None
								dialog3.Destroy()
								if self.animal_vs_bg==0:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal brighter, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal brighter, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
								elif self.animal_vs_bg==1:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal darker, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal darker, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
								else:
									if self.ex_end is None:
										self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window (in seconds) from '+str(self.ex_start)+' to the end.')
									else:
										self.text_detection.SetLabel('Background subtraction: animal partially brighter/darker, using time window (in seconds) from '+str(self.ex_start)+' to '+str(self.ex_end)+'.')
						dialog2.Destroy()
				dialog1.Destroy()

			else:

				self.use_detector=True
				self.animal_number={}
				self.detector_path = self.config['detectors']
				logger.debug('%s: %r', 'self.detector_path', self.detector_path)

				detectors=[i for i in os.listdir(self.detector_path) if os.path.isdir(os.path.join(self.detector_path,i))]
				if '__pycache__' in detectors:
					detectors.remove('__pycache__')
				if '__init__' in detectors:
					detectors.remove('__init__')
				if '__init__.py' in detectors:
					detectors.remove('__init__.py')
				detectors.sort()
				if 'Choose a new directory of the Detector' not in detectors:
					detectors.append('Choose a new directory of the Detector')

				dialog1=wx.SingleChoiceDialog(self,message='Select a Detector for animal detection',caption='Select a Detector',choices=detectors)
				if dialog1.ShowModal()==wx.ID_OK:
					detector=dialog1.GetStringSelection()
					if detector=='Choose a new directory of the Detector':
						dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
						if dialog2.ShowModal()==wx.ID_OK:
							self.path_to_detector=dialog2.GetPath()
						dialog2.Destroy()
					else:
						self.path_to_detector=os.path.join(self.detector_path,detector)
					with open(os.path.join(self.path_to_detector,'model_parameters.txt')) as f:
						model_parameters=f.read()
					animal_names=json.loads(model_parameters)['animal_names']
					if len(animal_names)>1:
						dialog2=wx.MultiChoiceDialog(self,message='Specify which animals/objects involved in behavior examples',caption='Animal/Object kind',choices=animal_names)
						if dialog2.ShowModal()==wx.ID_OK:
							self.animal_kinds=[animal_names[i] for i in dialog2.GetSelections()]
						else:
							self.animal_kinds=animal_names
						dialog2.Destroy()
					else:
						self.animal_kinds=animal_names
					if self.behavior_mode>=3:
						dialog2=wx.NumberEntryDialog(self,"Enter the Detector's detection threshold (0~100%)","The higher detection threshold,\nthe higher detection accuracy,\nbut the lower detection sensitivity.\nEnter 0 if don't know how to set.",'Detection threshold',0,0,100)
						if dialog2.ShowModal()==wx.ID_OK:
							detection_threshold=dialog2.GetValue()
							self.detection_threshold=detection_threshold/100
						self.text_detection.SetLabel('Detector: '+detector+' (detection threshold: '+str(detection_threshold)+'%); The animals/objects: '+str(self.animal_kinds)+'.')
						dialog2.Destroy()
					else:
						for animal_name in self.animal_kinds:
							self.animal_number[animal_name]=1
						self.text_animalnumber.SetLabel('The number of '+str(self.animal_kinds)+' is: '+str(list(self.animal_number.values()))+'.')
						self.text_detection.SetLabel('Detector: '+detector+'; '+'The animals/objects: '+str(self.animal_kinds)+'.')
				dialog1.Destroy()

		dialog.Destroy()


	def specify_timing(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.use_detector is False:
				dialog=wx.MessageDialog(self,'light on and off in videos?','Illumination shifts?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.delta=1.2
				else:
					self.delta=10000
				dialog.Destroy()

			if self.delta==1.2 and self.use_detector is False:
				methods=['Automatic (for light on and off)','Decode from filenames: "_bt_"','Enter a time point']
			else:
				methods=['Decode from filenames: "_bt_"','Enter a time point']

			dialog=wx.SingleChoiceDialog(self,message='Specify beginning time to generate behavior examples',caption='Beginning time for generator',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Automatic (for light on and off)':
					self.autofind_t=True
					self.decode_t=False
					self.text_startgenerate.SetLabel('Automatically find the onset of the 1st time when light on / off as the beginning time.')
				elif method=='Decode from filenames: "_bt_"':
					self.autofind_t=False
					self.decode_t=True
					self.text_startgenerate.SetLabel('Decode from the filenames: the "t" immediately after the letter "b"" in "_bt_".')
				else:
					self.autofind_t=False
					self.decode_t=False
					dialog2=wx.NumberEntryDialog(self,'Enter beginning time to generate examples','The unit is second:','Beginning time to generate examples',0,0,100000000000000)
					if dialog2.ShowModal()==wx.ID_OK:
						self.t=float(dialog2.GetValue())
						if self.t<0:
							self.t=0
						self.text_startgenerate.SetLabel('Start to generate behavior examples at the: '+str(self.t)+' second.')
					dialog2.Destroy()
			dialog.Destroy()


	def input_duration(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox("No need to specify this since the selected behavior mode is 'Static images'.",'Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'Enter the duration for generating examples','The unit is second:','Duration for generating examples',0,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.duration=int(dialog.GetValue())
				if self.duration!=0:
					self.text_duration.SetLabel('The generation of behavior examples lasts for '+str(self.duration)+' seconds.')
				else:
					self.text_duration.SetLabel('The generation of behavior examples lasts for the entire duration of a video.')
			dialog.Destroy()


	def specify_animalnumber(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			methods=['Decode from filenames: "_nn_"','Enter the number of animals']

			dialog=wx.SingleChoiceDialog(self,message='Specify the number of animals in a video',caption='The number of animals in a video',choices=methods)
			if dialog.ShowModal()==wx.ID_OK:
				method=dialog.GetStringSelection()
				if method=='Enter the number of animals':
					self.decode_animalnumber=False
					if self.use_detector:
						self.animal_number={}
						for animal_name in self.animal_kinds:
							dialog1=wx.NumberEntryDialog(self,'','The number of '+str(animal_name)+': ',str(animal_name)+' number',1,1,100)
							if dialog1.ShowModal()==wx.ID_OK:
								self.animal_number[animal_name]=int(dialog1.GetValue())
							else:
								self.animal_number[animal_name]=1
							dialog1.Destroy()
						self.text_animalnumber.SetLabel('The number of '+str(self.animal_kinds)+' is: '+str(list(self.animal_number.values()))+'.')
					else:
						dialog1=wx.NumberEntryDialog(self,'','The number of animals:','Animal number',1,1,100)
						if dialog1.ShowModal()==wx.ID_OK:
							self.animal_number=int(dialog1.GetValue())
						else:
							self.animal_number=1
						self.text_animalnumber.SetLabel('The total number of animals in a video is '+str(self.animal_number)+'.')
						dialog1.Destroy()
				else:
					self.decode_animalnumber=True
					self.text_animalnumber.SetLabel('Decode from the filenames: the "n" immediately after the letter "n" in _"nn"_.')
			dialog.Destroy()


	def input_length(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'Enter the number of frames\nfor a behavior example','Enter a number\n(minimum=3):','Behavior episode duration',15,1,1000)
			if dialog.ShowModal()==wx.ID_OK:
				self.length=int(dialog.GetValue())
				if self.length<3:
					self.length=3
				self.text_length.SetLabel('The duration of a behavior example is: '+str(self.length)+' frames.')
			dialog.Destroy()


	def specify_redundant(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'How many frames to skip?','Enter a number:','Interval for generating examples',15,0,100000000000000)
			if dialog.ShowModal()==wx.ID_OK:
				self.skip_redundant=int(dialog.GetValue())
				self.text_skipredundant.SetLabel('Generate a pair of example every '+str(self.skip_redundant)+' frames.')
			else:
				self.skip_redundant=1
				self.text_skipredundant.SetLabel('Generate a pair of example at every frame.')
			dialog.Destroy()


	def generate_data(self,event):

		if self.path_to_videos is None or self.result_path is None:

			wx.MessageBox('No input video(s) / output folder selected.','Error',wx.OK|wx.ICON_ERROR)

		else:

			do_nothing=True

			dialog=wx.MessageDialog(self,'Include background in animations? Select "No"\nif background is behavior irrelevant.','Including background?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.background_free=False
			else:
				self.background_free=True
				dialog1=wx.MessageDialog(self,'Set background black? "Yes"=black background;\n"No"=white background (if animals are black).','Black background?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.black_background=True
				else:
					self.black_background=False
				dialog1.Destroy()
			dialog.Destroy()

			if self.behavior_mode>=3:

				if self.path_to_detector is None:
					wx.MessageBox('You need to select a Detector.','Error',wx.OK|wx.ICON_ERROR)
				else:
					AnalyzeAnimalDetector=import_generate_examples_analyzer('detector')
					if AnalyzeAnimalDetector is None:
						return
					AAD=AnalyzeAnimalDetector()
					AAD.analyze_images_individuals(self.path_to_detector,self.path_to_videos,self.result_path,self.animal_kinds,generate=True,imagewidth=self.framewidth,detection_threshold=self.detection_threshold,background_free=self.background_free,black_background=self.black_background)

			else:

				dialog=wx.MessageDialog(self,'Include body parts in pattern images?\nSelect "No" if limb movement is neglectable.','Including body parts?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.include_bodyparts=True
					dialog2=wx.NumberEntryDialog(self,'Leave it as it is if dont know what it is.','Enter a number between 0 and 255:','STD for motionless pixels',0,0,255)
					if dialog2.ShowModal()==wx.ID_OK:
						self.std=int(dialog2.GetValue())
					else:
						self.std=0
					dialog2.Destroy()
				else:
					self.include_bodyparts=False
				dialog.Destroy()

				dialog=wx.MessageDialog(self,'Start to generate behavior examples?','Start to generate examples?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					do_nothing=False
				else:
					do_nothing=True
				dialog.Destroy()

				if do_nothing is False:

					if self.use_detector is False:
						AnalyzeAnimal=import_generate_examples_analyzer('animal')
						if AnalyzeAnimal is None:
							return
					else:
						AnalyzeAnimalDetector=import_generate_examples_analyzer('detector')
						if AnalyzeAnimalDetector is None:
							return

					for i in self.path_to_videos:

						filename=os.path.splitext(os.path.basename(i))[0].split('_')
						if self.decode_animalnumber:
							if self.use_detector:
								self.animal_number={}
								number=[x[1:] for x in filename if len(x)>1 and x[0]=='n']
								for a,animal_name in enumerate(self.animal_kinds):
									self.animal_number[animal_name]=int(number[a])
							else:
								for x in filename:
									if len(x)>1:
										if x[0]=='n':
											self.animal_number=int(x[1:])
						if self.decode_t:
							for x in filename:
								if len(x)>1:
									if x[0]=='b':
										self.t=float(x[1:])
						if self.decode_extraction:
							for x in filename:
								if len(x)>2:
									if x[:2]=='xs':
										self.ex_start=int(x[2:])
									if x[:2]=='xe':
										self.ex_end=int(x[2:])

						if self.animal_number is None:
							if self.use_detector:
								self.animal_number={}
								for animal_name in self.animal_kinds:
									self.animal_number[animal_name]=1
							else:
								self.animal_number=1

						if self.use_detector is False:
							AA=AnalyzeAnimal()
							AA.prepare_analysis(i,self.result_path,self.animal_number,delta=self.delta,framewidth=self.framewidth,stable_illumination=self.stable_illumination,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,animation_analyzer=False,path_background=self.background_path,autofind_t=self.autofind_t,t=self.t,duration=self.duration,ex_start=self.ex_start,ex_end=self.ex_end,length=self.length,animal_vs_bg=self.animal_vs_bg)
							if self.behavior_mode==0:
								AA.generate_data(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							else:
								AA.generate_data_interact_basic(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
						else:
							AAD=AnalyzeAnimalDetector()
							AAD.prepare_analysis(self.path_to_detector,i,self.result_path,self.animal_number,self.animal_kinds,self.behavior_mode,framewidth=self.framewidth,channel=3,include_bodyparts=self.include_bodyparts,std=self.std,categorize_behavior=False,animation_analyzer=False,t=self.t,duration=self.duration,length=self.length,social_distance=self.social_distance)
							if self.behavior_mode==0:
								AAD.generate_data(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							elif self.behavior_mode==1:
								AAD.generate_data_interact_basic(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant)
							else:
								AAD.generate_data_interact_advance(background_free=self.background_free,black_background=self.black_background,skip_redundant=self.skip_redundant,color_costar=self.color_costar)



class PanelLv2_SortBehaviors(wx.Panel):

	'''
	The 'Sort Behavior Examples' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)
		boxsizer.Add(0,40,0)

		button_sortexamples=wx.Button(panel,label='Sort Examples (LabGym UI)',size=(300,40))
		button_sortexamples.Bind(wx.EVT_BUTTON,self.sort_examples)
		wx.Button.SetToolTip(button_sortexamples,'Use LabGym sorting UI to sort behavior examples that are generated by LabGym.')
		boxsizer.Add(button_sortexamples,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,20,0)

		button_sortexamplescsv=wx.Button(panel,label='Sort Examples (from .csv)',size=(300,40))
		button_sortexamplescsv.Bind(wx.EVT_BUTTON,self.sort_examples_csv)
		wx.Button.SetToolTip(button_sortexamplescsv,'Sort behavior examples that are generated by LabGym according to a .csv file that stores the frame-wise behavior labels annotated with other tools.')
		boxsizer.Add(button_sortexamplescsv,0,wx.ALIGN_CENTER,10)
		boxsizer.Add(0,30,0)

		# Align with the centered 300px button column (same wx.ALIGN_CENTER as buttons above).
		boxsizer.Add(
			create_hyperlink(
				panel,
				'Sorting Behavior Examples using LabGym',
				'https://youtu.be/WDCJ2HdrYJo?si=O6orNTNZiwR1girH',
			),
			0, wx.ALIGN_CENTER, 10)
		boxsizer.Add(0, 10, 0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def sort_examples(self,event):

		title = 'Sort Examples (LabGym UI)'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv3_SortExamples(self.notebook), title)


	def sort_examples_csv(self,event):

		title = 'Sort Examples (from .csv)'
		add_or_select_notebook_page(self.notebook, lambda: PanelLv3_SortExamplesCSV(self.notebook), title)



class PanelLv3_SortExamples(wx.Panel):

	'''
	The 'Sort Examples (LabGym UI)' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.input_path=None # the folder that stores unsorted behavior examples (one example is a pair of an animation and a pattern image)
		self.result_path=None # the folder that stores the sorted behavior examples
		self.keys_behaviors={} # stores the pairs of shortcut key-behavior name
		self.keys_behaviorpaths={} # stores the pairs of shortcut key-path to behavior examples

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_inputfolder=wx.Button(panel,label='Select the folder that stores\nunsorted behavior examples',size=(300,40))
		button_inputfolder.Bind(wx.EVT_BUTTON,self.input_folder)
		wx.Button.SetToolTip(button_inputfolder,'Select a folder that stores the behavior examples generated by "Generate Behavior Examples" functional unit. All examples in this folder should be in pairs (animation + pattern image).')
		self.text_inputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputfolder.Add(button_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputfolder.Add(self.text_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select the folder to store\nthe sorted behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.output_folder)
		wx.Button.SetToolTip(button_outputfolder,'A subfolder will be created for each behavior type under the behavior name.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_keynames=wx.BoxSizer(wx.HORIZONTAL)
		button_keynames=wx.Button(panel,label='Enter a single character shortcut key and\nthe corresponding behavior name',size=(300,40))
		button_keynames.Bind(wx.EVT_BUTTON,self.input_keys)
		wx.Button.SetToolTip(button_keynames,'Format: "shortcutkey-behaviorname". "o", "p", "q", and "u" are reserved for "Previous", "Next", "Quit", and "Undo". When hit a shortcut key, the behavior example pair will be moved to the folder named after the corresponding behavior name.')
		self.text_keynames=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_keynames.Add(button_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_keynames.Add(self.text_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_keynames,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_sort=wx.Button(panel,label='Sort behavior examples',size=(300,40))
		button_sort.Bind(wx.EVT_BUTTON,self.sort_behaviors)
		wx.Button.SetToolTip(button_sort,'You will see each example pair in the screen one by one and can use shortcut keys to sort them into folders of the behavior types.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_sort,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def input_folder(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.input_path=dialog.GetPath()
			self.text_inputfolder.SetLabel('Unsorted behavior examples are in: '+self.input_path+'.')
		dialog.Destroy()


	def output_folder(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Sorted behavior examples will be in: '+self.result_path+'.')
		dialog.Destroy()


	def input_keys(self,event):

		keynamepairs=''
		stop=False

		while stop is False:
			dialog=wx.TextEntryDialog(self,'Enter key-behaviorname pairs separated by ",".','Format: key1-name1,key2-name2,...',value=keynamepairs)
			if dialog.ShowModal()==wx.ID_OK:
				keynamepairs=dialog.GetValue()
				try:
					for pair in keynamepairs.split(','):
						key=pair.split('-')[0]
						name=pair.split('-')[1]
						if len(key)>1:
							wx.MessageBox('Key must be a single character.','Error',wx.OK|wx.ICON_ERROR)
							break
						if key in ['O','o','P','p','U','u','Q','q']:
							wx.MessageBox('The '+key+' is reserved. Please use another key.','Error',wx.OK|wx.ICON_ERROR)
							break
						else:
							self.keys_behaviors[key]=name
					self.text_keynames.SetLabel('The key-behaviorname pairs: '+keynamepairs+'.')
					stop=True
				except:
					wx.MessageBox('Please follow the correct format: key1-name1,key2-name2,....','Error',wx.OK|wx.ICON_ERROR)
			else:
				stop=True
		dialog.Destroy()


	def sort_behaviors(self,event):

		if self.input_path is None or self.result_path is None or len(self.keys_behaviors.items())==0:

			wx.MessageBox('No input / output folder or shortcut key - behavior name pair specified.','Error',wx.OK|wx.ICON_ERROR)

		else:

			for key in self.keys_behaviors:
				behavior_path=os.path.join(self.result_path,self.keys_behaviors[key])
				self.keys_behaviorpaths[key]=behavior_path
				os.makedirs(behavior_path,exist_ok=True)

			cv2.namedWindow('Sorting Behavior Examples',cv2.WINDOW_NORMAL)
			actions=[]
			index=0
			stop=False
			moved=False
			only_image=False

			check_animations=[i for i in os.listdir(self.input_path) if i.endswith('.avi')]
			if len(check_animations)==0:
				check_images=[i for i in os.listdir(self.input_path) if i.endswith('.jpg')]
				if len(check_images)==0:
					wx.MessageBox('No examples!','Error',wx.OK|wx.ICON_ERROR)
					stop=True
				else:
					only_image=True

			while stop is False:

				if moved:
					moved=False
					if only_image is False:
						shutil.move(os.path.join(self.input_path,example_name+'.avi'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.avi'))
					shutil.move(os.path.join(self.input_path,example_name+'.jpg'),os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.jpg'))

				pattern_images=[i for i in os.listdir(self.input_path) if i.endswith('.jpg')]
				pattern_images=sorted(pattern_images,key=lambda name:int(name.split('_len')[0].split('_')[-1]))

				if len(pattern_images)>0 and index<len(pattern_images):

					example_name=pattern_images[index].split('.jpg')[0]
					pattern_image=cv2.resize(cv2.imread(os.path.join(self.input_path,example_name+'.jpg')),(600,600),interpolation=cv2.INTER_AREA)

					if only_image is False:
						frame_count=example_name.split('_len')[0].split('_')[-1]
						animation=cv2.VideoCapture(os.path.join(self.input_path,example_name+'.avi'))
						fps=animation.get(cv2.CAP_PROP_FPS)

					while True:

						if only_image is False:
							ret,frame=animation.read()
							if not ret:
								animation.set(cv2.CAP_PROP_POS_FRAMES,0)
								continue
							frame=cv2.resize(frame,(600,600),interpolation=cv2.INTER_AREA)
							combined=np.hstack((frame,pattern_image))
							cv2.putText(combined,'frame count: '+frame_count,(10,15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							x_begin=550
						else:
							combined=pattern_image
							x_begin=5

						n=1
						for i in ['o: Prev','p: Next','q: Quit','u: Undo']:
							cv2.putText(combined,i,(x_begin,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							n+=1
						n+=1
						for i in self.keys_behaviors:
							cv2.putText(combined,i+': '+self.keys_behaviors[i],(x_begin,15*n),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,255),1)
							n+=1

						cv2.imshow('Sorting Behavior Examples',combined)
						cv2.moveWindow('Sorting Behavior Examples',50,0)

						if only_image is False:
							key=cv2.waitKey(int(1000/fps)) & 0xFF
						else:
							key=cv2.waitKey(1) & 0xFF

						for shortcutkey in self.keys_behaviorpaths:
							if key==ord(shortcutkey):
								example_name=pattern_images[index].split('.')[0]
								actions.append([shortcutkey,example_name])
								moved=True
								break
						if moved:
							break

						if key==ord('u'):
							if len(actions)>0:
								last=actions.pop()
								shortcutkey=last[0]
								example_name=last[1]
								if only_image is False:
									shutil.move(os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.avi'),os.path.join(self.input_path,example_name+'.avi'))
								shutil.move(os.path.join(self.keys_behaviorpaths[shortcutkey],example_name+'.jpg'),os.path.join(self.input_path,example_name+'.jpg'))
								break
							else:
								wx.MessageBox('Nothing to undo.','Error',wx.OK|wx.ICON_ERROR)
								continue

						if key==ord('p'):
							index+=1
							break

						if key==ord('o'):
							if index>=1:
								index-=1
							break

						if key==ord('q'):
							stop=True
							break

					if only_image is False:
						animation.release()

				else:
					if len(pattern_images)==0:
						wx.MessageBox('Behavior example sorting completed!','Completed!',wx.OK|wx.ICON_INFORMATION)
						stop=True
					else:
						wx.MessageBox('This is the last behavior example!','To the end.',wx.OK|wx.ICON_INFORMATION)
						index=0

			cv2.destroyAllWindows()



class PanelLv3_SortExamplesCSV(wx.Panel):

	'''
	The 'Sort Examples (from .csv)' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent
		self.path_to_examples=None # path to unsorted behavior examples generated by LabGym, should also contain the annotation '.csv' file
		self.result_path=None # the folder for storing sorted behavior examples

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe unsorted behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_inpath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should directly store unsorted behavior examples generated by LabGym, as well as a .csv file that stores the frame-wise behavior labels.')
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(self.text_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_outputfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_outputfolder=wx.Button(panel,label='Select a folder to store\nthe sorted behavior examples',size=(300,40))
		button_outputfolder.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_outputfolder,'The sorted behavior examples will be in the selected folder.')
		self.text_outputfolder=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_outputfolder.Add(button_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_outputfolder.Add(self.text_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_outputfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_sortfromcsv=wx.Button(panel,label='Sort examples based on the .csv',size=(300,40))
		button_sortfromcsv.Bind(wx.EVT_BUTTON,self.sort_fromcsv)
		wx.Button.SetToolTip(button_sortfromcsv,'The unsorted behavior examples should be generated from the begining (the 0th second) of the video.')
		boxsizer.Add(0,5,0)
		boxsizer.Add(button_sortfromcsv,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_inpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.path_to_examples=dialog.GetPath()
			self.text_inputexamples.SetLabel('Unsorted examples are in: '+self.path_to_examples+'.')
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.result_path=dialog.GetPath()
			self.text_outputfolder.SetLabel('Sorted examples will be in: '+self.result_path+'.')
		dialog.Destroy()


	def sort_fromcsv(self,event):

		if self.path_to_examples is None or self.result_path is None:
			wx.MessageBox('No input / output folder.','Error',wx.OK|wx.ICON_ERROR)
		else:
			sort_examples_from_csv(self.path_to_examples,self.result_path)



class PanelLv2_TrainCategorizers(wx.Panel):

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		# Get all of the values needed from config.get_config().
		self.config = config.get_config('models')

		self.file_path=None # the folder that stores sorted, unprepared behavior examples (each category is a subfolder)
		self.new_path=None # the folder that stores prepared behavior examples (contains all examples with a category tag in their names)
		self.behavior_mode=0 # 0--non-interactive, 1--interactive basic, 2--interactive advanced, 3--static images
		self.animation_analyzer=True # whether to include Animation Analyzer in the Categorizers
		self.level_tconv=2 # complexity level of Animation Analyzer in Categorizer
		self.level_conv=2 # complexity level of Pattern Recognizer in Categorizer
		self.dim_tconv=32 # input dimension for Animation Analyzer in Categorizer
		self.dim_conv=32 # input dimension for Pattern Recognizer in Categorizer
		self.channel=1 # input channel for Animation Analyzer, 1--gray scale, 3--RGB scale
		self.length=15 # input time step for Animation Analyzer, also the duration / length for a behavior example
		self.aug_methods=[] # the methods for augment training and validation examples
		self.augvalid=True # whether to perform augmentation for validation data as well
		self.data_path=None # the folder that stores prepared behavior examples
		self.model_path = self.config['models']  # the 'LabGym/models' folder, which stores all the trained Categorizers
		logger.debug('%s: %r', 'self.model_path', self.model_path)
		self.path_to_categorizer = os.path.join(self.config['models'], 'New_model')  # path to the Categorizer
		logger.debug('%s: %r', 'self.path_to_categorizer', self.path_to_categorizer)
		self.out_path=None # the folder for storing the training reports
		self.include_bodyparts=False # whether to include body parts in the pattern images
		self.std=0 # a value between 0 and 255, higher value, less body parts will be included in the pattern images
		self.resize=None # resize the frames and pattern images before data augmentation
		self.background_free=True # whether to include background in animations
		self.black_background=True # whether to set background black
		self.social_distance=0 # a threshold (folds of size of a single animal) on whether to include individuals that are not main character in behavior examples
		self.color_costar=False # in 'interactive advanced' mode, whether to make the supporting roles RGB scale in animations
		self.out_folder=None # if not None, the folder stores the augmented examples
		self.training_onfly=False # whether to train a Categorizer using behavior examples that are already augmented previously

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe sorted behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_filepath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders will be read by LabGym as the behavior names.')
		# Right-hand content: path label + compact count button (always present; Enable/Disable only)
		inputexamples_right=wx.BoxSizer(wx.VERTICAL)
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		self.button_view_sorted_counts=wx.Button(panel,label='View Behavior Counts',size=(200,28))
		self.button_view_sorted_counts.Bind(wx.EVT_BUTTON,self.show_sorted_count_popup)
		self.button_view_sorted_counts.Disable()
		wx.Button.SetToolTip(self.button_view_sorted_counts,'View example counts for each sorted behavior category.')
		inputexamples_right.Add(self.text_inputexamples,0,wx.EXPAND)
		inputexamples_right.Add(self.button_view_sorted_counts,0,wx.TOP,4)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(inputexamples_right,1,wx.EXPAND|wx.LEFT|wx.RIGHT,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_renameexample=wx.BoxSizer(wx.HORIZONTAL)
		button_renameexample=wx.Button(panel,label='Select a new folder to store\nall the prepared behavior examples',size=(300,40))
		button_renameexample.Bind(wx.EVT_BUTTON,self.select_outpath)
		wx.Button.SetToolTip(button_renameexample,'This folder will store all the prepared behavior examples and can be directly used for training. Preparing behavior examples is copying all examples into this folder and renaming them to put behavior name labels to their file names.')
		self.text_renameexample=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_renameexample.Add(button_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_renameexample.Add(self.text_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_renameexample,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_prepare=wx.Button(panel,label='Start to prepare the training examples',size=(300,40))
		button_prepare.Bind(wx.EVT_BUTTON,self.rename_files)
		wx.Button.SetToolTip(button_prepare,'All prepared behavior examples will be stored in the same folder and ready to be input for training.')
		boxsizer.Add(button_prepare,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		module_categorizertype=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizertype=wx.Button(panel,label='Specify the type / complexity of\nthe Categorizer to train',size=(300,40))
		button_categorizertype.Bind(wx.EVT_BUTTON,self.specify_categorizer)
		wx.Button.SetToolTip(button_categorizertype,'Categorizer with both Animation Analyzer and Pattern Recognizer is slower but a little more accurate than that with Pattern Recognizer only. Higher complexity level means deeper and more complex network architecture. See Extended Guide for details.')
		self.text_categorizertype=wx.StaticText(panel,label='Default: Categorizer (Animation Analyzer LV2 + Pattern Recognizer LV2). Behavior mode: Non-interact (identify behavior for each individual).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizertype.Add(button_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizertype.Add(self.text_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_categorizertype,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_categorizershape=wx.BoxSizer(wx.HORIZONTAL)
		button_categorizershape=wx.Button(panel,label='Specify the input shape for\nAnimation Analyzer / Pattern Recognizer',size=(300,40))
		button_categorizershape.Bind(wx.EVT_BUTTON,self.set_categorizer)
		wx.Button.SetToolTip(button_categorizershape,'The input frame / image size should be an even integer and larger than 8. The larger size, the wider of network architecture. Use large size only when there are detailed features in frames / images that are important for identifying behaviors. See Extended Guide for details.')
		self.text_categorizershape=wx.StaticText(panel,label='Default: (width,height,channel) is (32,32,1) / (32,32,3).',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_categorizershape.Add(button_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_categorizershape.Add(self.text_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_categorizershape,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_length=wx.BoxSizer(wx.HORIZONTAL)
		button_length=wx.Button(panel,label='Specify the number of frames for\nan animation / pattern image',size=(300,40))
		button_length.Bind(wx.EVT_BUTTON,self.input_timesteps)
		wx.Button.SetToolTip(button_length,'The duration (how many frames) of a behavior example. This info can be found in the filenames of the generated behavior examples, "_lenXX_" where "XX" is the number you need to enter here.')
		self.text_length=wx.StaticText(panel,label='Default: 15.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_length.Add(button_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_length.Add(self.text_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_length,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_trainingfolder=wx.BoxSizer(wx.HORIZONTAL)
		button_trainingfolder=wx.Button(panel,label='Select the folder that stores\nall the prepared training examples',size=(300,40))
		button_trainingfolder.Bind(wx.EVT_BUTTON,self.select_datapath)
		wx.Button.SetToolTip(button_trainingfolder,'The folder that stores all the prepared behavior examples. If these are previously augmented, this folder should contain a "train" and a "vadilation" subfolder. If body parts are included, the STD value can be found in the filenames of the generated behavior examples with "_stdXX_" where "XX" is the STD value.')
		# Right-hand content: path label + compact count button (always present; Enable/Disable only)
		trainingfolder_right=wx.BoxSizer(wx.VERTICAL)
		self.text_trainingfolder=wx.StaticText(panel,label='None',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		self.button_view_counts=wx.Button(panel,label='View Behavior Counts',size=(200,28))
		self.button_view_counts.Bind(wx.EVT_BUTTON,self.show_count_popup)
		self.button_view_counts.Disable()
		wx.Button.SetToolTip(self.button_view_counts,'View example counts for each prepared training category.')
		trainingfolder_right.Add(self.text_trainingfolder,0,wx.EXPAND)
		trainingfolder_right.Add(self.button_view_counts,0,wx.TOP,4)
		module_trainingfolder.Add(button_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_trainingfolder.Add(trainingfolder_right,1,wx.EXPAND|wx.LEFT|wx.RIGHT,10)
		boxsizer.Add(module_trainingfolder,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_augmentation=wx.BoxSizer(wx.HORIZONTAL)
		button_augmentation=wx.Button(panel,label='Specify the methods to\naugment training examples',size=(300,40))
		button_augmentation.Bind(wx.EVT_BUTTON,self.specify_augmentation)
		wx.Button.SetToolTip(button_augmentation,'Randomly manipulate the training examples to increase their amount and diversity and benefit the training. If the amount of examples less than 1,000 before augmentation, choose "Also augment the validation data". You can also export the augmented examples to save this step in future training. See Extended Guide for details.')
		self.text_augmentation=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_augmentation.Add(button_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_augmentation.Add(self.text_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_augmentation,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_report=wx.BoxSizer(wx.HORIZONTAL)
		button_report=wx.Button(panel,label='Select a folder to\nexport training reports',size=(300,40))
		button_report.Bind(wx.EVT_BUTTON,self.select_reportpath)
		wx.Button.SetToolTip(button_report,'This is the folder to store the reports of training history and metrics. It is optional.')
		self.text_report=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_report.Add(button_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_report.Add(self.text_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		button_train=wx.Button(panel,label='Train the Categorizer',size=(300,40))
		button_train.Bind(wx.EVT_BUTTON,self.train_categorizer)
		wx.Button.SetToolTip(button_train,'Need to name the Categorizer to train. English letters, numbers, underscore “_”, or hyphen “-” are acceptable but do not use special characters such as “@” or “^”.')
		boxsizer.Add(button_train,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def _count_examples(self,folder_path):
		return count_prepared_examples(folder_path)


	def _update_count_display(self,folder_path):
		counts=self._count_examples(folder_path)
		if not counts_enable_diagnostics(counts):
			self._counts={}
			self.button_view_counts.Disable()
			return
		self._counts=counts
		self.button_view_counts.Enable()


	def _iter_count_rows(self,counts):
		'''Yield behavior-name rows matching the 3-items-per-row body layout.'''
		names=sorted(counts)
		i=0
		while i<len(names):
			chunk=names[i:i+3]
			if len(chunk)==3:
				row_text='  |  '.join(f'{n}: {counts[n]} examples' for n in chunk)
				if len(row_text)>200:
					chunk=names[i:i+2]
			yield chunk
			i+=len(chunk)


	def _count_display_lines(self,counts,threshold):
		'''Return (count_rows, add_rows) for the body layout at the given threshold.'''
		count_rows=0
		add_rows=0
		for row in self._iter_count_rows(counts):
			count_rows+=1
			if any(counts[name]<threshold for name in row):
				add_rows+=1
		return count_rows,add_rows


	def _counts_area_height(self,counts,threshold,max_h):
		'''Natural height for the counts area; capped only when content exceeds max_h.

		Returns (display_height, needs_scroll).
		'''
		# Generous per-line budget so ordinary small datasets do not show a scrollbar
		count_row_h=26
		add_row_h=20
		pad=18
		count_rows,add_rows=self._count_display_lines(counts,threshold)
		natural=count_rows*count_row_h+add_rows*add_row_h+pad
		if natural<=max_h:
			return natural,False
		return max_h,True


	def _measure_popup_width(self,title,counts,threshold,min_w,max_w):
		'''Content-based width from longest title/legend/threshold/count line.'''
		dc=wx.ScreenDC()
		normal=wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		title_font=wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
		widths=[]
		dc.SetFont(title_font)
		widths.append(dc.GetTextExtent(title)[0])
		dc.SetFont(normal)
		widths.append(dc.GetTextExtent(
			f'Red text: Example count is below {threshold} (minimum threshold)')[0])
		widths.append(dc.GetTextExtent(
			'Yellow highlight: Example count is outside 1 population '
			'standard deviation from the mean')[0])
		# label + text field + Update button
		widths.append(dc.GetTextExtent('Minimum recommended examples:')[0]+70+72+24)
		for row in self._iter_count_rows(counts):
			line='  |  '.join(f'{n}: {counts[n]} examples' for n in row)
			widths.append(dc.GetTextExtent(line)[0])
			below=[(name,threshold-counts[name]) for name in row if counts[name]<threshold]
			if below:
				add_line='    add: '+', '.join(f'{n} ({needed})' for n,needed in below)
				widths.append(dc.GetTextExtent(add_line)[0])
		content_w=max(widths)+40
		return max(min_w,min(max_w,content_w))


	def _render_body(self,rtc,counts,threshold):
		# Population SD (divide by n, not n-1); yellow when |count - mean| > SD
		values=list(counts.values())
		mean=sum(values)/len(values)
		std=(sum((v-mean)**2 for v in values)/len(values))**0.5
		rtc.Clear()
		for row in self._iter_count_rows(counts):
			for i_item,name in enumerate(row):
				count=counts[name]
				attr=wx.richtext.RichTextAttr()
				attr.SetTextColour(wx.Colour(180,0,0) if count<threshold else wx.Colour(0,0,0))
				if std>0 and abs(count-mean)>std:
					attr.SetBackgroundColour(wx.YELLOW)
				rtc.BeginStyle(attr)
				rtc.WriteText(f'{name}: {count} examples')
				rtc.EndStyle()
				if i_item<len(row)-1:
					sep_attr=wx.richtext.RichTextAttr()
					sep_attr.SetTextColour(wx.Colour(0,0,0))
					sep_attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
					rtc.BeginStyle(sep_attr)
					rtc.WriteText('  |  ')
					rtc.EndStyle()
			rtc.WriteText('\n')
			below_t=[(name,threshold-counts[name]) for name in row if counts[name]<threshold]
			if below_t:
				add_attr=wx.richtext.RichTextAttr()
				add_attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
				add_attr.SetFontSize(10)
				add_attr.SetTextColour(wx.Colour(60,60,60))
				rtc.BeginStyle(add_attr)
				rtc.WriteText('    add: '+', '.join(f'{n} ({needed})' for n,needed in below_t)+'\n')
				rtc.EndStyle()


	def _show_behavior_count_popup(self,title,counts,threshold,set_threshold):
		'''Shared builder for prepared/sorted View Behavior Counts popups.'''
		bg=wx.Colour(255,255,255)
		fg=wx.Colour(0,0,0)
		btn_bg=wx.Colour(230,230,230)
		red_fg=wx.Colour(180,0,0)
		margin=10

		frame=self.GetTopLevelParent()
		fr=frame.GetRect()
		min_w=360
		max_w=max(min_w,min(720,fr.width-40))
		max_counts_h=max(120,min(360,fr.height//2))

		popup_w=self._measure_popup_width(title,counts,threshold,min_w,max_w)
		counts_h,needs_scroll=self._counts_area_height(counts,threshold,max_counts_h)

		popup=wx.PopupTransientWindow(self,wx.NO_BORDER)
		popup.SetBackgroundColour(bg)
		popup._applied_threshold=threshold

		def on_paint(evt,_p=popup):
			dc=wx.PaintDC(_p)
			dc.SetPen(wx.Pen(wx.BLACK,1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			w,h=_p.GetClientSize()
			dc.DrawRectangle(0,0,w,h)
		popup.Bind(wx.EVT_PAINT,on_paint)

		outer=wx.BoxSizer(wx.VERTICAL)

		# Title + close control (outside-click dismissal still works)
		title_row=wx.BoxSizer(wx.HORIZONTAL)
		title_lbl=wx.StaticText(popup,label=title,style=wx.ALIGN_CENTRE_HORIZONTAL)
		title_lbl.SetFont(wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD))
		title_lbl.SetForegroundColour(fg)
		title_lbl.SetBackgroundColour(bg)
		close_btn=wxbuttons.GenButton(popup,label='×',size=(24,24))
		close_btn.SetBackgroundColour(btn_bg)
		close_btn.SetForegroundColour(fg)
		close_btn.SetFont(wx.Font(14,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD))
		close_btn.SetBezelWidth(1)
		close_btn.SetUseFocusIndicator(False)
		close_btn.SetToolTip('Close')
		title_row.Add((24,24),0,wx.ALIGN_CENTER_VERTICAL)  # balance the close button
		title_row.Add(title_lbl,1,wx.ALIGN_CENTER_VERTICAL)
		title_row.Add(close_btn,0,wx.ALIGN_CENTER_VERTICAL)
		outer.Add(title_row,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Legend: plain StaticText rows (no RichTextCtrl / scrollbars)
		leg_font=wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

		leg1=wx.BoxSizer(wx.HORIZONTAL)
		red_sample=wx.StaticText(popup,label='Red text:')
		red_sample.SetFont(leg_font)
		red_sample.SetForegroundColour(red_fg)
		red_sample.SetBackgroundColour(bg)
		red_explain=wx.StaticText(
			popup,label=f' Example count is below {threshold} (minimum threshold)')
		red_explain.SetFont(leg_font)
		red_explain.SetForegroundColour(fg)
		red_explain.SetBackgroundColour(bg)
		leg1.Add(red_sample,0,wx.ALIGN_CENTER_VERTICAL)
		leg1.Add(red_explain,0,wx.ALIGN_CENTER_VERTICAL)
		outer.Add(leg1,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		leg2=wx.BoxSizer(wx.HORIZONTAL)
		# Small coloured chip so the sample is visible even when StaticText bg is ignored
		yl_chip=wx.Panel(popup)
		yl_chip.SetBackgroundColour(wx.YELLOW)
		yl_chip_s=wx.BoxSizer(wx.HORIZONTAL)
		yl_sample=wx.StaticText(yl_chip,label='Yellow highlight:')
		yl_sample.SetFont(leg_font)
		yl_sample.SetForegroundColour(fg)
		yl_sample.SetBackgroundColour(wx.YELLOW)
		yl_chip_s.Add(yl_sample,0,wx.ALL,1)
		yl_chip.SetSizer(yl_chip_s)
		yl_explain=wx.StaticText(
			popup,label=(
				' Example count is outside 1 population standard deviation '
				'from the mean'))
		yl_explain.SetFont(leg_font)
		yl_explain.SetForegroundColour(fg)
		yl_explain.SetBackgroundColour(bg)
		leg2.Add(yl_chip,0,wx.ALIGN_CENTER_VERTICAL)
		leg2.Add(yl_explain,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,2)
		outer.Add(leg2,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Threshold row (same white surface as the rest of the dialog)
		thr_row=wx.BoxSizer(wx.HORIZONTAL)
		thr_lbl=wx.StaticText(popup,label='Minimum recommended examples:')
		thr_lbl.SetFont(leg_font)
		thr_lbl.SetForegroundColour(fg)
		thr_lbl.SetBackgroundColour(bg)
		thr_txt=wx.TextCtrl(
			popup,value=str(threshold),size=(64,-1),
			style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT)
		thr_txt.SetForegroundColour(fg)
		thr_txt.SetBackgroundColour(bg)
		# GenButton paints its own colours; native wx.Button often does not on macOS
		btn=wxbuttons.GenButton(popup,label='Update',size=(72,26))
		btn.SetBackgroundColour(btn_bg)
		btn.SetForegroundColour(fg)
		btn.SetBezelWidth(1)
		btn.SetUseFocusIndicator(False)
		thr_row.Add(thr_lbl,0,wx.ALIGN_CENTER_VERTICAL)
		thr_row.Add(thr_txt,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,6)
		thr_row.Add(btn,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT,6)
		outer.Add(thr_row,0,wx.LEFT|wx.RIGHT|wx.TOP,margin)

		# Counts (RichTextCtrl kept only for mixed red/yellow inline formatting)
		rtc_style=wx.TE_READONLY|wx.NO_BORDER
		if not needs_scroll:
			rtc_style|=wx.TE_NO_VSCROLL
		rtc_counts=wx.richtext.RichTextCtrl(
			popup,size=(popup_w-2*margin,counts_h),style=rtc_style)
		rtc_counts.SetBackgroundColour(bg)
		rtc_counts.SetForegroundColour(fg)
		rtc_counts.SetEditable(False)
		rtc_counts.SetMinSize((popup_w-2*margin,counts_h))
		self._render_body(rtc_counts,counts,threshold)
		outer.Add(rtc_counts,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM,margin)

		popup.SetSizer(outer)
		outer.Layout()
		popup_h=outer.GetMinSize().height+2
		popup.SetClientSize(popup_w,popup_h)

		def _parse_threshold():
			s=thr_txt.GetValue().strip()
			if not s.isdigit():
				return None
			v=int(s)
			return v if v>=1 else None

		def _filter_threshold_char(evt):
			key=evt.GetKeyCode()
			if key in (
					wx.WXK_BACK,wx.WXK_DELETE,wx.WXK_TAB,wx.WXK_LEFT,wx.WXK_RIGHT,
					wx.WXK_HOME,wx.WXK_END,wx.WXK_RETURN,wx.WXK_NUMPAD_ENTER,
					wx.WXK_NUMPAD_DELETE):
				evt.Skip()
				return
			if wx.WXK_NUMPAD0<=key<=wx.WXK_NUMPAD9:
				evt.Skip()
				return
			if 32<=key<256 and chr(key).isdigit():
				evt.Skip()
				return
			# ignore non-digit characters

		def on_apply(evt):
			t=_parse_threshold()
			if t is None:
				thr_txt.SetValue(str(popup._applied_threshold))
				return
			popup._applied_threshold=t
			set_threshold(t)
			red_explain.SetLabel(f' Example count is below {t} (minimum threshold)')
			self._render_body(rtc_counts,counts,t)
			new_h,_=self._counts_area_height(counts,t,max_counts_h)
			rtc_counts.SetMinSize((popup_w-2*margin,new_h))
			rtc_counts.SetSize((popup_w-2*margin,new_h))
			outer.Layout()
			popup.SetClientSize(popup_w,outer.GetMinSize().height+2)

		thr_txt.Bind(wx.EVT_CHAR,_filter_threshold_char)
		thr_txt.Bind(wx.EVT_TEXT_ENTER,on_apply)
		btn.Bind(wx.EVT_BUTTON,on_apply)
		close_btn.Bind(wx.EVT_BUTTON,lambda evt:popup.Dismiss())

		ph=popup.GetSize().height
		popup.SetPosition(wx.Point(fr.x+(fr.width-popup_w)//2,fr.y+(fr.height-ph)//2))
		popup.Popup()


	def show_count_popup(self,event):
		counts=getattr(self,'_counts',{})
		if not counts_enable_diagnostics(counts):
			return
		if not hasattr(self,'_count_threshold'):
			self._count_threshold=250
		self._show_behavior_count_popup(
			'Prepared Training Examples',counts,self._count_threshold,
			lambda t:setattr(self,'_count_threshold',t))


	def _count_from_subfolders(self,folder_path):
		return count_sorted_examples(folder_path)


	def _update_sorted_count_display(self,folder_path):
		counts=self._count_from_subfolders(folder_path)
		if not counts_enable_diagnostics(counts):
			self._sorted_counts={}
			self.button_view_sorted_counts.Disable()
			return
		self._sorted_counts=counts
		self.button_view_sorted_counts.Enable()


	def show_sorted_count_popup(self,event):
		counts=getattr(self,'_sorted_counts',{})
		if not counts_enable_diagnostics(counts):
			return
		if not hasattr(self,'_sorted_count_threshold'):
			self._sorted_count_threshold=250
		self._show_behavior_count_popup(
			'Sorted Behavior Examples',counts,self._sorted_count_threshold,
			lambda t:setattr(self,'_sorted_count_threshold',t))


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_inputexamples.SetLabel('Path to sorted behavior examples: '+self.file_path+'.')
			self._update_sorted_count_display(self.file_path)
		dialog.Destroy()


	def select_outpath(self,event):

		dialog=wx.DirDialog(self,'Select a new directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.new_path=dialog.GetPath()
			self.text_renameexample.SetLabel('Will copy and rename the examples to: '+self.new_path+'.')
		dialog.Destroy()

		dialog=wx.MessageDialog(self,'Reducing frame / image size can speed up training\nSelect "No" if dont know what it is.','Resize the frames / images?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.NumberEntryDialog(self,'Enter the desired width dimension','No smaller than the\ndesired input dimension of the Categorizer:','Frame / image dimension',32,1,300)
			if dialog1.ShowModal()==wx.ID_OK:
				self.resize=int(dialog1.GetValue())
			if self.resize<16:
				self.resize=16
			self.text_renameexample.SetLabel('Will copy, rename, and resize (to '+str(self.resize)+') the examples to: '+self.new_path+'.')
			dialog1.Destroy()
		else:
			self.resize=None
		dialog.Destroy()


	def rename_files(self,event):

		if self.file_path is None or self.new_path is None:
			wx.MessageBox('Please select a folder that stores the sorted examples /\na new folder to store prepared training examples!','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			CA.rename_label(self.file_path,self.new_path,resize=self.resize)


	def specify_categorizer(self,event):

		behavior_modes=['Non-interact (identify behavior for each individual)','Interact basic (identify behavior for the interactive pair / group)','Interact advanced (identify behavior for both each individual and each interactive pair / group)','Static images (non-interactive): behaviors of each individual in static images (each image contains one animal / object)']
		dialog=wx.SingleChoiceDialog(self,message='Specify the mode of behavior for the Categorizer to identify',caption='Behavior mode',choices=behavior_modes)
		if dialog.ShowModal()==wx.ID_OK:
			behavior_mode=dialog.GetStringSelection()
			if behavior_mode=='Non-interact (identify behavior for each individual)':
				self.behavior_mode=0
			elif behavior_mode=='Interact basic (identify behavior for the interactive pair / group)':
				self.behavior_mode=1
			elif behavior_mode=='Interact advanced (identify behavior for both each individual and each interactive pair / group)':
				self.behavior_mode=2
				self.channel=3
				dialog1=wx.NumberEntryDialog(self,'Interactions happen within the interaction distance.',"How many folds of the animals's diameter\nis the interaction distance (0=inf):",'interaction distance (Enter an integer)',0,0,100000000000000)
				if dialog1.ShowModal()==wx.ID_OK:
					self.social_distance=int(dialog1.GetValue())
				else:
					self.social_distance=0
				dialog1.Destroy()
				dialog1=wx.MessageDialog(self,'Make both main and supporting characters RGB scale?\nSelect "No" if dont know what it is.','(Optional) RGB supporting characters?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.color_costar=True
				else:
					self.color_costar=False
				dialog1.Destroy()
			else:
				self.behavior_mode=3
				self.text_length.SetLabel('No need to specify this since the selected behavior mode is "Static images".')
		dialog.Destroy()

		if self.behavior_mode>=3:
			categorizer_types=['Categorizer (Pattern Recognizer only) (faster / a little less accurate)']
		else:
			categorizer_types=['Categorizer (Animation Analyzer + Pattern Recognizer)','Categorizer (Pattern Recognizer only) (faster / a little less accurate)']
		dialog=wx.SingleChoiceDialog(self,message='Select the Categorizer type',caption='Categorizer types',choices=categorizer_types)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer_tp=dialog.GetStringSelection()
			if categorizer_tp=='Categorizer (Pattern Recognizer only) (faster / a little less accurate)':
				self.animation_analyzer=False
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog1.GetValue())
				dialog1.Destroy()
				level=self.level_conv
			else:
				self.animation_analyzer=True
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Animation Analyzer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_tconv=int(dialog1.GetValue())
				dialog1.Destroy()
				dialog1=wx.NumberEntryDialog(self,'Complexity level from 1 to 7\nhigher level = deeper network','Enter a number (1~7)','Pattern Recognizer level',2,1,7)
				if dialog1.ShowModal()==wx.ID_OK:
					self.level_conv=int(dialog1.GetValue())
				dialog1.Destroy()
				level=[self.level_tconv,self.level_conv]
		else:
			categorizer_tp=''
			level=''
		dialog.Destroy()

		if self.behavior_mode==0:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of each non-interactive individual.')
		elif self.behavior_mode==1:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of the interactive group.')
		elif self.behavior_mode==2:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of the interactive individuals and groups. interaction distance: '+str(self.social_distance)+' folds of the animal diameter.')
		else:
			self.text_categorizertype.SetLabel(categorizer_tp+' (LV '+str(level)+') to identify behaviors of each non-interactive individual in static images.')


	def set_categorizer(self,event):

		if self.animation_analyzer:
			dialog=wx.NumberEntryDialog(self,'Input dimension of Animation Analyzer\nlarger dimension = wider network','Enter a number:','Animation Analyzer input',32,1,300)
			if dialog.ShowModal()==wx.ID_OK:
				self.dim_tconv=int(dialog.GetValue())
			dialog.Destroy()
			if self.behavior_mode==2:
				self.channel=3
			else:
				dialog=wx.MessageDialog(self,'Grayscale input of Animation Analyzer?\nSelect "Yes" if the color of animals is behavior irrelevant.','Grayscale Animation Analyzer?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.channel=1
				else:
					self.channel=3
				dialog.Destroy()

		dialog=wx.NumberEntryDialog(self,'Input dimension of Pattern Recognizer\nlarger dimension = wider network','Enter a number:','Input the dimension',32,1,300)
		if dialog.ShowModal()==wx.ID_OK:
			self.dim_conv=int(dialog.GetValue())
			if self.behavior_mode>=3:
				dialog1=wx.MessageDialog(self,'Grayscale input?\nSelect "Yes" if the color of animals is behavior irrelevant.','Grayscale inputs?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog1.ShowModal()==wx.ID_YES:
					self.channel=1
				else:
					self.channel=3
				dialog.Destroy()
		dialog.Destroy()

		shape_tconv='('+str(self.dim_tconv)+','+str(self.dim_tconv)+','+str(self.channel)+')'
		if self.behavior_mode>=3:
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+str(self.channel)+')'
		else:
			shape_conv='('+str(self.dim_conv)+','+str(self.dim_conv)+','+'3)'
		if self.animation_analyzer is False:
			self.text_categorizershape.SetLabel('Input shapes: Pattern Recognizer'+shape_conv+'.')
		else:
			self.text_categorizershape.SetLabel('Input shapes: Animation Analyzer'+shape_tconv+'; Pattern Recognizer'+shape_conv+'.')


	def input_timesteps(self,event):

		if self.behavior_mode>=3:

			wx.MessageBox('No need to specify this since the selected behavior mode is "Static images".','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.NumberEntryDialog(self,'The number of frames of\na behavior example','Enter a number (minimum=3):','Behavior episode duration',15,1,1000)
			if dialog.ShowModal()==wx.ID_OK:
				self.length=int(dialog.GetValue())
				if self.length<3:
					self.length=3
				self.text_length.SetLabel('The duration of a behavior example is :'+str(self.length)+'.')
			dialog.Destroy()


	def select_datapath(self,event):

		dialog=wx.MessageDialog(self,'Are the behavior examples already augmented previously?','Examples already augmented?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			self.training_onfly=True
			self.text_augmentation.SetLabel('No need to do augmentation because the training data is already augmented.')
		else:
			self.training_onfly=False
			self.out_folder=None
		dialog.Destroy()

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.data_path=dialog.GetPath()
		dialog.Destroy()

		if self.data_path is None:

			wx.MessageBox('No data path has been specified.','Error',wx.OK|wx.ICON_ERROR)

		else:

			if self.behavior_mode>=3:

				self.include_bodyparts=False

				dialog=wx.MessageDialog(self,'Are the images in\ntraining examples background free?','Background-free images?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.background_free=True
					dialog1=wx.MessageDialog(self,'Are the background in images black? "Yes"=black background;\n"No"=white background.','Black background?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog1.ShowModal()==wx.ID_YES:
						self.black_background=True
					else:
						self.black_background=False
					dialog1.Destroy()
					self.text_trainingfolder.SetLabel('Static images w/o background in: '+self.data_path+'.')
				else:
					self.background_free=False
					self.text_trainingfolder.SetLabel('Static images w/ background in: '+self.data_path+'.')
				dialog.Destroy()

			else:

				if self.animation_analyzer:
					dialog=wx.MessageDialog(self,'Are the animations (in any) in\ntraining examples background free?','Background-free animations?',wx.YES_NO|wx.ICON_QUESTION)
					if dialog.ShowModal()==wx.ID_YES:
						self.background_free=True
						dialog1=wx.MessageDialog(self,'Are the background in animations black?\n"Yes"=black background; "No"=white background.','Black background?',wx.YES_NO|wx.ICON_QUESTION)
						if dialog1.ShowModal()==wx.ID_YES:
							self.black_background=True
						else:
							self.black_background=False
						dialog1.Destroy()
					else:
						self.background_free=False
					dialog.Destroy()

				dialog=wx.MessageDialog(self,'Do the pattern images in training examples\ninclude body parts?','Body parts in pattern images?',wx.YES_NO|wx.ICON_QUESTION)
				if dialog.ShowModal()==wx.ID_YES:
					self.include_bodyparts=True
					dialog2=wx.NumberEntryDialog(self,'Should match the STD of the pattern images in training examples.','Enter a number between 0 and 255:','STD for motionless pixels',0,0,255)
					if dialog2.ShowModal()==wx.ID_OK:
						self.std=int(dialog2.GetValue())
					else:
						self.std=0
					dialog2.Destroy()
				else:
					self.include_bodyparts=False
				dialog.Destroy()

				if self.include_bodyparts:
					if self.animation_analyzer:
						if self.background_free:
							self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
						else:
							self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
					else:
						self.text_trainingfolder.SetLabel('Pattern images w/ bodyparts ('+str(self.std)+') in: '+self.data_path+'.')
				else:
					if self.animation_analyzer:
						if self.background_free:
							self.text_trainingfolder.SetLabel('Animations w/o background, pattern images w/o bodyparts in: '+self.data_path+'.')
						else:
							self.text_trainingfolder.SetLabel('Animations w/ background, pattern images w/o bodyparts in: '+self.data_path+'.')
					else:
						self.text_trainingfolder.SetLabel('Pattern images w/o bodyparts in: '+self.data_path+'.')

		if self.data_path is not None:
			self._update_count_display(self.data_path)


	def specify_augmentation(self,event):

		if self.training_onfly is True:

			wx.MessageBox('You chose to train a Categorizer using the examples that are already augmented. No need to augment them again.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.MessageDialog(self,'Export the augmented training examples? If yes, the Categorizer\nwill be trained on the exported, augmented examples to\navoid memory overload, but the training will be slower.','Export training examples?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog2.ShowModal()==wx.ID_OK:
					self.out_folder=dialog2.GetPath()
				dialog2.Destroy()
			else:
				self.out_folder=None
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Use default augmentation methods?\nSelect "Yes" if dont know how to specify.','Use default augmentation?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				selected='default'
				self.aug_methods=['default']
			else:
				aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening','random dimming','random shearing','random rescaling','random deletion']
				selected=''
				dialog1=wx.MultiChoiceDialog(self,message='Data augmentation methods',caption='Augmentation methods',choices=aug_methods)
				if dialog1.ShowModal()==wx.ID_OK:
					self.aug_methods=[aug_methods[i] for i in dialog1.GetSelections()]
					for i in dialog1.GetSelections():
						if selected=='':
							selected=selected+aug_methods[i]
						else:
							selected=selected+','+aug_methods[i]
				else:
					self.aug_methods=[]
				dialog1.Destroy()
			if len(self.aug_methods)<=0:
				selected='none'
			else:
				if self.aug_methods[0]=='default':
					self.aug_methods=['random rotation','horizontal flipping','vertical flipping','random brightening','random dimming']
			dialog.Destroy()

			dialog=wx.MessageDialog(self,'Also augment the validation data?\nSelect "No" if dont know what it is.','Augment validation data?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				self.augvalid=True
				if self.out_folder is None:
					self.text_augmentation.SetLabel('Augment both training and validation examples with: '+selected+'.')
				else:
					self.text_augmentation.SetLabel('Augment and export both training and validation examples with: '+selected+'.')
			else:
				self.augvalid=False
				if self.out_folder is None:
					self.text_augmentation.SetLabel('Augment training examples with: '+selected+'.')
				else:
					self.text_augmentation.SetLabel('Augment and export training examples with: '+selected+'.')
			dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.MessageDialog(self,'Export the training reports?','Export training reports?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog2=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog2.ShowModal()==wx.ID_OK:
				self.out_path=dialog2.GetPath()
				self.text_report.SetLabel('Training reports will be in: '+self.out_path+'.')
			dialog2.Destroy()
		else:
			self.out_path=None
		dialog.Destroy()


	def train_categorizer(self,event):

		if self.data_path is None:

			wx.MessageBox('No path to training examples.','Error',wx.OK|wx.ICON_ERROR)

		else:

			dialog=wx.MessageDialog(self,'Export the trained Categorizer to a folder?','Export trained Categorizer?',wx.YES_NO|wx.ICON_QUESTION)
			if dialog.ShowModal()==wx.ID_YES:
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.model_path=dialog1.GetPath()
				dialog1.Destroy()
			dialog.Destroy()

			do_nothing=False

			stop=False
			while stop is False:
				dialog=wx.TextEntryDialog(self,'Enter a name for the Categorizer to train','Categorizer name')
				if dialog.ShowModal()==wx.ID_OK:
					if dialog.GetValue()!='':
						self.path_to_categorizer=os.path.join(self.model_path,dialog.GetValue())
						if not os.path.isdir(self.path_to_categorizer):
							os.makedirs(self.path_to_categorizer)
							stop=True
						else:
							wx.MessageBox('The name already exists.','Error',wx.OK|wx.ICON_ERROR)
				else:
					do_nothing=True
					stop=True
				dialog.Destroy()

			if do_nothing is False:
				CA=Categorizers()
				if self.animation_analyzer is False:
					if self.behavior_mode>=3:
						self.length=0
						self.std=0
						self.include_bodyparts=False
					else:
						self.channel=3
					if self.training_onfly:
						CA.train_pattern_recognizer_onfly(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim=self.dim_conv,channel=self.channel,time_step=self.length,level=self.level_conv,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance)
					else:
						CA.train_pattern_recognizer(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim=self.dim_conv,channel=self.channel,time_step=self.length,level=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,out_folder=self.out_folder)
				else:
					if self.behavior_mode==2:
						self.channel=3
					if self.training_onfly:
						CA.train_combnet_onfly(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,level_tconv=self.level_tconv,level_conv=self.level_conv,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,color_costar=self.color_costar)
					else:
						CA.train_combnet(self.data_path,self.path_to_categorizer,out_path=self.out_path,dim_tconv=self.dim_tconv,dim_conv=self.dim_conv,channel=self.channel,time_step=self.length,level_tconv=self.level_tconv,level_conv=self.level_conv,aug_methods=self.aug_methods,augvalid=self.augvalid,include_bodyparts=self.include_bodyparts,std=self.std,background_free=self.background_free,black_background=self.black_background,behavior_mode=self.behavior_mode,social_distance=self.social_distance,color_costar=self.color_costar,out_folder=self.out_folder)



class PanelLv2_TestCategorizers(wx.Panel):

	'''
	The 'Test Categorizers' functional unit
	'''

	def __init__(self, parent):

		super().__init__(parent)
		self.notebook = parent

		self.config = config.get_config('models')

		self.file_path=None
		self.model_path = self.config['models']
		logger.debug('%s: %r', 'self.model_path', self.model_path)
		self.path_to_categorizer=None
		self.out_path=None

		self.display_window()


	def display_window(self):

		panel = self
		boxsizer=wx.BoxSizer(wx.VERTICAL)
		add_info_button(self, boxsizer, INFO_COLOUR_S3)

		module_selectcategorizer=wx.BoxSizer(wx.HORIZONTAL)
		button_selectcategorizer=wx.Button(panel,label='Select a Categorizer\nto test',size=(300,40))
		button_selectcategorizer.Bind(wx.EVT_BUTTON,self.select_categorizer)
		wx.Button.SetToolTip(button_selectcategorizer,'The behavioral names in ground-truth dataset should exactly match those in the selected Categorizer.')
		self.text_selectcategorizer=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_selectcategorizer.Add(button_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_selectcategorizer.Add(self.text_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,10,0)
		boxsizer.Add(module_selectcategorizer,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_inputexamples=wx.BoxSizer(wx.HORIZONTAL)
		button_inputexamples=wx.Button(panel,label='Select the folder that stores\nthe ground-truth behavior examples',size=(300,40))
		button_inputexamples.Bind(wx.EVT_BUTTON,self.select_filepath)
		wx.Button.SetToolTip(button_inputexamples,'This folder should contain all the sorted behavior examples. Each subfolder in this folder should contain behavior examples of a behavior type. The names of the subfolders are the ground-truth behavior names, which should match those in the selected Categorizer.')
		self.text_inputexamples=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_inputexamples.Add(button_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_inputexamples.Add(self.text_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_inputexamples,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_report=wx.BoxSizer(wx.HORIZONTAL)
		button_report=wx.Button(panel,label='Select a folder to\nexport testing reports',size=(300,40))
		button_report.Bind(wx.EVT_BUTTON,self.select_reportpath)
		wx.Button.SetToolTip(button_report,'This is the folder to store the reports of testing results and metrics. It is optional.')
		self.text_report=wx.StaticText(panel,label='None.',style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_END)
		module_report.Add(button_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		module_report.Add(self.text_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(module_report,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		module_interactive=wx.BoxSizer(wx.HORIZONTAL)
		self.checkbox_open_interactive=wx.CheckBox(
			panel,
			label='Show interactive results after testing',
		)
		self.checkbox_open_interactive.SetValue(True)
		module_interactive.Add(self.checkbox_open_interactive,0,wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL,10)
		boxsizer.Add(module_interactive,0,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
		boxsizer.Add(0,5,0)

		testanddelete=wx.BoxSizer(wx.HORIZONTAL)
		button_test=wx.Button(panel,label='Test the Categorizer',size=(300,40))
		button_test.Bind(wx.EVT_BUTTON,self.test_categorizer)
		wx.Button.SetToolTip(button_test,'Test the selected Categorizer on the ground-truth behavior examples')
		button_delete=wx.Button(panel,label='Delete a Categorizer',size=(300,40))
		button_delete.Bind(wx.EVT_BUTTON,self.remove_categorizer)
		wx.Button.SetToolTip(button_delete,'Permanently delete a Categorizer. The deletion CANNOT be restored.')
		testanddelete.Add(button_test,0,wx.RIGHT,50)
		testanddelete.Add(button_delete,0,wx.LEFT,50)
		boxsizer.Add(0,5,0)
		boxsizer.Add(testanddelete,0,wx.RIGHT|wx.ALIGN_RIGHT,90)
		boxsizer.Add(0,10,0)

		panel.SetSizer(boxsizer)

		self.Centre()
		self.Show(True)


	def select_categorizer(self,event):

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()
		if 'Choose a new directory of the Categorizer' not in categorizers:
			categorizers.append('Choose a new directory of the Categorizer')

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to test',caption='Select a Categorizer',choices=categorizers)

		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			if categorizer=='Choose a new directory of the Categorizer':
				dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
				if dialog1.ShowModal()==wx.ID_OK:
					self.path_to_categorizer=dialog1.GetPath()
					self.text_selectcategorizer.SetLabel('The path to the Categorizer to test is: '+self.path_to_categorizer+'.')
				else:
					self.path_to_categorizer=None
				dialog1.Destroy()
			else:
				self.path_to_categorizer=os.path.join(self.model_path,categorizer)
				self.text_selectcategorizer.SetLabel('Categorizer to test: '+categorizer+'.')

		dialog.Destroy()


	def select_filepath(self,event):

		dialog=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
		if dialog.ShowModal()==wx.ID_OK:
			self.file_path=dialog.GetPath()
			self.text_inputexamples.SetLabel('Path to ground-truth behavior examples: '+self.file_path+'.')
		dialog.Destroy()


	def select_reportpath(self,event):

		dialog=wx.MessageDialog(self,'Export the testing reports?','Export testing reports?',wx.YES_NO|wx.ICON_QUESTION)
		if dialog.ShowModal()==wx.ID_YES:
			dialog1=wx.DirDialog(self,'Select a directory','',style=wx.DD_DEFAULT_STYLE)
			if dialog1.ShowModal()==wx.ID_OK:
				self.out_path=dialog1.GetPath()
				self.text_report.SetLabel('Testing reports will be in: '+self.out_path+'.')
			dialog1.Destroy()
		else:
			self.out_path=None
		dialog.Destroy()


	def test_categorizer(self,event):

		if self.file_path is None or self.path_to_categorizer is None:
			wx.MessageBox('No Categorizer selected / path to ground-truth behavior examples.','Error',wx.OK|wx.ICON_ERROR)
		else:
			CA=Categorizers()
			try:
				report, cm, example_map, embedding_map = CA.test_categorizer(self.file_path,self.path_to_categorizer,result_path=self.out_path)
			except CategorizerClassMismatchError as e:
				message = (
					'Behavior folder names must exactly match the Categorizer classes.\n\n'
					f'Unrecognized behavior folders: {e.unrecognized_folders}\n'
					f'Model classes absent from the fixture: {e.missing_classes}'
				)
				wx.MessageBox(message, 'Class name mismatch', wx.OK|wx.ICON_ERROR)
				return

			classnames = [k for k in report.keys() if k not in ['accuracy', 'macro avg', 'weighted avg']]

			if self.checkbox_open_interactive.GetValue():
				dialog = AutomatedDiagnosticsDialog(
					self,
					report,
					cm,
					classnames,
					example_map,
					embedding_map,
					source_dataset_root=self.file_path,
				)
				dialog.ShowModal()
				dialog.Destroy()


	def remove_categorizer(self,event):

		categorizers=[i for i in os.listdir(self.model_path) if os.path.isdir(os.path.join(self.model_path,i))]
		if '__pycache__' in categorizers:
			categorizers.remove('__pycache__')
		if '__init__' in categorizers:
			categorizers.remove('__init__')
		if '__init__.py' in categorizers:
			categorizers.remove('__init__.py')
		categorizers.sort()

		dialog=wx.SingleChoiceDialog(self,message='Select a Categorizer to delete',caption='Delete a Categorizer',choices=categorizers)
		if dialog.ShowModal()==wx.ID_OK:
			categorizer=dialog.GetStringSelection()
			dialog1=wx.MessageDialog(self,'Delete '+str(categorizer)+'?','CANNOT be restored!',wx.YES_NO|wx.ICON_QUESTION)
			if dialog1.ShowModal()==wx.ID_YES:
				shutil.rmtree(os.path.join(self.model_path,categorizer))
			dialog1.Destroy()
		dialog.Destroy()

class AutomatedDiagnosticsDialog(wx.Dialog):
	def __init__(self, parent, report, cm, classnames, example_map, embedding_map, source_dataset_root=None):
		super().__init__(parent, title="Automated Diagnostics - Test Results", size=(1000, 800), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)

		self.report = report
		self.cm = cm
		self.classnames = classnames
		self.example_map = example_map
		self.embedding_map = embedding_map
		self.source_dataset_root = source_dataset_root

		self.cm_normalized = self.calculate_normalized_cm(cm)
		self.is_normalized = False

		self.init_ui()

		self.Maximize(True)

	def calculate_normalized_cm(self, cm):
		norm_cm = []
		for row in cm:
			row_sum = sum(row)
			if row_sum > 0:
				norm_cm.append([round((val / row_sum) * 100, 1) for val in row])
			else:
				norm_cm.append([0.0 for _ in row])
		return norm_cm

	def init_ui(self):
		sizer = wx.BoxSizer(wx.VERTICAL)
		font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

		header_sizer = wx.BoxSizer(wx.HORIZONTAL)
		cm_label = wx.StaticText(self, label="Confusion Matrix:")
		cm_label.SetFont(font)
		header_sizer.Add(cm_label, 1, wx.ALIGN_CENTER_VERTICAL)

		self.toggle_btn = wx.ToggleButton(self, label="Show Normalized (%)")
		self.toggle_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_cm)
		header_sizer.Add(self.toggle_btn, 0, wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 10)

		self.cm_grid = wx.grid.Grid(self)
		self.cm_grid.CreateGrid(len(self.classnames), len(self.classnames))

		for i, name in enumerate(self.classnames):
			self.cm_grid.SetRowLabelValue(i, name)
			self.cm_grid.SetColLabelValue(i, name)

		self.cm_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_cell_click)

		self.cm_grid.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
		self.cm_grid.SetColLabelSize(wx.grid.GRID_AUTOSIZE)

		self.cm_grid.DisableDragRowSize()
		self.cm_grid.DisableDragColSize()

		self.update_grid_data()
		sizer.Add(self.cm_grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		bottom_dashboard_sizer = wx.BoxSizer(wx.HORIZONTAL)

		nlp_sizer = wx.BoxSizer(wx.VERTICAL)

		self.synopsis_label = wx.StaticText(self, label="Analyzing model performance...")
		self.synopsis_label.SetFont(font)
		nlp_sizer.Add(self.synopsis_label, 0, wx.BOTTOM | wx.ALL, 5)

		btn_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
		(
			label_overview,
			label_major,
			label_minor,
			label_successes,
			label_triage,
		) = DIAGNOSTIC_BUTTON_LABELS
		self.btn_help = wx.Button(self, label=label_overview)
		self.btn_major = wx.Button(self, label=label_major)
		self.btn_minor = wx.Button(self, label=label_minor)
		self.btn_successes = wx.Button(self, label=label_successes)

		self.btn_help.Bind(wx.EVT_BUTTON, self.show_help_view)
		self.btn_major.Bind(wx.EVT_BUTTON, self.show_major_confusions_view)
		self.btn_minor.Bind(wx.EVT_BUTTON, self.show_minor_confusions_view)
		self.btn_successes.Bind(wx.EVT_BUTTON, self.show_successes_view)

		btn_row_sizer.Add(self.btn_help, 0, wx.RIGHT, 5)
		btn_row_sizer.Add(self.btn_major, 0, wx.RIGHT, 5)
		btn_row_sizer.Add(self.btn_minor, 0, wx.RIGHT, 5)
		btn_row_sizer.Add(self.btn_successes, 0, 0, 0)

		self.btn_triage = wx.Button(self, label=label_triage)
		self.btn_triage.Bind(wx.EVT_BUTTON, self.on_build_triage)
		self.btn_triage.SetForegroundColour(wx.Colour(255, 203, 5))
		btn_row_sizer.Add(self.btn_triage, 0, wx.LEFT, 15)

		nlp_sizer.Add(btn_row_sizer, 0, wx.BOTTOM | wx.LEFT, 5)

		sort_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sort_label = wx.StaticText(self, label="Rank Insights By: ")
		sort_sizer.Add(self.sort_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

		self.sort_dropdown = wx.Choice(self, choices=["Instances", "Proportion"])
		self.sort_dropdown.SetSelection(0)
		self.sort_dropdown.Bind(wx.EVT_CHOICE, self.on_sort_changed)
		sort_sizer.Add(self.sort_dropdown, 0, wx.ALIGN_CENTER_VERTICAL)

		nlp_sizer.Add(sort_sizer, 0, wx.BOTTOM | wx.LEFT, 5)


		self.nlp_html = wx.html.HtmlWindow(self, style=wx.html.HW_SCROLLBAR_AUTO | wx.BORDER_NONE)
		self.nlp_html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.on_insight_link_clicked)

		nlp_sizer.Add(self.nlp_html, 1, wx.EXPAND | wx.ALL, 5)
		bottom_dashboard_sizer.Add(nlp_sizer, 1, wx.EXPAND | wx.RIGHT, 10)

		table_sizer = wx.BoxSizer(wx.VERTICAL)

		table_header_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.table_label = wx.StaticText(self, label="Highlight behaviors below 0.60: ")
		self.table_label.SetFont(font)
		self.metric_choice = wx.Choice(self, choices=["F1-score", "Precision", "Recall"])
		self.metric_choice.SetSelection(0)
		self.metric_choice.Bind(wx.EVT_CHOICE, self.on_metric_change)

		table_header_sizer.Add(self.table_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		table_header_sizer.Add(self.metric_choice, 0, wx.ALIGN_CENTER_VERTICAL)
		table_sizer.Add(table_header_sizer, 0, wx.BOTTOM, 5)

		self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, "Behavior", width=120)
		self.list_ctrl.InsertColumn(1, "Precision", width=80)
		self.list_ctrl.InsertColumn(2, "Recall", width=80)
		self.list_ctrl.InsertColumn(3, "F1", width=80)
		self.list_ctrl.InsertColumn(4, "Support", width=80)
		self.update_table_data()

		table_sizer.Add(self.list_ctrl, 1, wx.EXPAND)
		bottom_dashboard_sizer.Add(table_sizer, 1, wx.EXPAND | wx.LEFT, 10)

		sizer.Add(bottom_dashboard_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
		close_btn.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL))
		btn_sizer.Add(close_btn, 0, wx.ALL, 10)
		sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT)

		self.analyze_confusion_data()
		self.show_help_view(None)

		self.SetSizer(sizer)
		self.Layout()

	def on_build_triage(self, event):
		"""Gathers all confusions and launches the Triage Builder."""
		all_confusions = []

		for count, i, j, prop in self.nlp_major:
			item = f"{self.classnames[i]} -> {self.classnames[j]} ({count} errors)"
			if item not in all_confusions:
				all_confusions.append(item)

		for mc in self.nlp_minor:
			for err_count, pred_class in mc['top_confusions']:
				item = f"{mc['class']} -> {pred_class} ({err_count} errors)"
				if item not in all_confusions:
					all_confusions.append(item)

		if not all_confusions:
			wx.MessageBox("No confusions detected to triage!", "All Clear", wx.OK | wx.ICON_INFORMATION)
			return

		dialog = TriageBuilderDialog(
			self,
			all_confusions,
			self.example_map,
			self.report,
			self.cm,
			self.classnames,
			self.embedding_map,
			source_dataset_root=self.source_dataset_root,
		)
		dialog.ShowModal()
		dialog.Destroy()

	def on_sort_changed(self, event):
		"""Re-sorts the NLP data and refreshes the views when the dropdown changes."""
		self.analyze_confusion_data()

		if getattr(self, 'current_view', 'major') == 'minor':
			self.show_minor_confusions_view(None)
		else:
			self.show_major_confusions_view(None)

	def update_grid_data(self):
		cm_rows = len(self.cm)
		cm_cols = len(self.cm[0]) if cm_rows > 0 else 0
		data_to_use = self.cm_normalized if self.is_normalized else self.cm

		for i in range(len(self.classnames)):
			row_sum = sum(self.cm[i]) if i < cm_rows else 0

			for j in range(len(self.classnames)):
				if i < cm_rows and j < cm_cols:
					val = f"{data_to_use[i][j]}%" if self.is_normalized else str(data_to_use[i][j])

					if i != j and self.cm[i][j] > 0:
						err_pct = self.cm[i][j] / row_sum if row_sum > 0 else 0
						intensity = min(1.0, err_pct / 0.5)
						r_val = int(40 + (215 * intensity))
						bg_color = wx.Colour(r_val, 0, 0)
					elif i == j and row_sum > 0:
						accuracy = self.cm[i][j] / row_sum if row_sum > 0 else 0
						bg_color = wx.Colour(*cm_correct_cell_rgb(accuracy))
					else:
						bg_color = wx.Colour(30, 30, 30)
				else:
					val = "0.0%" if self.is_normalized else "0"
					bg_color = wx.Colour(30, 30, 30)

				self.cm_grid.SetCellValue(i, j, val)
				self.cm_grid.SetReadOnly(i, j, True)
				self.cm_grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
				self.cm_grid.SetCellBackgroundColour(i, j, bg_color)
				self.cm_grid.SetCellTextColour(i, j, wx.Colour(255, 255, 255))

		self.refresh_cm_column_widths()
		self.cm_grid.ForceRefresh()

	def refresh_cm_column_widths(self):
		"""Size columns from current labels/values, with a padded floor for ``100.0%``."""
		grid = self.cm_grid
		grid.AutoSizeColumns(False)
		font = grid.GetDefaultCellFont()
		text_w, _h, _d, _el = grid.GetFullTextExtent('100.0%', font)
		# Modest horizontal padding so centered percentages are not clipped.
		min_width = text_w + 16
		for col in range(grid.GetNumberCols()):
			if grid.GetColSize(col) < min_width:
				grid.SetColSize(col, min_width)

	def on_toggle_cm(self, event):
		self.is_normalized = self.toggle_btn.GetValue()
		if self.is_normalized:
			self.toggle_btn.SetLabel("Show Raw Counts")
		else:
			self.toggle_btn.SetLabel("Show Normalized (%)")

		self.update_grid_data()

	def on_insight_link_clicked(self, event):
		"""Highlights the specific grid cell or row when a user clicks the diagnostic text."""
		href = event.GetLinkInfo().GetHref()

		self.update_grid_data()

		if href.startswith('cell:'):
			coords = href.replace('cell:', '').split(',')
			row, col = int(coords[0]), int(coords[1])
			self.cm_grid.SetCellBackgroundColour(row, col, wx.Colour(255, 203, 5))
			self.cm_grid.SetCellTextColour(row, col, wx.Colour(0, 0, 0))
			self.cm_grid.MakeCellVisible(row, col)

		elif href.startswith('row:'):
			row = int(href.replace('row:', ''))
			self.cm_grid.MakeCellVisible(row, row)

			self.cm_grid.SetCellBackgroundColour(row, row, wx.Colour(0, 255, 255))
			self.cm_grid.SetCellTextColour(row, row, wx.Colour(0, 0, 0))

			cm_rows = len(self.cm)
			confusions = []
			for j in range(cm_rows):
				if row != j and self.cm[row][j] > 0:
					confusions.append((self.cm[row][j], j))

			confusions.sort(reverse=True, key=lambda x: x[0])
			for err_val, col in confusions[:3]:
				self.cm_grid.SetCellBackgroundColour(row, col, wx.Colour(255, 203, 5))
				self.cm_grid.SetCellTextColour(row, col, wx.Colour(0, 0, 0))

		self.cm_grid.ForceRefresh()
		self.cm_grid.ClearSelection()

	def analyze_confusion_data(self):
		"""Runs once to pre-calculate errors and successes using proportional math."""
		cm_rows = len(self.cm)
		self.nlp_major = []
		self.nlp_minor = []
		self.nlp_success = []
		self.nlp_meaningless = []

		self.nlp_meaningless = collect_insufficient_support_entries(self.classnames, self.report)
		low_support_classes = {entry['class'] for entry in self.nlp_meaningless}

		for i in range(cm_rows):
			true_class = self.classnames[i]
			metrics = self.report.get(true_class, {})
			support = float(metrics.get('support', 0))
			f1_score = float(metrics.get('f1-score', 0.0))

			if true_class in low_support_classes:
				continue

			if f1_score >= 0.85:
				self.nlp_success.append({
					'index': i,
					'class': true_class,
					'f1': f1_score,
					'support': support
				})
				continue

			found_major_confusion = False
			for j in range(cm_rows):
				if i != j and self.cm[i][j] > 0:
					error_count = self.cm[i][j]
					error_proportion = error_count / support

					if error_proportion >= 0.10:
						self.nlp_major.append((error_count, i, j, error_proportion))
						found_major_confusion = True

			if not found_major_confusion:
				row_errors = sum(self.cm[i]) - self.cm[i][i]
				pct_errors = (row_errors / support) * 100 if support > 0 else 0

				specific_confusions = []
				for j in range(cm_rows):
					if i != j and self.cm[i][j] > 0:
						specific_confusions.append((self.cm[i][j], self.classnames[j]))

				specific_confusions.sort(reverse=True, key=lambda x: x[0])
				top_specifics = specific_confusions[:3]

				self.nlp_minor.append({
					'index': i,
					'class': true_class,
					'support': support,
					'total_errors': row_errors,
					'pct_errors': pct_errors,
					'top_confusions': top_specifics
				})


		sort_mode = self.sort_dropdown.GetStringSelection()

		if sort_mode == "Proportion":
			self.nlp_major.sort(reverse=True, key=lambda x: x[3])
			self.nlp_minor.sort(reverse=True, key=lambda x: x['pct_errors'])
		else:
			self.nlp_major.sort(reverse=True, key=lambda x: x[0])
			self.nlp_minor.sort(reverse=True, key=lambda x: x['total_errors'])


		major_count = len(self.nlp_major)
		if major_count == 0:
			self.synopsis_label.SetLabel("No major confusion patterns were identified at the configured thresholds.")
		elif major_count > 5:
			self.synopsis_label.SetLabel(f"{major_count} major systematic confusions detected. Showing top 5 most severe.")
		else:
			self.synopsis_label.SetLabel(f"{major_count} major systematic confusions detected.")


	def show_major_confusions_view(self, event=None):
		self.current_view = 'major'
		self.sort_label.Show(True)
		self.sort_dropdown.Show(True)
		self.Layout()

		html = "<body bgcolor='#141414' text='#F8FAFC' style='font-family: Arial; font-size: 14px;'>"

		if not self.nlp_major:
			html += "<h3 style='color: #4ADE80;'>No major confusion patterns</h3><p>No major confusion patterns were identified at the configured thresholds.</p>"
		else:
			html += "<h3 style='color: #FFCB05; margin-bottom: 10px; margin-top: 0;'>Major Systematic Confusions:</h3>"
			for count, i, j, prop in self.nlp_major[:5]:
				true_class = self.classnames[i]
				pred_class = self.classnames[j]
				prop_pct = round(prop * 100, 1)

				link = f"<a href='cell:{i},{j}' style='color: #60A5FA; text-decoration: none;'><b>{true_class} &#8594; {pred_class}</b></a>"
				html += "<div style='background-color: #1e1e1e; border-left: 4px solid #FFCB05; padding: 10px; margin-bottom: 12px; border-radius: 4px;'>"

				error_txt = f"<span style='color: #F87171;'>{count} errors, {prop_pct}% of {true_class} data</span>"

				html += f"<p style='margin: 0;'>{link} ({error_txt})</p>"

				html += "</div>"

		html += "</body>"
		self.nlp_html.SetPage(html)

	def show_minor_confusions_view(self, event=None):
		self.current_view = 'minor'
		self.sort_label.Show(True)
		self.sort_dropdown.Show(True)
		self.Layout()

		html = "<body bgcolor='#141414' text='#F8FAFC' style='font-family: Arial; font-size: 14px;'>"


		if not self.nlp_minor:
			html += "<h3 style='color: #4ADE80;'>No dispersed minor confusion patterns</h3><p>No dispersed minor confusion patterns were identified at the configured thresholds.</p>"
		else:
			html += "<h3 style='color: #F87171; margin-bottom: 10px; margin-top: 0;'>Dispersed / Minor Confusions:</h3>"
			html += "<p style='margin-top: 0;'>The Categorizer struggles with these behaviors, but the mistakes are scattered across many categories rather than just one. This usually indicates weak feature extraction signals, highly variable subject movement, or simply, too few video examples.</p>"

			for mc in self.nlp_minor:
				c_idx = mc['index']
				c_name = mc['class']
				supp = int(mc['support'])
				errs = mc['total_errors']
				pct = round(mc['pct_errors'], 1)

				warning = " (fewer than 100 examples)" if supp < 100 else ""
				link = f"<a href='row:{c_idx}' style='color: #60A5FA; text-decoration: none;'><b>{c_name}</b></a>"

				html += f"<div style='background-color: #1e1e1e; border-left: 4px solid #F87171; padding: 10px; margin-bottom: 12px; border-radius: 4px;'>"
				html += f"<p style='margin: 0;'>{link}<span style='color: #F87171;'>{warning}</span><br>"
				html += f"<span style='color: #94a3b8; font-size: 13px;'>Support: <span style='color: #FFFFFF;'>{supp} examples</span> | Total Errors: <span style='color: #F87171;'>{errs} ({pct}% of data)</span></span></p>"

				if mc['top_confusions']:
					html += "<p style='margin-top: 8px; margin-bottom: 2px; font-size: 13px;'>Top confusions:</p><ul style='margin-top: 0; margin-bottom: 0; padding-left: 20px; font-size: 13px;'>"
					for err_count, pred_class in mc['top_confusions']:
						html += f"<li>To <b>{pred_class}</b>: {err_count} errors</li>"
					html += "</ul>"
				html += "</div>"

		html += "</body>"
		self.nlp_html.SetPage(html)

	def show_successes_view(self, event=None):
		self.current_view = 'successes'
		self.sort_label.Show(False)
		self.sort_dropdown.Show(False)
		self.Layout()

		html = "<body bgcolor='#141414' text='#F8FAFC' style='font-family: Arial; font-size: 14px;'>"

		if self.nlp_success:
			html += "<h3 style='color: #4ADE80; margin-top: 5px;'>Performing Reliably (F1 ≥ 85%):</h3>"
			html += "<p>On this test set, the following behaviors meet the F1 ≥ 85% threshold (advisory; not a guarantee of field performance):</p>"
			html += "<ul>"
			for sc in self.nlp_success:
				c_idx = sc['index']
				c_name = sc['class']
				f1_pct = round(sc['f1'] * 100, 1)
				supp = int(sc['support'])

				link = f"<a href='row:{c_idx}' style='color: #60A5FA; text-decoration: none;'><b>{c_name}</b></a>"
				html += f"<li style='margin-bottom: 6px;'>{link} <span style='color: #4ADE80;'>({f1_pct}% F1)</span> <span style='color: #FFFFFF; font-size: 12px;'>[{supp} examples]</span></li>"
			html += "</ul>"
		else:
			html += "<h3 style='color: #FFCB05; margin-top: 5px;'>F1 threshold not met</h3>"
			html += "<p>No behaviors reached the F1 ≥ 85% threshold on this test set.</p>"
			html += "<p>Review Major and Minor Confusions for advisory patterns.</p>"

		if self.nlp_meaningless:
			html += "<h3 style='color: #94a3b8; margin-top: 15px;'>Too few examples for automated analysis</h3>"
			html += "<p style='margin-top: 0;'>These classes remain listed. Observed support is below the minimum required for automated major/minor interpretation. They are omitted from automated major/minor ranking only.</p>"
			html += "<ul style='color: #94a3b8;'>"
			for mc in self.nlp_meaningless:
				html += (
					f"<li>{mc['class']}: {mc['support']} examples; "
					f"at least {mc['min_support']} required</li>"
				)
			html += "</ul>"

		html += "</body>"
		self.nlp_html.SetPage(html)

	def show_help_view(self, event=None):
		"""Generates the HTML for the layman's explanation."""
		self.current_view = 'help'
		self.sort_label.Show(False)
		self.sort_dropdown.Show(False)
		self.Layout()

		html = """
		<body bgcolor='#141414' text='#F8FAFC' style='font-family: Arial; font-size: 14px;'>
			<h3 style='color: #60A5FA; margin-top: 5px;'>Overview</h3>
			<p>A <b>Confusion Matrix</b> is a table that shows where the Categorizer gets confused on this test set.</p>
				<p><b>Rows (Left):</b> What the subject was <i>actually</i> doing (Ground Truth).</p>
				<p><b>Columns (Top):</b> What the Categorizer <i>guessed</i> the subject was doing (Prediction).</p>
			<p>If you look at the diagonal line going from top-left to bottom-right, those are the <b>correct guesses</b>. Any numbers sitting outside that diagonal line represent mistakes.</p>
			<p>You can click on any cell in the matrix to view the video examples of where the Categorizer either correctly or incorrectly guessed the behavior.</p>
			<p>Diagnostic summaries are <b>advisory</b> and are based on the configured thresholds and this test set only.</p>
		</body>
		"""
		self.nlp_html.SetPage(html)

	def on_metric_change(self, event):
		self.update_table_data()

	def update_table_data(self):
		self.list_ctrl.DeleteAllItems()

		selection = self.metric_choice.GetStringSelection()
		metric_key = 'f1-score'
		if selection == "Precision":
			metric_key = 'precision'
		elif selection == "Recall":
			metric_key = 'recall'

		index = 0
		for name in self.classnames:
			if name in self.report and isinstance(self.report[name], dict):
				metrics = self.report[name]
				self.list_ctrl.InsertItem(index, name)

				precision = float(metrics.get('precision', 0.0))
				recall = float(metrics.get('recall', 0.0))
				f1 = float(metrics.get('f1-score', 0.0))
				support = float(metrics.get('support', 0.0))

				self.list_ctrl.SetItem(index, 1, f"{precision:.2f}")
				self.list_ctrl.SetItem(index, 2, f"{recall:.2f}")
				self.list_ctrl.SetItem(index, 3, f"{f1:.2f}")
				self.list_ctrl.SetItem(index, 4, str(int(support)))

				val_to_check = float(metrics.get(metric_key, 0.0))
				if val_to_check < 0.60:
					self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(150, 0, 0))
				else:
					self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(30, 30, 30))

				self.list_ctrl.SetItemTextColour(index, wx.Colour(255, 255, 255))
				index += 1

	def generate_diagnostic_insights_html(self, top_n=3, support_threshold=50):
		cm_rows = len(self.cm)
		errors = []
		perfect_classes = []

		for i in range(cm_rows):
			true_class = self.classnames[i]
			support_true = self.report.get(true_class, {}).get('support', 0)

			if support_true == 0:
				continue

			row_errors = sum(self.cm[i]) - self.cm[i][i]
			if row_errors == 0:
				perfect_classes.append(true_class)

			for j in range(cm_rows):
				if i != j and self.cm[i][j] > 0:
					errors.append((self.cm[i][j], i, j))

		errors.sort(reverse=True, key=lambda x: x[0])

		html = "<body bgcolor='#141414' text='#F8FAFC' style='font-family: Arial; font-size: 14px;'>"

		if not errors:
			html += "<h3 style='color: #4ADE80;'>No major confusion patterns</h3><p>No major confusion patterns were identified at the configured thresholds.</p>"
		else:
			html += "<h3 style='color: #FFCB05; margin-bottom: 10px; margin-top: 0;'>Here is where the Categorizer is struggling:</h3>"

			for count, i, j in errors[:top_n]:
				true_class = self.classnames[i]
				pred_class = self.classnames[j]
				support_true = self.report.get(true_class, {}).get('support', 0)
				support_pred = self.report.get(pred_class, {}).get('support', 0)

				link = f"<a href='cell:{i},{j}' style='color: #60A5FA; text-decoration: none;'><b>{true_class} &#8594; {pred_class}</b></a>"

				html += "<div style='background-color: #1e1e1e; border-left: 4px solid #FFCB05; padding: 10px; margin-bottom: 12px; border-radius: 4px;'>"

				if support_true >= support_threshold and support_pred >= support_threshold:
					html += f"<p style='margin: 0;'>{link} ({count} errors)<br><br><span style='color: #94a3b8;'><b>Possible pattern (advisory):</b> Both behaviors have relatively robust support on this test set. Because the Categorizer is still confusing them, they might be visually similar. Consider reviewing whether labels overlap.</span></p>"
				else:
					lowest_class = true_class if support_true < support_pred else pred_class
					html += f"<p style='margin: 0;'>{link} ({count} errors)<br><br><span style='color: #94a3b8;'><b>Possible pattern (advisory):</b> Support for <i>{lowest_class}</i> is limited on this test set. Adding more examples may help, but this is not a definitive diagnosis.</span></p>"

				html += "</div>"

		if perfect_classes:
			html += "<br><h3 style='color: #4ADE80; margin-bottom: 5px;'>What's working perfectly:</h3>"
			html += "<p style='margin-top: 0;'>Zero confusions predicting: <b>" + ", ".join(perfect_classes) + "</b></p>"

		html += "</body>"
		return html

	def on_cell_click(self, event):
		row = event.GetRow()
		col = event.GetCol()

		self.cm_grid.ClearSelection()

		if row == -1 or col == -1:
			return

		if row < len(self.classnames) and col < len(self.classnames):
			true_class = self.classnames[row]
			pred_class = self.classnames[col]

			key = (true_class, pred_class)
			examples = self.example_map.get(key, [])

			if examples:
				viewer = ExampleViewerDialog(self, true_class, pred_class, examples)
				viewer.ShowModal()
				viewer.Destroy()
			else:
				wx.MessageBox(f"No examples found for True: '{true_class}', Predicted: '{pred_class}'", "No Data", wx.OK | wx.ICON_INFORMATION)


class ExampleViewerDialog(wx.Dialog):
	def __init__(self, parent, true_class, pred_class, examples):
		title = f"Reviewing Examples: True '{true_class}' -> Predicted '{pred_class}'"
		super().__init__(parent, title=title, size=(600, 400), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

		self.examples = examples
		self.init_ui()

	def init_ui(self):
		sizer = wx.BoxSizer(wx.VERTICAL)

		info_label = wx.StaticText(self, label=f"Found {len(self.examples)} example(s). Double-click a file to open it:")
		sizer.Add(info_label, 0, wx.ALL, 10)

		self.list_box = wx.ListBox(self, choices=self.examples, style=wx.LB_SINGLE | wx.LB_HSCROLL)
		self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_double_click)
		sizer.Add(self.list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
		close_btn.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL))
		btn_sizer.Add(close_btn, 0, wx.ALL, 10)
		sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT)

		self.SetSizer(sizer)
		self.Layout()

	def on_double_click(self, event):
		selection = self.list_box.GetSelection()
		if selection != wx.NOT_FOUND:
			filepath = self.examples[selection]

			try:
				if sys.platform == "win32":
					os.startfile(filepath)
				elif sys.platform == "darwin":
					subprocess.call(["open", filepath])
				else:
					subprocess.call(["xdg-open", filepath])
			except Exception as e:
				wx.MessageBox(f"Failed to open file:\n{e}", "Error", wx.OK | wx.ICON_ERROR)


class TriageBuilderDialog(wx.Dialog):
	NOMINAL_CLIENT_SIZE = (960, 720)
	OPS_HELP_HEIGHT_NOMINAL = 150
	OPS_HELP_HEIGHT_FLOOR = 100

	def __init__(self, parent, confusions_list, example_map, report, cm, classnames, embedding_map, source_dataset_root=None):
		super().__init__(
			parent,
			title="Triage Action Plan Builder",
			style=wx.DEFAULT_DIALOG_STYLE,
		)
		self.confusions_list = confusions_list
		self.example_map = example_map
		self.embedding_map = embedding_map

		self.report = report
		self.cm = cm
		self.classnames = classnames
		self.source_dataset_root = source_dataset_root

		self.init_ui()
		self._apply_fitted_fixed_size()

	def _work_area_size(self):
		"""Return usable display client area for fitting this dialog."""
		try:
			index = wx.Display.GetFromWindow(self)
			if index == wx.NOT_FOUND and self.GetParent() is not None:
				index = wx.Display.GetFromWindow(self.GetParent())
			if index == wx.NOT_FOUND:
				index = 0
			area = wx.Display(index).GetClientArea()
			if area.width > 0 and area.height > 0:
				return area.width, area.height
		except Exception:
			pass
		parent = self.GetParent()
		if parent is not None:
			top = parent.GetTopLevelParent()
			if top is not None:
				size = top.GetClientSize()
				if size.width > 0 and size.height > 0:
					return size.width, size.height
		return 1024, 768

	def _apply_fitted_fixed_size(self):
		"""Fit nominal client size to the active display and lock resizing."""
		nominal_w, nominal_h = self.NOMINAL_CLIENT_SIZE
		work_w, work_h = self._work_area_size()
		fitted_w, fitted_h = fit_dialog_client_size(nominal_w, nominal_h, work_w, work_h)
		# Shrink ops-help pane on short fitted heights while keeping a usable floor.
		shrink = max(0, nominal_h - fitted_h)
		ops_h = max(self.OPS_HELP_HEIGHT_FLOOR, self.OPS_HELP_HEIGHT_NOMINAL - min(shrink, 50))
		if hasattr(self, 'ops_help_html'):
			self.ops_help_html.SetMinSize((-1, ops_h))
			self.ops_help_html.SetSize((-1, ops_h))
		if hasattr(self, 'intro_lbl'):
			self.intro_lbl.Wrap(max(200, fitted_w - 40))
		self.SetClientSize(fitted_w, fitted_h)
		# Lock outer size after client size accounts for title-bar chrome.
		outer = self.GetSize()
		self.SetMinSize(outer)
		self.SetMaxSize(outer)
		if self.GetParent() is not None:
			self.CentreOnParent()
		else:
			self.Centre()
		self.Layout()

	def get_centroid(self, file_list):
		"""Calculates the mathematical centroid of a cluster of videos and returns the most representative file."""
		if not file_list:
			return None
		if len(file_list) == 1:
			return file_list[0]

		import numpy as np

		embs = [self.embedding_map[f] for f in file_list]

		mean_emb = np.mean(embs, axis=0)
		mean_norm = np.linalg.norm(mean_emb)
		if mean_norm == 0:
			return file_list[0]

		best_sim = -2.0
		centroid_file = file_list[0]

		for f, emb in zip(file_list, embs):
			emb_norm = np.linalg.norm(emb)
			if emb_norm == 0: continue

			sim = np.dot(emb, mean_emb) / (emb_norm * mean_norm)
			if sim > best_sim:
				best_sim = sim
				centroid_file = f

		return centroid_file

	def init_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		title_lbl = wx.StaticText(self, label="Assign confusions to a root-cause hypothesis to generate your action plan.")
		title_font = wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		title_lbl.SetFont(title_font)
		title_lbl.SetForegroundColour(wx.Colour(255, 203, 5))
		main_sizer.Add(title_lbl, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 15)

		intro_lbl = wx.StaticText(
			self,
			label=(
				"Triage Plan: You are reviewing confusion patterns from this test set. "
				"Assign each selected pattern to a possible follow-up hypothesis (H1, H2, or H3). "
				"These hypotheses are advisory—they are not diagnoses or required actions. "
				"LabGym prepares the plan from your selections; scientific decisions remain yours."
			),
		)
		self.intro_lbl = intro_lbl
		intro_lbl.Wrap(900)
		main_sizer.Add(intro_lbl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		self.ops_help_html = wx.html.HtmlWindow(
			self,
			size=(-1, self.OPS_HELP_HEIGHT_NOMINAL),
			style=wx.html.HW_SCROLLBAR_AUTO | wx.BORDER_SIMPLE,
		)
		self.ops_help_html.SetPage(
			"""
			<body bgcolor='#1e1e1e' text='#F8FAFC' style='font-family: Arial; font-size: 12px;'>
			<p><b>H1 — Merge hypothesis (advisory):</b> Confusion may indicate overlapping behavior definitions.
			On Finish, LabGym creates a Triage Plan package and, on the <b>revised sorted test examples only</b>,
			moves all examples from the true-class folder into the predicted-class folder and removes the emptied folder.
			The original selected test fixture is unchanged. If scientifically accepted, apply the same class-definition
			decision to separate training data; do not copy evaluation examples into training; train and reevaluate a new Categorizer.</p>
			<p><b>H2 — New-class / extract hypothesis (advisory):</b> H2 is advisory only. LabGym does not create the new class or move examples.
			In <code>revised_sorted_test_examples</code>, manually review and organize examples if you accept this hypothesis.
			Do not copy evaluation examples into training. Reproduce accepted taxonomy changes in separate training data,
			then train and reevaluate a new Categorizer.</p>
			<p><b>H3 — Needs-more-data hypothesis (advisory):</b> Confusion may indicate insufficient variety of training examples.
			On Finish, LabGym copies up to three reference example pairs into
			<code>LabGym_Diagnostics/H3_Variance_References</code> in the package.
			These references illustrate variance in the evaluation set. Collect or prepare additional independent training examples;
			do not move these evaluation references into training. Train and reevaluate a new Categorizer afterward.
			The source dataset is unchanged.</p>
			</body>
			"""
		)
		main_sizer.Add(self.ops_help_html, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		columns_sizer = wx.BoxSizer(wx.HORIZONTAL)

		left_sizer = wx.BoxSizer(wx.VERTICAL)
		lbl_unassigned = wx.StaticText(self, label="Unassigned Confusions:")
		lbl_unassigned.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		left_sizer.Add(lbl_unassigned, 0, wx.BOTTOM, 8)

		self.lb_unassigned = wx.ListBox(self, choices=self.confusions_list, style=wx.LB_EXTENDED)
		self.lb_unassigned.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		left_sizer.Add(self.lb_unassigned, 1, wx.EXPAND)
		columns_sizer.Add(left_sizer, 4, wx.EXPAND | wx.ALL, 10)

		mid_sizer = wx.BoxSizer(wx.VERTICAL)
		mid_sizer.AddStretchSpacer()

		btn_h1 = wx.Button(self, label="Assign to H1 (Merge)", size=(190, 40))
		btn_h1.Bind(wx.EVT_BUTTON, lambda evt: self.move_items(self.lb_unassigned, self.lb_h1))
		mid_sizer.Add(btn_h1, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 15)

		btn_h2 = wx.Button(self, label="Assign to H2 (Extract)", size=(190, 40))
		btn_h2.Bind(wx.EVT_BUTTON, self.on_move_h2)
		mid_sizer.Add(btn_h2, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 15)

		btn_h3 = wx.Button(self, label="Assign to H3 (Add Data)", size=(190, 40))
		btn_h3.Bind(wx.EVT_BUTTON, lambda evt: self.move_items(self.lb_unassigned, self.lb_h3))
		mid_sizer.Add(btn_h3, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 15)

		btn_return = wx.Button(self, label="Return Selected", size=(190, 40))
		btn_return.Bind(wx.EVT_BUTTON, self.on_return_items)
		mid_sizer.Add(btn_return, 0, wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, 40)

		mid_sizer.AddStretchSpacer()
		columns_sizer.Add(mid_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

		right_sizer = wx.BoxSizer(wx.VERTICAL)

		lbl_h1 = wx.StaticText(self, label="H1: Merge on clone:")
		lbl_h1.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		lbl_h1.SetForegroundColour(wx.Colour(100, 200, 100))
		right_sizer.Add(lbl_h1, 0, wx.BOTTOM, 4)
		self.lb_h1 = wx.ListBox(self, style=wx.LB_EXTENDED)
		right_sizer.Add(self.lb_h1, 1, wx.EXPAND | wx.BOTTOM, 10)

		lbl_h2 = wx.StaticText(self, label="H2: New class (manual):")
		lbl_h2.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		lbl_h2.SetForegroundColour(wx.Colour(100, 150, 255))
		right_sizer.Add(lbl_h2, 0, wx.BOTTOM, 4)
		self.lb_h2 = wx.ListBox(self, style=wx.LB_EXTENDED)
		right_sizer.Add(self.lb_h2, 1, wx.EXPAND | wx.BOTTOM, 10)

		lbl_h3 = wx.StaticText(self, label="H3: Needs more data:")
		lbl_h3.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		lbl_h3.SetForegroundColour(wx.Colour(255, 150, 100))
		right_sizer.Add(lbl_h3, 0, wx.BOTTOM, 4)
		self.lb_h3 = wx.ListBox(self, style=wx.LB_EXTENDED)
		right_sizer.Add(self.lb_h3, 1, wx.EXPAND)

		columns_sizer.Add(right_sizer, 5, wx.EXPAND | wx.ALL, 10)

		main_sizer.Add(columns_sizer, 1, wx.EXPAND)

		footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_finish = wx.Button(self, label="Finish and Generate Report", size=(220, 40))
		btn_finish.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		btn_finish.SetForegroundColour(wx.Colour(100, 200, 100))
		btn_finish.Bind(wx.EVT_BUTTON, self.on_finish)
		footer_sizer.Add(btn_finish, 0, wx.ALL, 10)

		btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel", size=(100, 40))
		footer_sizer.Add(btn_cancel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

		main_sizer.Add(footer_sizer, 0, wx.ALIGN_RIGHT)
		self.SetSizer(main_sizer)
		self.Layout()

	def move_items(self, source_lb, target_lb, append_text=""):
		selections = source_lb.GetSelections()
		if not selections:
			return

		for idx in reversed(selections):
			item_text = source_lb.GetString(idx)
			target_lb.Append(f"{item_text} {append_text}")
			source_lb.Delete(idx)

	def on_move_h2(self, event):
		if not self.lb_unassigned.GetSelections():
			return

		dlg = wx.TextEntryDialog(self, "What is the name of this new emergent behavior?", "Define Emergent Class")
		if dlg.ShowModal() == wx.ID_OK:
			new_name = dlg.GetValue().strip()
			if new_name:
				self.move_items(self.lb_unassigned, self.lb_h2, f"[NEW: {new_name}]")
		dlg.Destroy()

	def on_return_items(self, event):
		"""Returns selected items from any right-side bucket back to unassigned."""
		for lb in [self.lb_h1, self.lb_h2, self.lb_h3]:
			selections = lb.GetSelections()
			for idx in reversed(selections):
				text = lb.GetString(idx)
				if "[NEW:" in text:
					text = text.split(" [NEW:")[0]
				self.lb_unassigned.Append(text)
				lb.Delete(idx)

	def _resolve_source_dataset_root(self):
		"""Return absolute normalized source root, or (None, error_message)."""
		explicit = self.source_dataset_root
		if explicit:
			root = os.path.abspath(os.path.normpath(explicit))
			if not os.path.isdir(root):
				return None, f"Selected source dataset root is not a directory:\n{root}"
			return root, None

		sample_file = None
		for files in self.example_map.values():
			if files:
				sample_file = files[0]
				break
		if not sample_file:
			return None, "Could not locate source files for the Triage Plan package."
		root = os.path.abspath(os.path.normpath(os.path.dirname(os.path.dirname(sample_file))))
		if not os.path.isdir(root):
			return None, f"Inferred source dataset root is not a directory:\n{root}"
		return root, None

	def _collect_h1_pairs(self):
		pairs = []
		for i in range(self.lb_h1.GetCount()):
			text = self.lb_h1.GetString(i)
			source_class = text.split(" -> ")[0].strip()
			target_class = text.split(" -> ")[1].split(" (")[0].strip()
			pairs.append((source_class, target_class))
		return pairs

	def _open_folder_safely(self, folder):
		try:
			if sys.platform == "win32":
				os.startfile(folder)
			elif sys.platform == "darwin":
				subprocess.call(["open", folder])
			else:
				subprocess.call(["xdg-open", folder])
			return True, None
		except Exception as e:
			return False, str(e)

	def on_finish(self, event):
		if not triage_assignment_counts(self.lb_h1.GetCount(), self.lb_h2.GetCount(), self.lb_h3.GetCount()):
			wx.MessageBox(
				"Assign at least one confusion to H1, H2, or H3 before generating a triage plan.",
				"Empty triage plan",
				wx.OK | wx.ICON_ERROR,
			)
			return

		ok_pdf, pdf_err = reportlab_importable()
		if not ok_pdf:
			wx.MessageBox(
				f"ReportLab is required to generate PDFs ({pdf_err}). Please install reportlab before generating a triage plan.",
				"Missing Dependency",
				wx.OK | wx.ICON_ERROR,
			)
			return

		source_root, source_err = self._resolve_source_dataset_root()
		if source_root is None:
			wx.MessageBox(source_err, "Source Error", wx.OK | wx.ICON_ERROR)
			return

		parent_dir = os.path.dirname(source_root)
		suggested_name = next_versioned_triage_package_name(parent_dir, os.path.basename(source_root))

		dlg = wx.TextEntryDialog(
			self,
			"Enter a name for the Triage Plan package folder:",
			"Triage Plan Package",
			suggested_name,
		)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		package_name = dlg.GetValue()
		dlg.Destroy()

		ok_name, name_err = validate_triage_package_name(package_name)
		if not ok_name:
			wx.MessageBox(name_err, "Invalid Package Name", wx.OK | wx.ICON_ERROR)
			return

		package_dir = os.path.join(parent_dir, package_name)
		if os.path.exists(package_dir):
			wx.MessageBox(
				f"A folder named \"{package_name}\" already exists.\n\n{package_dir}",
				"Package Exists",
				wx.OK | wx.ICON_ERROR,
			)
			return

		h1_pairs = self._collect_h1_pairs()
		if h1_pairs:
			collisions, missing = collect_h1_filename_collisions(source_root, h1_pairs)
			if missing:
				lines = []
				for kind, cls in missing:
					label = "true-class (source)" if kind == "source" else "predicted-class (target)"
					lines.append(f"- Missing {label} folder: {cls}")
				wx.MessageBox(
					"H1 class folders are missing from the selected source dataset. "
					"No package was created.\n\n" + "\n".join(lines),
					"H1 class folder missing",
					wx.OK | wx.ICON_ERROR,
				)
				return
			if collisions:
				lines = []
				for rec in collisions:
					true_c, pred_c = rec['pair']
					names = ", ".join(rec['filenames'])
					lines.append(f"{true_c} → {pred_c}: {names}")
				wx.MessageBox(
					"The H1 merge would place entries with the same name in one behavior folder. "
					"No package was created. Resolve the listed filename collisions, then generate "
					"the Triage Plan again.\n\n" + "\n".join(lines),
					"H1 filename collision",
					wx.OK | wx.ICON_ERROR,
				)
				return

		revised_dir = os.path.join(package_dir, "revised_sorted_test_examples")
		diagnostics_dir = os.path.join(package_dir, "LabGym_Diagnostics")
		busy = False
		package_created = False

		try:
			total_size = sum(
				os.path.getsize(os.path.join(dirpath, f))
				for dirpath, _, filenames in os.walk(source_root)
				for f in filenames
			)
			total_size_mb = total_size / (1024 * 1024)

			total, used, free = shutil.disk_usage(parent_dir)
			if total_size > free:
				wx.MessageBox(
					f"Not enough disk space to create the Triage Plan package.\n"
					f"Required: {total_size_mb:.2f} MB\nAvailable: {free / (1024*1024):.2f} MB",
					"Disk Space Error",
					wx.OK | wx.ICON_ERROR,
				)
				return

			wx.BeginBusyCursor()
			busy = True

			os.makedirs(package_dir)
			package_created = True
			shutil.copytree(source_root, revised_dir)
			os.makedirs(diagnostics_dir)

			for source_class, target_class in h1_pairs:
				revised_source_dir = os.path.join(revised_dir, source_class)
				revised_target_dir = os.path.join(revised_dir, target_class)
				if not os.path.isdir(revised_source_dir) or not os.path.isdir(revised_target_dir):
					raise OSError(
						f"H1 class folder missing after copy: {source_class} -> {target_class}"
					)
				for filename in os.listdir(revised_source_dir):
					shutil.move(
						os.path.join(revised_source_dir, filename),
						os.path.join(revised_target_dir, filename),
					)
				shutil.rmtree(revised_source_dir)

			pdf_path = next_versioned_pdf_path(diagnostics_dir)

			if self.lb_h3.GetCount() > 0:
				import random
				h3_ref_dir = os.path.join(diagnostics_dir, "H3_Variance_References")
				os.makedirs(h3_ref_dir, exist_ok=True)

				for i in range(self.lb_h3.GetCount()):
					text = self.lb_h3.GetString(i)
					source_class = text.split(" -> ")[0].strip()
					target_class = text.split(" -> ")[1].split(" (")[0].strip()

					key = (source_class, target_class)
					examples = self.example_map.get(key, [])

					if examples:
						samples = random.sample(examples, min(3, len(examples)))
						for idx, avi_path in enumerate(samples):
							if os.path.exists(avi_path):
								safe_source = source_class.replace(" ", "_")
								safe_target = target_class.replace(" ", "_")

								new_avi_name = f"{safe_source}_to_{safe_target}_sample{idx+1}.avi"
								shutil.copy2(avi_path, os.path.join(h3_ref_dir, new_avi_name))

								jpg_path = avi_path.replace(".avi", ".jpg")
								if os.path.exists(jpg_path):
									new_jpg_name = f"{safe_source}_to_{safe_target}_sample{idx+1}.jpg"
									shutil.copy2(jpg_path, os.path.join(h3_ref_dir, new_jpg_name))

			pdf_ok, pdf_fail_reason = self.generate_pdf_report(pdf_path, package_name)

			if busy:
				wx.EndBusyCursor()
				busy = False

			if not pdf_ok or not os.path.isfile(pdf_path):
				detail = pdf_fail_reason or "PDF was not created."
				wx.MessageBox(
					"The Triage Plan package exists, but the expected PDF was not created.\n\n"
					f"Package:\n{package_dir}\n\n"
					f"Revised sorted test examples:\n{revised_dir}\n\n"
					f"Failure detail:\n{detail}",
					"Partial triage outcome",
					wx.OK | wx.ICON_WARNING,
				)
				return

			wx.MessageBox(
				"Triage Plan package created.\n\n"
				f"Package:\n{package_dir}\n\n"
				f"Revised sorted test examples (select this folder in LabGym):\n{revised_dir}\n\n"
				f"PDF:\n{pdf_path}\n\n"
				"The original source fixture was not modified.",
				"Triage Complete",
				wx.OK | wx.ICON_INFORMATION,
			)

			self.EndModal(wx.ID_OK)

			opened, open_err = self._open_folder_safely(package_dir)
			if not opened:
				wx.MessageBox(
					"The Triage Plan package was created, but LabGym could not open the package folder.\n\n"
					f"Package:\n{package_dir}\n\n"
					f"Detail:\n{open_err}",
					"Folder Open Failed",
					wx.OK | wx.ICON_WARNING,
				)

		except PermissionError:
			if busy:
				wx.EndBusyCursor()
			msg = "LabGym does not have permission to write to this directory. Check your folder permissions."
			if package_created:
				msg += f"\n\nA partial Triage Plan package may remain at:\n{package_dir}"
			wx.MessageBox(msg, "Permission Error", wx.OK | wx.ICON_ERROR)
		except Exception as e:
			if busy:
				wx.EndBusyCursor()
			msg = f"An OS error occurred during triage execution:\n{e}"
			if package_created:
				msg += f"\n\nA partial Triage Plan package may remain at:\n{package_dir}"
			wx.MessageBox(msg, "System Error", wx.OK | wx.ICON_ERROR)

	def generate_pdf_report(self, filepath, dataset_name):
		"""Generate triage PDF. Returns (ok, error_message_or_None)."""
		try:
			from reportlab.lib.pagesizes import letter
			from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
			from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
			from reportlab.lib.colors import HexColor, Color
			from reportlab.lib import colors
			from reportlab.lib.units import inch
			import datetime
			import os
		except ImportError as e:
			return False, f"ReportLab is required to generate PDFs ({e})."

		try:
			doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
			styles = getSampleStyleSheet()

			title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=HexColor("#00274C"), spaceAfter=16)
			h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=HexColor("#333333"), spaceBefore=16, spaceAfter=8)
			body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=HexColor("#1A1A1A"))
			action_style = ParagraphStyle('Action', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=HexColor("#D82C20"), spaceAfter=12)
			item_style = ParagraphStyle('Item', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, leftIndent=20, spaceAfter=6)
			caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=HexColor("#666666"), leftIndent=20, spaceBefore=4, spaceAfter=16)

			Story = []

			accuracy = self.report.get('accuracy', 0.0)
			macro_f1 = self.report.get('macro avg', {}).get('f1-score', 0.0)

			Story.append(Paragraph(f"LabGym Triage Action Plan", title_style))
			Story.append(Paragraph(f"<b>Package:</b> {dataset_name}", body_style))
			Story.append(Paragraph(f"<b>Date Generated:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
			Story.append(Paragraph(f"<b>Overall Accuracy:</b> {accuracy*100:.1f}% | <b>Macro F1-Score:</b> {macro_f1*100:.1f}%", body_style))
			Story.append(Spacer(1, 15))

			Story.append(Paragraph("Package layout and remediation", h2_style))
			Story.append(Paragraph(
				"<b>revised_sorted_test_examples</b> contains the revised sorted test examples, cloned from the selected evaluation fixture. "
				"<b>LabGym_Diagnostics</b> contains this report and optional H3 references. The original source fixture is unchanged. "
				"This package is a Triage Plan result, not a complete repair or training workflow. For later LabGym sorted-example steps, "
				"select <b>revised_sorted_test_examples</b>, not the package root. Reproduce accepted remediation in separate training data, "
				"do not copy evaluation examples into training, and train and reevaluate a new Categorizer.",
				body_style,
			))
			Story.append(Spacer(1, 15))

			Story.append(Paragraph("Confusion Matrix Overview", h2_style))
			Story.append(Paragraph("Cells highlighted with a thick gold border indicate confusions that were addressed in this triage session.", caption_style))

			headers = ["True \\ Pred"] + [str(idx + 1) for idx in range(len(self.classnames))]
			cm_data = [headers]

			for i in range(len(self.classnames)):
				row_data = [f"{i + 1}. {self.classnames[i]}"]
				for j in range(len(self.classnames)):
					row_data.append(str(self.cm[i][j]))
				cm_data.append(row_data)

			t_style = TableStyle([
				('BACKGROUND', (0,0), (-1,0), HexColor("#00274C")),
				('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
				('ALIGN', (0,0), (-1,-1), 'CENTER'),
				('ALIGN', (0,1), (0,-1), 'LEFT'),
				('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
				('FONTSIZE', (0,0), (-1,-1), 7),
				('BOTTOMPADDING', (0,0), (-1,0), 6),
				('BACKGROUND', (0,1), (0,-1), HexColor("#f0f0f0")),
				('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
				('GRID', (0,0), (-1,-1), 0.5, colors.grey),
			])

			for i in range(len(self.classnames)):
				row_sum = sum(self.cm[i])
				for j in range(len(self.classnames)):
					val = self.cm[i][j]
					if val > 0:
						if i == j:
							intensity = min(1.0, val / row_sum) if row_sum > 0 else 0
							bg_color = Color(0, 0.8, 0, alpha=0.1 + (0.4 * intensity))
						else:
							pct = val / row_sum if row_sum > 0 else 0
							intensity = min(1.0, pct / 0.5)
							bg_color = Color(0.9, 0, 0, alpha=0.1 + (0.5 * intensity))
						t_style.add('BACKGROUND', (j+1, i+1), (j+1, i+1), bg_color)

			addressed_pairs = []
			for lb in [self.lb_h1, self.lb_h2, self.lb_h3]:
				for idx in range(lb.GetCount()):
					item_text = lb.GetString(idx)
					clean_text = item_text.split(" [NEW:")[0]
					source_class = clean_text.split(" -> ")[0].strip()
					target_class = clean_text.split(" -> ")[1].split(" (")[0].strip()
					addressed_pairs.append((source_class, target_class))

			for src, tgt in addressed_pairs:
				if src in self.classnames and tgt in self.classnames:
					i = self.classnames.index(src)
					j = self.classnames.index(tgt)
					t_style.add('BOX', (j+1, i+1), (j+1, i+1), 2, HexColor("#FFCB05"))

			first_col_width = 1.5 * inch
			remaining_width = 5.0 * inch
			data_col_width = remaining_width / max(len(self.classnames), 1)

			col_widths = [first_col_width] + [data_col_width] * len(self.classnames)

			cm_table = Table(cm_data, colWidths=col_widths)
			cm_table.setStyle(t_style)
			Story.append(cm_table)
			Story.append(Spacer(1, 15))

			Story.append(Paragraph("Hypothesis 1: Merge on revised sorted test examples (advisory)", h2_style))
			Story.append(Paragraph(
				"Confusion may indicate overlapping behavior definitions. H1 is an advisory merge hypothesis. "
				"The merge is applied only to the revised sorted test examples: LabGym moves all examples from each listed "
				"true-class folder into the predicted-class folder and removes the emptied folder. The original selected test fixture remains unchanged. "
				"If scientifically accepted, apply the same class-definition decision to the separate training dataset. "
				"Do not copy evaluation examples into training. Train and reevaluate a new Categorizer.",
				body_style,
			))
			Story.append(Spacer(1, 5))

			if self.lb_h1.GetCount() == 0:
				Story.append(Paragraph("<i>None selected.</i>", item_style))
			for i in range(self.lb_h1.GetCount()):
				Story.append(Paragraph(f"• {self.lb_h1.GetString(i)}", item_style))
			Story.append(Spacer(1, 10))

			Story.append(Paragraph("Hypothesis 2: New class / extract (advisory)", h2_style))
			Story.append(Paragraph(
				"H2 is advisory only. LabGym does not create the new class or move examples. "
				"In revised_sorted_test_examples, manually review and organize examples if you accept this hypothesis. "
				"Do not copy evaluation examples into training. Reproduce accepted taxonomy changes in separate training data, "
				"then train and reevaluate a new Categorizer.",
				body_style,
			))
			Story.append(Paragraph(
				"USER ACTION: In revised_sorted_test_examples, manually review and organize examples if you accept this hypothesis. "
				"Reproduce accepted changes in separate training data; do not copy evaluation examples into training.",
				action_style,
			))

			if self.lb_h2.GetCount() == 0:
				Story.append(Paragraph("<i>None selected.</i>", item_style))
			else:
				for i in range(self.lb_h2.GetCount()):
					item_text = self.lb_h2.GetString(i)
					Story.append(Paragraph(f"• {item_text}", item_style))

					source_class = item_text.split(" -> ")[0].strip()
					target_class = item_text.split(" -> ")[1].split(" (")[0].strip()
					key = (source_class, target_class)
					examples = self.example_map.get(key, [])

					if examples:
						avi_path = self.get_centroid(examples)
						jpg_path = avi_path.replace(".avi", ".jpg")
						file_name = os.path.basename(avi_path)

						if os.path.exists(jpg_path):
							img = Image(jpg_path)
							img.drawWidth = 2 * inch
							img.drawHeight = 2 * inch
							Story.append(img)
						Story.append(Paragraph(f"Reference file: {file_name}", caption_style))

			Story.append(Paragraph("Hypothesis 3: Needs more data (advisory)", h2_style))
			Story.append(Paragraph(
				"Confusion may indicate insufficient variety of training examples. LabGym copies up to three reference example pairs into "
				"LabGym_Diagnostics/H3_Variance_References and does not merge classes. "
				"These references illustrate variance in the evaluation set. Collect or prepare additional independent training examples; "
				"do not move these evaluation references into training. Train and reevaluate a new Categorizer afterward. "
				"The source dataset is unchanged.",
				body_style,
			))
			Story.append(Paragraph(
				"USER ACTION (optional): Collect or prepare additional independent training examples; do not move these evaluation references into training.",
				action_style,
			))

			if self.lb_h3.GetCount() == 0:
				Story.append(Paragraph("<i>None selected.</i>", item_style))
			else:
				export_dir = os.path.dirname(filepath)
				h3_ref_dir = os.path.join(export_dir, "H3_Variance_References")

				for i in range(self.lb_h3.GetCount()):
					item_text = self.lb_h3.GetString(i)
					Story.append(Paragraph(f"• {item_text}", item_style))

					source_class = item_text.split(" -> ")[0].strip()
					target_class = item_text.split(" -> ")[1].split(" (")[0].strip()
					safe_source = source_class.replace(" ", "_")
					safe_target = target_class.replace(" ", "_")

					for idx in range(3):
						jpg_name = f"{safe_source}_to_{safe_target}_sample{idx+1}.jpg"
						avi_name = f"{safe_source}_to_{safe_target}_sample{idx+1}.avi"
						jpg_path = os.path.join(h3_ref_dir, jpg_name)

						if os.path.exists(jpg_path):
							img = Image(jpg_path)
							img.drawWidth = 2 * inch
							img.drawHeight = 2 * inch
							Story.append(img)
							Story.append(Paragraph(f"Reference file: H3_Variance_References/{avi_name}", caption_style))

			Story.append(Paragraph("Baseline References (True Positives)", h2_style))
			Story.append(Paragraph("Below are representative examples of correctly classified behaviors on this test set. Use these as a visual baseline for what the model currently treats as an example of the class.", body_style))

			has_baselines = False
			for i in range(len(self.classnames)):
				cls_name = self.classnames[i]
				if self.cm[i][i] > 0:
					key = (cls_name, cls_name)
					examples = self.example_map.get(key, [])

					if examples:
						has_baselines = True
						Story.append(Paragraph(f"• {cls_name}", item_style))

						avi_path = self.get_centroid(examples)
						jpg_path = avi_path.replace(".avi", ".jpg")
						file_name = os.path.basename(avi_path)

						if os.path.exists(jpg_path):
							img = Image(jpg_path)
							img.drawWidth = 2 * inch
							img.drawHeight = 2 * inch
							Story.append(img)
						Story.append(Paragraph(f"Reference file: {file_name}", caption_style))

			if not has_baselines:
				Story.append(Paragraph("<i>No correct classifications available to generate baselines.</i>", item_style))

			doc.build(Story)
			if not os.path.isfile(filepath):
				return False, "PDF build completed but the output file was not found."
			return True, None
		except Exception as e:
			return False, str(e)
