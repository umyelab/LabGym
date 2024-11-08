# Changelog

## v2.6.2
### What's Changed
* Bug fixed in the function of 'calculate distances'.

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.6.1...v2.6.2>

## v2.6.1
### What's Changed
* Increased the limit of iteration number of training a Detector.
* Changed the model saving method in training a Detector so that only the final model will be saved, which minimizes the size of a trained Detector.
* Changed the colors for shortest and traveling distances in the function of 'calculate distances'.

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.6.0...v2.6.1>

## v2.6.0
### What's Changed
* Added the function of 'calculate distances', which calculates the shortest distance and actual traveling distance among locations when animals perform the selected behaviors.
* Added an option for users to specify a minimum length (duration in frames) for an identified behavior to filter out potential false positive identifications.
* Fixed a bug when outputing the testing metrics of binary behavior categorization in both training and testing Categorizers.
* Made the output of trajectories lines instead of dots.

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.6...v2.6.0>

## v2.5.6
### What's Changed
* Bug fix in 'interactive basic' mode

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.5...v2.5.6>

## v2.5.5
### What's Changed
* Bug fix in 'interactive basic' mode

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.4...v2.5.5>


## v2.5.4
### What's Changed
* Bug fix in 'interactive basic' mode

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.3...v2.5.4>

## v2.5.3
### What's Changed
* Bug fix in 'interactive basic' mode
* Changed output raster plot according to the longest instead of shortest video in a batch
* Changed the wording 'social distance' to 'interaction distance'
* Added a LabGym practical 'How to' guide

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.2...v2.5.3>

## v2.5.2
### What's Changed
* Bug fix in 'interactive basic' mode
* Restrain numpy version during installation

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.1...v2.5.2>

## v2.5.1
### What's Changed
* Optimized analysis flow allowing Detectors to fail on some frames without disrupting and aborting the analysis process

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.5.0...v2.5.1>

## v2.5.0
### What's Changed
* Added the function of 'draw markers in videos'
* Added LabGym Zoo
* Added documentation on how to use LabGym via command prompt (see extended user guide)

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.6...v2.5.0>

## v2.4.6
### What's Changed
* Added the function of outputting trajectories of detected animals/objects
* Fixed bugs
* Major code clean up
* Added annotations for each function

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.5...v2.4.6>

## v2.4.5
### What's Changed
* Fix bugs in "Train Categorizers" module
* Add internal notes section to documentation

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.4...v2.4.5>

## v2.4.4
### What's Changed
* Fix crash that occurs when no detectors are present
* Constrain tensorflow version on non-Windows systems

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.3...v2.4.4>

## v2.4.3
### What's Changed
* Fix bug in static image mode

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.3...v2.4.4>

## v2.4.2
### What's Changed
* Fix bug that prevented using the cropping feature in the preprocessing module

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.1...v2.4.2>

## v2.4.1
### What's Changed
* Standardize order of Animation Analyzer and Pattern Recognizer in GUI
* Fix OpenCV type error when using Background Subtraction
* Allow for older versions of dependencies
* Close window preview when canceling contrast in Preprocessing Module

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.4.0...v2.4.1>

## v2.4.0
### What's Changed
* Remove all references to `THE_ABSOLUTE_CURRENT_PATH`
* Increase line length in format configuration
* Add date/time changes
* Refactor detector code
* Add excel file with animal positions in analysis export
* Fix text scale in annotated video


**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.5...v2.4.0>

## v2.3.5
### What's Changed
* Add ruff format rules
* Update installation instructions
* Add automated test suite
* Fix bug in sorting behavior file name
* Fix detector batch size bug


**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.4...v2.3.5>

## v2.3.4
### What's Changed
* Fix `cv2.typing` import error

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.3...v2.3.4>

## v2.3.3
### What's Changed
* Fix model path bug in `behavior_examples.py`
* Update installation documentation by
* Release v2.3.3


**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.2...v2.3.3>

## v2.3.2
### What's Changed
* Prevent crash when version checking fails
* Update python-publish.yml

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.1...v2.3.2>

## v2.3.1
### New Features

* The recommended way to install LabGym is now through `pipx`. Please see the [installation documentation](https://labgym.readthedocs.io/en/latest/installation/index.html) for more information.
* It's now possible to start LabGym by using the `LabGym` command at the terminal! Now, there's no need to type `from LabGym import gui; gui.gui()` at the terminal.

### What's Changed
* Fix incompatibility issues with Python 3.9

**Full Changelog**: <https://github.com/umyelab/LabGym/compare/v2.3.0...v2.3.1>

## v2.3.0
### New Features
* The recommended way to install LabGym is now through `pipx`. Please see the [installation documentation](https://labgym.readthedocs.io/en/latest/installation/index.html) for more information.
* It's now possible to start LabGym by using the `LabGym` command at the terminal! Now, there's no need to type `from LabGym import gui; gui.gui()` at the terminal.

### What's Changed
* Refactor codebase
* Move documentation to <https://labgym.readthedocs.io>
* Start LabGym using the `LabGym` command at the terminal
* Add option to downscale video FPS in preprocessing module

**Full Changelog**: <https://github.com/umyelab/LabGym/commits/v2.3.0>

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
