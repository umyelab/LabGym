# Linux/WSL

Depending on which distribution of Linux you use, the process of installing packages will look slightly different. Select the appropriate distribution below and follow along from there. These instructions also work for the Windows Subsystem for Linux (WSL).

```{note}
If you're using Arch Linux or one of its derivatives, we assume you have the `yay` package manager installed to install dependencies from the AUR.
```

1. Update your system's package manager, then install `gcc`, `git`, and Python 3.10.

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

   First, install and/or update your GPU drivers at [this link](https://www.nvidia.com/Download/index.aspx). Select your GPU model and click "Search", then click "Download". After installing the drivers, reboot your system to ensure they take effect.

   Then, install [CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Linux&target_arch=x86_64). Select your version of Linux, then follow the instructions to install CUDA for your operating system.

   To verify your installation of CUDA, use the following command.

   ```pwsh-session
   $ nvcc --version
   nvcc: NVIDIA (R) Cuda compiler driver
   Copyright (c) 2005-2022 NVIDIA Corporation
   Built on Wed_Sep_21_10:41:10_Pacific_Daylight_Time_2022
   Cuda compilation tools, release 11.8, V11.8.89
   Build cuda_11.8.r11.8/compiler.31833905_0
   ```

   Finally, install cuDNN by following [these instructions](https://docs.nvidia.com/deeplearning/cudnn/installation/linux.html#installing-on-linux). Scroll down until you see instructions for your operating system, then follow them. You will need to register an NVIDIA Developer account, which you can do for free.

3. Upgrade `pip`, `wheel`, `setuptools`.

   ```console
   $ python3 -m pip install --upgrade pip wheel setuptools
   ```
   
4. Install wxPython

   ```console
   $ sudo apt update
   $ apt-get install libgtk-3-dev
   $ sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0
   $ python3 -m pip install six
   $ python3 -m pip install --upgrade six
   $ python3 -m pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython
   ```

5. Install LabGym via `pip`.
 
   ```console
   $ python3 -m pip install LabGym
   ```

6. If you're using an NVIDIA GPU, Install Pytorch v2.0.1 with CUDA 11.8.
   
   ```console
   $ python3 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
   ```
   
&nbsp;

Launch LabGym:

   ```console
   $ LabGym
   ```

   The GUI will take a few minutes to start up during the first launch. If the LabGym GUI shows up, you have successfully installed LabGym!

   If this doesn't work, which typically is because the python3/script is not in your environment path. You can google 'add python3 script to path linux' to add it to path, or simply use the following commands to initiate LabGym:

   ```console
   $ python3

   >>> from LabGym import __main__
   >>> __main__.main()
   ```
