# Linux

Depending on which distribution of Linux you use, the process of installing
packages will look slightly different. Select the appropriate distribution
below and follow along from there. These instructions also work for the
Windows Subsystem for Linux (WSL).

```{note}
If you're using Arch Linux or one of its derivatives, we assume you have the 
`yay` package manager installed to install dependencies from the AUR.
```

1. Update your system's package manager, then install `gcc`, `git`, and 
   Python 3.10.

   ````{tab} Ubuntu/Debian
   ```console
   $ sudo apt update
   $ sudo apt install build-essential git python3.10
   ```
   ````

   ````{tab} Arch
   ```console
   $ sudo pacman -Syu
   $ sudo pacman -S gcc git
   $ yay -S python310
   ```
   ````

2. Install `pipx` by following 
   [these instructions](https://pipx.pypa.io/stable/installation/). 
   
   To test your installation of `pipx`, close and reopen your terminal window,
   then type the following command:

   ```console
   $ pipx --version
   1.4.3
   ```
   If the version number prints successfully, then your installation is working
   properly. Otherwise, try running the `pipx ensurepath` command again.

3. Install LabGym via `pipx`.
   
   ```console
   $ pipx install --python python3.10 LabGym
   ```

4. Install [Detectron2][] in the LabGym's virtual environment.
   
   ```console
   $ pipx runpip LabGym install 'git+https://github.com/facebookresearch/detectron2.git'
   ```

5. Launch LabGym.

   ```console
   $ LabGym
   ```
   
   The GUI will take a few minutes to start up during the first launch. If the 
   LabGym GUI shows up, you have successfully installed LabGym!

[Detectron2]: https://github.com/facebookresearch/detectron2
