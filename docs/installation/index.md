# Installation

In order to successfully install LabGym, you will need to have the following
dependencies installed and available on `PATH`:

 - Python 3.9 or 3.10 or 3.11
 - Git
 - A C/C++ compiler (e.g. `gcc`, `clang`, or Microsoft Visual C++)

If you are on a Windows or Linux system with an Nvidia GPU, you will need the
following installed to enable GPU-accelerated training:

 - CUDA Toolkit 11.8
 - cuDNN

We recommend that you follow the instructions below for your operating system
to ensure that the installation goes smoothly. However, if your system
configuration requires that you install these dependencies in a different way,
(e.g. you're using a computing cluster that uses Lmod to load Python) feel 
free to go ahead and do that.

The simplest way to install LabGym is using `pip`. You can also use 
[`pipx`](https://pipx.pypa.io/stable/installation/) to install LabGym in case
you use Python for other research tasks and have multiple version of
Python or Python libraries like NumPy and TensorFlow installed. Using `pipx` ensures that LabGym and its 
dependencies can be installed in an isolated environment with the correct 
version of Python, while allowing the `LabGym` command to be recognized 
globally in the terminal. For more information, please see the system-specific 
instructions below.

```{toctree}
windows
macos
linux
```
