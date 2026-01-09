"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

Public Functions
	labgym_version_with_hash -- Return a hash-embellished version string
		for LabGym.

The term "hash" is commonly used both as verb and as noun.
To reduce confusion, these terms may be used to improve clarity.
	get_hashval -- the function (the verb)
	hashval -- the return string value (the noun) from the function

Examples
	pkghash.labgym_version_with_hash()
	returns a str like '2.9.6 (be19e53c16ff24a33c48b517d870147b)'

Why?  Isn't LabGym.__version__ sufficiently identifying?
The purpose of this "enhanced" version-string is to make it possible
to discern when the user or developer is running customized/modified LabGym.
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


def labgym_version_with_hash() -> str:
	"""Return a hash-embellished version string for LabGym."""

	hashval: str = get_hashval(labgym_package_folder)

	version_with_longhash = f'{version} ({hashval})'
	logger.debug('%s: %r', 'version_with_longhash', version_with_longhash)

	return version_with_longhash
