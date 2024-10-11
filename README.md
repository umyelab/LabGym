# LabGym: quantifying user-defined behaviors

[![PyPI - Version](https://img.shields.io/pypi/v/LabGym)](https://pypi.org/project/LabGym/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/LabGym)](https://pypi.org/project/LabGym/)
[![Downloads](https://static.pepy.tech/badge/LabGym)](https://pepy.tech/project/LabGym)
[![Documentation Status](https://readthedocs.org/projects/labgym/badge/?version=latest)](https://labgym.readthedocs.io/en/latest/?badge=latest)

<p>&nbsp;</p>

<!-- start elevator-pitch -->

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/LabGym_logo.png?raw=true)

<p>&nbsp;</p>

## Identifies social behaviors in multi-individual interactions

<p>&nbsp;</p>

**Distinguishing different social roles of multiple similar-looking interacting individuals**

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_multi_individual_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_multi_individual_2.gif?raw=true)

<p>&nbsp;</p>

**Distinguishing different interactive behaviors among multiple animal-object interactions**

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_animal_object_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_animal_object_2.gif?raw=true)

<p>&nbsp;</p>

**Distinguishing different social roles of animals in the field with unstable recording environments**

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_wild_animal_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_wild_animal_2.gif?raw=true)

<p>&nbsp;</p>

## Identifies non-social behaviors

<p>&nbsp;</p>

**Identifying behaviors in diverse species in various recording environments**

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_social_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_social_2.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_social_3.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_social_4.gif?raw=true)

<p>&nbsp;</p>

**Identifying behaviors with no posture changes such as cells 'changing color' and neurons 'firing'**

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_posture_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_posture_2.gif?raw=true)

<p>&nbsp;</p>

## Quantifies each user-defined behavior

Computes a range of motion and kinematics parameters for each behavior. The parameters include **count**, **duration**, and **latency** of behavioral incidents, as well as **speed**, **acceleration**, **distance traveled**, and the **intensity** and **vigor** of motions during the behaviors. These parameters are output in spreadsheets.

Also provides visualization of analysis results, including annotated videos/images that visually mark each behavior event, temporal raster plots that show every behavior event of every individual overtime.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify_behavior.jpg?raw=true)

<p>&nbsp;</p>

A tutorial video for a high-level understanding of what LabGym can do and how it works:

[![Watch the video](https://img.youtube.com/vi/YoYhHMPbf_o/hqdefault.jpg)](https://youtu.be/YoYhHMPbf_o)

Cite LabGym: [LabGym 1.x](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) & [LabGym 2.x](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1)

<p>&nbsp;</p>

<!-- end elevator-pitch -->

# How to use LabGym?

## Overview

You can use LabGym via its user interface (no coding knowledge needed), or via command prompt. See [**Extended User Guide**](https://github.com/yujiahu415/LabGym/blob/master/LabGym_extended_user_guide.pdf) for details. 

If the extended user guide is difficult to follow, see this [**Practical "How To" Guide**](https://github.com/yujiahu415/LabGym/blob/master/LabGym_practical_guide.pdf) with layman language and examples.

<p>&nbsp;</p>

***Put your mouse cursor above each button in the user interface to see a detailed description for it***.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User_interface.jpg?raw=true)

<p>&nbsp;</p>

LabGym comprises three modules, each tailored to streamline the analysis process. Together, these modules create a cohesive workflow, enabling users to prepare, train, and analyze their behavioral data with accuracy and ease.

1. **'Preprocessing Module'**: This module is for optimizing video footage for analysis. It can trim videos to focus solely on the necessary time windows, crop frames to remove irrelevant regions, enhance video contrast to make the relevant details more discernible, reduce video fps to increase processing speed, or draw colored markers in videos to mark specific locations.

2. **'Training Module'**: Here, you can customize LabGym according to your specific research needs. You can train a Detector in this module to detect animals or objects of your interest in videos/images. You can also train a Categorizer to recognize specific behaviors that are defined by you.

3. **'Analysis Module'**: After customizing LabGym to your need, you can use this module for automated behavioral analysis in videos/images. It not only outputs comprehensive analysis results but also delves into these results to mine significant findings.

<p>&nbsp;</p>

## Usage Step 1: detect animals/objects

LabGym employs two distinct methods for detecting animals or objects in different scenarios.

<p>&nbsp;</p>

### 1. Subtract background

This method is fast and accurate but requires stable illumination and static background in videos to analysis. It does not require training neural networks, but you need to define a time window during which the animals are in motion for effective background extraction. A shorter time window leads to quicker processing. Typically, a duration of 10 to 30 seconds is adequate.

***How to select an appropriate time window for background extraction?***

To determine the optimal time window for background extraction, consider the animal's movement throughout the video. In the example below, in a 60-second video, selecting a 20-second window where the mouse moves frequently and covers different areas is ideal. The following three images are backgrounds extracted using the time windows of the first, second, and last 20 seconds, respectively. In the first and last 20 seconds, the mouse mostly stays either in left or right side and moves little and the extracted backgrounds contain animal trace, which is not ideal. In the second 20 seconds, the mouse frequently moves around and the extracted background is perfect:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

<p>&nbsp;</p>

### 2. Use trained Detectors

This method incorporates [Detectron2](https://github.com/facebookresearch/detectron2), offering more versatility but at a slower processing speed compared to the **‘Subtract Background’** method. It excels in differentiating individual animals or objects, even during collisions, which is particularly beneficial for the **'Interactive advanced'** mode. To enhance processing speed, use a GPU or reduce the frame size during analysis. To train a **Detector** in **‘Training Module’**: 

   1. Click the **‘Generate Image Examples’** button to extract image frames from videos.
   2. Use free online annotation tools like [Roboflow](https://roboflow.com) to annotate the outlines of animals or objects in these images. For annotation type, choose 'Instance Segmentation', and export the annotations in 'COCO instance segmentation' format, which generates a ‘*.json’ file. Importantly, when you generate a version of dataset, do NOT perform any preprocessing steps such as ‘auto orient’ and ‘resize (stretch)’. Instead, perform some augmentation based on which manipulations may occur in real scenarios.
   3. Use the **‘Train Detectors’** button to input these annotated images and commence training your **Detectors**.

<p>&nbsp;</p>

## Usage Step 2: identify and quantify behaviors

LabGym is equipped with four distinct modes of behavior identification to suit different scenarios.

<p>&nbsp;</p>

### 1. Interactive advanced

This mode is for analyzing the behavior of every individual in a group of animals or objects, such as a finger 'holding' or 'offering' a peanut, a chipmunk 'taking' or 'loading' a peanut, and a peanut 'being held', 'being taken', or 'being loaded'.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_interactive_advanced.gif?raw=true)

To train a **Categorizer** of this mode, you can sort the behavior examples (**Animation** and **Pattern Image**) according to the behaviors/social roles of the 'main character' highlighted in a magenta-color-coded 'spotlight'. In the four pairs of behavior examples below, behaviors are 'taking the offer', 'being taken', 'being held', and 'offering peanut', respectively.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Behavior_examples_interactive_advanced.gif?raw=true)

<p>&nbsp;</p>

### 2. Interactive basic

Optimized for speed, this mode considers the entire interactive group (2 or more individuals) as an entity, streamlining the processing time compared to the **'Interactive advanced'** mode. It is ideal for scenarios where individual behaviors within the group are uniform or when the specific actions of each member are not the primary focus of the study, such as 'licking' and 'attempted copulation' (where we only need to identify behaviors of the male fly).

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_interactive_basic.gif?raw=true)

To train a **Categorizer** of this mode, you can sort the behavior examples (**Animation** and **Pattern Image**) according to the behaviors of the entire interacting group or the individual of primary focus of the study. In the 3 pairs of behavior examples below, behaviors are behaviors like 'orientating', 'singing while licking', and 'attempted copulation', respectively.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Behavior_examples_interactive_basic.gif?raw=true)

<p>&nbsp;</p>

### 3. Non-interactive

This mode is for identifying solitary behaviors of individuals that are not engaging in interactive activities.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_non_interactive.gif?raw=true)

To train a **Categorizer** of this mode, you can sort the behavior examples (**Animation** and **Pattern Image**) according to the behaviors of individuals.

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Behavior_examples_non_interactive.gif?raw=true)

<p>&nbsp;</p>

### 4. Static image

This mode is for identifying solitary behaviors of individuals in static images.

<p>&nbsp;</p>

## [Installation](https://labgym.readthedocs.io/en/latest/installation/index.html)

## [LabGym Zoo (trained models and training examples)](https://github.com/umyelab/LabGym/blob/master/LabGym_Zoo.md)

## [Reporting Issues](https://labgym.readthedocs.io/en/latest/issues.html)

## [Changelog](https://labgym.readthedocs.io/en/latest/changelog.html)

## [Contributing](https://labgym.readthedocs.io/en/latest/contributing/index.html)
