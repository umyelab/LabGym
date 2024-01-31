# Walkthroughs

In order to generate behavior examples, LabGym supports two methods to isolate
animals from their backgrounds: static background subtraction and
Detector-based subtraction. 

Use background subtraction if:

 - The lighting is stable throughout the video frame
 - The background is static throughout the duration of the video

Use a Detector if:

 - The lighting is different in different parts of the video frame
 - The animals frequently collide and it's important to differentiate between
   them
 - You are using `Interactive Advanced` or `Static Image` mode


```{toctree}
:hidden:

background-subtraction
detector
static-image-analysis
```
