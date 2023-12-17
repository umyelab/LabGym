# Installation

In order to successfully install LabGym, you will need to have the following
dependencies installed and available on `PATH`:

 - Python 3.9 or 3.10
 - Git
 - A C/C++ compiler (e.g. `gcc`, `clang`, or Microsoft Visual C++)

We recommend that you follow the instructions below for your operating system
to ensure that the installation goes smoothly. However, if your system
configuration requires that you install these dependencies in a different way,
feel free to go ahead and do that.

## Windows

## macOS

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

2. Install [Homebrew](https://brew.sh/), a command-line package manager for 
   macOS that will simplify the installation of Python. To install Homebrew, run 
   the following command:

   ```console
   % /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   ```{note}
   If you're on an Apple Silicon Mac, you will need to add Homebrew to PATH. To
   do this, enter the following command, then close and reopen your terminal
   window.

   ```console
   % echo 'eval $(/opt/homebrew/bin/brew shellenv)' >> ~/.zprofile
   ```

3. Use Homebrew to install Python 3.10.
   
   ```console
   % brew install python@3.10
   ```

4. Install LabGym via `pip`.
   
   ```console
   % python3.10 -m pip install LabGym
   ```

5. Install Detectron2 via `pip`.

   ```console
   % python3.10 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
   ```

6. Test out your installation by launching LabGym.

   ```console
   % python3.10
   Python 3.10.13 (main, Jun 14 2023, 18:28:58) [Clang 14.0.3 (clang-1403.0.22.14.1)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> from LabGym import gui
   >>> gui.gui()
   ```
   If the LabGym GUI shows up, you have successfully installed LabGym!

## Linux
