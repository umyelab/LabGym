# Windows

To install LabGym on Windows, you will need to access the terminal. To do this, open the start menu by clicking the `Win` key, type "PowerShell", and hit enter. All terminal commands going forward should be entered in this terminal.

1. Install [Python 3.10](https://www.python.org/downloads/release/python-31011/).
   
   Scroll down to the bottom and click the `Windows installer (64-bit)` option. Run the installer and select "Add python to path" and "Disable long path limit".

   To test your Python installation, run the following command. If the version number prints out successfully, your Python installation is working.

   ```pwsh-session
   py -3.10 --version
   ```

2. If you're using an NVIDIA GPU, install CUDA Toolkit 11.8 and cuDNN, and install PyTorch v2.0.1 with cu118 support.

   First, install [CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64). Select your version of Windows, select "exe (local)," then click "Download."

   Next, install [cuDNN](https://developer.nvidia.com/rdp/cudnn-archive). You will need to register an NVIDIA Developer account, which you can do for free. You can choose cuDNN v8.9.7 that supports CUDA toolkit v11.8. Choose 'Local Installer for Windows (Zip)', download and extract it. And then copy the three folders 'bin', 'lib', and 'include' into where the CUDA toolkit is installed (typcially, 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\'), and replace all the three folders with the same names. After that, you may need to add the 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8' to the 'PATH' environmental variable.

   Finally, install PyTorch v2.0.1 with cu118 support.

   ```pwsh-session
   py -3.10 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
   ```

4. Upgrade `pip`, `wheel`, `setuptools`.
   
   ```pwsh-session
   py -3.10 -m pip install --upgrade pip wheel setuptools
   ```

5. Install LabGym via `pip`.
   
   ```pwsh-session
   py -3.10 -m pip install LabGym
   ```

&nbsp;

Launch LabGym:

   ```pwsh-session
   LabGym
   ```
   
   The GUI will take a few minutes to start up during the first launch. If the LabGym GUI shows up, you have successfully installed LabGym!

   If this doesn't work, which typically is because the python3/script is not in your environment path. You can google 'add python3 script to PATH environmental variable in windows' to add it to path, or simply use the following commands to initiate LabGym:

   ```pwsh-session
   py -3.10
   ```
   ```pwsh-session
   from LabGym import __main__
   ```
   ```pwsh-session
   __main__.main()
   ```

