"""Import the deprecated pkg_resources package and suppress the warning.

Subsequent imports will not reload pkg_resources and won't issue the warning.
"""

import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')  # Ignore all warnings
    import pkg_resources


# """Provide a replacement for the deprecated pkg_resources package.
# 
# LabGym and detectron2 presently (2025-07-28) use the pkg_resources 
# package in a single module, detectron2/model_zoo/model_zoo.py.
#      4	import pkg_resources
#         ...
#    139	    cfg_file = pkg_resources.resource_filename(
#    140	        "detectron2.model_zoo", os.path.join("configs", config_path)
#    141	    )
# 
# The pkg_resources package is deprecated.
# When loaded, the pkg_resources package produces a user-facing warning.
# 
# However, if this module is loaded before the genuine pkg_resources is loaded,
# then 
# 1.  the warning message is caught/suppressed,
# 2.  references to pkg_resources are mapped to this module, so
#     pkg_resources.resource_filename refers to the function defined here.
# 
# After this module is tested, 
# to show that the new_result follows the old_result,
# the load of pkg_resources can be eliminated, and we can rely on the new_result.
# """
# 
# import importlib.resources
# import logging
# import sys
# import warnings
# 
# 
# logger = logging.getLogger(__name__)
# logger.debug('pkg_resources -- Loading...')
# with warnings.catch_warnings():
#     warnings.simplefilter('ignore')  # Ignore all warnings
#     from pkg_resources import resource_filename as old_resource_filename
# logger.debug('pkg_resources -- Loaded')
# 
# 
# logger.debug('%s: %r', 
#     "sys.modules['pkg_resources']", sys.modules['pkg_resources'])
# logger.debug('%s: %r', 
#     "sys.modules.get(__name__)", sys.modules.get(__name__))
# sys.modules['pkg_resources'] = sys.modules.get(__name__)
# 
# 
# def resource_filename(*args, **kwargs):
#     logger.debug('old_resource_filename() -- Calling')
#     logger.debug('%s: %r', 'args', args)
#     logger.debug('%s: %r', 'kwargs', kwargs)
#     old_result = old_resource_filename(*args, **kwargs)
#     logger.debug('%s: %r', 'old_result', old_result)
# 
#     # re-implement with importlib.resources.files()
#     try: 
#         new_result = str(importlib.resources.files(args[0]) / args[1])
#         logger.debug('%s: %r', 'new_result', new_result)
# 
#         if new_result == old_result:
#             logger.info(f'agreement {new_result}')
#         else:
#             logger.info(f'disagreement {new_result}, {old_result}')
#     except:
#         logger.warning(e)
# 
#     return old_result
