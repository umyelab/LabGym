# Contributing

Thank you for contributing to LabGym! This guide is meant to be used by anyone
who wishes to make contributions to LabGym. 

```{toctree}
setup
```

## Getting Set Up to Contribute

1. Install Git from [https://git-scm.com/downloads](https://git-scm.com/downloads), then issue the following commands to properly configure Git.
   ```console
   git config --global user.name "First Last"
   git config --global user.email "name@example.com"
   git config --global core.editor editorname
   ```

2. Clone the repository. If you're using a fork of LabGym, replace the URL with that of your fork.
   ```console
   git clone https://github.com/umyelab/LabGym.git
   ```

3. Move into the LabGym directory and create a virtual environment. Replace the
   `python` command with whichever command points to Python 3.9 or Python 3.10
   on your system. Then, activate the virtual environment.
   ```console
   cd LabGym
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Install LabGym's dependencies in the virtual environment. This command uses
   `pip` to install all the dependencies listed in the `setup.py` file in the
   current directory (hence the `.`), and installs LabGym in editable mode
   (`-e`), which keeps the source files in place, allowing you to make changes
   to the code.
   ```console
   python -m pip install -e .
   ```

5. Install detectron2 in the virtual environment.
   ```console
   python -m pip install "git+https://github.com/facebookresearch/detectron2.git"
   ```

6. Test your setup by launching LabGym. If the LabGym GUI shows up, your setup
   is successful.
   ```console
   python -m LabGym
   ```

## Adding a New Feature

1. Switch to the master branch and pull the most recent changes from `origin/master`
   ```console
   git checkout master
   git pull
   ```

2. Create a new branch and switch to it. Replace `add-new-feature` with a short name that describes the feature you want to add; for example,
`feature/add-preprocessing-module`.
   ```console
   git branch feature/add-new-feature
   git switch feature/add-new-feature
   # OR
   git checkout -b feature/add-new-feature
   ```

3. Make your changes, commiting individual steps along the way. Please follow [these guidelines](https://cbea.ms/git-commit/) to write properly formatted commit messages.
Note that most of the time, a subject line is all that is needed. 

4. Push your branch to GitHub. The `-u` flag is important because it enables you to track changes made to your branch by other people.
   ```console
   git push -u origin feature/add-new-feature
   ```

5. Go to LabGym on GitHub ([https://github.com/umyelab/LabGym](https://github.com/umyelab/LabGym)) and click the orange banner to submit a Pull Request. Make sure to
write a description of the exact changes you made and why they are relevant. If your changes are accepted, they will be merged into `master`, and you can safely delete
`feature/add-new-feature` on your local repository.

## Collaborating on a Pull Request

To test out and modify code in a pull request authored by someone else, do the following:

1. If you're collaborating on this pull request for the first time, fetch the upstream branch and switch to it. 
   ```console
   git fetch origin branch-name
   git switch branch-name
   ```
   Otherwise, pull the latest changes. 
   ```console
   git checkout branch-name
   git pull
   ```

2. Test out the code. If you need to make edits, follow the same commit guidelines as in [Adding a New Feature](#adding-a-new-feature).

3. Once your changes are ready, then push them back to GitHub.
   ```console
   git push
   ```

## Submitting a Bug Fix

To submit a bug fix, follow the same instructions as in [Adding a New Feature](#adding-a-new-feature), but name your branch `bugfix/fix-this-bug` or `hotfix/fix-this-bug` instead. 

## Adding Documentation

LabGym uses Sphinx to generate HTML documentation from Markdown files with the [`Furo`](https://pradyunsg.me/furo/) documentation theme. To contribute to the documentation, you will need to install some dependencies. If you're using a virtual environment, activate it, then run the following command to install the documentation dependencies.

```console
python -m pip install -r docs/requirements.txt
```

To start the local documentation server, move into the `docs` directory and 
run the following command.

```console
cd docs
make livehtml
```

Navigate to `https://localhost:8000` in your browser, where you should see the LabGym documentation!

For a reference on documentation format, check out the [Furo documentation](https://pradyunsg.me/furo/reference). Make sure to select the tab that says `Markdown (MyST)` - we prefer writing documentation in Markdown instead of reStructuredText for readability for developers who might not be familiar with reStructuredText.
