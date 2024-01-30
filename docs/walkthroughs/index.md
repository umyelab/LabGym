# Walkthroughs

In order to generate behavior examples, LabGym supports two methods to isolate
animals from their backgrounds: static background subtraction and
Detector-based subtraction. 

Use background subtraction if:

 - The lighting is stable throughout the video
 - The background is static throughout the video

Use a Detector if:

 - The lighting is different in different parts of the video frame
 - The animals frequently collide and it's important to differentiate between
   them
 - You are performing static image analysis


```{toctree}
:hidden:

background-subtraction
detector
static-image-analysis
```
