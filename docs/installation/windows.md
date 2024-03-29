# Windows

To install LabGym on Windows, you will need to access the terminal. To do this,
open the start menu by clicking the `Win` key, type "PowerShell", and hit
enter. All terminal commands going forward should be entered in this terminal.

```{warning}
There is a known issue with LabGym that prevents it from running on Windows 11. 
If you are on Windows 11, we suggest using 
[Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) 
and following along with the [Linux installation instructions](./linux).
```

1. Install [Git][]. 

   If you're unsure of which installation method to use, select the `64-bit Git
   for Windows Setup` option. Run the installer, and accept all default values.

2. Install the [Visual Studio C++ Build Tools][]. 

   Scroll down to the entry that says `Build Tools for Visual Studio 2022` and
   click "Download". 

   ![VS Build Tools Website Screenshot][]
   
   When you run the downloaded executable, you will be prompted to choose what
   tools you will need. Select only the `Desktop Development With C++` 
   workload, then click "Install".

   ![VS Build Tools Installer Screenshot][]

3. Install [Python 3.10][]. Scroll down to the bottom and click the `Windows
   installer (64-bit)` option. Run the installer and accept all default
   options.

   To test your Python installation, run the following command. If the version
   number prints out successfully, your Python installation is working.

   ```pwsh-session
   > py -3.10 --version
   Python 3.10.10
   ```

4. If you're using an Nvidia GPU, install CUDA Toolkit 11.8 and cuDNN.

   First, install and/or update your GPU drivers at
   [this link](https://www.nvidia.com/Download/index.aspx). Select your GPU
   model and click "Search", then click "Download". After installing the
   drivers, reboot your system to ensure they take effect.

   Then, install [CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64).
   Select your version of Windows, select "exe (local)," then click "Download."

   ```{warning}
   If you're using Windows Subsystem for Linux (WSL), please refer to the 
   [Linux](linux) install instructions.
   ```

   To verify your installation of CUDA, use the following command.

   ```pwsh-session
   > set CUDA_HOME=%CUDA_HOME_V11_8%
   > nvcc --version
   nvcc: NVIDIA (R) Cuda compiler driver
   Copyright (c) 2005-2022 NVIDIA Corporation
   Built on Wed_Sep_21_10:41:10_Pacific_Daylight_Time_2022
   Cuda compilation tools, release 11.8, V11.8.89
   Build cuda_11.8.r11.8/compiler.31833905_0
   ```

   Finally, install [cuDNN](https://developer.nvidia.com/cudnn-downloads?target_os=Windows&target_arch=x86_64). 
   You will need to register an Nvidia Developer account, which you can do for
   free.

   ```{important}
   If you're using Windows 11, when installing cuDNN, select "Tarball" then 
   "11" under CUDA Version. Then, follow
   [these instructions](https://docs.nvidia.com/deeplearning/cudnn/installation/windows.html#installing-on-windows)
   to install cuDNN from the `.tar.gz` file.
   ```

   As of February 2024, the latest version is cuDNN 9.0.0, which is compatible
   with CUDA 11.8.


4. Install `pipx` by following 
   [these instructions](https://pipx.pypa.io/stable/installation/).
   
   To test your installation of `pipx`, close and reopen your terminal window,
   then type the following command:

   ```pwsh-session
   > pipx --version
   1.4.3
   ```
   If the version number prints successfully, then your installation is working
   properly. Otherwise, try running the `pipx ensurepath` command again.

5. Install LabGym via `pipx`.
   
   ```pwsh-session
   > pipx install --python 3.10 LabGym
   ```

6. Install PyTorch in LabGym's virtual environment.

   ```pwsh-session
   > pipx inject --index-url https://download.pytorch.org/whl/cu118 LabGym torch==2.0.1 torchvision==0.15.2
   ```

   If you are using LabGym without a GPU, use the following command instead.

   ```pwsh-session
   > pipx inject --index-url https://download.pytorch.org/whl/cpu LabGym torch==2.0.1 torchvision==0.15.2
   ```

6. Install [Detectron2][] in LabGym's virtual environment.
   
   First, download the Detectron2 code using the following command.

   ```pwsh-session
   > git clone https://github.com/facebookresearch/detectron2.git
   ```
   The code should be available in the `C:\Users\<username>\detectron2\`
   folder.

   If you're using a GPU, open the `setup.py` file inside the `detectron2` 
   folder using a text editor (e.g. Notepad, VS Code, etc.). Go to line 79 in 
   the code, then apply the following edit.

   Old version:
   ```{code} python
   :number-lines: 72

   if not is_rocm_pytorch:
       define_macros += [("WITH_CUDA", None)]
       extra_compile_args["nvcc"] = [
           "-O3",
           "-DCUDA_HAS_FP16=1",
           "-D__CUDA_NO_HALF_OPERATORS__",
           "-D__CUDA_NO_HALF_CONVERSIONS__",
           "-D__CUDA_NO_HALF2_OPERATORS__",
       ]
   else:
       define_macros += [("WITH_HIP", None)]
       extra_compile_args["nvcc"] = []
   ```
   New version:
   ```{code} python
   :number-lines: 72

   if not is_rocm_pytorch:
       define_macros += [("WITH_CUDA", None)]
       extra_compile_args["nvcc"] = [
           "-O3",
           "-DCUDA_HAS_FP16=1",
           "-D__CUDA_NO_HALF_OPERATORS__",
           "-D__CUDA_NO_HALF_CONVERSIONS__",
           "-D__CUDA_NO_HALF2_OPERATORS__",
           "-DWITH_CUDA",
       ]
   else:
       define_macros += [("WITH_HIP", None)]
       extra_compile_args["nvcc"] = []
   ```
   Save the `setup.py` file, then exit your text editor.

   Finally, reopen your terminal, then install Detectron2.
   
   ```pwsh-session
   > set CUDA_HOME=%CUDA_HOME_V11_8%
   > pipx runpip LabGym install -e detectron2
   ```

7. Launch LabGym.

   ```pwsh-session
   > LabGym
   ```
   
   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!


[Git]: https://git-scm.com/download/win
[Visual Studio C++ Build Tools]: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
[VS Build Tools Website Screenshot]: /_static/vs-build-tools-website.png
[VS Build Tools Installer Screenshot]: /_static/vs-build-tools-installer.png
[Python 3.10]: https://www.python.org/downloads/release/python-31011/
[Detectron2]: https://github.com/facebookresearch/detectron2
