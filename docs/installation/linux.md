# Linux

Using the Windows Subsystem for Linux (WSL), or a Linux machine, install LabGym with the following instructions.

1. Install miniconda.

   ```console
   $ sudo wget -c https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   $ sudo chmod +x Miniconda3-latest-Linux-x86_64.sh
   $ ./Miniconda3-latest-Linux-x86_64.sh
   ```
   Press enter to read through the licensing until you get a line prompting you for a `yes/no`, enter `yes`.

2. Restart your shell.

3. Create a virtual environment using miniconda.
   
   ```console
   $ conda create -n LabGym python=3.9.7
   ```
   Enter `y` to proceed.

4. Install LabGym in your virtual environment.
   First, to avoid build errors, install tensorrt and LibGTK
   ```console
   $ pip install tensorrt
   $ sudo apt install libgtk-3-dev
   ```

   Now to install LabGym proper.
   ```console
   $ python -m pip install LabGym
   ```

5. Install Detectron2 in your virtual environment.

   ```console
   $ python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
   ```

6. Test out your installation by launching LabGym.

   ```console
   $ python
   Python 3.9.7 (default, Sep 16 2021, 13:09:58)
   [GCC 7.5.0] :: Anaconda, Inc. on linux
   Type "help", "copyright", "credits" or "license" for more information.
   >>> from LabGym import gui
   >>> gui.gui()
   ```
   If the LabGym GUI shows up, you have successfully installed LabGym!
