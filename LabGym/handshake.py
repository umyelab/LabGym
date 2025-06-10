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
# import inspect
import logging
import os
from pathlib import Path
import sys


# Log the load of this module (by the module loader, on first import).
#
# These statements are intentionally positioned before this module's
# other imports (against the guidance of PEP 8), to log the load of this
# module before other import statements are executed and potentially
# produce their own log messages.

logger = logging.getLogger(__name__)
logger.debug('%s: %r', '(__name__, __package__)', (__name__, __package__))


# Related third party imports.
import certifi  # Python package for providing Mozilla's CA Bundle.
import requests  # Python HTTP for Humans.
from packaging import version  # Core utilities for Python packages

# Local application/library specific imports.
from LabGym import __version__


def handshake() -> None:
	"""Perform some pre-op probes and checks with outside resources.

	1.  Try to compare this LabGym version with pypi's LabGym
	    version, and warn if this LabGym is stale.
	2.  Send http get to https://dl.fbaipublic.com to expose a
	    potential cacert trouble, and fail early if trouble presents.

	Generally, it's better to expose any inevitable problems sooner
	rather than later.
	"""

	# 1.  Try to compare this LabGym version with pypi's LabGym
	#     version, and warn if this LabGym is stale.
	try:

		current_version=version.parse(__version__)
		logger.debug('%s: %r', 'current_version', current_version)
		pypi_json = requests.get(
                    'https://pypi.org/pypi/LabGym/json', timeout=8
                    ).json()
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

	except Exception as e:
		logger.warning('Exception: %r', e)
		logger.warning('Trouble confirming sw version is up to date.')


	# 2.  Send http get to https://dl.fbaipublic.com to expose a
	#     potential cacert trouble, and fail early if trouble presents.

	# On 2025-05-19 Google AI says,
	# Detectron2 relies on dl.fbaipublicfiles.com for distributing
	# pre-built binaries and model weights.
	# f you're using the pre-built versions of Detectron2 or
	# downloading pre-trained models, your system will likely be
	# downloading files from dl.fbaipublicfiles.com.

	url = 'https://dl.fbaipublicfiles.com/detectron2'

	# With good cacerts.pem & cert chain, requests.get(url) responds with
	#     <Response [403]>
	#
	# With a deficient cacerts.pem, or defective cert chain,
	# requests.get(url) raises an exception, like
	#     requests.exceptions.SSLError: HTTPSConnectionPool(host='dl.fbaipublicfiles.com', port=443): Max retries exceeded with url: /detectron2 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1007)')))

	try:
		# requests.get(url) returns <Response [403]>
		response = requests.get(url, timeout=8)
	except requests.exceptions.SSLError as e:
		# logger.error(e)

		# logger.error(f'{e.__module__}.{e.__class__.__name__}: {e}')
		logger.error('%s.%s: %s', e.__module__, e.__class__.__name__, e)

		logger.error('Trouble in SSL cert chain...')

		logger.debug('%s: %r', 'os.environ.get("REQUESTS_CA_BUNDLE")',
			os.environ.get("REQUESTS_CA_BUNDLE"))
		logger.debug('%s: %r', 'os.environ.get("CURL_CA_BUNDLE")',
			os.environ.get("CURL_CA_BUNDLE"))
		logger.debug('%s: %r', 'requests.certs.where()',
			requests.certs.where())
		logger.debug('%s: %r', 'certifi.where()',
			certifi.where())

		sys.exit(1)
