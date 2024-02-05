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

2. Install [Homebrew](https://brew.sh/), a command-line package manager for 
   macOS that will simplify the installation of Python. To install Homebrew, run 
   the following command:

   ```console
   % /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   ````{note}
   If you're on an Apple Silicon Mac, you will need to add Homebrew to PATH. To
   do this, enter the following command, then close and reopen your terminal
   window.

   ```console
   % echo 'eval $(/opt/homebrew/bin/brew shellenv)' >> ~/.zprofile
   ```
   ````

3. Use Homebrew to install Python 3.10.
   
   ```console
   % brew install python@3.10
   ```
   
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

6. Install [Detectron2][] in the LabGym's virtual environment.
   
   ```console
   % pipx runpip LabGym install 'git+https://github.com/facebookresearch/detectron2.git'
   ```

7. Launch LabGym.

   ```console
   % LabGym
   ```
   
   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

[Detectron2]: https://github.com/facebookresearch/detectron2
