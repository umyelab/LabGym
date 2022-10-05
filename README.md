# What is LabGym?

LabGym is a multi-animal-tracking and deep-learning based software for end-to-end **classification** and **quantification** of user-defined animal behaviors without restrictions on animal species or behavior types. Users can also use it to establish visualizable behavioral datasets across species.

Please cite the LabGym paper: https://www.biorxiv.org/content/10.1101/2022.02.17.480911v3.

The graphical user interface (GUI) of LabGym has 4 functional units: '**Generate Behavior Examples**', '**Train Categorizers**', '**Test Categorizers**', and '**Analyze Behaviors**':
 
![alt text](https://github.com/yujiahu415/LabGym/blob/0690671754addcaffa3350e6b400196550b3a1e7/Examples/GUI.jpg)

<p>&nbsp;</p>

# How to use LabGym?

## 'Generate Behavior Examples'

You can use this functional unit to generate visualizable behavior examples from your videos. A behavior example pair comprises an **animation** and its paired **pattern image**, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/a9c77cd1f25ca1edc97aadb2257dd8fc0552483d/Examples/Larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/4484050e52480cdc0e0611eaff3545dfedf03908/Examples/Flies.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Mice.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Rats.gif)

<p>&nbsp;</p>

The **animation duration** needs to be defined by users, which should approximate the duration of a behavior episode. If different behaviors have different durations, take the longest one as the animation duration when generating behavior examples.

## 'Train Categorizers'

The generated behavior examples can be used to 'teach' LabGym to recognize user-defined behaviors. To do so, you can sort these example pairs into different folders and name the folders with the behavior names. These folders can be input into this functional unit to train a **Categorizer** in LabGym. There are various complexity levels of the **Categorizer** for you to choose to suit behaviors of different complexity. 

## 'Test Categorizers'

After a **Categorizer** is trained, you can use this functional unit to test its accuracy. You can also delete a Categorizer that is no longer needed in this functional unit.

## 'Analyze Behaviors'

The trained **Categorizers** will appear in this functional unit. You can then select one to analyze behavioral videos and output the annotated videos with behavior names (and %confidence) marked in user-defined colors in each frame, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_2.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_2.gif)

<p>&nbsp;</p>

Notably, in this functional unit LabGym also calculates diverse behavioral parameters to provide **quantitative measurements** of the intensity and the body kinematics for each user-defined behavior, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_1.jpg)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_2.jpg)

<p>&nbsp;</p>

A raster plot for all the behavior events and their %confidence of all the animals in one analysis batch, the annotated videos, and the spreadsheets storing all behavioral parameter values will exported, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Analysis_output.jpg)

<p>&nbsp;</p>

The video tutorials for the GUI (prior to version 1.5) are in the /Tutorials/ folder (https://github.com/umyelab/LabGym/tree/master/Tutorials).

A manual containing the detailed explanations and the tips for use will come soon.

## Requirements on video recording

1. The background in a video can be any but needs to be still. 
2. The illumination in a video can have sudden transitions from dark to bright or from bright to dark but needs to be stable overtime before and after the sudden transitions.
3. Animals are expected to present some locational changes instead of being completely immobile all the time during a video recording.

## Tips on how to select an appropriate time window for background extraction

LabGym does not require manual labeling or training neural networks to detect and track the animals. The detection and tracking in LabGym is based on background subtraction. Users just need to specify a time window during which the animals are moving around for background extraction. Shorter time window means faster processing speed. Below is an example showing how choosing different time windows would affect the results of background extraction.

This is a 60-second video:

![alt text](https://github.com/yujiahu415/LabGym/blob/0690671754addcaffa3350e6b400196550b3a1e7/Examples/Background_extraction_demo.gif)

<p>&nbsp;</p>

If choose the 0th~20th second as the time window for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/0690671754addcaffa3350e6b400196550b3a1e7/Examples/Extracted_background_0-20.jpg)

<p>&nbsp;</p>

If choose the 20th~40th second as the time window for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/0690671754addcaffa3350e6b400196550b3a1e7/Examples/Extracted_background_20-40.jpg)

<p>&nbsp;</p>

If choose the 40th~60th second as the time window for background extraction, the extracted background is like:

![alt text](https://github.com/yujiahu415/LabGym/blob/0690671754addcaffa3350e6b400196550b3a1e7/Examples/Extracted_background_40-60.jpg)

<p>&nbsp;</p>

Obviously, choosing the time window of 20th~40th second achieves the best result of background extraction (clean background without any animal traces), because during this time window the mouse is moving around (from the left side to the right side) while during the other two time windows the mouse stays in either left side or right side for a long time.

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

Now the graphical user interface is initiated and LabGym is ready to use.

<p>&nbsp;</p>

# If you encounter any issue in using LabGym:

Please refer to the issue page (https://github.com/umyelab/LabGym/issues?q=) to see whether it was listed in addressed issues. If not, please contact the author: Yujia Hu (henryhu@umich.edu).

<p>&nbsp;</p>

# Change logs:

**v1.5**:

1. Simplified the user interface, making it more self-illustrative.
2. Added an option of whether to output the distances in pixels when calculating behavior parameters. Previously all the distances were just normalized by the size of a single animal.

**v1.4**:

1. Made the time points in the output time-series sheets more precise.
2. Fixed an error when using the 'load background image' option.

**v1.3**:

1. Improved background subtraction and the tracking is more accurate.
2. Now LabGym not only can work for videos with illumination transitions from dark to bright, but also can work for those from bright to dark.

**v1.2**:

1. Now LabGym can also be used in categorizing binary behaviors (yes or no behavior, or behaviors with only 2 categories)
2. Fixed a bug that caused a path error if users did not select any behavior parameters for quantification.
3. Now users have an option to choose whether to relink newly detected animals to deregistered IDs.

**v1.1**:

Changed a typo in setup.

**v1.0**:

Initial release.

<p>&nbsp;</p>
