# Initial Setup

1. Follow LabGym's [installation instructions](../installation/index) for
   your operating system, up to but NOT including the installation of `pipx`.
   After following these instructions, you should have the following
   installed:
      - Git
      - A C/C++ Compiler
      - Python 3.10
      - CUDA 11.8 (if using GPU)
      - cuDNN (if using GPU)

2. Install Python 3.9 using the OS-specific installation instructions described
   in Step 1. If you're on Windows, install Python 3.9 from 
   [this link](https://www.python.org/downloads/release/python-3913/). 

   ```{important}
   It's necessary to have both Python 3.9 and 3.10 installed in order to test
   LabGym on both versions of Python. This will ensure that, for example, 
   you don't accidentally use a feature of Python that is compatible with
   Python 3.10 but not Python 3.9, introducing an incompatibility for the
   users.

   ```

3. Issue the following commands to properly configure Git. For more information
   on editor configuration, please see [this source](https://docs.github.com/en/get-started/getting-started-with-git/associating-text-editors-with-git).

   ```console
   $ git config --global user.name "First Last"
   $ git config --global user.email "name@example.com"
   $ git config --global core.editor editorname
   ```

4. Create a [GitHub account](https://github.com/join), then clone the 
   repository.

   If you are a member of the Ye Lab, please send a Slack message to Henry Hu 
   to add you to the "umyelab" organization on GitHub. This will give you 
   access to make changes directly to the LabGym repository. Once you have 
   access, navigate to the directory where you store your code on your local 
   machine using `cd`, then use the following command to clone the repository.

   ```console
   $ git clone https://github.com/umyelab/LabGym.git
   ```

   If you aren't a member of the Ye Lab, create a fork by clicking the "Fork"
   button on LabGym's GitHub page. Then, clone the repository using the 
   following command.

   ```console
   $ git clone https://github.com/<your-github-username>/LabGym.git
   ```

3. Move into the LabGym directory, create a virtual environment, and activate 
   it. 
   ````{tab} macOS/Linux
   ```console
   $ cd LabGym
   $ python3.10 -m venv .venv
   $ source .venv/bin/activate
   ```
   ````

   ````{tab} Windows
   ```pwsh-session
   > cd LabGym
   > py -3.10 -m venv .venv
   > .venv\bin\activate
   ```
   ````

4. Install LabGym's dependencies in the virtual environment. 

   ```console
   $ python -m pip install -e .
   ```

   ```{note}
   Since you're in a virtual environment, you should no longer need to use the
   OS-specific `python` commands.
   ```

   This command uses `pip` to install all the dependencies listed in LabGym's 
   `pyproject.toml` file, which is located in the current directory 
   (hence the `.`). The `-e` flag installs LabGym in "editable mode", which
   means the code is kept in place for you to make changes to.

5. If you're on Windows or Linux, install PyTorch. If you're on macOS, PyTorch
   will already be installed.

   ````{tab} GPU
   ```console
   $ python -m pip install --index-url https://download.pytorch.org/whl/cu118 torch==2.0.1 torchvision==0.15.2
   ```
   ````

   ````{tab} CPU Only
   ```console
   $ python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.0.1 torchvision==0.15.2
   ```
   ````

5. Install Detectron2.

   ````{tab} macOS/Linux
   ```console
   $ python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
   ```
   ````

   ````{tab} Windows
   On Windows, you will need to configure your Detectron2 installation for
   GPU use.

   First, download the Detectron2 code using the following command.

   ```pwsh-session
   > git clone https://github.com/facebookresearch/detectron2.git
   ```

   The code will now be present in a `detectron2` subfolder within the
   LabGym folder.

   If you're using a GPU, open the `setup.py` file inside the `detectron2` 
   folder using your text editor (e.g. VS Code) and make the following change.

   Old version:
   ```{code} python
   :number-lines: 72

   if not is_rocm_pytorch:
       define_macros += [("WITH_CUDA", None)]
       extra_compile_args["nvcc"] = [
           "-O3",
           "-DCUDA_HAS_FP16=1",
           "-D__CUDA_NO_HALF_OPERATORS__",
           "-D__CUDA_NO_HALF_CONVERSIONS__",
           "-D__CUDA_NO_HALF2_OPERATORS__",
       ]
   else:
       define_macros += [("WITH_HIP", None)]
       extra_compile_args["nvcc"] = []
   ```
   New version:
   ```{code} python
   :number-lines: 72

   if not is_rocm_pytorch:
       define_macros += [("WITH_CUDA", None)]
       extra_compile_args["nvcc"] = [
           "-O3",
           "-DCUDA_HAS_FP16=1",
           "-D__CUDA_NO_HALF_OPERATORS__",
           "-D__CUDA_NO_HALF_CONVERSIONS__",
           "-D__CUDA_NO_HALF2_OPERATORS__",
           "-DWITH_CUDA",
       ]
   else:
       define_macros += [("WITH_HIP", None)]
       extra_compile_args["nvcc"] = []
   ```
   Save the `setup.py` file, then exit your text editor.

   Finally, reopen your terminal, `cd` to the main LabGym folder, then install 
   Detectron2.
   
   ```pwsh-session
   > set CUDA_HOME=%CUDA_HOME_V11_8%
   > python -m pip install -e detectron2
   ```
   ````

6. Test your setup by launching LabGym. If the LabGym GUI shows up, your setup
   is successful!

   ```console
   $ python -m LabGym
   ```

   ```{note}
   Launching LabGym while developing is intentionally different than launching
   LabGym as a user. 

   If you wanted to launch LabGym using the `LabGym` command, you would need to
   run `python -m pip install -e .` each time you made changes, which is
   unnecessarily cumbersome.

   Launching LabGym through `python -m LabGym` runs the `__main__.py` file,
   which allows you to immediately see the results of your changes.
   ```

10. Install [`nox`](https://nox.thea.codes/en/stable/), the development
    workflow runner for LabGym.

    ```console
    $ python -m pip install nox
    ```

11. Install [Ruff](https://docs.astral.sh/ruff/), a linter and formatter for
    Python. If you're using VS Code, you can install the 
    [Ruff VS Code Extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff).
    
    Then, configure your editor to format your code on save using Ruff. For 
    example, on VS Code, you can add the following to your User `settings.json`:

    ```json
    "[python]": {
       "editor.defaultFormatter": "charliermarsh.ruff"
       "editor.formatOnSave": true
    }
    ```
