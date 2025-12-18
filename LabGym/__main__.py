# pylint: disable=line-too-long
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


# noqa
# pylint: enable=line-too-long

# Standard library imports.
import logging
from pathlib import Path
import sys

# block begin
# These statements are intentionally positioned before this module's
# other imports (against the guidance of PEP 8), to log the loading of
# this module before other import statements are executed and
# potentially produce their own log messages.
# pylint: disable=wrong-import-position
from LabGym import mylogging  # pylint: disable=ungrouped-imports
# Collect logrecords and defer handling until logging is configured.
mylogging.defer()

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP 8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__name__}')

# Configure logging based on configfile, then handle collected logrecords.
mylogging.configure()
# pylint: enable=wrong-import-position
# block end

# Related third party imports.
from packaging import version  # Core utilities for Python packages
import requests  # Python HTTP for Humans.
from LabGym import mywx  # on load, monkeypatch wx.App to be a strict-singleton
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
# pylint: disable-next=unused-import
from LabGym import mypkg_resources  # replace deprecated pkg_resources
from LabGym import __version__, gui_main, probes
from LabGym import config, selftest


logger.debug('%s: %r', '(__name__, __package__)', (__name__, __package__))


def main() -> None:
	"""Perform some pre-op probing, then display the main window."""

	# Get all of the values needed from config.get_config().
	flag_selftest: bool = config.get_config()['selftest']

	if flag_selftest:
		logger.info('%s -- %s', 'run_selftests()', 'calling...')
		result = selftest.run_selftests()
		logger.info('%s -- %s', 'run_selftests()', f'returned {result!r}')
		logger.info('%s -- %s', f'sys.exit({result!r})', 'calling...')
		sys.exit(result)


	try:

		current_version=version.parse(__version__)
		logger.debug('%s: %r', 'current_version', current_version)
		pypi_json=requests.get('https://pypi.org/pypi/LabGym/json').json()
		latest_version=version.parse(pypi_json['info']['version'])
		logger.debug('%s: %r', 'latest_version', latest_version)

		if latest_version>current_version:

			if 'pipx' in str(Path(__file__)):
				upgrade_command='pipx upgrade LabGym'
			else:
				upgrade_command='python3 -m pip install --upgrade LabGym'

			print(f'You are using LabGym {current_version}, but version {latest_version} is available.')
			print(f'Consider upgrading LabGym by using the command "{upgrade_command}".')
			print('For the details of new changes, check https://github.com/umyelab/LabGym.\n')

	except:

		pass

	# Create a single persistent, wx.App instance, as it may be
	# needed for probe dialogs prior to calling gui_main.main_window.
	assert wx.GetApp() is None
	wx.App()
	mywx.bring_wxapp_to_foreground()

	# Perform some pre-op sanity checks and probes of outside resources.
	probes.probes()

	gui_main.main_window()

	logger.debug('Milestone -- exiting main')


if __name__=='__main__':  # pragma: no cover

	main()
