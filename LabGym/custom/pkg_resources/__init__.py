"""
Package resource API
--------------------

A resource is a logical file contained within a package, or a logical
subdirectory thereof.  The package resource API expects resource names
to have their path parts separated with ``/``, *not* whatever the local
path separator is.  Do not use os.path operations to manipulate resource
names being passed into the API.

The package resource API is designed to work with normal filesystem packages,
.egg files, and unpacked .egg files.  It can also work in a limited way with
.zip files and with custom PEP 302 loaders that support the ``get_data()``
method.

This module is deprecated. Users are directed to :mod:`importlib.resources`,
:mod:`importlib.metadata` and :pypi:`packaging` instead.

As to resource_filename(), Google's AI Overview explains
    In the pkg_resources module, resource_filename(package_or_requirement,
    resource_name) provides a way to obtain a filesystem path to a
    resource within a Python package.

    How it works:
    *   It takes two arguments:
        +   package_or_requirement: This can be a package name (e.g., 
            'my_package') or a Requirement object.
        +   resource_name: The path to the resource within the package 
            (e.g., 'data/config.json').
    *   If the resource is already a file on the filesystem (e.g., in an 
        unpacked directory), it returns the direct path to that file.
    *   If the resource is located inside an archive distribution (like 
        a zipped egg file), pkg_resources will:
        +   Extract: the resource (and potentially other related 
            resources like C extensions or eager resources) to a 
            temporary cache directory.
        +   Return the path: to this extracted temporary file.

    Key considerations:
    Temporary files: When resources are extracted from archives, temporary
    files are created. pkg_resources handles the cleanup of these
    temporary files implicitly.
    
    Directories: If resource_name refers to a directory, resource_filename
    will extract all resources within that directory (including
    subdirectories) to the cache and return the path to the extracted
    directory.
    
    Alternatives: For simply accessing resource content as a string or
    stream, pkg_resources.resource_string() or pkg_resources.resource_stream()
    are often preferred as they avoid the overhead of extracting files
    to disk.
    
    Deprecation: It is important to note that pkg_resources is considered
    deprecated. Newer Python projects should utilize importlib.resources
    and importlib.metadata (or their backports importlib_resources and
    importlib_metadata) for resource and package metadata access, as
    they offer a more modern and efficient approach.
"""

import importlib
import logging
import os


logger = logging.getLogger(__name__)
logger.debug('loading %s', __file__)


def resource_filename(package_or_requirement, resource_name):
    """Return a string path to the resource.

    This is a simple, naive re-implementation of the genuine 
    resource_filename().   
    (from the pkg_resources dir, from setuptools 80.9.0)

        +   package_or_requirement: This can be a package name (e.g., 
            'my_package') or a Requirement object.
        +   resource_name: The path to the resource within the package 
            (e.g., 'data/config.json').
    """

    pkg = importlib.import_module(package_or_requirement)
    result = os.path.join(pkg.__path__[0], resource_name)
    logging.debug('%s: %r', 'pkg_resource.resource_filename(...) returning ', result)
    return result
