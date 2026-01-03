"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

The LabGym package defines __version__ in LabGym/__init__.py.

Example
	from LabGym import __version__, pkghash
	# __version__ is like '2.9.6'

	version_with_hash = pkghash.labgym_version_with_hash()
	# version_with_hash is like '2.9.6 (7b2c)'

Development Notes
	These formats were considered:
		2.9.6.7b2c
		2.9.6+7b2c
		2.9.6 (7b2c)
		2.9.6 (hash: 7b2c)
"""

from .lookup import labgym_version_with_hash
