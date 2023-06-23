# What is LabGym?

LabGym is an end-to-end platform for **analyzing behaviors of your interest**. It can:

1. **IDENTIFY** non-interactive and interactive behaviors of animals / objects of your interest at each frame in various kinds of recording settings / environments or scenarios:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_larvae.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats.gif?raw=true)

<p>&nbsp;</p>

2. **GENERATE** stand-alone behavior examples for you to sort to 'teach' it the behaviors defined by you. Each behavior example is a pair of a short **Animation** and its paired **Pattern Image**, which spans a duration (a behavior episode) defined by you:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Chipmunks.gif?raw=true)
    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Flies.gif?raw=true)
    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Mice.gif?raw=true)
    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Rats.gif?raw=true)
    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Larvae.gif?raw=true)

    They can establish visualizable behavioral datasets.

<p>&nbsp;</p>

3. **QUANTIFY** diverse motion / kinematics parameters for each behavior, such as **count**, **duration**, **latency** of a behavior, and **speed**, **acceleration**, **distance traveled**, **motion vigor**, **motion intensity** during a behavior. It outputs annotated videos and a temporal raster plot for every behavior event for each animal at each frame in an analysis batch, and spread sheets for storing the calculated behavioral parameters:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior.jpg?raw=true)
    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Analysis_output.jpg?raw=true)

<p>&nbsp;</p>

4. Automatically **MINE** the analysis results to display significant findings, such as the behavioral parameters that show statistically significant difference among different groups, and then show the data details:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Results_mining.jpg?raw=true)

<p>&nbsp;</p>

5. Run smoothly on even average laptops **without GPUs**. It can be even faster with NVIDIA GPUs and CUDA toolkit installed.

<p>&nbsp;</p>

Cite LabGym: https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7. **LabGym 2.0** for more complex behaviors is coming!

<p>&nbsp;</p>

# How to use LabGym?

A graphical user interface (GUI) with 3 modules for you to use with **no need of coding**.

Extended user guide: (https://github.com/yujiahu415/LabGym/blob/master/LabGym%20user%20guide_v1.9.pdf).

***Put your mouse cursor above each button to see a detailed description for it***.

<p>&nbsp;</p>

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User%20interface.jpg?raw=true)

<p>&nbsp;</p>

## 'Preprocessing Module' (make videos fit your analysis goal better)

1. Select multiple time windows in a video to form a new, trimmed video.

2. Crop frames to exclude unnecessary regions.

3. Enhance video contrast.

<p>&nbsp;</p>

## 'Training Module' (teach LabGym detect obejcts & recognize behaviors)

To let LabGym detect animals / objects of your interest, you have two ways:

1. **Background subtraction** -based method is fast and accurate and is the first choice for videos with static background and stable illumination. No training is needed for this method but you need to specify a time window during which animals are moving for background extraction.

    ***How to select an appropriate time window for background extraction?***

    Shorter time window = faster processing speed. 10 to 30 seconds are sufficient. Here is an example showing how selections of different time windows would affect the background extraction.

    The video is of 60 seconds. The following three images are backgrounds extracted using the time windows of the first, second, and last 20 seconds, respectively. In the first and last 20 seconds, the mouse mostly stays either in left or right side and moves little and the extracted backgrounds contain animal trace, which is not ideal. In the second 20 seconds, the mouse frequently moves around and the extracted background is perfect:

    ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

<p>&nbsp;</p>

2. Detectron2 (https://github.com/facebookresearch/detectron2) -based **Detector** is slower but more versatile than the **background subtraction** -based method. It also differentiates individuals when they entangle and is useful for complex interactive behaviors. You can decrease the frame size during analysis to increase the processing speed.

    To train a **Detector**:

    1. Use ‘**Generate Image Examples**’ functional unit to extract images (frames) from videos.
    2. Use free online annotation tools such as Roboflow (https://roboflow.com) or CVAT (https://www.cvat.ai) or VGG Image Annotator (https://www.robots.ox.ac.uk/~vgg/software/via/) to annotate the outlines (NOT bounding boxes) of animals / objects of your interest in images. Select 'Instance Segmentation' for annotation type and 'COCO instance segmentation' format when exporting the annotation, which is a ‘*.json’ file.
    3. Train your **Detectors** in ‘**Train Detectors**’ functional unit.

<p>&nbsp;</p>

To let LabGym recognize behaviors of your interest, you need to train a **Categorizer**:

1. Use ‘**Generate Behavior Examples**’ functional unit to generate behavior examples (**Animations** + **Pattern Images**). You need to decide the **duration** of each **Animation** / **Pattern Image**, which should span a behavior episode. The **duration** must be the same across all the examples that are used to train one **Categorizer**. If the **duration** of different behavior episode is different, use the longest one. 

2. Select and sort some examples into different behavior types. ‘**Sort Behavior Examples**’ functional unit can make this much easier. More examples (and more diverse) = higher categorization accuracy, but 100 pairs of well-selected examples for each behavior type can train a good **Categorizer** in general.

3. Customize your own **Categorizer** in the ‘**Train Categorizers**’ functional unit and train it on the sorted behavior examples.

<p>&nbsp;</p>

## 'Analysis Module' (analyze behaviors & data mining)

1. ‘**Analyze Behaviors**’ functional unit analyzes videos and outputs annotated video copies with behavior names (and %confidence) marked in colors selected by you. It also calculates diverse behavioral parameters to provide **quantitative measurements** of the intensity and kinematics for each behavior.

2. After analysis, use ‘**Mine Results**’ functional unit to let LabGym automatically perform parametric / non-parametric statistical analysis among groups selected by you, according to the data distribution, to compare the mean / median of different groups and display the significant findings.

<p>&nbsp;</p>

# Installation and usage:

1. Install Python3 (version >= 3.9.7)

    Not to install the latest version of Python3 since it might not be compatible yet.

2. In your terminal / cmd prompt, type:

        pip install LabGym

    or

        python3 -m pip install LabGym

    or

        py -m pip install LabGym

3. For >= v1.9, after LabGym is installed, install Detectron2 seperately (https://detectron2.readthedocs.io/en/latest/tutorials/install.html):

        python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'


4. Activate python3 by typing 'python3' or 'py' in the terminal / cmd prompt. Then type:

        from LabGym import gui

    Then:

        gui.gui()

    Now the GUI is initiated and ready to use.

<p>&nbsp;</p>

# If you encounter any issues when using LabGym:

Refer to the issue page (https://github.com/umyelab/LabGym/issues?q=) or contact the author: Yujia Hu (henryhu@umich.edu).

<p>&nbsp;</p>

# Changelog:

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
