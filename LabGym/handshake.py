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
import getpass
import json
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
import packaging  # Core utilities for Python packages

# Local application/library specific imports.
from LabGym import __version__ as version
from LabGym import myargparse, registration


# central logger, for reporting usage to the central receiver
central_logger = logging.getLogger('Central Logger')


def handshake() -> None:
	"""Perform some pre-op checks and probes of outside resources.

	It's generally preferable to expose any inevitable problems sooner
	rather than later.
	Some checks can be suppressed by command line options.
	"""

	opts = myargparse.parse_args()
	# opts.anonymous is a bool
	# opts.configdir is either a string or None.

	# Configure the central logger.
	configure_central_logger()
	if opts.anonymous == True:
		# Disable the central logger, and warn.
		central_logger.disabled = True
		logger.warning('Operating anonymously.')

	# Honor enable/disable of feature 'centrallogging'.
	if opts.enabled.get('centrallogging', True) == False:
		# Disable the central logger, and warn.
		central_logger.disabled = True
		logger.warning('Central Logging explicitly disabled.')

	# initialize userinfo
	userinfo = {'username': getpass.getuser()}

	if opts.anonymous == False:
                # Get validatation of registration.  (Register if unregistered).
		result = registration.validate(opts.configdir)
		userinfo.update(result)
		
	# Report the sw start via the central logger to the central receiver.
	# If central_logger is disabled (due to '--anonymous' option, or due
	# to feature 'centrallogging' disabled), then no log record will be
	# prepared.
	context = {}
	# context = ['schema version': 1]
	context['userinfo'] = userinfo
	context['version'] = version
	central_logger.info('%s Started (context: %r)',
		__package__, json.dumps(context))

	raise Exception('Intential abend')

	# Warn if the installed sw is stale.
	probe_pypi_check_freshness()

	# Check for cacert trouble which might be a fouled installation.
	probe_url_to_verify_cacert()


def configure_central_logger() -> None:
	"""Set level, and add handler that reports to the central receiver."""

	central_logger.setLevel(logging.INFO)

	# Add handler that reports to the central receiver.

	# TODO: replace these simple handlers that output to console and
        #     logfile with a handler that reports to the central receiver.

	h1 = logging.StreamHandler()
	f = logging.Formatter(
		fmt='%(asctime)s\t%(levelname)s\t[%(name)s]\t%(message)s',
		datefmt='%Y-%m-%d %H:%M:%S%z',
		)
	h1.setFormatter(f)

	central_logger.addHandler(h1)

        # if config dir exists so that logfile can be written...
	h2 = logging.FileHandler(
            os.path.join(os.path.expanduser('~'), '.mydev.centrallogger.log'), 
            mode='a')
	h2.setFormatter(f)
	central_logger.addHandler(h2)


def probe_pypi_check_freshness() -> None:
	"""Probe pypi for sw version, and warn if the installed sw is stale.

	Probe pypi for the LabGym sw version, and compare with the installed
	sw version, and warn if the installed sw is stale.
	"""

	try:

		current_version=packaging.version.parse(__version__)
		logger.debug('%s: %r', 'current_version', current_version)
		pypi_json = requests.get(
			'https://pypi.org/pypi/LabGym/json', timeout=8
			).json()
		latest_version=packaging.version.parse(pypi_json['info']['version'])
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


def probe_url_to_verify_cacert() -> None:
	"""Check for cacert trouble which might be a fouled installation.

	Send http get to https://dl.fbaipublic.com to expose potential
	cacert trouble, and fail early if trouble presents.

	On 2025-05-19 Google AI says,
	  Detectron2 relies on dl.fbaipublicfiles.com for distributing pre-
	  built binaries and model weights.
	  If you're using the pre-built versions of Detectron2 or
	  downloading pre-trained models, your system will likely be
	  downloading files from dl.fbaipublicfiles.com.
	"""

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
		logger.debug('%s: %r', 'certifi.where()',
			certifi.where())
		logger.debug('%s: %r', 'os.environ.get("REQUESTS_CA_BUNDLE")',
			os.environ.get("REQUESTS_CA_BUNDLE"))
	except requests.exceptions.SSLError as e:
		# logger.error(e)

		# logger.error(f'{e.__module__}.{e.__class__.__name__}: {e}')
		logger.error('%s.%s: %s', e.__module__, e.__class__.__name__, e)

		logger.error('Trouble in SSL cert chain...')

		logger.debug('%s: %r', 'os.environ.get("REQUESTS_CA_BUNDLE")',
			os.environ.get("REQUESTS_CA_BUNDLE"))
		logger.debug('%s: %r', 'os.environ.get("CURL_CA_BUNDLE")',
			os.environ.get("CURL_CA_BUNDLE"))
		# logger.debug('%s: %r', 'requests.certs.where()',
		# 	requests.certs.where())
		logger.debug('%s: %r', 'certifi.where()',
			certifi.where())

		sys.exit(1)
