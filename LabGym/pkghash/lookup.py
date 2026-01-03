"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

Public Functions
	labgym_version_with_hash -- Return a hash-included version string
		for LabGym.

The term "hash" is commonly used both as verb and as noun.
To reduce confusion, these terms may be used to improve clarity.
	get_hashval -- the function (the verb)
	hashval -- the return string value (the noun) from the function

Examples
	pkghash.labgym_version_with_hash()
	returns a str like '2.9.6+be19',
	or returns '2.9.6' if the version+hashval is in known_versions.

	pkghash.labgym_version_with_hash(maxlen=6)
	returns a str like '2.9.6+be19e5',
	or returns '2.9.6' if the version+hashval is in known_versions.

	pkghash.labgym_version_with_hash(maxlen=None,
		suppress_if_known=False)
	returns a str like '2.9.6+be19e53c16ff24a33c48b517d870147b'
	even if version+hashval is in known_versions.

Why?  Isn't LabGym.__version__ sufficiently identifying?
The purpose of this "enhanced" version-string is to make obvious
when the user or developer is running customized/modified LabGym.

This helps to
1.  make developer usage scrubbable from LabGym from overall usage
	stats.
2.  avoid developer-investigation effort for behavior of a
	customized LabGym.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
from pathlib import Path
from typing import List

# Related third party imports.
try:
	# tomllib is included in the Python Standard Library since version 3.11
	import tomllib  # type: ignore
except ModuleNotFoundError:
	import tomli as tomllib  # A lil' TOML parser

# Local application/library specific imports.
from .hash import get_hashval
import LabGym


logger = logging.getLogger(__name__)


labgym_package_folder = str(Path(LabGym.__file__).parent)
version = LabGym.__version__
versions_file = Path(__file__).parent / 'versions.toml'


def _get_known_versions() -> List[str]:
	"""Read list of known version+hash strings from toml-file, and return it."""

	try:
		with open(versions_file, 'rb') as f:
			known_versions = tomllib.load(f).get('known_versions')
		assert isinstance(known_versions, list)
	except Exception as e:
		# an unreadable toml-file produces an empty list
		logger.warning(f'Trouble reading {versions_file}.  {e}')
		known_versions = []

	logger.debug('%s: %r', 'known_versions', known_versions)

	return known_versions


def labgym_version_with_hash(
		maxlen=4,
		suppress_if_known=True,
		) -> str:
	"""Return a hash-included version string for LabGym.

	If this LabGym package's version_with_hash package matches a
	reference value stored in versions.toml, then this LabGym is judged
	genuine/unmodified, so the hashval suffix is suppressed (unless
	suppress_if_known is True).
	"""

	hashval: str = get_hashval(labgym_package_folder)

	known_enhanced_versions = _get_known_versions()

	if (f'{version} ({hashval})' in known_enhanced_versions
			and suppress_if_known == True):
		result = version  # without hashval

	elif maxlen is not None:
		result = f'{version} ({hashval[:maxlen]})'
	else:
		result = f'{version} ({hashval})'

	logger.debug('%s: %r', 'result', result)
	return result
