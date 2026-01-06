"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

The LabGym package defines __version__ in LabGym/__init__.py.

Example
	from LabGym import __version__, pkghash
	# __version__ is like '2.9.6'

	version_with_hash = pkghash.labgym_version_with_hash()
	# version_with_hash is like '2.9.6 (7b2c)'

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

*   As a final step before releasing a new version, the developer should
	update versions.toml with the reference version+hashval.

	1.  run
			LabGym --debug --version
		which reports like
			...
			DEBUG:LabGym.pkghash.lookup:version_with_longhash: '2.9.7 (a48c52287fc078897a30f19b05f1c12a)'
			DEBUG:LabGym.pkghash.lookup:known_versions: ['2.9.6 (d41d8cd98f00b204e9800998ecf8427e)']
			DEBUG:LabGym.pkghash.lookup:result: '2.9.7 (a48c)'
			version: 2.9.7 (a48c)

	2.  update versions.toml from old, like
			known_versions = [
				'2.9.6 (d41d8cd98f00b204e9800998ecf8427e)',
			]
		to new like
			known_versions = [
				# '2.9.6 (d41d8cd98f00b204e9800998ecf8427e)',
				'2.9.7 (a48c52287fc078897a30f19b05f1c12a)',
			]

	Should we keep old known_values in the list defined in versions.toml?
	They won't be matched, because LabGym.__version__ is updated, but
	they have some value, so, yes preserve them as a comment.

	What if this final step (update versions.toml) is inadvertently
	skipped during a release?
	Only that the user-visible id will contain the hashval even when
	LabGym is clean... if there's no reference value to match, then it
	can't be suppressed.  In other words, a little extra visual noise.
"""

from .lookup import labgym_version_with_hash
