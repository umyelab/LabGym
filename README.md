# What is LabGym?

LabGym is a multi-animal-tracking and deep-learning based software for end-to-end **classification** and **quantification** of user-defined behaviors without restrictions on animal species or behavior types. Users may also use it to establish **visualizable behavioral datasets** across species.

Please cite the LabGym paper: https://www.biorxiv.org/content/10.1101/2022.02.17.480911v3.

<p>&nbsp;</p>

# How to use LabGym?

LabGym has a graphical user interface (GUI) for users to use with **no need of writing code**. 

The **full manual** for using the GUI of LabGym: https://github.com/yujiahu415/LabGym/blob/master/The%20full%20manual%20of%20LabGym_v1.6.pdf.

The GUI has 4 functional units: '**Generate Behavior Examples**', '**Train Categorizers**', '**Test Categorizers**', and '**Analyze Behaviors**':
 
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/User%20interface.png?raw=true)

<p>&nbsp;</p>

## 'Generate Behavior Examples'

This functional unit is used to generate visualizable behavior examples from videos. A behavior example pair comprises an **animation** and its paired **pattern image**, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Mice.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Rats.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Larvae.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Flies.gif?raw=true)

<p>&nbsp;</p>

The **animation duration** needs to be defined by users, which should approximate the duration of a behavior episode. The **animation duration** needs to be the same across all the animations that are used to train one Categorizer. If the duration of different behaviors is different, use the longest one as the **animation duration**.

## 'Train Categorizers'

The generated behavior examples can be used to 'teach' LabGym to recognize user-defined behaviors. To do so, users need to select and sort these example pairs into different folders and name the folders with the behavior names. These folders can be input into this functional unit to train a **Categorizer** in LabGym. There are various complexity levels of the **Categorizer** for you to choose to suit behaviors of different complexity. 

## 'Test Categorizers'

After a **Categorizer** is trained, users may use this functional unit to test its accuracy. In this functional unit, users may also delete a **Categorizer** that is no longer needed.

## 'Analyze Behaviors'

The trained **Categorizers** will appear in this functional unit. Users may select one to analyze behavioral videos and output the annotated videos with behavior names (and %confidence) marked in user-defined colors in each frame, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_larvae.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_1.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_mice_2.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats_1.gif?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Categorizer_rats_2.gif?raw=true)

<p>&nbsp;</p>

Notably, LabGym also calculates diverse behavioral parameters in this functional unit to provide **quantitative measurements** of the intensity and the body kinematics for each user-defined behavior, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior_1.jpg?raw=true)
![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Quantify%20behavior_2.jpg?raw=true)

<p>&nbsp;</p>

The exported analysis results inlcude a raster plot for all the behavior events and their %confidence for all the animals in one analysis batch, an annotated video for each video in the analysis batch, and the spreadsheets storing all the behavioral parameter values, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Analysis_output.jpg?raw=true)

<p>&nbsp;</p>

## Requirements on the video recording

1. Although LabGym does not have restriction on the kind of background, enclosure, or camera angle needed, these aspects needs to be static during the period for behavior analysis.
2. The illumination in a video can have sudden transitions from dark to bright or from bright to dark but needs to be stable overtime before and after the transitions.
3. Animals need to move around in relation to the background in order for LabGym to differentiate them from the background. Thus, a time window during which animals are moving is needed for background extraction in LabGym.

## Tips on how to select an appropriate time window for background extraction

LabGym does not require manual labeling or model training to detect and track the animals. Users only need to specify a time window to let LabGym extract the background for accurate detection and tracking. This time window can be any period during which the animals are moving around. Shorter time window means faster processing speed (typically a period of 10~30 seconds is sufficient for such time window). Below is an example showing how selecting different time windows would affect the background extraction.

This is a 60-second video:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Background_extraction_demo.gif?raw=true)

<p>&nbsp;</p>

If select the time window of 0th~20th second for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_0-20.jpg?raw=true)

<p>&nbsp;</p>

If select the time window of 20th~40th second for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_20-40.jpg?raw=true)

<p>&nbsp;</p>

If select the time window of 40th~60th second for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/master/Examples/Extracted_background_40-60.jpg?raw=true)

<p>&nbsp;</p>

Obviously, selecting the time window of 20th~40th second achieves the best result of background extraction (clean background without any animal traces), because during this time window the mouse is moving around (from the left side to the right side) while during the other two time windows the mouse stays in either left side or right side for a long time, and it might be considered as a part of the static background.

<p>&nbsp;</p>

# Installation and usage:

First install Python3 (version >= 3.9.7)

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
