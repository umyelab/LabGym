# Linux/WSL

Depending on which distribution of Linux you use, the process of installing
packages will look slightly different. Select the appropriate distribution
below and follow along from there. These instructions also work for the
Windows Subsystem for Linux (WSL).

```{note}
If you're using Arch Linux or one of its derivatives, we assume you have the 
`yay` package manager installed to install dependencies from the AUR.
```

1. Update your system's package manager, then install `gcc`, `git`, and 
   Python 3.10.

   ````{tab} Ubuntu/Debian/WSL
   ```console
   $ sudo apt update
   $ sudo apt install build-essential git python3.10
   ```
   ````

   ````{tab} Arch
   ```console
   $ sudo pacman -Syu
   $ sudo pacman -S gcc git
   $ yay -S python310
   ```
   ````

2. If you're using an NVIDIA GPU, install CUDA Toolkit 11.8 and cuDNN.

   First, install and/or update your GPU drivers at
   [this link](https://www.nvidia.com/Download/index.aspx). Select your GPU
   model and click "Search", then click "Download". After installing the
   drivers, reboot your system to ensure they take effect.

   Then, install [CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Linux&target_arch=x86_64).
   Select your version of Linux, then follow the instructions to install CUDA
   for your operating system.

   To verify your installation of CUDA, use the following command.

   ```pwsh-session
   > nvcc --version
   nvcc: NVIDIA (R) Cuda compiler driver
   Copyright (c) 2005-2022 NVIDIA Corporation
   Built on Wed_Sep_21_10:41:10_Pacific_Daylight_Time_2022
   Cuda compilation tools, release 11.8, V11.8.89
   Build cuda_11.8.r11.8/compiler.31833905_0
   ```

   ```{note}
   If you run into issues installing CUDA, check out these resources:
    - [CUDA Installation Documentation](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#package-manager-installation)
      (these instructions are for the latest version of CUDA, so make sure to 
      refer to the previous link for instructions specific to CUDA 11.8)
    - [Detailed instructions for Ubuntu](https://gist.github.com/MihailCosmin/affa6b1b71b43787e9228c25fe15aeba)
      (ignore the PyTorch installation instructions at the bottom, as LabGym
      requires specific versions of PyTorch specified below)
    - [Detailed instructions for WSL](https://rachitsingh.com/notes/wsl-cuda/)
      (ignore the TensorRT and Python packages instructions at the bottom)
   ```

   Finally, install cuDNN by following [these instructions](https://docs.nvidia.com/deeplearning/cudnn/installation/linux.html#installing-on-linux). 
   Scroll down until you see instructions for your operating system, then
   follow them. You will need to register an Nvidia Developer account, which 
   you can do for free.

   As of February 2024, the latest version is cuDNN 9.0.0, which is compatible
   with CUDA 11.8.

3. Upgrade `pip`, `wheel`, `setuptools`.

   ```console
   $ python3 -m pip install --upgrade pip wheel setuptools
   ```

4. Install LabGym via `pip`.
 
   ```console
   $ python3 -m pip install LabGym
   ```

5. Install Pytorch v2.0.1.

   ```console
   $ python3 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
   ```

   If you are using LabGym without a GPU, use the following command instead.

   ```console
   $ python3 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
   ```


6. Install [Detectron2][].

   ```console
   $ python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git@a59f05630a8f205756064244bf5beb8661f96180'
   ```

7. Launch LabGym.

   ```console
   $ LabGym
   ```

   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

&nbsp;

If you use `pipx`, from step #4:

&nbsp;
   

4. Install `pipx` by following 
   [these instructions](https://pipx.pypa.io/stable/installation/). 
   
   To test your installation of `pipx`, close and reopen your terminal window,
   then type the following command:

   ```console
   $ pipx --version
   1.4.3
   ```
   If the version number prints successfully, then your installation is working
   properly. Otherwise, try running the `pipx ensurepath` command again.

5. Install LabGym via `pipx`.
   
   ```console
   $ pipx install --python python3.10 LabGym
   ```
   
   ```{note}
   If you're on WSL and you run into issues with the installation of wxPython,
   use [this resource](https://www.pixelstech.net/article/1599647177-Problem-and-Solution-for-Installing-wxPython-on-Ubuntu-20-04)
   to install the necessary dependencies for wxPython. Then, rerun the above
   command to install LabGym.
   ```

6. Install PyTorch in LabGym's virtual environment.

   ```console
   $ pipx inject --index-url https://download.pytorch.org/whl/cu118 LabGym torch==2.0.1 torchvision==0.15.2
   ```

   If you are using LabGym without a GPU, use the following command instead.

   ```console
   $ pipx inject --index-url https://download.pytorch.org/whl/cpu LabGym torch==2.0.1 torchvision==0.15.2
   ```

7. Install [Detectron2][] in the LabGym's virtual environment.
   
   ```console
   $ pipx runpip LabGym install 'git+https://github.com/facebookresearch/detectron2.git@a59f05630a8f205756064244bf5beb8661f96180'
   ```

8. Launch LabGym.

   ```console
   $ LabGym
   ```
   
   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

[Detectron2]: https://github.com/facebookresearch/detectron2
