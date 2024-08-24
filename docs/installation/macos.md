# macOS

To access the terminal on macOS, use `Cmd+Space` to enter Spotlight Search,
then search for "Terminal" and hit enter to open it. Next, follow these steps
to install LabGym.

1. Install the Xcode command line tools, a software package provided by
   Apple that includes `git` and a C/C++ compiler named `clang`.

   ```console
   % xcode-select --install
   ```
   A GUI installation window should pop up. Follow along and accept all
   the default values. 

2. Install [Python 3.10][]. Scroll down to the bottom and click the `macOS 64-bit universal2 installer` option. Run the installer and select "Add python to path".

3. Upgrade `pip`, `wheel`, `setuptools`.

   ```console
   % python3 -m pip install --upgrade pip wheel setuptools
   ```

4. Install LabGym via `pip`.
 
   ```console
   % python3 -m pip install LabGym
   ```

5. If you want to use LabGym Detector function:
   
   5.1. Install [Detectron2][].
   
      ```console
      % python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
      ```

   If you encounter the installation issues, we recommend you try downgrade PyTorch. You may try torch v2.0.1:
   
      ```console
      % python3 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
      ```

    And try installing Detectron2 again.

Launch LabGym:

   ```console
   % LabGym
   ```

   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

   If this doesn't work, which typically is because the python3/script is not in your environment path. You can google 'add python3 script to path mac' to add it to path, or simply use the following commands to initiate LabGym:

   ```console
   % python3

   >>> from LabGym import __main__
   >>> __main__.main()
   ```

&nbsp;

If you use `pipx`, from step #4:

&nbsp;
   
4. Install `pipx` by following 
   [these instructions](https://pipx.pypa.io/stable/installation/).

   To test your installation of `pipx`, close and reopen your terminal window,
   then type the following command:

   ```console
   % pipx --version
   1.4.3
   ```
   If the version number prints successfully, then your installation is working
   properly. Otherwise, try running the `pipx ensurepath` command again.

5. Install LabGym via `pipx`.

   ```console
   % pipx install --python python3.10 LabGym
   ```

6. If you want to use LabGym Detector function:

   6.1. Install [Detectron2][] in the LabGym's virtual environment.

      ```console
      % pipx runpip LabGym install 'git+https://github.com/facebookresearch/detectron2.git'
      ```

Launch LabGym:

   ```console
   % LabGym
   ```

   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

[Python 3.10]: https://www.python.org/downloads/release/python-31011/
[Detectron2]: https://github.com/facebookresearch/detectron2
