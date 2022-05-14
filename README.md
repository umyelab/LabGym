# What is LabGym?

LabGym is a multi-animal-tracking and deep-learning based package for end-to-end classification and quantification of user-defined animal behaviors without restrictions on animal species or behavior types. It also provides users a way to generate visualizable datasets for the user-defined behaviors.

Please cite:
https://www.biorxiv.org/content/10.1101/2022.02.17.480911v3






The graphical user interface (GUI) of LabGym has 4 functional units: 'Generate Datasets', 'Train Networks', 'Test Networks', and 'Analyze Behaviors':

![alt text](https://github.com/yujiahu415/LabGym/blob/3cac15a69c386673853d91a93f73818f35726e71/Examples/Graphical_user_interface.png)






First you need to use the 'Generate Datasets' functional unit to generate some visualizable behavior data pairs (a data pair comprises an animation & a pattern image) like:

![alt text](https://github.com/yujiahu415/LabGym/blob/a9c77cd1f25ca1edc97aadb2257dd8fc0552483d/Examples/Larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/4484050e52480cdc0e0611eaff3545dfedf03908/Examples/Flies.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Mice.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Rats.gif)






The duration of the animation is user-definable.

Next, you need to manually sort them into different folders under the behavior names defined by you. Then input all the folders into LabGym to let it generated a labeled training dataset for training a 'Categorizer' using the 'Train Network functional unit'. There are various complexity levels of the Categorizer for you to choose to suit different behavior datasets. This is the end-to-end process that you 'teach' LabGym to recognize the behaviors defined by you. 

After the Categorizer is trained, you can use 'Test Networks' functional unit to test it in unbiased manner and the trained Categorizer will appear in the 'Analyze Behavior' functional unit. You can select it to analyze behavior videos and output annotated videos with behavior names (and %confidence) in each frame, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_2.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_2.gif)






Notably, LabGym calculates diverse behavioral parameters to provide quantitative measurements of the intensity and dynamics of each user-defined behavior, and the animal movement kinetics during a behavior, like:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_1.jpg)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_2.jpg)






The outputs of analysis results are:

![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Analysis_output.jpg)










# How to use LabGym:

LabGym does not require labeling or training to track the animals. In turn, it does have preferred video recording setting: LabGym works best for videos with stable background and illumination (the illumination can have dark-to-bright or bright-to-dark transitions but need to be stable before and after the transitions). Animals are expected to present some locational changes instead of being completely immobile all the time during a video recording. Users need to specify a time window during which the animals are moving for background extraction (the shorter the duration of the time window is, the shorter processing time it would take).






To use LabGym:

First install Python3 (version >= 3.9)

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

Now the graphical user interface is initiated and is ready to use.



The video tutorials are in the /Tutorials/ folder (https://github.com/umyelab/LabGym/tree/master/Tutorials).

A manual containing explanations on all the buttons in the GUI and the tips for use will come soon.










# If you encounter any issue in using LabGym:

Please first refer to the issue page (https://github.com/umyelab/LabGym/issues?q=) to see whether it was listed in addressed issues. If not, please contact the author: Yujia Hu (henryhu@umich.edu).










# Change logs:



v1.3:

1. Improved background subtraction and the tracking is more accurate.
2. Now LabGym not only can work for videos with illumination transitions from dark to bright, but also can work for those from bright to dark, too.



v1.2:

1. Now LabGym can also be used in categorizing binary behaviors (yes or no behavior, or behaviors with only 2 categories)
2. Fixed a bug that caused a path error if users did not select any behavior parameters for quantification.
3. Now users have an option to choose whether to relink newly detected animals to deregistered IDs.



v1.1:

Changed a typo in setup.



v1.0:

Initial release.







