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
from __future__ import annotations

import datetime
import functools
import gc
import operator
import os
from collections import deque
from typing import Sequence, Tuple, Union

import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb
from cv2.typing import MatLike
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.colorbar import ColorbarBase
from numpy.typing import NDArray
from skimage import exposure
from tensorflow.keras.preprocessing.image import img_to_array


# Constants to store animal lighter vs darker than background
class AnimalVsBg:
    ANIMAL_LIGHTER = 0
    ANIMAL_DARKER = 1
    HARD_TO_TELL = 2


# Use Frame to refer to different representations of a frame
Frame = Union[NDArray[np.uint8], MatLike]


def _extract_background(
    frames: Sequence[MatLike],
    stable_illumination: bool = True,
    animal_vs_bg: int = AnimalVsBg.ANIMAL_LIGHTER,
) -> Frame | None:
    """
    Extracts the background from the given list of frames.

    Args:
        frames: A list of frames to extract the background from.
        stable_illumination: False if background lighting changes for
            optogenetic experiments, else True.
        animal_vs_bg: Whether the animal is lighter or darker than the
            background or whether it's hard to tell; use constants at top of
            tools.py for specific values.

    Returns:
        An NDArray containing the extracted background.

    Raises:
        None
    """

    len_frames = len(frames)

    # Need at least 4 frames to extract background
    if len_frames <= 3:
        return None

    # Convert to ndarray
    frames_arr = np.array(frames, dtype="float32")

    if animal_vs_bg == AnimalVsBg.HARD_TO_TELL:
        if len_frames <= 101:
            return np.uint8(np.median(frames_arr, axis=0))  # type: ignore

        frames_mean = []
        check_frames = []
        mean_overall = frames_arr.mean(0)
        for n in range(0, len_frames - 101, 30):
            frames_temp = frames_arr[n : n + 100]
            mean = frames_temp.mean(0)
            frames_mean.append(frames_temp.mean(0))
            check_frames.append(abs(mean - mean_overall) + frames_temp.std(0))
        frames_mean = np.array(frames_mean, dtype="float32")
        check_frames = np.array(check_frames, dtype="float32")
        background = np.uint8(
            np.take_along_axis(frames_mean, np.argsort(check_frames, axis=0), axis=0)[0]
        )
        del frames_mean
        del check_frames
        del frames_temp
        gc.collect()
        return background  # type: ignore

    if stable_illumination is True:
        return (
            np.uint8(frames_arr.max(0))
            if animal_vs_bg == AnimalVsBg.ANIMAL_DARKER
            else np.uint8(frames_arr.min(0))
        )  # type:ignore

    if len_frames > 101:
        frames_mean = []
        check_frames = []
        for n in range(0, len_frames - 101, 30):
            frames_temp = frames_arr[n : n + 100]
            mean = frames_temp.mean(0)
            frames_mean.append(mean)
            if animal_vs_bg == 1:
                frames_temp_inv = 255 - frames_temp
                check_frames.append(frames_temp_inv.mean(0) + frames_temp_inv.std(0))
            else:
                check_frames.append(mean + frames_temp.std(0))
        frames_mean = np.array(frames_mean, dtype="float32")
        check_frames = np.array(check_frames, dtype="float32")
        background = np.uint8(
            np.take_along_axis(frames_mean, np.argsort(check_frames, axis=0), axis=0)[0]
        )
        del frames_mean
        del check_frames
        del frames_temp
        gc.collect()
        return background  # type: ignore

    return (
        np.uint8(frames_arr.max(0))
        if animal_vs_bg == AnimalVsBg.ANIMAL_DARKER
        else np.uint8(frames_arr.min(0))
    )  # type: ignore


def extract_backgrounds_from_video(
    path_to_video: str,
    delta: float,
    frame_size: tuple[int, int] | None = None,
    stable_illumination: bool = True,
    start_time: float = 0.0,
    end_time: float | None = None,
    animal_vs_bg: int = AnimalVsBg.ANIMAL_LIGHTER,
) -> tuple[Frame, Frame, Frame]:
    """
    Extracts backgrounds from given video.

    Args:
        path_to_video: The path to the video file.
        delta: The factor by which to compare frame brightness. The mean
            brightness of each frame is compared to the mean brightness of the
            initial frame multiplied by and divided by delta to categorize the
            frame as default, low, or high.
        frame_size: The dimensions (width, height) by which to resize the frame
        stable_illumination: False if background lighting changes for
            optogenetic experiments, else True.
        start_time: The beginning of the time window to start extraction.
        end_time: The end of the time window to stop extraction.
        animal_vs_bg: Whether the animal is lighter or darker than the
            background or whether it's hard to tell; use constants at top of
            tools.py for specific values.

    Returns:
        A tuple (default, low, high) where `default` is the default
        background, `low` is the dim-light background, `high` is the
        bright-light background.

    Raises:
        None
    """
    print("Extracting the static background...")

    BG_TYPES = ["default", "low", "high"]
    capture = cv2.VideoCapture(path_to_video)
    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    initial_frame = None
    lower_threshold = None
    upper_threshold = None

    if start_time >= duration:
        print(
            "The beginning time for background extraction is later than the end of the video!"
        )
        print(
            "Will use the 1st second of the video as the beginning time for background extraction!"
        )
        start_time = 0
    if start_time == end_time:
        end_time = start_time + 1

    # Initialize data storage
    frames = {}
    counts = {}
    background_options = {}
    backgrounds = {}
    for bg_type in BG_TYPES:
        frames[bg_type] = deque(maxlen=1000)
        counts[bg_type] = 0
        background_options[bg_type] = deque(maxlen=1000)
        backgrounds[bg_type] = None

    for frame_number in range(1, frame_count + 1):
        _, frame = capture.read()

        reached_start = frame_number >= start_time * fps
        reached_end = (
            end_time is not None and frame_number >= end_time * fps or frame is None
        )

        if reached_end:
            break

        if not reached_start:
            continue

        if frame_size is not None:
            frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_AREA)

        frame = np.array(frame, dtype=np.uint8)

        if initial_frame is None:
            initial_frame = frame
            lower_threshold = np.mean(initial_frame) / delta
            upper_threshold = np.mean(initial_frame) * delta

        if np.mean(frame) < lower_threshold:  # type: ignore
            frames["low"].append(frame)
            counts["low"] += 1
        elif np.mean(frame) > upper_threshold:  # type: ignore
            frames["high"].append(frame)
            counts["high"] += 1
        else:
            frames["default"].append(frame)
            counts["default"] += 1

        # Extract background if frame buffer has reached 1000 frames
        for bg_type in BG_TYPES:
            if counts[bg_type] == 1001:
                counts[bg_type] = 1
                background = _extract_background(
                    frames[bg_type], stable_illumination, animal_vs_bg
                )
                if background is not None:
                    background_options[bg_type].append(background)

    capture.release()

    for bg_type in BG_TYPES:
        if len(background_options[bg_type]) > 0:
            # Process any remaining frames
            if counts[bg_type] > 600:
                background = _extract_background(
                    frames[bg_type], stable_illumination, animal_vs_bg
                )
                if background is not None:
                    background_options[bg_type].append(background)

            # Pick the best background option
            if len(background_options[bg_type]) == 1:
                backgrounds[bg_type] = background_options[bg_type][0]
            else:
                options = np.array(background_options[bg_type], dtype="uint8")
                if animal_vs_bg == AnimalVsBg.ANIMAL_LIGHTER:
                    backgrounds[bg_type] = options.min(axis=0)
                elif animal_vs_bg == AnimalVsBg.ANIMAL_DARKER:
                    backgrounds[bg_type] = options.max(axis=0)
                elif animal_vs_bg == AnimalVsBg.HARD_TO_TELL:
                    backgrounds[bg_type] = np.median(options, axis=0)
                del options
                gc.collect()
        else:
            backgrounds[bg_type] = _extract_background(
                frames[bg_type], stable_illumination, animal_vs_bg
            )

    if backgrounds["default"] is None:
        background = initial_frame
    if backgrounds["low"] is None:
        backgrounds["low"] = backgrounds["default"]
    if backgrounds["high"] is None:
        backgrounds["high"] = backgrounds["default"]

    print("Background extraction completed!")

    return (backgrounds["default"], backgrounds["low"], backgrounds["high"])  # type: ignore


def load_backgrounds_from_folder(
    folder: str, frame_size: tuple[int, int] | None = None
) -> tuple[Frame, Frame, Frame]:
    """
    Loads background images from given folder, resizing them if required.

    Args:
        folder: The path to the folder containing the background images.
        frame_size: The dimensions (width, height) by which to resize the frame

    Returns:
        A tuple (default, low, high) where `default` is the default
        background, `low` is the dim-light background, `high` is the
        bright-light background.

    Raises:
        None
    """
    default = cv2.imread(os.path.join(folder, "background.jpg"))
    low = cv2.imread(os.path.join(folder, "background_low.jpg"))
    high = cv2.imread(os.path.join(folder, "background_high.jpg"))
    if frame_size is not None:
        default = cv2.resize(default, frame_size, interpolation=cv2.INTER_AREA)
        low = cv2.resize(low, frame_size, interpolation=cv2.INTER_AREA)
        high = cv2.resize(high, frame_size, interpolation=cv2.INTER_AREA)
    return (default, low, high)


def get_stimulation_time(path_to_video: str, delta: float) -> float | None:
    """
    Calculates optogenetic stimulation time from given video.

    Args:
        path_to_video: The path to the video.
        delta: The factor by which to compare frame brightness. The mean
            brightness of each frame is compared to the mean brightness of the
            initial frame multiplied by and divided by delta to categorize the
            frame as default, low, or high.

    Returns:
        The time of the lighting change in seconds, None if no lighting change
        is detected.

    Raises:
        None
    """
    capture = cv2.VideoCapture(path_to_video)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    lower_threshold = None
    upper_threshold = None

    for frame_number in range(1, frame_count + 1):
        _, frame = capture.read()

        if frame is None:
            break
        frame = np.array(frame, dtype="uint8")

        if lower_threshold is None or upper_threshold is None:
            lower_threshold = np.mean(frame) / delta
            upper_threshold = np.mean(frame) * delta

        if np.mean(frame) < lower_threshold:  # type: ignore[reportGeneralTypeIssues]
            capture.release()
            return frame_number / fps
        if np.mean(frame) > upper_threshold:  # type: ignore[reportGeneralTypeIssues]
            capture.release()
            return frame_number / fps

    return None


def estimate_animal_area(
    path_to_video: str,
    delta: float,
    background_default: Frame,
    background_low: Frame,
    background_high: Frame,
    animal_number: int,
    frame_size: tuple[int, int] | None = None,
    stim_t: float | None = None,
    start_time: float | None = None,
    duration: float = 10.0,
    animal_vs_bg: int = AnimalVsBg.ANIMAL_LIGHTER,
    kernel_size: int = 3,
) -> float | None:
    """
    Estimates animal size from a video.

    For all frames within the given time window, the background is subtracted
    and morphological transformations (see https://docs.opencv.org/4.7.0/d9/d61/tutorial_py_morphological_ops.html)
    are applied to fill in any holes within the animal mask. The average area
    of all animals in each frame is divided by the number of animals to return
    average animal size in pixels.

    Args:
        path_to_video: The path to the video.
        delta: The factor by which to compare frame brightness. The mean
            brightness of each frame is compared to the mean brightness of the
            initial frame multiplied by and divided by delta to categorize the
            frame as default, low, or high.
        background_default: The default-lighting background.
        background_low: The low-light background.
        background_high: The bright-light background.
        animal_number: The number of animals present in the video.
        frame_size: The dimensions (width, height) by which to resize the frame
        stim_t: The time in seconds of a lighting change in the video, used
            in optogenetic experiments.
        start_time: The time in seconds at which to start animal size
            estimation.
        duration: The duration in seconds of the animal size estimation.
        animal_vs_bg: Whether the animal is lighter or darker than the
            background or whether it's hard to tell; use constants at top of
            tools.py for specific values.
        kernel_size: The kernel size to use for morphological transformations,
            see https://docs.opencv.org/4.7.0/d9/d61/tutorial_py_morphological_ops.html
            for more information

    Returns:
        The area of the animal in pixels after accounting for frame resizing.

    Raises:
        None
    """
    if animal_number == 0:
        print("Animal number is 0. Please enter the correct animal number!")
        return None

    print("Estimating the animal size...")
    print(datetime.datetime.now())

    capture = cv2.VideoCapture(path_to_video)
    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if start_time is None:
        start_time = stim_t if stim_t is not None else 0.0

    # Cap estimation duration at 30 sec
    if not 0 < duration <= 30:
        duration = 30.0

    end_time = start_time + duration

    min_area = (background_default.shape[1] / 100) * (background_default.shape[0] / 100)
    max_area = (background_default.shape[1] * background_default.shape[0]) * 3 / 4

    background_estimation = background_default
    background_low_estimation = background_low
    background_high_estimation = background_high

    # Make animal lighter than background for morphological transformation
    if animal_vs_bg == AnimalVsBg.ANIMAL_DARKER:
        background_estimation = 255 - background_default  # type: ignore
        background_low_estimation = 255 - background_low  # type: ignore
        background_high_estimation = 255 - background_high  # type: ignore

    lower_threshold = None
    upper_threshold = None
    total_contour_areas = []
    for frame_number in range(1, frame_count + 1):
        _, frame = capture.read()

        reached_start = frame_number >= start_time * fps
        reached_end = (
            end_time is not None and frame_number >= end_time * fps or frame is None
        )
        if reached_end:
            break
        if not reached_start:
            continue

        # Preprocess frame
        if frame_size is not None:
            frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_AREA)
        frame = np.array(frame, dtype=np.uint8)

        # Make animal brighter than background for morphological transformation
        if animal_vs_bg == AnimalVsBg.ANIMAL_DARKER:
            frame = 255 - frame

        if lower_threshold is None or upper_threshold is None:
            lower_threshold = np.mean(frame) / delta
            upper_threshold = np.mean(frame) * delta

        # Select correct background to use
        if np.mean(frame) < lower_threshold:
            background = background_low_estimation
        elif np.mean(frame) > upper_threshold:
            background = background_high_estimation
        else:
            background = background_estimation

        # Subtract background and convert to grayscale
        if animal_vs_bg == AnimalVsBg.HARD_TO_TELL:
            foreground = cv2.absdiff(frame, background)
        else:
            foreground = cv2.subtract(frame, background)
        foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)

        # Extract contours from frame
        _, thred = cv2.threshold(
            foreground, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        thred = cv2.morphologyEx(thred, cv2.MORPH_CLOSE, kernel)
        if animal_vs_bg == AnimalVsBg.HARD_TO_TELL:
            kernel_erode_size = max(kernel_size - 4, 1)
            kernel_erode = np.ones((kernel_erode_size, kernel_erode_size), np.uint8)
            thred = cv2.erode(thred, kernel_erode)
        contours, _ = cv2.findContours(thred, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        # Get total contour area and append to list
        contour_area = 0
        for contour in contours:
            if min_area < cv2.contourArea(contour) < max_area:
                contour_area += cv2.contourArea(contour)
        total_contour_areas.append(contour_area)

    capture.release()

    print("Estimation completed!")

    if len(total_contour_areas) <= 0:
        print("No animal detected!")
        return None

    animal_area = sum(total_contour_areas) / len(total_contour_areas) / animal_number
    print(f"Single animal size: {animal_area}")
    return animal_area


def crop_frame(frame, contours):
    lfbt = np.array(
        [contours[i].min(0) for i in range(len(contours)) if contours[i] is not None]
    ).min(0)[0]
    x_lf = lfbt[0]
    y_bt = lfbt[1]
    rttp = np.array(
        [contours[i].max(0) for i in range(len(contours)) if contours[i] is not None]
    ).max(0)[0]
    x_rt = rttp[0]
    y_tp = rttp[1]

    w = x_rt - x_lf + 1
    h = y_tp - y_bt + 1

    difference = int(abs(w - h) / 2) + 1

    if w > h:
        y_bt = max(y_bt - difference - 1, 0)
        y_tp = min(y_tp + difference + 1, frame.shape[0])
        x_lf = max(x_lf - 1, 0)
        x_rt = min(x_rt + 1, frame.shape[1])
    if w < h:
        y_bt = max(y_bt - 1, 0)
        y_tp = min(y_tp + 1, frame.shape[0])
        x_lf = max(x_lf - difference - 1, 0)
        x_rt = min(x_rt + difference + 1, frame.shape[1])

    return (y_bt, y_tp, x_lf, x_rt)


def extract_blob(frame, contour, channel=1):
    mask = np.zeros_like(frame)

    cv2.drawContours(mask, [contour], 0, (255, 255, 255), -1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    x, y, w, h = cv2.boundingRect(contour)
    difference = int(abs(w - h) / 2) + 1

    if w > h:
        y_bt = max(y - difference - 1, 0)
        y_tp = min(y + h + difference + 1, frame.shape[0])
        x_lf = max(x - 1, 0)
        x_rt = min(x + w + 1, frame.shape[1])
    else:
        y_bt = max(y - 1, 0)
        y_tp = min(y + h + 1, frame.shape[0])
        x_lf = max(x - difference - 1, 0)
        x_rt = min(x + w + difference + 1, frame.shape[1])

    masked_frame = frame * (mask / 255.0)
    blob = masked_frame[y_bt:y_tp, x_lf:x_rt]
    blob = np.uint8(exposure.rescale_intensity(blob, out_range=(0, 255)))

    if channel == 1:
        blob = cv2.cvtColor(blob, cv2.COLOR_BGR2GRAY)
        blob = img_to_array(blob)

    return blob


def extract_blob_background(
    frame, contours, contour=None, channel=1, background_free=False
):
    (y_bt, y_tp, x_lf, x_rt) = crop_frame(frame, contours)
    if background_free is True:
        mask = np.zeros_like(frame)
        cv2.drawContours(mask, [contour], 0, (255, 255, 255), -1)
        masked_frame = frame * (mask / 255.0)
    else:
        masked_frame = frame
    blob = masked_frame[y_bt:y_tp, x_lf:x_rt]
    blob = np.uint8(exposure.rescale_intensity(blob, out_range=(0, 255)))

    if channel == 1:
        blob = cv2.cvtColor(blob, cv2.COLOR_BGR2GRAY)
        blob = img_to_array(blob)

    return blob


def extract_blob_all(
    frame, y_bt, y_tp, x_lf, x_rt, contours=None, channel=1, background_free=False
):
    if background_free is True:
        mask = np.zeros_like(frame)
        cv2.drawContours(mask, contours, -1, (255, 255, 255), -1)
        masked_frame = frame * (mask / 255.0)
    else:
        masked_frame = frame
    blob = masked_frame[y_bt:y_tp, x_lf:x_rt]
    blob = np.uint8(exposure.rescale_intensity(blob, out_range=(0, 255)))

    if channel == 1:
        blob = cv2.cvtColor(blob, cv2.COLOR_BGR2GRAY)
        blob = img_to_array(blob)

    return blob


def get_inner(masked_frame_gray, contour):
    blur = cv2.GaussianBlur(masked_frame_gray, (3, 3), 0)
    edges = cv2.Canny(blur, 20, 75, apertureSize=3, L2gradient=True)
    cnts, _ = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

    if len(cnts) > 3:
        inner = sorted(cnts, key=cv2.contourArea, reverse=True)[2:]
    else:
        inner = [contour, contour]

    return inner


def contour_frame(
    frame,
    animal_number,
    background,
    background_low,
    background_high,
    delta,
    contour_area,
    animal_vs_bg=0,
    include_bodyparts=False,
    animation_analyzer=False,
    channel=1,
    kernel=5,
):
    if animal_vs_bg == 1:
        frame = np.uint8(255 - frame)

    if np.mean(frame) < np.mean(background) / delta:
        if animal_vs_bg == 2:
            foreground = cv2.absdiff(frame, background_low)
        else:
            foreground = cv2.subtract(frame, background_low)
    elif np.mean(frame) > delta * np.mean(background):
        if animal_vs_bg == 2:
            foreground = cv2.absdiff(frame, background_high)
        else:
            foreground = cv2.subtract(frame, background_high)
    else:
        if animal_vs_bg == 2:
            foreground = cv2.absdiff(frame, background)
        else:
            foreground = cv2.subtract(frame, background)

    foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
    thred = cv2.threshold(foreground, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    thred = cv2.morphologyEx(
        thred, cv2.MORPH_CLOSE, np.ones((kernel, kernel), np.uint8)
    )
    if animal_vs_bg == 2:
        kernel_erode = max(kernel - 4, 1)
        thred = cv2.erode(thred, np.ones((kernel_erode, kernel_erode), np.uint8))
    cnts, _ = cv2.findContours(thred, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    contours = []
    centers = []
    heights = []
    inners = []
    blobs = []

    if animal_number > 1:
        for i in cnts:
            if contour_area * 0.2 < cv2.contourArea(i) < contour_area * 1.5:
                contours.append(i)
        contours = sorted(contours, key=cv2.contourArea)[-animal_number:]
    else:
        contours = [sorted(cnts, key=cv2.contourArea, reverse=True)[0]]

    if len(contours) > 0:
        for i in contours:
            centers.append(
                (
                    int(cv2.moments(i)["m10"] / cv2.moments(i)["m00"]),
                    int(cv2.moments(i)["m01"] / cv2.moments(i)["m00"]),
                )
            )
            (_, _), (w, h), _ = cv2.minAreaRect(i)
            heights.append(max(w, h))
            if include_bodyparts is True:
                mask = np.zeros_like(frame)
                cv2.drawContours(mask, [i], 0, (255, 255, 255), -1)
                mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
                masked_frame = frame * (mask / 255)
                gray = cv2.cvtColor(np.uint8(masked_frame), cv2.COLOR_BGR2GRAY)
                inners.append(get_inner(gray, i))
            if animation_analyzer is True:
                blobs.append(extract_blob(frame, i, channel=channel))

    return (contours, centers, heights, inners, blobs)


def generate_patternimage(frame, outlines, inners=None, std=0):
    if inners is not None:
        background_inners = np.zeros_like(frame)
        background_outers = np.zeros_like(frame)

    background_outlines = np.zeros_like(frame)

    if std > 0:
        backgrounds_std = []

    (y_bt, y_tp, x_lf, x_rt) = crop_frame(frame, outlines)

    length = len(outlines)
    p_size = int(max(abs(y_bt - y_tp), abs(x_lf - x_rt)) / 150 + 1)

    for n, outline in enumerate(outlines):
        if outline is not None:
            if std > 0:
                background_std = np.zeros_like(frame)
                if inners is not None:
                    cv2.drawContours(background_std, inners[n], -1, (255, 255, 255), -1)
                    backgrounds_std.append(background_std)

            if n < length / 4:
                d = n * int((255 * 4 / length))
                cv2.drawContours(background_outlines, [outline], 0, (255, d, 0), p_size)
                if inners is not None:
                    cv2.drawContours(
                        background_inners, inners[n], -1, (255, d, 0), p_size
                    )
            elif n < length / 2:
                d = int((n - length / 4) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255, 255, d), p_size
                )
                if inners is not None:
                    cv2.drawContours(
                        background_inners, inners[n], -1, (255, 255, d), p_size
                    )
            elif n < 3 * length / 4:
                d = int((n - length / 2) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255, 255 - d, 255), p_size
                )
                if inners is not None:
                    cv2.drawContours(
                        background_inners, inners[n], -1, (255, 255 - d, 255), p_size
                    )
            else:
                d = int((n - 3 * length / 4) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255 - d, 0, 255), p_size
                )
                if inners is not None:
                    cv2.drawContours(
                        background_inners, inners[n], -1, (255 - d, 0, 255), p_size
                    )

            if inners is not None:
                cv2.drawContours(
                    background_outers, [outline], 0, (255, 255, 255), int(2 * p_size)
                )

    outlines_image = background_outlines[y_bt:y_tp, x_lf:x_rt]

    if inners is not None:
        inners_image = background_inners[y_bt:y_tp, x_lf:x_rt]
        outers_image = background_outers[y_bt:y_tp, x_lf:x_rt]
        inners_image = cv2.subtract(inners_image, outers_image)

    if std > 0:
        backgrounds_std = np.array(backgrounds_std, dtype="float32")
        std_images = backgrounds_std[:, y_bt:y_tp, x_lf:x_rt]
        std_image = std_images.std(0)

        inners_image[std_image < std] = 0

    if inners is not None:
        pattern_image = cv2.add(inners_image, outlines_image)
    else:
        pattern_image = outlines_image

    return pattern_image


def generate_patternimage_all(
    frame, y_bt, y_tp, x_lf, x_rt, outlines_list, inners_list, std=0
):
    inners_length = len(inners_list[0])

    if inners_length > 0:
        background_inners = np.zeros_like(frame)
        background_outers = np.zeros_like(frame)

    background_outlines = np.zeros_like(frame)

    if std > 0:
        backgrounds_std = []

    length = len(outlines_list)
    p_size = int(max(abs(y_bt - y_tp), abs(x_lf - x_rt)) / 150 + 1)

    for n, outlines in enumerate(outlines_list):
        if std > 0:
            background_std = np.zeros_like(frame)
            if inners_length > 0:
                for inners in inners_list[n]:
                    cv2.drawContours(background_std, inners, -1, (255, 255, 255), -1)
                backgrounds_std.append(background_std)

        if n < length / 4:
            d = n * int((255 * 4 / length))
            cv2.drawContours(background_outlines, outlines, -1, (255, d, 0), p_size)
            if inners_length > 0:
                for inners in inners_list[n]:
                    cv2.drawContours(background_inners, inners, -1, (255, d, 0), p_size)
        elif n < length / 2:
            d = int((n - length / 4) * (255 * 4 / length))
            cv2.drawContours(background_outlines, outlines, -1, (255, 255, d), p_size)
            if inners_length > 0:
                for inners in inners_list[n]:
                    cv2.drawContours(
                        background_inners, inners, -1, (255, 255, d), p_size
                    )
        elif n < 3 * length / 4:
            d = int((n - length / 2) * (255 * 4 / length))
            cv2.drawContours(
                background_outlines, outlines, -1, (255, 255 - d, 255), p_size
            )
            if inners_length > 0:
                for inners in inners_list[n]:
                    cv2.drawContours(
                        background_inners, inners, -1, (255, 255 - d, 255), p_size
                    )
        else:
            d = int((n - 3 * length / 4) * (255 * 4 / length))
            cv2.drawContours(
                background_outlines, outlines, -1, (255 - d, 0, 255), p_size
            )
            if inners_length > 0:
                for inners in inners_list[n]:
                    cv2.drawContours(
                        background_inners, inners, -1, (255 - d, 0, 255), p_size
                    )

        if inners_length > 0:
            cv2.drawContours(
                background_outers, outlines, -1, (255, 255, 255), int(2 * p_size)
            )

    outlines_image = background_outlines[y_bt:y_tp, x_lf:x_rt]

    if inners_length > 0:
        inners_image = background_inners[y_bt:y_tp, x_lf:x_rt]
        outers_image = background_outers[y_bt:y_tp, x_lf:x_rt]
        inners_image = cv2.subtract(inners_image, outers_image)

    if std > 0:
        backgrounds_std = np.array(backgrounds_std, dtype="float32")
        std_images = backgrounds_std[:, y_bt:y_tp, x_lf:x_rt]
        std_image = std_images.std(0)

        inners_image[std_image < std] = 0

    if inners_length > 0:
        pattern_image = cv2.add(inners_image, outlines_image)
    else:
        pattern_image = outlines_image

    return pattern_image


def generate_patternimage_interact(
    frame, outlines, other_outlines, inners=None, other_inners=None, std=0
):
    total_outlines = functools.reduce(operator.iconcat, other_outlines, [])
    total_outlines += outlines
    (y_bt, y_tp, x_lf, x_rt) = crop_frame(frame, total_outlines)

    if inners is not None:
        background_inners = np.zeros_like(frame)
        background_outers = np.zeros_like(frame)

    background_outlines = np.zeros_like(frame)

    if std > 0:
        backgrounds_std = []

    length = len(outlines)
    p_size = int(max(abs(y_bt - y_tp), abs(x_lf - x_rt)) / 150 + 1)

    for n, outline in enumerate(outlines):
        other_outline = other_outlines[n]
        if len(other_outline) > 0:
            if other_outline[0] is not None:
                cv2.drawContours(
                    background_outlines, other_outline, -1, (150, 150, 150), p_size
                )

        if outline is not None:
            if inners is not None:
                inner = inners[n]
                other_inner = functools.reduce(operator.iconcat, other_inners[n], [])
                if other_inner is not None:
                    cv2.drawContours(
                        background_inners, other_inner, -1, (150, 150, 150), p_size
                    )
                if std > 0:
                    background_std = np.zeros_like(frame)
                    if inner is not None:
                        cv2.drawContours(background_std, inner, -1, (255, 255, 255), -1)
                    if other_inner is not None:
                        cv2.drawContours(
                            background_std, other_inner, -1, (255, 255, 255), -1
                        )
                    backgrounds_std.append(background_std)
            else:
                inner = None

            if n < length / 4:
                d = n * int((255 * 4 / length))
                cv2.drawContours(background_outlines, [outline], 0, (255, d, 0), p_size)
                if inner is not None:
                    cv2.drawContours(background_inners, inner, -1, (255, d, 0), p_size)
            elif n < length / 2:
                d = int((n - length / 4) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255, 255, d), p_size
                )
                if inner is not None:
                    cv2.drawContours(
                        background_inners, inner, -1, (255, 255, d), p_size
                    )
            elif n < 3 * length / 4:
                d = int((n - length / 2) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255, 255 - d, 255), p_size
                )
                if inner is not None:
                    cv2.drawContours(
                        background_inners, inner, -1, (255, 255 - d, 255), p_size
                    )
            else:
                d = int((n - 3 * length / 4) * (255 * 4 / length))
                cv2.drawContours(
                    background_outlines, [outline], 0, (255 - d, 0, 255), p_size
                )
                if inner is not None:
                    cv2.drawContours(
                        background_inners, inner, -1, (255 - d, 0, 255), p_size
                    )

            if inners is not None:
                cv2.drawContours(
                    background_outers, [outline], 0, (255, 255, 255), int(2 * p_size)
                )
                if len(other_outline) > 0:
                    if other_outline[0] is not None:
                        cv2.drawContours(
                            background_outers,
                            other_outline,
                            -1,
                            (150, 150, 150),
                            int(2 * p_size),
                        )

    outlines_image = background_outlines[y_bt:y_tp, x_lf:x_rt]

    if inners is not None:
        inners_image = background_inners[y_bt:y_tp, x_lf:x_rt]
        outers_image = background_outers[y_bt:y_tp, x_lf:x_rt]
        inners_image = cv2.subtract(inners_image, outers_image)

    if std > 0:
        backgrounds_std = np.array(backgrounds_std, dtype="float32")
        std_images = backgrounds_std[:, y_bt:y_tp, x_lf:x_rt]
        std_image = std_images.std(0)

        inners_image[std_image < std] = 0

    if inners is not None:
        pattern_image = cv2.add(inners_image, outlines_image)
    else:
        pattern_image = outlines_image

    return pattern_image


def plot_evnets(
    result_path,
    event_probability,
    time_points,
    names_and_colors,
    behavior_to_include,
    width=0,
    height=0,
):
    print("Exporting the raster plot for this analysis batch...")
    print(datetime.datetime.now())

    if width == 0 or height == 0:
        time_length = len(time_points)
        if time_length > 30000:
            width = round(time_length / 3000) + 1
            x_intvl = 3000
        elif time_length > 3000:
            width = round(time_length / 300) + 1
            x_intvl = 300
        else:
            width = round(time_length / 30) + 1
            x_intvl = 30
        height = round(len(event_probability) / 4) + 1
        if height < 3:
            height = 3
        figure, ax = plt.subplots(figsize=(width, height))
        if height <= 5:
            figure.subplots_adjust(bottom=0.25)

    for behavior_name in behavior_to_include:
        all_data = []
        masks = []

        for i in event_probability:
            data = []
            mask = []
            for n in range(len(event_probability[i])):
                if event_probability[i][n][0] == behavior_name:
                    data.append(event_probability[i][n][1])
                    mask.append(0)
                else:
                    data.append(-1)
                    mask.append(True)
            all_data.append(data)
            masks.append(mask)

        all_data = np.array(all_data)
        masks = np.array(masks)
        dataframe = pd.DataFrame(
            all_data, columns=[float("{:.1f}".format(i)) for i in time_points]
        )

        heatmap = sb.heatmap(
            dataframe,
            mask=masks,
            xticklabels=x_intvl,
            cmap=LinearSegmentedColormap.from_list("", names_and_colors[behavior_name]),
            cbar=False,
            vmin=0,
            vmax=1,
        )
        heatmap.set_xticklabels(heatmap.get_xticklabels(), rotation=90)
        # no ticks
        # ax.tick_params(axis='both',which='both',length=0)

    plt.savefig(os.path.join(result_path, "behaviors_plot.png"))

    for behavior_name in behavior_to_include:
        colorbar_fig = plt.figure(figsize=(5, 1))
        ax = colorbar_fig.add_axes([0, 1, 1, 1])
        colorbar = ColorbarBase(
            ax,
            orientation="horizontal",
            cmap=LinearSegmentedColormap.from_list("", names_and_colors[behavior_name]),
            norm=Normalize(vmin=0, vmax=1),
            ticks=[],
        )
        colorbar.outline.set_linewidth(0)

        plt.savefig(
            os.path.join(result_path, behavior_name + "_colorbar.png"),
            bbox_inches="tight",
        )
        plt.close()

    plt.close("all")

    print("The raster plot stored in: " + str(result_path))


def extract_frames(
    path_to_video, out_path, framewidth=None, start_t=0, duration=0, skip_redundant=1000
):
    capture = cv2.VideoCapture(path_to_video)
    fps = round(capture.get(cv2.CAP_PROP_FPS))
    full_duration = capture.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    video_name = os.path.splitext(os.path.basename(path_to_video))[0]

    if start_t >= full_duration:
        print("The beginning time is later than the end of the video!")
        print("Will use the beginning of the video as the beginning time!")
        start_t = 0
    if duration <= 0:
        duration = full_duration
    end_t = start_t + duration

    frame_count = 1
    frame_count_generate = 0

    while True:
        retval, frame = capture.read()
        t = (frame_count) / fps
        if frame is None:
            break
        if t >= end_t:
            break

        if t >= start_t:
            if frame_count_generate % skip_redundant == 0:
                if framewidth is not None:
                    frameheight = int(frame.shape[0] * framewidth / frame.shape[1])
                    frame = cv2.resize(
                        frame, (framewidth, frameheight), interpolation=cv2.INTER_AREA
                    )

                cv2.imwrite(
                    os.path.join(
                        out_path, video_name + "_" + str(frame_count_generate) + ".jpg"
                    ),
                    frame,
                )

            frame_count_generate += 1

        frame_count += 1

    capture.release()

    print("The image examples stored in: " + out_path)


def preprocess_video(
    path_to_video: str,
    out_folder: str,
    framewidth: int | None,
    trim_video: bool = False,
    time_windows: list[Tuple[float, float]] = [(0, 10)],
    enhance_contrast: bool = True,
    contrast: float = 1.0,
    crop_frame: bool = True,
    left: int = 0,
    right: int = 0,
    top: int = 0,
    bottom: int = 0,
    fps_reduction_factor: float = 1.0,
):
    """
    Preprocess the given video for faster model training.

    Args:
        path_to_video: The path to the video to process.
        out_folder: The folder in which to store the processed video.
        framewidth: The width of the frame after resizing.
        trim_video: Whether or not to apply the given time windows.
        time_windows: A list of lists, where each inner list is of format
            [start, end] and indicates the start time and end time of a
            subsection of the video to include in preprocessing.
        enhance_contrast: Whether or not to enhance the contrast of the video.
            NOTE: The current implementation doesn't actually increase the
            contrast -- instead, it increases the brightness. This feature will
            need to be rewritten at some point.
        contrast: The factor by which to increase the brightness (see NOTE
            above for explanation).
        crop_frame: Whether or not to crop the video.
        left: The left coordinate to crop at.
        right: The right coordinate to crop at.
        top: The top coordinate to crop at.
        bottom: The bottom coordinate to crop at.
        fps_reduction_factor: The factor by which to reduce the FPS of the
            video. For example, if the video is originally at 60 FPS and
            fps_reduction_factor is 4, then the new video will be scaled down
            to 15 FPS while maintaining the same duration.

    Returns:
        None. The processed videos will be stored in `out_folder`.

    Raises:
        None
    """

    # Get video and metadata
    capture = cv2.VideoCapture(path_to_video)
    name = os.path.basename(path_to_video).split(".")[0]
    fps = round(capture.get(cv2.CAP_PROP_FPS))
    num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # Calculate width and height if necessary
    if framewidth is not None:
        height = framewidth * height / width
        width = framewidth

    # Add video windows to filename if necessary
    added_name = ""
    if trim_video is True:
        for start, end in time_windows:
            added_name += "_" + str(start) + "-" + str(end)

    # Create VideoWriter with given parameters
    writer = cv2.VideoWriter(
        filename=os.path.join(out_folder, name + added_name + "_processed.avi"),
        fourcc=cv2.VideoWriter_fourcc(*"MJPG"),  # type: ignore
        fps=fps / fps_reduction_factor,
        frameSize=(int(width), int(height)),
        isColor=True,
    )

    # Get the indices of all dropped frames
    dropped_frames = get_dropped_frames(num_frames, fps_reduction_factor)

    frame_count = 0
    while True:
        frame_count += 1

        ret, frame = capture.read()
        if frame is None:
            break

        if frame_count - 1 in dropped_frames:
            continue

        # Apply preprocessing to the frame
        if framewidth is not None:
            frame = cv2.resize(
                frame,
                (int(width), int(height)),
                interpolation=cv2.INTER_AREA,
            )
        if crop_frame is True:
            frame = frame[top:bottom, left:right, :]
        if enhance_contrast is True:
            frame = frame * contrast  # type: ignore
            frame[frame > 255] = 255

        # Add frame to video file
        frame = np.uint8(frame)  # type: ignore
        if trim_video is True:
            t = frame_count / fps
            for start, end in time_windows:
                if start <= t <= end:
                    writer.write(frame)  # type: ignore
        else:
            writer.write(frame)  # type: ignore

    writer.release()
    capture.release()

    print("The processed video(s) stored in: " + out_folder)


def get_dropped_frames(n: int, reduction_factor: float) -> list[int]:
    """
    Return a list of indices of frames to be dropped after an FPS reduction

    Args:
        n: The number of frames in the original video.
        reduction_factor: The FPS reduction factor, where the new FPS is
            calculated using new_fps = old_fps / reduction_factor.

    Returns:
        A list of indices of frames to be dropped.

    Raises:
        None
    """
    if n <= 1.0:
        return []
    num_dropped_frames = int(n * (1 - 1 / reduction_factor))
    block_size = n / (n * (1 - 1 / reduction_factor) - 1)
    return [round(block_size * i) for i in range(num_dropped_frames)]
