import logging
import os
import pprint
import sys

import pytest  # pytest: simple powerful testing with Python

from LabGym import mypkg_resources  # replace deprecated pkg_resources

# The mypkg_resources module copies itself into sys.modules['pkg_resources'],
# so this next import statement will not load the pkg_resources package.
import pkg_resources  # will not load pkg_resources

import LabGym.detectron2.model_zoo
from LabGym.detectron2 import model_zoo  # redundant, but convenient
from LabGym.detectron2.config import get_cfg
from LabGym.detectron2.modeling import build_model


logger = logging.getLogger(__name__)
logger.debug('%s:\n%s', 'sys.path', pprint.pformat(sys.path))


def test_dummy():
    # Arrange
    # Act
    pass
    # Assert not necessary.  This unit test passes unless exception was raised.


def test_resource_filename():
    """Test that resource_filename emulates the genuine resource_filename."""

    # Arrange
    args = (
        # package_or_requirement: The name of the package (e.g., 
        # 'my_package') or a Requirement object.
        'LabGym.detectron2.model_zoo',

        # resource_name: The path to the resource within that package 
        # (e.g., 'data/config.ini', 'images/icon.png')
        'configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml',
        )

    # Act
    result = pkg_resources.resource_filename(*args)

    # Assert
    assert result == os.path.normpath(os.path.join(
        os.path.dirname(LabGym.detectron2.model_zoo.__file__),
        'configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml',
        ))


def test_pkg_resources_is_mypkg_resources():
    """Test that pkg_resources has been replaced by mypkg_resources."""

    assert sys.modules['pkg_resources'] == sys.modules['LabGym.mypkg_resources']


# def test_get_returns_model():
#     """Test that model_zoo.get() successfully returns a model."""
def test_prepare_model_cfg():
    """Test that a model cfg can be prepared from default and config file."""

    # Choose a common model from the model zoo for testing
    config_path = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"

    # Get the default configuration for the chosen model
    cfg = get_cfg()
    full_config_path = model_zoo.get_config_file(config_path)
    cfg.merge_from_file(full_config_path)

    return

    # Build the model using the configuration
    model = build_model(cfg)

    # Assert that the model object an instance of torch.nn.Module
    assert model is not None
    assert isinstance(model, type(build_model(get_cfg())))


def test_get_config_file_returns_path():
    """Test that model_zoo.get_config_file() returns a valid file path."""

    config_path = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
    file_path = model_zoo.get_config_file(config_path)

    # Assert that the returned path is a string and points to an existing file
    assert isinstance(file_path, str)
    assert os.path.exists(file_path)


def test_get_checkpoint_url_returns_url():
    """Test that model_zoo.get_checkpoint_url() returns a valid URL."""

    config_path = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
    checkpoint_url = model_zoo.get_checkpoint_url(config_path)

    # Assert that the returned value is likely a URL (starts with http/https)
    assert isinstance(checkpoint_url, str)
    assert (checkpoint_url.startswith("http://")
        or checkpoint_url.startswith("https://"))
