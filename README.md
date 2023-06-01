# What is LabGym?

LabGym is an end-to-end platform for **analyzing user-defined behaviors**. It can **IDENTIFY** behaviors for each animal / object at each frame:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_2.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats_1.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats_3.gif?raw=true)

even when animals / objects entangle with others or under unstable illumination or in changing environment:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_larvae.gif?raw=true)![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats_2.gif?raw=true)

<p>&nbsp;</p>

It can **GENERATE** stand-alone behavior examples and users can sort them to 'teach' it user-defined behaviors. Each behavior example is a pair of a short **Animation** and its paired **Pattern Image**, which spans a user-defined duration (a behavior episode):

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Mice.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Rats.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Larvae.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Flies.gif?raw=true)    These examples can establish visualizable behavioral datasets.

<p>&nbsp;</p>

It can also **QUANTIFY** diverse motion / kinematics parameters for each behavior, such as **count**, **duration**, **latency** of a behavior, and **speed**, **acceleration**, **distance traveled**, **motion vigor**, **motion intensity** during a behavior. It outputs an annotated video and a temporal raster plot for every behavior event for each animal at each frame in an analysis batch, and the spread sheets for storing the calculated behavioral parameters:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior.jpg?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Analysis_output.jpg?raw=true)

<p>&nbsp;</p>

Lastly, it can automatically **MINE** the analysis results to discover significant findings, like the behavioral parameter that shows statistically significant difference among different groups, and then show the data details:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Results_mining.jpg?raw=true)

<p>&nbsp;</p>

Notably, LabGym is fast and accurate, and can be run smoothly on even common laptops **without GPUs**. The processing speed can be even faster when NVIDIA GPUs with CUDA toolkit are used.

Please cite the LabGym paper: https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7.

Next update, **LabGym 2.0**, will be able to work for complex interactive behaviors and social behaviors.

<p>&nbsp;</p>

# How to use LabGym?

LabGym has a graphical user interface (GUI) for users to use with **no need of coding**. The **full manual** for using the GUI of LabGym: https://github.com/yujiahu415/LabGym/blob/master/The%20full%20manual%20of%20LabGym_v1.9.pdf.

The GUI has 9 functional units: '**Generate Object Images**', '**Train Detectors**', '**Test Detectors**', '**Generate Behavior Examples**', '**Train Categorizers**', '**Test Categorizers**', '**Preprocess Data**', '**Analyze Behaviors**', and '**Mine Analysis Results**':

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User%20interface.png?raw=true)

<p>&nbsp;</p>

## 'Generate Object Images'

Use this to extract frames (images) from videos. The extracted frames can be used for annotating the outline of animals / objects in them. The annotated images can then be used to train a Detector in ‘**Train Detectors**’ functional unit. After images are generated, users may use free online annotation tools such as Roboflow (https://roboflow.com) or CVAT (https://www.cvat.ai) or VGG Image Annotator (https://www.robots.ox.ac.uk/~vgg/software/via/) to annotate the outlines (NOT bounding boxes) of animals / objects of interest in images. When annotated images, make sure to select 'Instance Segmentation' for the annotation type. When exporting the annotation file, make sure to select 'COCO instance segmentation' format, which will be a ‘*.json’ file.

<p>&nbsp;</p>

## 'Train Detectors'

Use this to train Detectron2 (https://github.com/facebookresearch/detectron2) -based **Detectors**. The trained **Detectors** will be listed in the detection methods in ‘**Test Detectors**’, ‘**Generate Behavior Examples**’, and ‘**Analyze Behaviors**’ functional units. In LabGym, there are two detection methods:

One is **Detector**-based method, which is versatile. It is useful in any kind of videos or experimental settings. It is also useful for differentiating individual animals when they entangle. But well-annotated images are needed to train a **Detector** of high detection accuracy, and the analysis speed can be slow. However, users may decrease the inferencing frame size of the **Detector** to increase the speed.

The other is background subtraction-based method, which is the first choice for videos with static background and stable illumination because it is fast and accurate in such videos. This method might also be useful in analyses where the total number of behavior events is more important than distinguishing animal IDs, because it cannot distinguish entangled animals and the IDs might switch after they re-separate. When using this method, users need to specify a time window during which animals are moving for background extraction.

**Tips on how to select an appropriate time window for background extraction**

Shorter time window means faster processing speed (typically a period of 10~30 seconds is sufficient for such time window). Below is an example showing how selecting different time windows would affect the background extraction.

This is a 60-second video. In the first 20 seconds, the mouse mostly stays in left side; in the second 20 seconds, it moves around (from the left side to the right side); in the last 20 seconds, it mostly stays in right side:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)


If select the time window of 0th~20th second for background extraction, the extracted background is not ideal (contains animal trace):

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)


If select the time window of 20th~40th second for background extraction, the extracted background is perfect:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)


If select the time window of 40th~60th second for background extraction, the extracted background is not ideal (contains animal trace):

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

<p>&nbsp;</p>

## 'Test Detectors'

Input a video to test a trained **Detector**. Users can also delete a trained **Detector** in this functional unit.

<p>&nbsp;</p>

## 'Generate Behavior Examples'

Use this to generate stand-alone, visualizable behavior examples from videos. These behavior example pairs can be sorted into different folders according to their behavior types (categories) and input to the ‘**Train Categorizers**’ functional unit to train **Categorizers** for identifying user-defined behaviors. They can also be sorted and input to the ‘**Test Categorizers**’ functional unit for testing the accuracy of a trained **Categorizer**. 

The **duration** of an **Animation** / **Pattern Image** needs to be defined by users, which should approximate the duration of a behavior episode. It has to be the same across all the examples that are used to train one **Categorizer**. If the duration of different behavior episode is different, use the longest one.

<p>&nbsp;</p>

## 'Train Categorizers'

The generated behavior examples can be used to 'teach' LabGym (train **Categorizers**) to recognize user-defined behaviors. To do so, users need to select and sort these example pairs into different folders and name the folders after the behavior names. The ‘Sort Behavior Examples’ module in ‘**Preprocess Data**’ functional unit can be used to help sorting. There are various complexity levels of the **Categorizer** for users to choose to suit behaviors of different complexity. The trained Categorizers will be automatically added into the **Categorizer** list for the usage in ‘**Test Categorizers**’ and ‘**Analyze Behaviors**’ functional units.

<p>&nbsp;</p>

## 'Test Categorizers'

After a **Categorizer** is trained, users can test its accuracy. Users can also delete a trained **Categorizer** in this functional unit.

<p>&nbsp;</p>

## 'Preprocess Data'

Two modules in this functional unit: ‘Preprocess Videos’ and ‘Sort Behavior Examples’. The former is for preprocessing the videos (trim videos into shorter video clips / crop video frame to exclude unnecessary areas in frames / enhance video contrast) to make them more suitable for analysis; the latter is for visualizing behavior examples in an easier way and using shortcut keys to sort them.

<p>&nbsp;</p>

## 'Analyze Behaviors'

Use this to analyze behavioral videos and output the annotated videos with behavior names (and %confidence) marked in user-defined colors in each frame. It also
calculates diverse behavioral parameters to provide **quantitative measurements** of the intensity and the body kinematics for each user-defined behavior.

<p>&nbsp;</p>

## 'Mine Analysis Results'

Automatically performs parametric / non-parametric statistical analysis among groups that users selected, according to the data distribution, to compare the mean / median of different groups and display the significant findings.

A p value needs to be specified for determining the significance threshold for statistical analysis. The Shapiro test will be first performed to assess the normality of data distribution. For normally distributed data, if unpaired, unpaired t-test for 2 groups, ANOVA for more than 2 groups, with either Tukey (comparing each pair) or Dunnett's (comparing all groups against the control group) posthoc comparison; if paired, paired t-test for 2 groups, ANOVA for more than 2 groups, with either Tukey (comparing each pair) or Dunnett's (comparing all groups against the control group) posthoc comparison. For data that is not normally distributed, if unpaired, Mann Whitney U test for 2 groups, Kruskal Wallis for more than 2 groups, with Dunn's posthoc comparison for both comparing all groups and against control; if paired, Wilcoxon test for 2 groups, Friedman for more than 2 groups with Dunn’s posthoc. The selections of the tests are consistent with those in GraphPad Prism 9.

<p>&nbsp;</p>

# Installation and usage:

First install Python3 (version >= 3.9.7)

Note: not recommend to install the latest version of Python3 since many Python libraries LabGym uses might not be updated in time to be compatible with the latest version of Python3.

Then in your terminal or cmd prompt, type:

    pip install LabGym

or

    pip3 install LabGym

or

    python3 -m pip install LabGym

or

    py -m pip install LabGym

After LabGym is installed, activate python interaction shell by typing 'python3' or 'py' in the terminal or cmd prompt.

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

1. Implemented Detector-based detection method.
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
