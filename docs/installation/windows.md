# Windows

To install LabGym on your Windows system, first ensure that [Git](https://git-scm.com/download/win) is installed. The installer will give you the option to add it to your path variable, it is recommended that you do so.

1. Install the [Visual Studio C++ build tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022). 
   
   When you run the downloaded executable, you will be prompted to choose what tools you will need. Select only the Desktop development with C++ workload.

   Visual Studio C++ build tools are a set of packages managed and distributed by Microsoft -- they're also a  dependency of LabGym. Users unfamiliar with software development are unlikely to have this dependency met and should use the installer linked above.
   Accept all defaults from the installer.


2. Install [Python 3.9.7](https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe). 

   LabGym is built with Python, and it's necessary for its installation as well as its use.
   Using the installer linked above, select all default options. When asked to add Python to your PATH variable, do so, and then proceed to accept all default options.

   Verify that Python is successfully installed
   ```console
   C:\Users\...>python --version
   Python 3.9.7
   ```


3. Open Windows Powershell
   Using either the keyboard shortcut `Windows+X` and selecting `Terminal`, or by using your taskbar's search, open Windows PowerShell.


4. Install LabGym via `pip`.
   
   In Windows PowerShell, enter the following command. The installation may take a few minutes.
   ```console
   C:\Users\...>python -m pip install LabGym
   ```


5. Install Detectron2 via `pip`. `git` is required for the Detectron2.
   
   Continuing in Windows PowerShell, enter the following command.
   ```console
   C:\Users\...>python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
   ```


6. Launch LabGym.

   ```console
   C:\Users\...>python
   Python 3.9.7 (tags/v3.9.7:1016ef3, Aug 30 2021, 20:19:38) [MSC v.1929 64 bit (AMD64)] on win32
   Type "help", "copyright", "credits" or "license" for more information.
   >>> from LabGym import gui
   >>> gui.gui()
   ```
   If the LabGym GUI shows up, you have successfully installed LabGym!

To close LabGym, enter `Ctrl+C` while on your terminal to terminate the process.