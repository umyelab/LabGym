# LabGym: a platform for analyzing user-defined behaviors

1. **IDENTIFY** behaviors without restrictions on **behavior types** / **animal species** / **recording environments**. Such as:

    * Which individual does what in complex interactive behaviors, like a finger 'holds peanut' / 'offers peanut', a chipmunk 'takes the offer' / 'loads peanut', and a peanut 'being held' / 'being taken' / 'being loaded'. Or, which fly sings a love song and which fly is being courted in a courtship interactive group.

        ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_1.gif?raw=true)

    * Behaviors of the whole interactive group can be analyzed as one for faster processing speed, if you don't care about which individual does what.

        ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_2.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_2.gif?raw=true)

    * Non-interactive behaviors of individuals.

        ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_1.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_2.gif?raw=true)

        ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_larvae.gif?raw=true)    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats.gif?raw=true)

<p>&nbsp;</p>

2. **QUANTIFY** diverse motion / kinematics parameters for each behavior, such as **count**, **duration**, **latency** of a behavior, and **speed**, **acceleration**, **distance traveled**, **motion vigor**, **motion intensity** during a behavior. It outputs annotated videos and a temporal raster plot for every behavior event for each animal at each frame in an analysis batch, and spread sheets for storing the calculated behavioral parameters:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior.jpg?raw=true)

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Analysis_output.jpg?raw=true)

<p>&nbsp;</p>

3. **MINE** the analysis results to display significant findings, such as the behavioral parameters that show statistically significant difference among different groups, and then show the data details:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Results_mining.jpg?raw=true)

<p>&nbsp;</p>

4. **NO NEED** of writing code, **NO NEED** of GPU (but can be even faster with NVIDIA GPUs and CUDA toolkit installed).

<p>&nbsp;</p>

Cite LabGym: https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7.

<p>&nbsp;</p>

# How to use LabGym?

Extended user guide: (https://github.com/yujiahu415/LabGym/blob/master/LabGym%20user%20guide_v2.0.pdf).

***Put your mouse cursor above each button in the user interface to see a detailed description for it***.

<p>&nbsp;</p>

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User%20interface.jpg?raw=true)

<p>&nbsp;</p>

**'Preprocessing Module'** enhances video contrast / trims videos to include only necessary time windows / crops frames to exclude unnecessary regions.

**'Training Module'** is for you to teach LabGym to detect animals / objects of your interest, and to recognize behaviors that are defined by you.

**'Analysis Module'** analyzes videos, outputs annotated video copies with behavior names (and %confidence) marked in colors selected by you, calculates diverse behavioral parameters to provide **quantitative measurements** of the intensity and kinematics for each behavior, and mines analysis results to display the significant findings.

<p>&nbsp;</p>

## Teaching LabGym

To **QUANTIFY** behaviors, LabGym first needs to **IDENTIFY** them. To teach LabGym to recognize behaviors defined by you, use **'Generate Behavior Examples'** functional unit to generate stand-alone behavior examples and sort them based on their types. Then input the sorted examples into **'Train Categorizers'** functional unit to train a **Categorizer**. Each behavior example is a pair of a short **Animation** and its paired **Pattern Image**, which spans a duration (a behavior episode) defined by you. There are three types of behavior examples:

1. **'Interactive advance'** tells which individual does what in complex interactive behaviors. Each 'spotlight' **Animation** / **Pattern Image** contains all 'characters' in an interactive group with a 'spotlight' on the main character. Sort them based on the behavior type of the main character. The below 4 examples have 4 different main characters: a chipmunk taking the offer; a peanut being taken; another peanut being held; a finger offering peanut.

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Chipmunks.gif?raw=true)

2. **'Interactive basic'** tells the behaviors of the whole interactive group. If you don't care about which individual does what in an interaction, select this for faster processing speed. Each **Animation** / **Pattern Image** contains all the animals / objects of your interest in a video. Sort them as one. For example, if you only care about what the male does in a courtship interaction, the below 3 can be sorted as: male fly orientating; male fly singing while licking; male fly attempted copulation.

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Flies.gif?raw=true)

3. **'Non-interactive'** tells the behaviors of individuals. Each **Animation** / **Pattern Image** is a 'monodrama' of each animal / object in a video.

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Mice.gif?raw=true)

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Larvae.gif?raw=true)

<p>&nbsp;</p>

To **GENERATE** behavior examples or to **IDENTIFY** behaviors, LabGym needs to detect the animals / objects. There are two detection methods in LabGym to fit different scenarios:

1. **Background subtraction** -based method is fast and accurate and is the first choice for videos with static background and stable illumination. No training is needed but you need to specify a time window during which animals are moving, for background extraction.

    ***How to select an appropriate time window for background extraction?***

    Shorter time window = faster processing speed. 10 to 30 seconds are sufficient. Here is an example showing how selections of different time windows would affect the background extraction.

    The video is of 60 seconds. The following three images are backgrounds extracted using the time windows of the first, second, and last 20 seconds, respectively. In the first and last 20 seconds, the mouse mostly stays either in left or right side and moves little and the extracted backgrounds contain animal trace, which is not ideal. In the second 20 seconds, the mouse frequently moves around and the extracted background is perfect:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

2. Detectron2 (https://github.com/facebookresearch/detectron2) -based **Detector** is slower but more versatile than the **background subtraction** -based method. It also differentiates individuals when they entangle and is useful for complex interactive behaviors. You can decrease the frame size during analysis to increase the processing speed.

    To train a **Detector**:

    1. Use **‘Generate Image Examples’** functional unit to extract images (frames) from videos.
    2. Use free online annotation tools such as Roboflow (https://roboflow.com) or CVAT (https://www.cvat.ai) or VGG Image Annotator (https://www.robots.ox.ac.uk/~vgg/software/via/) to annotate the outlines (NOT bounding boxes) of animals / objects of your interest in images. Select 'Instance Segmentation' for annotation type and 'COCO instance segmentation' format when exporting the annotation, which is a ‘*.json’ file.
    3. Train your **Detectors** in **‘Train Detectors’** functional unit.

<p>&nbsp;</p>

# Installation

1. Install Python3 (version >= 3.9.7)

    Do not install the latest version of Python3 since it might not be compatible yet.

2. In your terminal / cmd prompt, type:

        pip install LabGym

    or

        python3 -m pip install LabGym

3. If want to use **Detectors**, after LabGym is installed, install Detectron2 separately (https://detectron2.readthedocs.io/en/latest/tutorials/install.html):

        python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

<p>&nbsp;</p>

# For each use

1. Activate Python3 by typing 'python3' or 'py' in the terminal / cmd prompt. Then type:

        from LabGym import gui

2. Then type:

        gui.gui()

    Now the GUI is initiated and ready to use.

<p>&nbsp;</p>

# If you encounter any issues when using LabGym:

Refer to the open / closed issues or contact the author: Yujia Hu (henryhu@umich.edu).

<p>&nbsp;</p>

# Changelog:

**v2.0**:

1. Implemented the analysis pipeline for complex interactive behaviors. 
2. Major improvement on analysis speed.
3. Bug fix.

**v1.9**:

1. Implemented Detector-based detection method. Now the changing background or illumination in videos is no longer a problem for LabGym. 
2. Implemented data mining functional unit.
3. Implemented preprocessing functional unit.
4. Simplified code and further optimized the processing speed.
5. Implemented basic analysis for interactive behavior.

**v1.8**:

1. In previous versions, if no animal is detected in a frame, this frame will be skipped. From now on, such frames will not be skipped, and the behavioral classification and quantification will be output as 'NA's so that the raster plots and the quantification results can be perfectly aligned for every frame with other data (e.g., ephys recordings).
2. An 'uncertain level' can be added into the Categorizers for reducing the false positives in behavior classification. The Categorizer will output an ‘NA’ if the difference between probability of the highest-likely behavior and the second highest-likely behavior is less than the uncertainty level.
3. Simplified the GUI. 
4. Optimized the processing speed.

**v1.7**:

1. Improved the background extraction and the tracking, making them faster and more accurate. 

**v1.6**:

1. Added a version checker. If a newer version of LabGym is available, users will see a reminder when initiate the GUI. 

**v1.5**:

1. Simplified the GUI and made it more self-illustrative.
2. Added an option of whether to output the distances in pixels when calculating behavior parameters. Previously all the distances were just normalized by the size of a single animal.

**v1.4**:

1. Made the time points in the output time-series sheets more precise.
2. Fixed an error when using the option of 'load background image'.

**v1.3**:

1. Improved background subtraction and the tracking is more accurate.
2. Now LabGym not only can work for videos with illumination transitions from dark to bright, but can also work for those from bright to dark.

**v1.2**:

1. Now LabGym can also be used in categorizing binary behaviors (yes or no behavior, or behaviors with only 2 categories)
2. Fixed a bug that caused a path error if users did not select any behavior parameters for quantification.
3. Now users have an option to choose whether to relink newly detected animals to deregistered IDs.

**v1.1**:

1. Changed a typo in setup.

**v1.0**:

Initial release.

<p>&nbsp;</p>
