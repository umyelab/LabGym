import logging
from pathlib import Path
import sys

import pytest

from LabGym import central_logging
# from .exitstatus import exitstatus


# basicConfig here isn't effective, maybe pytest has already configured logging?
# instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


# success cases
def test_enable_true(monkeypatch):
    # Arrange
    _config = {'enable': {'central_logger': True}}
    monkeypatch.setattr(central_logging.config, 'get_config', lambda: _config)
    logging.debug('%s: %r', '_config', _config)

    # Act
    central_logger = central_logging.get_central_logger(reset=True)

    # Assert
    assert central_logger.disabled == False

    assert central_logger.name == 'Central Logger'
    assert central_logger.level == logging.INFO
