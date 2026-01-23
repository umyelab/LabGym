"""
/tests/conftest.py

Shared pytest fixtures for LabGym tests
"""

# Standard library imports
import sys

# Related third party imports
import pytest

@pytest.fixture(scope="session")
def wx_app():
    from LabGym.ui.gui import wxutils
    import wx
    app = wx.App()
    yield app


@pytest.fixture
def mock_argv(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['LabGym'])


@pytest.fixture
def sample_greyscale_frame():
    import numpy as np
    import cv2
    frame = np.full((100, 100), 200, dtype = np.uint8)
    cv2.circle(frame, (50, 50), 15, 50, -1)
    return frame

@pytest.fixture
def sample_video_frames():
    import numpy as np
    import cv2
    frames = []

    for i in range(60):
        frame = np.full((100, 100), 200, dtype = np.uint8)
        cv2.circle(frame, (20 + i % 60, 50), 15, 50, -1)
        frames.append(frame)

    return frames