"""
Discovery: By default, pytest.main() will discover all tests in the current directory and subdirectories unless you specify a specific path or file.
Caching: Be aware that calling pytest.main() multiple times in the same process may not reflect code changes due to Python's import caching.
Exit Codes: The function returns standard pytest exit codes: 0 for all tests passed, 1 for failures, and 5 if no tests were found.
Advanced Reporting: To retrieve detailed results programmatically rather than just the exit code, you can pass a custom plugin object to the plugins argument of pytest.main().

See Also AI for "I want to add a feature to my python code that will, on demand, run a selftest using pytest.  Also, tell me more about using a custom plugin for advanced reporting."
"""

# Standard library imports.
import logging
import os
import sys
import textwrap

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP 8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__name__}')

# Related third party imports.
import pytest
import wx

# Local application/library specific imports.
from LabGym import mywx


def fmt(s):
	"""Format a multi-line string."""
	return textwrap.dedent(s).strip()


def run_selftests_help():
	"""Display Help to a wx.Dialog."""
	title = 'How to run LabGym selftests'
	msg = fmt(f"""
		In this version of LabGym, running selftests from a normal
		running LabGym process is not supported.

		The supported approach to running LabGym selftests is to select
		the alternate behavior via LabGym configuration.  Then LabGym
		runs the selftests, then exits instead of continuing as normal
		LabGym.

		For example,
		*   start the LabGym app from the command line with option
			--selftest specified.
				% LabGym --debug --selftest
		*   or, specify in the configfile, like this in a toml-file,
				selftest = true
			(Remember to revert, to return to normal LabGym behavior!)
		""")

	logger.info(msg)
	with mywx.OK_Cancel_Dialog(None, title=title, msg=msg) as dlg:
		result = dlg.ShowModal()

	if result == wx.ID_OK:
		pass
	elif result == wx.ID_CANCEL:
		pass
	else:
		raise Exception('Impossible')


def run_selftests():
	"""Run pytest ..."""

	logger.info('%s', "Running self-tests...")

	opts = [
		# '-s',  # disables capturing of stdout and stderr
		'--log-cli-level=DEBUG',  # sets log level
		'-v',  # enables verbose output
		]

	# __file__,  # tells pytest to only run tests in this file
	exit_code = pytest.main([*opts, __file__])

	if exit_code == 0:
		logger.info("All tests passed!")
	else:
		logger.info(f"Tests failed with exit code: {exit_code}")

	# pytest targets individually
	# test identifiers, that is, test-modules, test-module-test-functions
	tests = [
		# 'LabGym.tests.test_dummy_module',
		# 'LabGym.tests.test_dummy_module::test_bravo',
		'LabGym.tests',
	]

	for test in tests:
		# replace
		logger.info(f'Testing {test}')
		result = pytest.main([*opts, '--pyargs', test])
		if result == 0:
			logger.info(f'pytest {test}: all passed')
		else:
			logger.info(f'pytest {test} failed with exit code: {result}')


def test_dummy():
	# Arrange
	# Act
	pass
	# Assert


if __name__ == "__main__":
	# Example: Run selftests if a specific flag is passed
	if "--run-tests" in sys.argv:
		run_selftests()
	else:
		logger.info("Normal application execution...")
