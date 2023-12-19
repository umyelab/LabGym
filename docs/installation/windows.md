# Windows

To install LabGym on Windows, you will need to access the terminal. To do this,
open the start menu by clicking the `Win` key, type "PowerShell", and hit
enter. All terminal commands going forward should be entered in this terminal.

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

3. Install [Python 3.9.7][]. Accept all default values from the installer.

   LabGym only supports Python 3.9 and 3.10. Since your PC might have multiple
   versions of Python installed, we highly recommend using the `py.exe`
   launcher to ensure you're using the correct version of Python. `py.exe`
   is installed by default with every Python installation, so to test your
   Python installation, run the following command in a terminal:

   ```pwsh-session
   > py -3.9 --version
   Python 3.9.7
   ```

   ```{important}
   In general, any time you see the command `python` in this documentation,
   you should replace it with `py -3.9` to ensure you're using Python 3.9.
   ```

4. Install LabGym via `pip`.
   
   ```pwsh-session
   > py -3.9 -m pip install LabGym
   ```

5. Install Detectron2 via `pip`. 
   
   ```pwsh-session
   > py -3.9 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
   ```

6. Launch LabGym.

   ```pwsh-session
   > py -3.9
   Python 3.9.7 (tags/v3.9.7:1016ef3, Aug 30 2021, 20:19:38) [MSC v.1929 64 bit (AMD64)] on win32
   Type "help", "copyright", "credits" or "license" for more information.
   >>>
   ```
   In the Python interpreter, type the following commands. LabGym might take a
   few minutes to start up upon first installation.
   
   ```pycon
   >>> from LabGym import gui
   >>> gui.gui()
   ```

   If the LabGym GUI shows up, you have successfully installed LabGym! To exit
   LabGym, close the GUI window that pops up.

[Git]: https://git-scm.com/download/win
[Visual Studio C++ Build Tools]: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
[VS Build Tools Website Screenshot]: /_static/vs-build-tools-website.png
[VS Build Tools Installer Screenshot]: /_static/vs-build-tools-installer.png
[Python 3.9.7]: https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe
