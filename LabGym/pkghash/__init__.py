"""
This package supports an enhanced "version" reporting.

The LabGym package defines its __version__ in LabGym/__init__.py.
It's available to LabGym modules as
	from . import __version__
	# or, from LabGym import __version__

To support enhanced version reporting that includes hash info for
integrity checking,
	from . import __version__, pkghash
	# or, from LabGym import __version__, pkghash

	version_with_hash = pkghash.make_version(__version__)
"""

from .hash import get_hash
from .lookup import lookup, make_version
