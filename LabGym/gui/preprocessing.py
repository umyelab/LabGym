"""
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext. 

For license issues, please contact:

Dr. Bing Ye
Life Sciences Institute
University of Michigan
210 Washtenaw Avenue, Room 5403
Ann Arbor, MI 48109-2216
USA

Email: bingye@umich.edu
"""


import os
from typing import Callable
import wx

import cv2
import numpy as np

from ..tools import preprocess_video


class PreprocessingModule(wx.Frame):
    """Contains functions related to preprocessing videos for analysis."""

    def __init__(self):
        super().__init__(parent=None, title="Preprocess Videos", size=(1000, 370))
        self.path_to_videos = None
        self.framewidth = None
        self.result_path = None
        self.trim_video = False
        self.time_windows = []
        self.enhance_contrast = False
        self.contrast = 1.0
        self.crop_frame = False
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0
        self.decode_t = False
        self.fps_reduction_factor = 1.0

        self.panel = wx.Panel(self)
        self.boxsizer = wx.BoxSizer(wx.VERTICAL)

        # Video selection module
        self.text_inputvideos = self.get_module_text("None.")
        self.add_module(
            button_label="Select the video(s)\nfor preprocessing",
            button_handler=self.select_videos,
            tool_tip="Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.",
            text=self.text_inputvideos,
        )

        # Output folder selection module
        self.text_outputfolder = self.get_module_text("None.")
        self.add_module(
            button_label="Select a folder to store\nthe processed videos",
            button_handler=self.select_outpath,
            tool_tip="Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video.",
            text=self.text_outputfolder,
        )

        # Video trimming module
        self.text_duration = self.get_module_text("Default: not to trim a video.")
        self.add_module(
            button_label="Specify whether to enter time windows\nto form a trimmed video",
            button_handler=self.input_duration,
            tool_tip='If "Yes", specify time windows by format: starttime1-endtime1,starttime2-endtime2,...to form the new, trimmed videos. See Extended Guide how to set different time windows for different videos.',
            text=self.text_duration,
        )

        # Frame crop module
        self.text_cropframe = self.get_module_text("Default: not to crop frames.")
        self.add_module(
            button_label="Specify whether to crop\nthe video frames",
            button_handler=self.crop_frames,
            tool_tip="Cropping frames to exclude unnecessary areas can increase the analysis efficiency. You need to specify the 4 corner points of the cropping window. This cropping window will be applied for all videos selected.",
            text=self.text_cropframe,
        )

        # Contrast module
        # TODO: This feature increases brightness, not contrast (see tools.preprocess_video())
        self.text_enhancecontrast = self.get_module_text(
            "Default: not to enhance contrast."
        )
        self.add_module(
            button_label="Specify whether to enhance\nthe contrast in videos",
            button_handler=self.enhance_contrasts,
            tool_tip="Enhancing video contrast will increase the detection accuracy especially when the detection method is background subtraction based. Enter a contrast value to see whether it is good to apply or re-enter it.",
            text=self.text_enhancecontrast,
        )

        # FPS reduction module
        self.text_fps = self.get_module_text("Default: original FPS")
        self.add_module(
            button_label="Specify whether to reduce\nthe video FPS",
            button_handler=self.reduce_fps,
            tool_tip="Reducing video FPS will decrease model training time",
            text=self.text_fps,
        )

        # Start button
        button_preprocessvideos = wx.Button(
            self.panel, label="Start to preprocess the videos", size=(300, 40)
        )
        button_preprocessvideos.Bind(wx.EVT_BUTTON, self.preprocess_videos)
        wx.Button.SetToolTip(button_preprocessvideos, "Preprocess each selected video.")
        self.boxsizer.Add(0, 10, 0)
        self.boxsizer.Add(button_preprocessvideos, 0, wx.RIGHT | wx.ALIGN_RIGHT, 90)
        self.boxsizer.Add(0, 5, 0)

        self.panel.SetSizer(self.boxsizer)

        self.Centre()
        self.Show(True)

    def add_module(
        self,
        button_label: str,
        button_handler: Callable,
        tool_tip: str,
        text: wx.StaticText,
    ):
        """
        Adds a button and text box to the main sizer.

        Args:
            button_label: The button label.
            button_handler: The function to handle the button press.
            tooltip: The text displayed when the user hovers over the button.
            text: The wx.StaticText to be displayed next to the button.
        """
        module = wx.BoxSizer(wx.HORIZONTAL)
        button = wx.Button(self.panel, label=button_label, size=(300, 40))
        button.Bind(wx.EVT_BUTTON, button_handler)
        wx.Button.SetToolTip(button, tool_tip)
        module.Add(button, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        module.Add(text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        self.boxsizer.Add(0, 10, 0)
        self.boxsizer.Add(module, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

    def get_module_text(self, label: str) -> wx.StaticText:
        """Return a wx.StaticText instance with the given label."""
        return wx.StaticText(
            self.panel, label=label, style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END
        )

    def select_videos(self, event):
        wildcard = "Video files(*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov)|*.avi;*.mpg;*.mpeg;*.wmv;*.mp4;*.mkv;*.m4v;*.mov"
        dialog = wx.FileDialog(
            self, "Select video(s)", "", "", wildcard, style=wx.FD_MULTIPLE
        )

        if dialog.ShowModal() == wx.ID_OK:
            self.path_to_videos = dialog.GetPaths()
            self.path_to_videos.sort()
            path = os.path.dirname(self.path_to_videos[0])
            dialog1 = wx.MessageDialog(
                self,
                "Proportional resize the video frames?",
                "(Optional) resize the frames?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if dialog1.ShowModal() == wx.ID_YES:
                dialog2 = wx.NumberEntryDialog(
                    self,
                    "Enter the desired frame width",
                    "The unit is pixel:",
                    "Desired frame width",
                    480,
                    1,
                    10000,
                )
                if dialog2.ShowModal() == wx.ID_OK:
                    self.framewidth = int(dialog2.GetValue())
                    if self.framewidth < 10:
                        self.framewidth = 10
                    self.text_inputvideos.SetLabel(
                        "Selected "
                        + str(len(self.path_to_videos))
                        + " video(s) in: "
                        + path
                        + " (proportionally resize framewidth to "
                        + str(self.framewidth)
                        + ")."
                    )
                else:
                    self.framewidth = None
                    self.text_inputvideos.SetLabel(
                        "Selected "
                        + str(len(self.path_to_videos))
                        + " video(s) in: "
                        + path
                        + " (original framesize)."
                    )
                dialog2.Destroy()
            else:
                self.framewidth = None
                self.text_inputvideos.SetLabel(
                    "Selected "
                    + str(len(self.path_to_videos))
                    + " video(s) in: "
                    + path
                    + " (original framesize)."
                )
            dialog1.Destroy()

        dialog.Destroy()

    def select_outpath(self, event):
        dialog = wx.DirDialog(self, "Select a directory", "", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                "Processed videos will be in: " + self.result_path + "."
            )
        dialog.Destroy()

    def input_duration(self, event):
        dialog = wx.MessageDialog(
            self,
            "Whether to trim a video?",
            "Trim videos?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if dialog.ShowModal() == wx.ID_YES:
            self.trim_video = True
        else:
            self.trim_video = False
        dialog.Destroy()

        if self.trim_video is True:
            methods = [
                'Decode from filenames: "_stt_" and "_edt_"',
                "Enter time points",
            ]
            dialog = wx.SingleChoiceDialog(
                self,
                message="Specify the time windows for trimming videos",
                caption="Time windows for trimming videos",
                choices=methods,
            )
            if dialog.ShowModal() == wx.ID_OK:
                method = dialog.GetStringSelection()
                if method == 'Decode from filenames: "_stt_" and "_edt_"':
                    self.decode_t = True
                else:
                    self.decode_t = False
                    dialog1 = wx.TextEntryDialog(
                        self,
                        "Format: starttime1-endtime1,starttime2-endtime2,...",
                        "Enter the time windows (in seconds)",
                    )
                    if dialog1.ShowModal() == wx.ID_OK:
                        time_windows = dialog1.GetValue()
                        self.time_windows = []
                        try:
                            for i in time_windows.split(","):
                                times = i.split("-")
                                self.time_windows.append([times[0], times[1]])
                            self.text_duration.SetLabel(
                                "The time windows to form the new, trimmed video: "
                                + str(self.time_windows)
                                + "."
                            )
                        except:
                            self.trim_video = False
                            self.text_duration.SetLabel("Not to trim the videos.")
                            wx.MessageBox(
                                "Please enter the time windows in correct format!",
                                "Error",
                                wx.OK | wx.ICON_ERROR,
                            )
                    else:
                        self.trim_video = False
                        self.text_duration.SetLabel("Not to trim the videos.")
                    dialog1.Destroy()
            dialog.Destroy()

    def crop_frames(self, event):
        if self.path_to_videos is None:
            wx.MessageBox("No video selected.", "Error", wx.OK | wx.ICON_ERROR)

        else:
            capture = cv2.VideoCapture(self.path_to_videos[0])
            while True:
                retval, frame = capture.read()
                break
            capture.release()

            if self.framewidth is not None:
                frame = cv2.resize(
                    frame,
                    (
                        self.framewidth,
                        int(frame.shape[0] * self.framewidth / frame.shape[1]),
                    ),
                    interpolation=cv2.INTER_AREA,
                )

            canvas = np.copy(frame)
            h, w = frame.shape[:2]
            for y in range(0, h, 50):
                cv2.line(canvas, (0, y), (w, y), (255, 0, 255), 1)
                cv2.putText(
                    canvas,
                    str(y),
                    (5, y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 255),
                    1,
                )
            for x in range(0, w, 50):
                cv2.line(canvas, (x, 0), (x, h), (255, 0, 255), 1)
                cv2.putText(
                    canvas,
                    str(x),
                    (x + 5, 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 255),
                    1,
                )
            cv2.namedWindow("The first frame in coordinates", cv2.WINDOW_NORMAL)
            cv2.imshow("The first frame in coordinates", canvas)

            stop = False
            while stop is False:
                dialog = wx.TextEntryDialog(
                    self,
                    "Enter the coordinates (integers) of the cropping window",
                    "Format:[left,right,top,bottom]",
                )
                if dialog.ShowModal() == wx.ID_OK:
                    coordinates = list(dialog.GetValue().split(","))
                    if len(coordinates) == 4:
                        try:
                            self.left = int(coordinates[0])
                            self.right = int(coordinates[1])
                            self.top = int(coordinates[2])
                            self.bottom = int(coordinates[3])
                            self.crop_frame = True
                            stop = True
                            self.text_cropframe.SetLabel(
                                "The cropping window is from left: "
                                + str(self.left)
                                + " to right: "
                                + str(self.right)
                                + ", from top: "
                                + str(self.top)
                                + " to bottom: "
                                + str(self.bottom)
                                + "."
                            )
                        except:
                            self.crop_frame = False
                            wx.MessageBox(
                                "Please enter 4 integers.",
                                "Error",
                                wx.OK | wx.ICON_ERROR,
                            )
                            self.text_cropframe.SetLabel("Not to crop the frames")
                    else:
                        self.crop_frame = False
                        wx.MessageBox(
                            "Please enter the coordinates (integers) in correct format.",
                            "Error",
                            wx.OK | wx.ICON_ERROR,
                        )
                        self.text_cropframe.SetLabel("Not to crop the frames")
                else:
                    self.crop_frame = False
                    self.text_cropframe.SetLabel("Not to crop the frames")
                    stop = True
                dialog.Destroy()

            cv2.destroyAllWindows()

    def enhance_contrasts(self, event):
        if self.path_to_videos is None:
            wx.MessageBox("No video selected.", "Error", wx.OK | wx.ICON_ERROR)

        else:
            capture = cv2.VideoCapture(self.path_to_videos[0])
            while True:
                retval, frame = capture.read()
                break
            capture.release()

            if self.framewidth is not None:
                frame = cv2.resize(
                    frame,
                    (
                        self.framewidth,
                        int(frame.shape[0] * self.framewidth / frame.shape[1]),
                    ),
                    interpolation=cv2.INTER_AREA,
                )

            stop = False
            while stop is False:
                cv2.destroyAllWindows()
                cv2.namedWindow("The first frame in coordinates", cv2.WINDOW_NORMAL)
                cv2.imshow("The first frame in coordinates", frame)
                dialog = wx.TextEntryDialog(
                    self,
                    "Enter the fold changes for contrast enhancement",
                    "A number between 1.0~5.0",
                )
                if dialog.ShowModal() == wx.ID_OK:
                    contrast = dialog.GetValue()
                    try:
                        self.contrast = float(contrast)
                        show_frame = frame * self.contrast
                        show_frame[show_frame > 255] = 255
                        show_frame = np.uint8(show_frame)
                        cv2.destroyAllWindows()
                        cv2.namedWindow(
                            "The first frame in coordinates", cv2.WINDOW_NORMAL
                        )
                        cv2.imshow("The first frame in coordinates", show_frame)
                        dialog1 = wx.MessageDialog(
                            self,
                            "Apply the current contrast value?",
                            "Apply value?",
                            wx.YES_NO | wx.ICON_QUESTION,
                        )
                        if dialog1.ShowModal() == wx.ID_YES:
                            stop = True
                            self.enhance_contrast = True
                            self.text_enhancecontrast.SetLabel(
                                "The contrast enhancement fold change is: "
                                + str(self.contrast)
                                + "."
                            )
                        else:
                            self.enhance_contrast = False
                            self.text_enhancecontrast.SetLabel(
                                "Not to enhance contrast."
                            )
                        dialog1.Destroy()
                    except:
                        self.enhance_contrast = False
                        wx.MessageBox(
                            "Please enter a float number between 1.0~5.0.",
                            "Error",
                            wx.OK | wx.ICON_ERROR,
                        )
                        self.text_enhancecontrast.SetLabel("Not to enhance contrast.")
                else:
                    self.enhance_contrast = False
                    stop = True
                    self.text_enhancecontrast.SetLabel("Not to enhance contrast.")
                dialog.Destroy()
            cv2.destroyAllWindows()

    @property
    def fps_reduction_factor(self):
        return self._fps_reduction_factor

    @fps_reduction_factor.setter
    def fps_reduction_factor(self, factor: float):
        """Ensure reduction factor is greater than 1 before setting.

        The new FPS of the video will be calculated using the formula
        new_fps = old_fps / factor. If the factor is less than 1, then
        new_fps will be greater than old_fps, which is not supported.
        """
        if factor < 1.0:
            raise ValueError("FPS reduction factor must be greater than or equal to 1.")
        self._fps_reduction_factor = factor

    def reduce_fps(self, event):
        """Let user enter FPS reduction factor."""
        while True:
            fps_dialog = wx.TextEntryDialog(
                self,
                "Enter a number greater than 1.0",
                "Enter FPS reduction factor",
            )
            if fps_dialog.ShowModal() == wx.ID_OK:
                try:
                    factor = float(fps_dialog.GetValue())
                    try:
                        self.fps_reduction_factor = factor
                        self.text_fps.SetLabel(f"FPS Reduction Factor: {factor}")
                        break
                    except ValueError as e:
                        wx.MessageBox(
                            str(e),
                            "Error",
                            wx.OK | wx.ICON_ERROR,
                        )
                except ValueError:
                    wx.MessageBox(
                        "Please enter a number.",
                        "Error",
                        wx.OK | wx.ICON_ERROR,
                    )
            else:
                break
        fps_dialog.Destroy()

    def preprocess_videos(self, event):
        if self.path_to_videos is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / output folder.", "Error", wx.OK | wx.ICON_ERROR
            )

        else:
            print("Start to preprocess video(s)...")

            for i in self.path_to_videos:
                if self.decode_t is True:
                    self.time_windows = []
                    filename = os.path.splitext(os.path.basename(i))[0].split("_")
                    starttime_windows = [
                        x[2:] for x in filename if len(x) > 2 and x[:2] == "st"
                    ]
                    endtime_windows = [
                        x[2:] for x in filename if len(x) > 2 and x[:2] == "ed"
                    ]
                    for x, startt in enumerate(starttime_windows):
                        self.time_windows.append([startt, endtime_windows[x]])

                preprocess_video(
                    i,
                    self.result_path,
                    self.framewidth,
                    trim_video=self.trim_video,
                    time_windows=self.time_windows,
                    enhance_contrast=self.enhance_contrast,
                    contrast=self.contrast,
                    crop_frame=self.crop_frame,
                    left=self.left,
                    right=self.right,
                    top=self.top,
                    bottom=self.bottom,
                    fps_reduction_factor=self.fps_reduction_factor,
                )

            print("Preprocessing completed!")
