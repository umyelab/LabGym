"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

The LabGym package defines __version__ in LabGym/__init__.py.

Example
	from LabGym import __version__, pkghash
	# __version__ is like '2.9.7'

	version_with_hash = pkghash.labgym_version_with_hash()
	# version_with_hash is like '2.9.7 (a48c52287fc078897a30f19b05f1c12a)'

Notes
*   These formats were considered...
		2.9.6.7b2c
		2.9.6+7b2c
		2.9.6 (7b2c)
		2.9.6 (hash: 7b2c)

*   One way to silence the LabGym.pkghash.hash debug messages is to set
	the logger's level to INFO, by modifying ~/.labgym/logging.yaml, in
	loggers, like
		LabGym.pkghash.hash:
			level: INFO
"""

from .lookup import labgym_version_with_hash
