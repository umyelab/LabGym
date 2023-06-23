# What is LabGym?

LabGym is an end-to-end platform for **analyzing behaviors of your interest**. 

1. It can **IDENTIFY** non-interactive and interactive behaviors of animals / objects of your interest at each frame in various kinds of recording settings / environments or scenarios:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_chipmunks_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_flies_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_voles_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_voles_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_larvae.gif?raw=true)

<p>&nbsp;</p>

2. It can **GENERATE** stand-alone behavior examples for you to sort to 'teach' it the behaviors defined by you. Each behavior example is a pair of a short **Animation** and its paired **Pattern Image**, which spans a duration (a behavior episode) defined by you:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Chipmunks.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Flies.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Voles.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Mice.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Rats.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Larvae.gif?raw=true)

These behavior examples can establish visualizable behavioral datasets.

<p>&nbsp;</p>

3. It can also **QUANTIFY** diverse motion / kinematics parameters for each behavior, such as **count**, **duration**, **latency** of a behavior, and **speed**, **acceleration**, **distance traveled**, **motion vigor**, **motion intensity** during a behavior. It outputs an annotated video and a temporal raster plot for every behavior event for each animal at each frame in an analysis batch, and the spread sheets for storing the calculated behavioral parameters:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior.jpg?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Analysis_output.jpg?raw=true)

<p>&nbsp;</p>

4. It can automatically **MINE** the analysis results to discover significant findings, such as the behavioral parameter that shows statistically significant difference among different groups, and then show the data details:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Results_mining.jpg?raw=true)

<p>&nbsp;</p>

Notably, LabGym is fast and accurate, and can be run smoothly on even average laptops **without GPUs**. The processing speed can be even faster with NVIDIA GPUs with CUDA toolkit installed.

Please cite the LabGym paper: https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7.

Next update, **LabGym 2.0**, will be able to track individuals during complex interactive behaviors and distinguish which individual does what.

<p>&nbsp;</p>

# How to use LabGym?

LabGym has a graphical user interface (GUI) for users to use with **no need of coding**. 

**Put your mouse cursor above each button to see a detailed description for it**.

<p>&nbsp;</p>

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User%20interface.jpg?raw=true)

<p>&nbsp;</p>

Extended user guide: (https://github.com/yujiahu415/LabGym/blob/master/LabGym%20user%20guide_v1.9.pdf).

The GUI has 3 modules: '**Preprocessing Module**' can preprocess your videos to make them fit your analysis goal better; '**Training Module**' is for you to teach LabGym to detect animals / objects of your interest and recognize behaviors defined by you; '**Analysis Module**' can automatically track animals / objects, identify, and quantify their behaviors. It can also automatically mine the analysis results to display the data details that show statistically significant differences among groups of your selection.

<p>&nbsp;</p>

## 'Preprocessing Module'

You can: 1. select multiple time windows in a video to form a new, trimmed video; 2. crop frames to exclude unnecessary regions; 3. enhance video contrast.

<p>&nbsp;</p>

## 'Training Module'

LabGym has two detection methods to detect animals / objects of your interest. One is background subtraction-based, which is the first choice for videos with static background and stable illumination because it is fast and accurate in such videos. When using this method, you need to specify a time window during which animals are moving for background extraction.

<p>&nbsp;</p>

**Tips on how to select an appropriate time window for background extraction**

Shorter time window means faster processing speed (typically a period of 10~30 seconds is sufficient for such time window). Below is an example showing how selecting different time windows would affect the background extraction.

The most left is a video of 60 seconds. The next three images are background extraction results based on the time windows of first, second, and last 20 seconds, respectively. In the first and last 20 seconds, the mouse mostly stays either in left or right side and moves little. Therefore, the extracted backgrounds contain animal trace and are not ideal. In the middle 20 seconds, the mouse frequently moves around so extracted background is perfect:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)  ![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

<p>&nbsp;</p>

The other detection method is using Detectron2 (https://github.com/facebookresearch/detectron2) -based **Detector**, which is versatile and useful in any kind of videos or experimental settings or to differentiate individuals when they entangle. This method can be slow but you may decrease its inferencing frame size to increase speed.

To train a **Detector**, you need to use free online annotation tools such as Roboflow (https://roboflow.com) or CVAT (https://www.cvat.ai) or VGG Image Annotator (https://www.robots.ox.ac.uk/~vgg/software/via/) to annotate the outlines (NOT bounding boxes) of animals / objects of your interest in images. Make sure to select 'Instance Segmentation' for the annotation type and select 'COCO instance segmentation' format when exporting the annotation file, which will be a ‘*.json’ file.

To let LabGym recognize behaviors defined by you, you need to train a **Categorizer**. First, you need to use ‘**Generate Behavior Examples**’ functional unit to generate some behavior example pairs (**Animations** + **Pattern Images**). You need to decide the **duration** of each **Animation** / **Pattern Image**, which should approximate the duration of a behavior episode. It must be the same across all the examples that are used to train one **Categorizer**. If the duration of different behavior episode is different, use the longest one. 

Next, you need to select and sort some examples into different categories (behavior types). ‘**Sort Behavior Examples**’ functional unit can make the sorting process much easier. 

Finally, you can customize a **Categorizer** in ‘**Train Categorizers**’ functional unit and train it on the sorted behavior examples.

<p>&nbsp;</p>

## 'Analysis Module'

Analyze behavioral videos and output the annotated videos with behavior names (and %confidence) marked in colors selected by you in each frame. It also
calculates diverse behavioral parameters to provide **quantitative measurements** of the intensity and the body kinematics for each behavior.

After analysis, you can use ‘**Mine Results**’ functional unit to let LabGym automatically perform parametric / non-parametric statistical analysis among groups that you selected, according to the data distribution, to compare the mean / median of different groups and display the significant findings.

The Shapiro test will be first performed to assess the normality of data distribution. For normally distributed data, if unpaired, unpaired t-test for 2 groups, ANOVA for more than 2 groups, with either Tukey (comparing each pair) or Dunnett's (comparing all groups against the control group) posthoc comparison; if paired, paired t-test for 2 groups, ANOVA for more than 2 groups, with either Tukey (comparing each pair) or Dunnett's (comparing all groups against the control group) posthoc comparison. For data that is not normally distributed, if unpaired, Mann Whitney U test for 2 groups, Kruskal Wallis for more than 2 groups, with Dunn's posthoc comparison for both comparing all groups and against control; if paired, Wilcoxon test for 2 groups, Friedman for more than 2 groups with Dunn’s posthoc. The selections of the tests are consistent with those in GraphPad Prism 9.

<p>&nbsp;</p>

# Installation and usage:

First install Python3 (version >= 3.9.7)

Note: not recommend to install the latest version of Python3 since some libraries LabGym uses might not be updated in time to be compatible with the latest Python3.

Then in your terminal or cmd prompt, type:

    pip install LabGym

or

    pip3 install LabGym

or

    python3 -m pip install LabGym

or

    py -m pip install LabGym

<p>&nbsp;</p>

**IMPORTANT** Starting from v1.9, after LabGym is installed, install Detectron2 by typing:

    python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

For issues in installing Detectron2, refer to https://detectron2.readthedocs.io/en/latest/tutorials/install.html. 

<p>&nbsp;</p>

After Detectron2 is installed, activate python interaction shell by typing 'python3' or 'py' in the terminal or cmd prompt.

Then type:

    from LabGym import gui

Then type:

    gui.gui()

Now the GUI is initiated and ready to use.

<p>&nbsp;</p>

# If you encounter any issues when using LabGym:

Please refer to the issue page (https://github.com/umyelab/LabGym/issues?q=) to see whether it is listed in addressed issues. If not, please contact the author: Yujia Hu (henryhu@umich.edu).

<p>&nbsp;</p>

# Changelog:

**v1.9**:

1. Implemented Detector-based detection method. Now the changing background or illumination in videos is no longer a problem for LabGym. 
2. Implemented data mining functional unit.
3. Implemented preprocessing functional unit.
4. Simplified code and further optimized the processing speed.

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
