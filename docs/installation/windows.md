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

3. Install [Python 3.10][]. Scroll down to the bottom and click the `Windows
   installer (64-bit)` option. Run the installer and accept all default
   options.

   To test your Python installation, run the following command. If the version
   number prints out successfully, your Python installation is working.

   ```pwsh-session
   > py -3.10 --version
   Python 3.10.10
   ```

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

6. Install [Detectron2][] in the LabGym's virtual environment.
   
   ```pwsh-session
   > pipx runpip LabGym install 'git+https://github.com/facebookresearch/detectron2.git'
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
