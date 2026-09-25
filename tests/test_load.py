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
may not require updating.
"""

import glob
import importlib
import logging
import os
from pathlib import Path
import pprint
import sys
import textwrap

import LabGym

submodules = []


def test_cwd():
	"""
	Test that cwd is the LabGym package's parent dir (the repo dir).

	This condition isn't strictly necessary for these unit tests, but a
	a failed assert would indicate either (a) noxfile.py was moved (the
	starting cwd is same as location of noxfile.py), or, (b) some other
	unit test in the session did a chdir (possibly by exercising code
	that used an os.chdir instead of a contextlib.chdir).

	As currently organized, the repo dir contains noxfile.py and the
	Labgym package dir.

	"In github running nox on a PR commit, what is my cwd? Is it my
	repo dir?"

	Google AI Overview responds:
		When running Nox in a GitHub Actions workflow on a PR commit, your
		current working directory (cwd) is the root of your repository on
		the runner's machine.

		The working directory in GitHub Actions is a specific path on the
		runner, typically /home/runner/work/<repo>/<repo> on Linux, which is
		where the actions/checkout action places your code by default.

		Nox itself also has a default behavior: it automatically changes its
		working directory to the directory containing the noxfile.py script
		before running any sessions.

		Therefore:
		*   The initial working directory for the GitHub Actions step
			running Nox is the repository root.
		*   Once the nox command executes, the working directory for the
			individual Nox sessions (the Python functions in your
			noxfile.py) will be the directory where the noxfile.py is
			located.

		This means you can generally rely on paths within your Nox sessions
		being relative to the noxfile.py location, which is usually at the
		root of your repository (unless you've specified a different
		location in your workflow or using the --noxfile argument).
	"""
	assert os.path.isfile('noxfile.py')
	assert os.getcwd() == os.path.dirname(os.path.dirname(LabGym.__file__))


def test_import_LabGym_package():
	"""Load LabGym.__init__.py and get a list of submodules."""

	# Prepare a list of all submodule py-files in LabGym dir, but not subdirs.
	pyfiles = glob.glob(os.path.join(os.path.dirname(LabGym.__file__), '*.py'))
	pyfiles.sort()  # result from glob.glob() isn't sorted
	submodules.extend([os.path.basename(f).removesuffix('.py')
		for f in pyfiles])

	# Remove __init__.py.  There's no need to challenge it, as it was
	# already loaded by the "import LabGym" statement at the beginning
	# of this in this test.  And furthermore, as it is already loaded,
	# importing it (again) would not reload it.  OTOH, if it wasn't
	# specifically removed here, there would be no harm done.
	submodules.remove('__init__')

	# Add subpackages?  This requires maintenance... find subdirs with
	# py-files and load them?  Loading the package doesn't necessarily
	# load all of the package's py-files... (that's why we are
	# attempting to load all of LabGym package's first-generation
	# py-files)
	submodules.extend(['detectron2', 'mywx', 'pkghash', 'selftest'])


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
		print(f"submodules: {textwrap.indent(pprint.pformat(submodules), '  ')}")

	while len(submodules) > 0:
		submodule = submodules[0]
		logging.info(f"importlib.import_module('LabGym.{submodule}')")
		importlib.import_module(f'LabGym.{submodule}')
		submodules.pop(0)

	logging.debug('%s:\n%s', 'Milepost 2, submodules',
		textwrap.indent(pprint.pformat(submodules), '  '))
