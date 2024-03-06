# Developing a Contribution

## Making Your Changes

1. Switch to the master branch and pull the most recent changes from 
   `origin/master`

   ```console
   $ git checkout master
   $ git pull --rebase
   ```

   ```{important}
   If you're using a fork to develop LabGym, you should go to your fork and
   click the "Sync fork" button before running the above commands. This will 
   pull the latest changes from the main LabGym repository. For more
   information, see [this page](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork).
   ```

2. Create a branch for the changes you want to make and switch to it.

   ```console
   $ git switch -c new-branch-name
   ```

   Make sure your branch name is descriptive of the change you're making. If
   you're submitting a bugfix, please start your branch name with `bugfix-` to
   help us differentiate it.

3. Create your contribution! Use the command `python -m LabGym` to launch 
   LabGym with your changes.

   ```{tip}
   Make sure to commit individual steps along the way, following
   [these guidelines](https://cbea.ms/git-commit/) to write good commit
   messages. If you create any new files, add them by using the 
   `git add <file>` command prior to creating the commit.
   ```

4. Make sure that your code passes the test suite.

   ```console
   $ nox -s tests
   ```

   The test suite is a work-in-progress. It currently checks that LabGym will 
   launch properly on both Python 3.9 and 3.10. 

   ```{important}
   Make sure that you've followed the [setup instructions](./setup) to install
   _both_ Python 3.9 and 3.10. This will ensure that the test suite runs
   properly.
   ```

   You might find it necessary to modify or add tests in the suite. To do so,
   go to the `tests` directory and find the corresponding test. 

   The layout of the `tests` directory is intended to mirror that of the 
   `LabGym` package, except each file begins with `tools_`. For example, the 
   tests for the functions in `LabGym/tools.py` go in the 
   `tests/test_tools.py`. Each test is a Python function that begins with
   `test_`. These two naming conventions ensure that the test runner, `pytest`, 
   is able to detect the tests.

5. Document your changes. 

   This is perhaps the most important step, as LabGym is a complex app, and 
   explaining your code will make it easier for other developers to understand 
   how LabGym works. Make sure to follow all of the following guidelines.

   - When writing or modifying a function, be sure to add type signatures to 
     the function's parameters and the return type. This will ensure that
     static analysis tools build into IDEs like VS Code will catch
     type-related bugs, reducing the potential for such bugs reaching users.

   - Always write docstrings for each function and class you create or modify.
     We prefer using [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) 
     docstrings, so make sure to familiarize yourself with these guidelines.

   - If necessary, make changes to LabGym's documentation website by following
     the [documentation website guide](./docs).

## Submitting a Pull Request

1. Push your branch to GitHub.

   ```console
   $ git push -u origin new-branch-name
   ```

   If you need to make changes after submitting your Pull Request, you can 
   simply use `git push`.

2. Open a Pull Request (PR). 

   Go to LabGym's [GitHub repository](https://github.com/umyelab/LabGym) and
   click the orange banner to submit a PR. In the text box, write a message 
   explaining the changes you've made.

   If you need to review changes you made to the documentation website, you 
   can do so by clicking the "View details" button, then click the "Details" 
   button next to the ReadTheDocs.io workflow.

   If your changes are accepted, they will be merged into `master` and you can
   safely delete your new branch on your local repository.

## Collaborating on a Pull Request

When collaborating with someone else, you will likely need to make changes to
another person's Pull Request. Follow these instructions to do so successfully.

```{note}
Currently, these instructions are only guaranteed to work for members of the
Ye Lab who have write access to the main `umyelab/LabGym` repository.
```

1. If this is the first time you're collaborating on this PR, fetch the
   upstream branch and switch to it.

   ```console
   $ git fetch origin branch-name
   $ git switch branch-name
   ```

   Otherwise, pull the latest changes from GitHub.

   ```console
   $ git checkout branch-name
   $ git pull
   ```

2. Make changes to the code, following the guidelines in 
   [Making Your Changes](#making-your-changes).

3. Once your changes are ready, push them back to GitHub.

   ```console
   $ git push
   ```

   Your changes will appear in the commit timeline under the Pull Request.

