# """Import the deprecated pkg_resources package and suppress the warning.
#
# Subsequent imports will not reload pkg_resources and won't issue the warning.
# """
#
# import warnings
# with warnings.catch_warnings():
#     warnings.simplefilter('ignore')  # Ignore all warnings
#     import pkg_resources


"""Provide a replacement for the deprecated pkg_resources package.

LabGym and detectron2 presently (2025-07-28) use the pkg_resources
package in a single module, detectron2/model_zoo/model_zoo.py.
	 4  import pkg_resources
		...
   139      cfg_file = pkg_resources.resource_filename(
   140          "detectron2.model_zoo", os.path.join("configs", config_path)
   141      )

The pkg_resources package is deprecated.
When the pkg_resources package is loaded, it produces a user-facing warning.

However, if this module is loaded before the genuine pkg_resources is
loaded, then references to pkg_resources are mapped to this module, so
(a) pkg_resources will not be loaded, and,
(b) pkg_resources.resource_filename refers to the function defined in
	this module.
"""

import importlib.resources
import logging
import sys


# This module replaces the genuine pkg_resources package.
sys.modules['pkg_resources'] = sys.modules.get(__name__)


def resource_filename(*args):
	"""Emulate the pkg_resources.resource_filename function.

	(from Google AI Overview)
	pkg_resources.resource_filename() is a function from the
	pkg_resources module (part of setuptools) in Python. It is used to
	obtain the true filesystem path for a specified resource within a
	Python package.

	Purpose:
	This function is particularly useful when you need to access files
	within a package as actual files on the filesystem, rather than just
	as strings or streams. This is often necessary for tasks like
	loading configuration files, image assets, or other data files that
	external libraries or tools might expect to find at a specific file
	path.

	How it works:
	Package Resources: pkg_resources.resource_filename() takes two main
	arguments:
	*   package_or_requirement: The name of the package (e.g.,
		'my_package') or a Requirement object.
	*   resource_name: The path to the resource within that package
		(e.g., 'data/config.ini', 'images/icon.png').

	Extraction (if needed): If the package is distributed in an archive
	format (like a zipped .egg file), resource_filename() will extract
	the requested resource (and potentially other related resources) to
	a temporary cache directory and return the path to that extracted
	file.

	Direct Path (if available): If the package is installed directly
	on the filesystem (e.g., as a directory), it will return the
	direct path to the resource within that directory.
	"""

	assert len(args) == 2

	# re-implement with importlib.resources.files()
	return str(importlib.resources.files(args[0]) / args[1])
