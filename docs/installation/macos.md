# macOS

To access the terminal on macOS, use `Cmd+Space` to enter Spotlight Search, then search for "Terminal" and hit enter to open it. Next, follow these steps to install LabGym.


1. Install [Python 3.10](https://www.python.org/downloads/release/python-31011/). Scroll down to the bottom and click the `macOS 64-bit universal2 installer` option. Run the installer and select "Add python to path".

2. Upgrade `pip`, `wheel`, `setuptools`.

   ```console
   python3 -m pip install --upgrade pip wheel setuptools
   ```

3. Install LabGym via `pip`.
 
   ```console
   python3 -m pip install LabGym
   ```

4. You may want to downgrade PyTorch to v2.0.1:
   
   ```console
   python3 -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
   ```

&nbsp;

Launch LabGym:

   ```console
   LabGym
   ```

   The GUI will take a few minutes to start up during the first launch. If the LabGym GUI shows up, you have successfully installed LabGym!

   If this doesn't work, which typically is because the python3/script is not in your environment path. You can google 'add python3 script to path mac' to add it to path, or simply use the following commands to initiate LabGym:

   ```console
   python3
   ```
   ```console
   from LabGym import __main__
   ```
   ```console
   __main__.main()
   ```

