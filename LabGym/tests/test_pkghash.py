from LabGym import pkghash

def test_pkghash(capsys):
	# Arrange
	# Act
	version_with_hash = pkghash.labgym_version_with_hash()
	# Assert

	with capsys.disabled():
		print('\n' f'version_with_hash: {version_with_hash}')
