"""
The term "hash" is commonly used both as verb and as noun.
Here, to avoid confusion,
	hash is the name of the package module implementing the function
	get_hash is the function (the verb)
	hash_value is the return value (the noun)
"""
from . import get_hash

def lookup():
	pass

def make_version(version):
	hash_value = get_hash()
	return f'{version}+{hash_value[:4]}'
