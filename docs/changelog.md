# Changelog

## v2.2

1. Added functions of testing Detectors / Categorizers so that the accuracy of a trained Detector / Categorizer can be tested and reported.
2. Added behavior mode 'Static image' so that LabGym can now analyze behaviors in static images.
3. Made the spreadsheets for storing behavioral metrics transposed so that they can be more compatible with other platforms.
4. Other minor optimizations.

## v2.1

1. Improved the user interface and the Extended User Guide. 
2. Added a tutorial video.

## v2.0

1. Implemented the analysis pipeline for complex interactive behaviors. 
2. Major improvement on analysis speed.
3. Bug fix.

## v1.9

1. Implemented Detector-based detection method. Now the changing background or illumination in videos is no longer a problem for LabGym. 
2. Implemented data mining functional unit.
3. Implemented preprocessing functional unit.
4. Simplified code and further optimized the processing speed.
5. Implemented basic analysis for interactive behavior.

## v1.8

1. In previous versions, if no animal is detected in a frame, this frame will be skipped. From now on, such frames will not be skipped, and the behavioral classification and quantification will be output as 'NA's so that the raster plots and the quantification results can be perfectly aligned for every frame with other data (e.g., ephys recordings).
2. An 'uncertain level' can be added into the Categorizers for reducing the false positives in behavior classification. The Categorizer will output an ‘NA’ if the difference between probability of the highest-likely behavior and the second highest-likely behavior is less than the uncertainty level.
3. Simplified the user interface. 
4. Optimized the processing speed.

## v1.7

1. Improved the background extraction and the tracking, making them faster and more accurate. 

## v1.6

1. Added a version checker. If a newer version of LabGym is available, users will see a reminder when initiate the user interface. 

## v1.5

1. Simplified the user interface and made it more self-illustrative.
2. Added an option of whether to output the distances in pixels when calculating behavior parameters. Previously all the distances were just normalized by the size of a single animal.

## v1.4

1. Made the time points in the output time-series sheets more precise.
2. Fixed an error when using the option of 'load background image'.

## v1.3

1. Improved background subtraction and the tracking is more accurate.
2. Now LabGym not only can work for videos with illumination transitions from dark to bright, but can also work for those from bright to dark.

## v1.2

1. Now LabGym can also be used in categorizing binary behaviors (yes or no behavior, or behaviors with only 2 categories)
2. Fixed a bug that caused a path error if users did not select any behavior parameters for quantification.
3. Now users have an option to choose whether to relink newly detected animals to deregistered IDs.

## v1.1

1. Changed a typo in setup.

## v1.0

Initial release.
