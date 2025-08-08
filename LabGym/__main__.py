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
'''  # noqa
# pylint: enable=line-too-long

# Standard library imports.
import logging
from pathlib import Path


# block begin
# These statements are intentionally positioned before this module's
# other imports (against the guidance of PEP 8), to log the loading of
# this module before other import statements are executed and
# potentially produce their own log messages.

from LabGym import mylogging
# Collect logrecords and defer handling until logging is configured.
mylogging.defer()

# Log the loading of this module (by the module loader, on first import).
logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Configure logging based on configfile, then handle collected logrecords.
mylogging.configure()
# block end


# Related third party imports.
import requests  # Python HTTP for Humans.
from packaging import version  # Core utilities for Python packages

# Local application/library specific imports.
from LabGym import mypkg_resources  # replace deprecated pkg_resources
from LabGym import __version__, gui_main, probes


logger.debug('%s: %r', '(__name__, __package__)', (__name__, __package__))


def main() -> None:
	"""Perform some pre-op probing, then display the main window."""

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

	# Perform some pre-op sanity checks and probes of outside resources.
	probes.probes()

	gui_main.main_window()

	logger.debug('Milestone -- exiting main')


if __name__=='__main__':  # pragma: no cover

	main()


