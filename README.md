LabGym is a multi-animal-tracking and deep-learning based package for quantifying user-defined animal behaviors without restrictions on animal species or behavior types. It also provides users a way to generate visualizable datasets for the user-defined behaviors.

The graphical user interface (GUI) of LabGym has 4 functional units: 'Generate Datasets', 'Train Networks', 'Test Networks', and 'Analyze Behaviors'.


![alt text](https://github.com/yujiahu415/LabGym/blob/3cac15a69c386673853d91a93f73818f35726e71/Examples/Graphical_user_interface.png)


First you need to use the 'Generate Datasets' functional unit to generate some visualizable behavior data pairs (a data pair comprises an animation & a pattern image) like:


![alt text](https://github.com/yujiahu415/LabGym/blob/a9c77cd1f25ca1edc97aadb2257dd8fc0552483d/Examples/Larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/4484050e52480cdc0e0611eaff3545dfedf03908/Examples/Flies.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Mice.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Rats.gif)


The duration of the animations are user-definable.

And manually sort them into different folders under the behavior names defined by you. Then input all the folders into LabGym to let it generated a labeled training dataset for training a 'Categorizer' using the 'Train Network functional unit'. There are various complexity levels of the Cateogirzer for you to choose to suit diffenret behavior datasets.

After the Categorizer is trained, you can use 'Test Networks' functional unit to test it in unbiased manner and it will appear in the 'Analyze Behavior' functional unit. You can select it to analyze behavior videos and output annoated videos with behavior names (and %confidence) in each frame, like:


![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_larvae.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_mice_2.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_1.gif)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Categorizer_rats_2.gif)


Notably, LabGym calculates diverse behavioral parameters to provide quantitatve measurements of the intensity and dynamics of each user-defined behavior, like:


![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_1.jpg)
![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Quantify%20behavior_2.jpg)


The outputs of analysis results are:


![alt text](https://github.com/yujiahu415/LabGym/blob/6ea290e8b86b30ae882631a8301ef6c80545f802/Examples/Analysis_output.jpg)
