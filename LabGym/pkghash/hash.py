"""Support hash-included version reporting for LabGym.

Provide functions to support hash-included version reporting for the
LabGym package.

Public Functions
	get_hashval -- Return a hashval (a signature) of the contents of the folder.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import hashlib
import itertools
import logging
import os
from pathlib import Path
import re
import sys
import time

# Related third party imports.
# None

# Local application/library specific imports.
# None


logger = logging.getLogger(__name__)

_cached_hashvals = {}


def get_hashval(folder: str) -> str:
	"""Return a hashval (a signature) of the contents of the folder.

	On first call to this function with this folder, compute the hash
	value string, and cache it in a module-level dictionary variable.
	On subsequent calls to this function with the same folder, return
	the cached hash value string.
	"""

	folder_pathobj = Path(folder).resolve()

	hashval = _cached_hashvals.get(folder_pathobj)

	if hashval is not None:
		return hashval

	hashval = _walk_and_hash(folder_pathobj)
	_cached_hashvals.update({folder_pathobj: hashval})

	return hashval


def _walk_and_hash(folder: Path) -> str:
	"""Walk a folder and return the accumulated the MD5 hash for files.

	*   Skip dirs that don't have __init__.py.
		All files of interest are in package dirs, right?

		Actually, no.  Generally, a package dir might have source-code
		in package subdirs that are not actually traditional packages
		themselves. (Implicit Namespace Packages)

		A different approach would be to create an empty file '.nohash'
		in dirs that should be skipped, and test for its existence
		during the walk.

	*   Skip top-level dirs detectron2, detectors, models.

	*   Skip non-py-files.
	"""

	hasher = hashlib.md5()
	os.chdir(folder)

	for root, dirs, files in os.walk('.'):
		# walk in "sorted" order
		dirs.sort()
		files.sort()

		# Skip dirs that don't have __init__.py.
		if '__init__.py' not in files:
			# this is not a "traditional" package dir...
			# skip further descent
			dirs.clear()
			# skip processing files in this dir
			continue

		# Skip top-level dirs detectron2, detectors, models.
		if root == '.':
			for name in ['detectron2', 'detectors', 'models']:
				if name in dirs:
					dirs.remove(name)

		for file in files:
			# Skip non-py-files.
			if not file.endswith('.py'):
				continue

			file_path = os.path.join(root, file)
			_add_file_to_hash(hasher, file_path)

	hashval = hasher.hexdigest()
	logger.debug('%s: %r', 'hashval', hashval)
	return hashval


def _add_file_to_hash(hasher, file_path: str) -> None:
	"""Add the filepath and the file content to the hash.

	Hash is sensitive to
		filename case -- foo.py is different from Foo.py
		file rename -- foo.py is different from goo.py

	*   replace leading tabs with 4-spaces,
		replace trailing \r\n with \n
		Why?  To normalize the content, as developers might run a genuine,
		but smudge-filtered copy.
	"""

	filename = Path(file_path).as_posix()  # forward slash, even on Windows

	hasher.update(filename.encode('utf-8'))

	try:
		# with open(file_path, 'rb') as f:
		#     # Read file in 8KB chunks to handle large files efficiently
		#     while chunk := f.read(8192):
		#         hasher.update(chunk)

		with open(file_path, 'r') as f:
			# Read file in 200-line chunks to handle large files efficiently
			for chunk in _myreadlines(f):
				for i, line in enumerate(chunk):
					line = _expand(line)  # expand leading tabs to 4 spaces
					# replace trailing space, incl LF or CRLF, with LF
					line = line.rstrip() + '\n'
					chunk[i] = line

				hasher.update(''.join(chunk).encode('utf-8'))

	except (OSError, IOError) as e:
		logger.warning(f'Trouble...{e}')

	logger.debug('%s: %r', 'filename, hasher.hexdigest()',
		(filename, hasher.hexdigest()))


def _myreadlines(f, n=200):
	"""Read n lines from f, and yield a list of the n strings."""
	while True:
		nline_chunk = list(itertools.islice(f, n))
		if not nline_chunk:
			 break
		yield nline_chunk


def _expand(line, n=4):
	"""Expand leading tabs to n spaces."""
	match = re.match(r'^(\t+)', line)
	if match:
		leading_tabs = match.group(0)
		spaces = ' ' * len(leading_tabs) * n
		return spaces + line[len(leading_tabs):]
	return line
