# Windows

To install LabGym on Windows, you will need to access the terminal. To do this, open the start menu by clicking the `Win` key, type "PowerShell", and hit enter. All terminal commands going forward should be entered in this terminal.

1. Install [Python 3.10](https://www.python.org/downloads/release/python-31011/).
   
   Scroll down to the bottom and click the `Windows installer (64-bit)` option. Run the installer and select "Add python to path" and "Disable long path limit".

   To test your Python installation, run the following command. If the version number prints out successfully, your Python installation is working.

   ```pwsh-session
   py -3.10 --version
   ```

2. Install the verified PyTorch 2.8 family for LabGym on Windows.

   The default, verified path is the official PyTorch CPU wheels:

   ```pwsh-session
   py -3.10 -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
   ```

   LabGym’s Windows package requirements use these base versions. Matching official CPU or CUDA builds (for example `2.8.0+cpu`) satisfy them.

   If you need GPU acceleration, install a PyTorch **2.8**-compatible CUDA wheel from [PyTorch’s current installation guidance](https://pytorch.org/get-started/locally/) for your supported hardware and CUDA runtime. Do not use older LabGym documentation that pinned PyTorch 2.0.1.

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
