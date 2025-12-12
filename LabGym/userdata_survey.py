"""
Provide functions for flagging user data that is located internal to LabGym.

Public functions
	Specialized Functions
		survey
		assert_userdata_dirs_are_separate
		offer_to_mkdir_userdata_dirs
		advise_on_internal_userdata_dirs
		get_instructions
		warn_on_orphaned_userdata

	General-purpose Functions
		is_path_under(path1: str|Path, path2: str|Path) -> bool
		is_path_equivalent(path1: str|Path, path2: str|Path) -> bool
		resolve(path1: str|Path) -> str
		dict2str(arg: dict, hanging_indent: str=' '*16) -> str
		get_list_of_subdirs(parent_dir: str|Path) -> List[str]
		open_html_in_browser(html_content)

Public classes: None

Design issues
*   Why is the user-facing text using the term "folder" instead of "dir"
	or "directory"?
	As Gemini says,
		When authoring dialog text for display to the user, "folder" is
		generally the better terminology for a general audience using a
		graphical user interface (GUI), while "directory" is appropriate
		for technical users or command-line interfaces (CLI). The
		abbreviation "dir" should be avoided in user-facing text.

*   Why sometimes use a webbrowser instead of only dialog text?
	Because
	+   The user can't select and copy the wx.Dialog text into a
		clipboard (observed on MacOS).
	+   A wx.Dialog disappears when LabGym is quit.  By displaying
		instructions in a separate app, they can still be referenced
		after LabGym is quit, until the user dismisses them.
	+   Formatting... It's more efficient to write content in html
		instead of hand-formatting text for a wx.Dialog.
	There are other possible approaches... prepare the instructions in
	html, then use html2text library to get formatted text from the
	html, and display that in a wx.Dialog.

The path args for the functions in this module should be absolute
(full) paths, not relative (partial) paths.  That's the assumption
during development.  If that assumption is violated, are unintended
consequences possible?
Instead of answering that question, implement guards.
(1) Enforce with asserts?
		assert Path(arg).is_absolute()
(2) Or, enforce with asserts in the Specialized functions, but not the
	General-purpose functions?
(3) Or, guard by decorating selected functions, instead of individually
	adding the right mix of assert statements to function bodies.
For now, choosing (2).

The survey function has an early-exit capability, for demonstration
purposes.  If LabGym is started with
	--enable userdata_survey_exit
then survey will call sys.exit('Exiting early') instead of returning and
proceeding.

Design with paths as strings, or, paths as pathlib.Path objects?
Since the paths are configured as strings, assume the calls from outside
this module pass strings, and inside this module, developer is free to
use pathlib where convenient.
In other words, for public functions, support string path args, and
optionally, extend to support Path object args.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import webbrowser

# Related third party imports.
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
from LabGym import config
from LabGym import mywx


logger = logging.getLogger(__name__)


def is_path_under(path1: str|Path, path2: str|Path) -> bool:
	"""Return True if path2 is under path1."""

	p1 = Path(path1).resolve()
	p2 = Path(path2).resolve()
	return p1 in p2.parents


def is_path_equivalent(path1: str|Path, path2: str|Path) -> bool:
	"""Return True if path1 & path2 are equivalent."""

	# if they both exist, are they the same?
	if Path(path1).exists() and Path(path2).exists():
		return Path(path1).samefile(Path(path2))

	# if neither exists, are the strings of the resolved paths the same?
	if not Path(path1).exists() and not Path(path2).exists():
		return resolve(path1) == resolve(path2)

	# At this point, one exists and the other doesn't, therefore False
	return False


def resolve(path1: str|Path) -> str:
	"""Return a string representation of the resolved string or Path obj."""

	return str(Path(path1).resolve())


def dict2str(arg: dict, hanging_indent: str=' '*16) -> str:
	"""Return a string representation of the dict, with a hanging indent.

	Return '' if the dict is empty.

	Why the hanging indent?  So that it can be tuned to avoid fouling
	the left-alignment when used inside a multiline string that will be
	dedented.
	"""

	result = ('\n' + hanging_indent).join(
		[f'{key}: {value}' for key, value in arg.items()]
		)

	return result


def get_list_of_subdirs(parent_dir: str|Path) -> List[str]:
	"""Return a sorted list of strings of the names of the child dirs.

	... excluding __pycache__.
	If parent_dir is not an existing dir, then return an empty list.
	"""

	parent_path = Path(parent_dir)

	if parent_path.is_dir():
		result = [item.name for item in parent_path.iterdir()
			# if item.name not in ['__init__', '__init__.py', '__pycache__']
			if item.name not in ['__pycache__']
			and (parent_path / item).is_dir()]
	else:
		result = []

	result.sort()
	return result


def open_html_in_browser(html_content):
	"""
	Creates a temporary HTML file with the provided content and opens it
	in a new web browser window.
	"""
	# Use NamedTemporaryFile to ensure the file is eventually deleted by the OS
	with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
		f.write(html_content)
		file_path = f.name

	# Create a file URL for the browser
	url = 'file://' + os.path.abspath(file_path)

	# Open the URL in a new browser window (new=1) or a new tab (new=2)
	# The default is to try opening in a new window/tab if possible.
	webbrowser.open(url, new=1)

	# Note: The temporary file will not be automatically deleted
	# as long as the Python script is running. You might need to
	# manually delete it after the browser is closed or when your
	# application exits if you need immediate cleanup.


def assert_userdata_dirs_are_separate(
		detectors_dir: str, models_dir: str) -> None:
	"""Verify the separation of configuration's userdata dirs.

	If not separate, then display an error message, then sys.exit().

	Enforce an expectation that the detectors_dir and models_dir are
	separate, and do not have a "direct, lineal relationshop", where one
	is under the other.

	"""

	# Enforce the expectation that the path args are absolute (full).
	assert Path(detectors_dir).is_absolute()
	assert Path(models_dir).is_absolute()

	if (is_path_equivalent(detectors_dir, models_dir)
			or is_path_under(detectors_dir, models_dir)
			or is_path_under(models_dir, detectors_dir)):

		# fatal configuration error
		title = 'LabGym Configuration Error'
		msg = textwrap.dedent(f"""\
			LabGym Configuration Error
			The userdata folders must be separate.
			The detectors folder is specified by config or defaults as
				{str(detectors_dir)}
				which resolves to
				{str(resolve(detectors_dir))}
			The models folder is specified by config or defaults as
				{str(models_dir)}
				which resolves to
				{str(resolve(models_dir))}
			""")

		logger.error('%s', msg)

		# Show the error msg with an OK_Dialog.
		with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
			result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss

		sys.exit('Bad configuration')


def survey(
		labgym_dir: str,
		detectors_dir: str,
		models_dir: str,
		) -> None:
	"""Warn (and display guidance?) if userdata dirs need reorganization.

	The locations of detectors and models dirs are specified by the
	configuration, obtained from the configuration before calling this
	function, and passed into this function.

	1.  Verify the separation of configuration's userdata dirs.
		If not separate, then display an error message, then sys.exit().

	2.  Check for userdata dirs that are defined/configured as
		"external" to LabGym, but don't exist.  If any, then warn.

		This action could be expanded -- offer to attempt mkdir?

	3.  Check for userdata dirs that are defined/configured as
		"internal" to LabGym.  If any, then warn.

		This action could be expanded --
		3a. provide info and specific instructions to the user for
			resolution.
		3b. (or,) for each internal userdata dir (detectors, models),
			automatically
			+   mkdir new external dir
			+   update the config to point at new external dir
			+   for each subdir of internal dir
			+       copy subdir to new external dir
			+       back up existing original
			+       delete existing original
			then exit (don't continue with old config!)

	4.  For any userdata dirs configured as external to LabGym tree,
		if there is "orphaned" data, remaining in the "traditional"
		location (internal, within the LabGym tree), then warn.
	"""

	# Enforce the expectation that the path args are absolute (full).
	assert Path(labgym_dir).is_absolute()
	assert Path(detectors_dir).is_absolute()
	assert Path(models_dir).is_absolute()

	logger.debug('%s: %r', 'labgym_dir', labgym_dir)
	logger.debug('%s: %r', 'detectors_dir', detectors_dir)
	logger.debug('%s: %r', 'models_dir', models_dir)

	userdata_dirs = {
		'detectors': detectors_dir,
		'models': models_dir,
		}
	internal_userdata_dirs = {key: value for key, value in userdata_dirs.items()
		if is_path_under(labgym_dir, value)}
	external_userdata_dirs = {key: value for key, value in userdata_dirs.items()
		if not is_path_under(labgym_dir, value)}

	# Get all of the values needed from config.get_config().
	enable_userdata_survey_exit: bool = config.get_config(
		)['enable'].get('userdata_survey_exit', False)

	# 1.  Verify the separation of configuration's userdata dirs.
	#	  If not separate, then display an error message, then sys.exit().
	assert_userdata_dirs_are_separate(detectors_dir, models_dir)

	# 2.  Check for user data dirs that are defined/configured as
	#     "external", but don't exist.  If any, then warn.
	#     (this action could be expanded -- offer to attempt mkdir?)

	# old:
	#     offer_to_mkdir_userdata_dirs(labgym_dir, detectors_dir, models_dir)

	missing_userdata_dirs = [value for value in external_userdata_dirs.values()
		if not os.path.isdir(value)]

	if missing_userdata_dirs:
		title = 'LabGym Configuration Warning'
		msg = textwrap.dedent(f"""\
			External Userdata folders specified by config don't exist.
			missing_userdata_dirs: {missing_userdata_dirs!r}'
			""").strip()

		logger.warning('%s', msg)

		# Show the warning msg with an OK_Dialog.
		with mywx.OK_Dialog(None, title=title, msg=textwrap.fill(msg)) as dlg:
			result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss

	# 3.  If any userdata dirs are configured as located within the
	#     LabGym tree, then warn.
	#     (this could be enhanced -- provide info and specific instructions
	#     to the user for resolution.)

	if internal_userdata_dirs:
		title = 'LabGym Configuration Warning'
		msg = textwrap.dedent(f"""\
			Found internal Userdata folders specified by config.
			The use of internal Userdata folders is deprecated.
			internal_userdata_dirs: {internal_userdata_dirs!r}
			""").strip()

		logger.warning('%s', msg)

		# Show the warning msg with an OK_Dialog.
		with mywx.OK_Dialog(None, title=title, msg=textwrap.fill(msg)) as dlg:
			result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss

		# advise_on_internal_userdata_dirs(
		#     labgym_dir, detectors_dir, models_dir)

	# 4.  For any userdata dirs configured as external to LabGym tree,
	#     if there is "orphaned" data, remaining in the "traditional"
	#     location (internal, within the LabGym tree), then warn.

	orphans = []
	if external_userdata_dirs:
		if 'detectors' in external_userdata_dirs.keys():
			 # contents of LabGym/detectors are orphans
			 old = Path(labgym_dir) / 'detectors' # old userdata dir
			 orphans.extend([
				 str(old / subdir) for subdir in get_list_of_subdirs(old)])
		if 'models' in external_userdata_dirs.keys():
			 # contents of LabGym/modelsare orphans
			 old = Path(labgym_dir) / 'models' # old userdata dir
			 orphans.extend([
				 str(old / subdir) for subdir in get_list_of_subdirs(old)])

	if orphans:
		title = 'LabGym Configuration Warning'
		msg = textwrap.dedent(f"""\
			Found Userdata orphaned in old Userdata folders.
			orphans: {orphans!r}
			""").strip()

		logger.warning('%s', msg)

		# Show the warning msg with an OK_Dialog.
		with mywx.OK_Dialog(None, title=title, msg=textwrap.fill(msg)) as dlg:
			result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss

		# warn_on_orphaned_userdata(labgym_dir, detectors_dir, models_dir)

	# If flag is set, then exit early instead of return normally.
	# (this for feature development and demonstration)
	if enable_userdata_survey_exit:
		sys.exit(f'Exiting early.'
			f'  enable_userdata_survey_exit: {enable_userdata_survey_exit}')
