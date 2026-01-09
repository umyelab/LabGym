"""
Load each of the package's top-level py-files.

...namely, LabGym/*.py.
These tests will expose basic syntax errors that prevent import.

Some tests are specific to a set of py-files, possibly because they
require setup.

The final test, test_remainder(), imports each of the remaining top-
level py-files.
The strength of this catch-all final test is that if a new top-level
py-file is introduced, full coverage is preserved and this test-file
may still be suitable.
"""

import glob
import importlib
import logging
import os
from pathlib import Path
import pprint
import sys
import textwrap


submodules = []


def list_dir_and_first_children(directory_path):
	"""
	Lists the contents of a directory and the contents of its first-generation children.

	Args:
		directory_path (str or Path): The path to the directory to inspect.
	"""
	base_path = Path(directory_path)
	if not base_path.is_dir():
		print(f"Error: {directory_path} is not a valid directory.")
		return

	print(f"--- Contents of Directory: {base_path} ---")

	# List immediate contents of the base directory
	immediate_contents = list(base_path.iterdir())
	for item in immediate_contents:
		print(f"- {item.name} ({'Directory' if item.is_dir() else 'File'})")

	print(f"\n--- Contents of First-Generation Children ---")

	# Iterate through immediate contents and list their children if they are directories
	for item in immediate_contents:
		if item.is_dir():
			print(f"\n  --- Subdirectory: {item.name} ---")
			for sub_item in item.iterdir():
				print(f"  - {sub_item.name} ({'Directory' if sub_item.is_dir() else 'File'})")


def test_import_LabGym_package(capsys):
	"""Load LabGym.__init__.py and get a list of submodules."""
	import LabGym

	# ?!
	with capsys.disabled():
		print(f'os.getcwd(): {os.getcwd()}')
		print(f'LabGym.__file__: {LabGym.__file__!r}')
		print(f'os.path.dirname(LabGym.__file__): {os.path.dirname(LabGym.__file__)!r}')
		print(f'os.path.dirname(os.path.dirname(LabGym.__file__)): {os.path.dirname(os.path.dirname(LabGym.__file__))!r}')
	# is cwd not relevant for this test?
	# is cwd not repeatable for this test?

	# Confirm the assumption that under pytest, cwd is LabGym package's
	# parent dir (the repo dir).
	try:
		assert os.getcwd() == os.path.dirname(os.path.dirname(LabGym.__file__))
	except:
		# if I'm not in LabGymRepo, where am I?  LabGymRepo's parent dir?
		with capsys.disabled():
			list_dir_and_first_children(os.getcwd())


	# Prepare a list of all submodule py-files in LabGym dir, but not subdirs.
	pyfiles = glob.glob(os.path.join(os.path.dirname(LabGym.__file__), '*.py'))
	pyfiles.sort()  # result from glob.glob() isn't sorted
	submodules.extend([os.path.basename(f).removesuffix('.py')
		for f in pyfiles])
	# logging.debug('%s:\n%s', 'Milepost 0, submodules',
	#     textwrap.indent(pprint.pformat(submodules), '  '))

	# Remove __init__.py.  There's no need to challenge it, as it was
	# already loaded by the "import LabGym" statement at the beginning
	# of this in this test.
	submodules.remove('__init__')

	# Add subpackages?
	submodules.extend(['detectron2', 'mywx', 'pkghash', 'selftest'])

	with capsys.disabled():
		print(f"Milepost 0, submodules: {textwrap.indent(pprint.pformat(submodules), '  ')}")


def test_imports_with_sysargv_initialized(monkeypatch):
	"""Test that some module imports don't raise exceptions.

	These module imports must be tested with sys.argv initialized.
	"""
	# Arrange sys.argv.  Otherwise sys.argv contains pytest args, and
	# myargparse raises an exception.
	monkeypatch.setattr(sys, 'argv', ['dummy'])

	# Act
	logging.info('import LabGym.__main__')
	import LabGym.__main__
	submodules.remove('__main__')

	logging.info('import LabGym.myargparse')
	import LabGym.myargparse
	submodules.remove('myargparse')


def test_remainder(capsys):
	"""Test that imports for the remaining modules don't raise exceptions."""
	with capsys.disabled():
		print(f"Milepost 1, submodules: {textwrap.indent(pprint.pformat(submodules), '  ')}")

	while len(submodules) > 0:
		submodule = submodules[0]
		logging.info(f"importlib.import_module('LabGym.{submodule}')")
		importlib.import_module(f'LabGym.{submodule}')
		submodules.pop(0)

	logging.debug('%s:\n%s', 'Milepost 2, submodules',
		textwrap.indent(pprint.pformat(submodules), '  '))
