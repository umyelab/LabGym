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
from pathlib import Path
from typing import Tuple
import wx

import cv2
import numpy as np

from LabGym.tools import preprocess_video

from .utils import WX_VIDEO_WILDCARD, LabGymWindow


class PreprocessingModule(LabGymWindow):
    """Contains functions related to preprocessing videos for analysis."""

    def __init__(self):
        super().__init__(title="Preprocess Videos", size=(1000, 370))
        self.video_paths = None
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

        # Video selection module
        self.text_inputvideos = self.module_text("None.")
        self.add_module(
            button_label="Select the video(s)\nfor preprocessing",
            button_handler=self.select_videos,
            tool_tip="Select one or more videos. Common video formats (mp4, mov, avi, m4v, mkv, mpg, mpeg) are supported except wmv format.",
            text=self.text_inputvideos,
        )

        # Output folder selection module
        self.text_outputfolder = self.module_text("None.")
        self.add_module(
            button_label="Select a folder to store\nthe processed videos",
            button_handler=self.select_outpath,
            tool_tip="Will create a subfolder for each video in the selected folder. Each subfolder is named after the file name of the video.",
            text=self.text_outputfolder,
        )

        # Video trimming module
        self.text_duration = self.module_text("Default: not to trim a video.")
        self.add_module(
            button_label="Specify whether to enter time windows\nto form a trimmed video",
            button_handler=self.input_duration,
            tool_tip='If "Yes", specify time windows by format: starttime1-endtime1,starttime2-endtime2,...to form the new, trimmed videos. See Extended Guide how to set different time windows for different videos.',
            text=self.text_duration,
        )

        # Frame crop module
        self.text_cropframe = self.module_text("Default: not to crop frames.")
        self.add_module(
            button_label="Specify whether to crop\nthe video frames",
            button_handler=self.crop_frames,
            tool_tip="Cropping frames to exclude unnecessary areas can increase the analysis efficiency. You need to specify the 4 corner points of the cropping window. This cropping window will be applied for all videos selected.",
            text=self.text_cropframe,
        )

        # Contrast module
        # TODO: This feature increases brightness, not contrast (see tools.preprocess_video())
        self.text_enhancecontrast = self.module_text(
            "Default: not to enhance contrast."
        )
        self.add_module(
            button_label="Specify whether to enhance\nthe contrast in videos",
            button_handler=self.enhance_contrasts,
            tool_tip="Enhancing video contrast will increase the detection accuracy especially when the detection method is background subtraction based. Enter a contrast value to see whether it is good to apply or re-enter it.",
            text=self.text_enhancecontrast,
        )

        # FPS reduction module
        self.text_fps = self.module_text("Default: original FPS")
        self.add_module(
            button_label="Specify whether to reduce\nthe video FPS",
            button_handler=self.reduce_fps,
            tool_tip="Reducing video FPS will decrease model training time",
            text=self.text_fps,
        )

        # Start button
        self.add_submit_button(
            label="Start to preprocess the videos",
            handler=self.preprocess_videos,
            tool_tip="Preprocess each selected video.",
        )

        self.display_window()

    def select_videos(self, event):
        """Opens file selection dialog to select videos to preprocess."""

        # Select videos
        video_selection_dialog = wx.FileDialog(
            parent=self,
            message="Select video(s)",
            wildcard=WX_VIDEO_WILDCARD,
            style=wx.FD_MULTIPLE,
        )

        if video_selection_dialog.ShowModal() != wx.ID_OK:
            video_selection_dialog.Destroy()
            return

        self.video_paths = video_selection_dialog.GetPaths()
        video_selection_dialog.Destroy()
        self.video_paths.sort()
        video_folder = os.path.dirname(self.video_paths[0])
        label_text = f"Selected {len(self.video_paths)} video(s) in: {video_folder}"

        # Ask whether or not to resize the videos
        resize_dialog = wx.MessageDialog(
            parent=self,
            message="Proportional resize the video frames?",
            caption="(Optional) resize the frames?",
            style=wx.YES_NO | wx.ICON_QUESTION,
        )

        if resize_dialog.ShowModal() != wx.ID_YES:
            self.framewidth = None
            self.text_inputvideos.SetLabel(label_text + " (original framesize).")
            resize_dialog.Destroy()
            return

        # Ask for the new frame width
        frame_width_dialog = wx.NumberEntryDialog(
            parent=self,
            message="Enter the desired frame width",
            prompt="The unit is pixel:",
            caption="Desired frame width",
            value=480,
            min=10,
            max=10000,
        )

        if frame_width_dialog.ShowModal() == wx.ID_OK:
            self.framewidth = int(frame_width_dialog.GetValue())
            label_text += f" (proportionally resize framewidth to {self.framewidth})."
        else:
            self.framewidth = None
            label_text += " (original framesize)."

        frame_width_dialog.Destroy()
        resize_dialog.Destroy()
        self.text_inputvideos.SetLabel(label_text)

    def select_outpath(self, event):
        """Opens folder selection dialog for storing processed video."""
        dialog = wx.DirDialog(
            parent=self, message="Select a directory", style=wx.DD_DEFAULT_STYLE
        )
        if dialog.ShowModal() == wx.ID_OK:
            self.result_path = dialog.GetPath()
            self.text_outputfolder.SetLabel(
                f"Processed videos will be in: {self.result_path}."
            )
        dialog.Destroy()

    def input_duration(self, event):
        """Opens dialogs to configure input time windows."""

        # Ask whether or not to trim a video
        trim_dialog = wx.MessageDialog(
            self,
            "Whether to trim a video?",
            "Trim videos?",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        self.trim_video = trim_dialog.ShowModal() == wx.ID_YES
        trim_dialog.Destroy()

        if not self.trim_video:
            return

        # Ask for method for time windows
        methods = [
            'Decode from filenames: "_stt_" and "_edt_"',
            "Enter time points",
        ]
        method_dialog = wx.SingleChoiceDialog(
            self,
            message="Specify the time windows for trimming videos",
            caption="Time windows for trimming videos",
            choices=methods,
        )

        if method_dialog.ShowModal() != wx.ID_OK:
            method_dialog.Destroy()
            return

        self.decode_t = False
        method = method_dialog.GetStringSelection()
        if method == methods[0]:  # Use st<start> and ed<end> tags
            self.decode_t = True
            self.text_duration.SetLabel('Decode from filenames: "_stt_" and "_edt_"')
            method_dialog.Destroy()
            return

        # Manual entry for time windows
        windows_dialog = wx.TextEntryDialog(
            self,
            "Format: starttime1-endtime1,starttime2-endtime2,...",
            "Enter the time windows (in seconds)",
        )

        if windows_dialog.ShowModal() != wx.ID_OK:
            self.trim_video = False
            self.text_duration.SetLabel("Not to trim the videos.")
            windows_dialog.Destroy()
            method_dialog.Destroy()
            return

        try:
            window_input: str = windows_dialog.GetValue()
            self.time_windows = self.parse_time_window_str(window_input)
            self.text_duration.SetLabel(
                f"The time windows to form the new, trimmed video: {self.time_windows}."
            )
        except ValueError as err:
            self.trim_video = False
            self.text_duration.SetLabel("Not to trim the videos.")
            wx.MessageBox(
                f"{str(err)} Please enter the time windows in correct format!",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        windows_dialog.Destroy()
        method_dialog.Destroy()

    def parse_time_window_str(self, window_input: str) -> list[Tuple[float, float]]:
        """
        Return the time windows to trim the videos by given user input.

        The user should input the time windows in the format
            start-end, start-end, start-end...
        where start and end represent times in seconds such that start < end.

        Args:
            windows: The user's time window entry.

        Returns:
            A list of tuples (start, end) where start and end are floats that
            represent the start and end times in seconds of each time window.

        Raises:
            ValueError: There was an error parsing the time window string.
        """
        windows = []
        for window in window_input.split(","):
            w = [i.strip() for i in window.split("-")]
            if len(w) != 2:
                raise ValueError(f"'{window}' is an invalid time window.")
            try:
                start = float(w[0].strip())
            except ValueError:
                raise ValueError(f"'{w[0]}' is an invalid start time.")
            try:
                end = float(w[1])
            except ValueError:
                raise ValueError(f"'{w[1]}' is an invalid end time.")
            if not start <= end:
                raise ValueError("Start time must be less than end time.")
            windows.append((start, end))
        return windows

    def crop_frames(self, event):
        """Opens dialogs to configure frame cropping."""

        if self.video_paths is None:
            wx.MessageBox("No video selected.", "Error", wx.OK | wx.ICON_ERROR)
            return

        capture = cv2.VideoCapture(self.video_paths[0])
        _, frame = capture.read()
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
        height, width = frame.shape[:2]
        for y in range(0, height, 50):
            cv2.line(canvas, (0, y), (width, y), (255, 0, 255), 1)
            cv2.putText(
                canvas,
                str(y),
                (5, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                1,
            )
        for x in range(0, width, 50):
            cv2.line(canvas, (x, 0), (x, height), (255, 0, 255), 1)
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

        while True:
            dialog = wx.TextEntryDialog(
                self,
                "Enter the coordinates (integers) of the cropping window",
                "Format:[left,right,top,bottom]",
            )
            if dialog.ShowModal() != wx.ID_OK:
                self.crop_frame = False
                self.text_cropframe.SetLabel("Not to crop the frames")
                dialog.Destroy()
                break

            coordinates = dialog.GetValue().split(",")
            if len(coordinates) != 4:
                self.crop_frame = False
                wx.MessageBox(
                    "Please enter the coordinates (integers) in correct format.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                self.text_cropframe.SetLabel("Not to crop the frames")
                continue
            try:
                self.left = int(coordinates[0])
                self.right = int(coordinates[1])
                self.top = int(coordinates[2])
                self.bottom = int(coordinates[3])
            except ValueError:
                self.crop_frame = False
                wx.MessageBox(
                    "Please enter 4 integers.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                self.text_cropframe.SetLabel("Not to crop the frames")
                continue

            self.crop_frame = True
            self.text_cropframe.SetLabel(
                f"The cropping window is from left: {self.left} to right: {self.right}, from top: {self.top} to bottom: {self.bottom}."
            )
            break

        cv2.destroyAllWindows()

    def enhance_contrasts(self, event):
        """Opens dialogs to configure frame cropping."""

        if self.video_paths is None:
            wx.MessageBox("No video selected.", "Error", wx.OK | wx.ICON_ERROR)
            return

        capture = cv2.VideoCapture(self.video_paths[0])
        _, frame = capture.read()
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

        while True:
            cv2.destroyAllWindows()
            cv2.namedWindow("The first frame in coordinates", cv2.WINDOW_NORMAL)
            cv2.imshow("The first frame in coordinates", frame)

            dialog = wx.TextEntryDialog(
                self,
                "Enter the fold changes for contrast enhancement",
                "A number between 1.0~5.0",
            )
            if dialog.ShowModal() != wx.ID_OK:
                self.enhance_contrast = False
                self.text_enhancecontrast.SetLabel("Not to enhance contrast.")
                dialog.Destroy()
                break

            contrast = dialog.GetValue()
            try:
                self.contrast = float(contrast)
            except ValueError:
                self.enhance_contrast = False
                wx.MessageBox(
                    "Please enter a float number between 1.0~5.0.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                self.text_enhancecontrast.SetLabel("Not to enhance contrast.")
                dialog.Destroy()
                continue

            show_frame = frame * self.contrast  # type: ignore
            show_frame[show_frame > 255] = 255
            show_frame = np.uint8(show_frame)
            cv2.destroyAllWindows()
            cv2.namedWindow("The first frame in coordinates", cv2.WINDOW_NORMAL)
            cv2.imshow("The first frame in coordinates", show_frame)  # type: ignore

            confirm = wx.MessageDialog(
                self,
                "Apply the current contrast value?",
                "Apply value?",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            if confirm.ShowModal() != wx.ID_YES:
                self.enhance_contrast = False
                self.text_enhancecontrast.SetLabel("Not to enhance contrast.")
                confirm.Destroy()
                dialog.Destroy()
                continue

            self.enhance_contrast = True
            self.text_enhancecontrast.SetLabel(
                f"The contrast enhancement fold change is: {self.contrast}."
            )
            confirm.Destroy()
            dialog.Destroy()
            cv2.destroyAllWindows()
            break

    @property
    def fps_reduction_factor(self):
        """
        The factor by which to reduce the video framerate.

        The new FPS of the video will be calculated using the formula
        new_fps = old_fps / factor. The reduction factor must be greater than
        1.0.
        """
        return self._fps_reduction_factor

    @fps_reduction_factor.setter
    def fps_reduction_factor(self, factor: float):
        """Ensure reduction factor is greater than or equal to 1.0 before setting."""
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
            if fps_dialog.ShowModal() != wx.ID_OK:
                break

            try:
                factor = float(fps_dialog.GetValue())
            except ValueError:
                wx.MessageBox(
                    "Please enter a number.",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                continue
            try:
                self.fps_reduction_factor = factor
            except ValueError as e:
                wx.MessageBox(
                    str(e),
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
                continue
            self.text_fps.SetLabel(f"FPS Reduction Factor: {factor}")
            break
        fps_dialog.Destroy()

    def parse_time_window_filename(self, video_path: str) -> list[Tuple[float, float]]:
        """
        Return the time windows to trim the video given the video file.

        The video filename should contain tags st<start> and ed<end> where
        start and end are the start and end times of the time window, and each
        tag is separated from the video file by an underscore.

        Ex. /path/to/video_st0_ed30_st120_ed150.mov will return the time
        windows (0, 30) and (120, 150).

        Args:
            video_path: The path to the video to extract time windows from.

        Returns:
            A list of tuples (start, end) where start and end are floats that
            represent the start and end times in seconds of each time window.

        Raises:
            ValueError: There was an error parsing the file path.
        """
        video = Path(video_path)
        parts = [
            part
            for part in video.stem.split("_")
            if part.startswith("st") or part.startswith("ed")
        ]

        windows = []
        for i in range(0, len(parts), 2):
            if i >= len(parts):
                raise ValueError(f"Missing ed tag in file {video.name}.")
            try:
                assert parts[i].startswith("st")
                start = float(parts[i][2:])
            except (ValueError, AssertionError):
                raise ValueError(f"Invalid tag {parts[i]} in file {video.name}.")
            try:
                assert parts[i + 1].startswith("ed")
                end = float(parts[i + 1][2:])
            except (ValueError, AssertionError):
                raise ValueError(f"Invalid tag {parts[i+1]} in file {video.name}.")
            windows.append((start, end))

        return windows

    def preprocess_videos(self, event):
        """Process videos given the current configuration."""

        if self.video_paths is None or self.result_path is None:
            wx.MessageBox(
                "No input video(s) / output folder.", "Error", wx.OK | wx.ICON_ERROR
            )
            return

        print("Start to preprocess video(s)...")
        for video_path in self.video_paths:
            if self.decode_t is True:
                self.time_windows = self.parse_time_window_filename(video_path)

            preprocess_video(
                video_path,
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
