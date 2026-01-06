# Internal Notes

This document contains notes for members of the 
[umyelab](https://github.com/umyelab) organization on LabGym's development
processes. If you are not a member of the Ye Lab, please disregard
these instructions.

## Releasing a New Version of LabGym

Before releasing a new version of LabGym, ensure you have your [development
environment](./setup.md) set up properly. Then, follow these instructions.

1. Select a new version number.

   LabGym uses [Semantic Versioning](https://semver.org/), so if the current
   version is `2.3.4`, for example, your new version number should be:
   
   1. `2.3.5` if you're making a bugfix in a backwards compatible way.

   2. `2.4.0` if you're introducing a new feature in a backwards compatible
      way.

   Since the name LabGym2 is used in the LabGym paper to differentiate it
   from LabGym1, the first number in the version should NOT be incremented
   unless a new paper is being written as a result of major changes to the
   application. 
   
2. Create a new branch for the release. 

   If you're introducing a bugfix, your new branch should be created off of
   the most recent release instead of `master` to ensure that any in-progress
   features are not released with the bugfix. If the old version is `2.3.4`,
   for example, then run the following commands:

   ```console
   $ git checkout v2.3.4
   $ git switch -c release-v2.3.5
   ```

   If you're releasing a new feature, then your new branch can be created off
   of `master`. If the old version is `2.3.4`, for example, then run the
   following commands:

   ```console
   $ git switch master
   $ git pull
   $ git switch -c release-v2.4.0
   ```

3. Bump the version number.

   To do this, go into the `LabGym/__init__.py` file and change the value of
   the `__version__` variable. Note that while the branch name will contain a
   "v" at the beginning (e.g. `v2.3.4`), the `__version__` variable should NOT
   contain the leading "v".

4. Update the changelog in `docs/changelog.md`. After updating the changelog, 
   run `nox -s docs` to ensure that the docs are built properly.

?. Ensure the working dir is "clean", in that there are no uncommitted 
   py-file changes, because py-file content impacts hash.

   Compute the hash for the LabGym package, and store it in 
   LabGym/pkghash/versions.toml.  
   (See instructions in the docstring in LabGym/pkghash/__init__.py.)

   Commit
   `$ git add LabGym/pkghash/versions.toml`
   `$ git commit -m "Add reference version+hashval to versions.toml."`  

5. Create a tag for the new version.

   Note that the Git tag DOES contain the leading "v". For example, if the new 
   version is `2.4.0`, then run:

   ```console
   $ git tag v2.4.0
   ```

6. Push the branch and the new tag to GitHub.
   
   ```console
   $ git push -u origin release-v2.4.0
   $ git push origin v2.4.0
   ```

7. Open a Pull Request for the new release branch, then wait for the test suite
   to pass. Do not merge the PR yet.

8. Go to the LabGym homepage, then click "Releases", then click "Draft a new
   release". 

   Under "Choose a tag", select the tag that you pushed. Then, click
   "Generate release notes". Ensure that the release notes look correct, then
   click "Publish release". 

   This will trigger a GitHub Action that deploys the new version to the Python
   Package Index (PyPI). For more information, see [CI/CD
   Pipeline](#ci-cd-pipeline).

9. After verifying that the deployment is successful, merge the release PR
   into `master`.

## CI/CD Pipeline

LabGym uses Continuous Integration (CI) to ensure that changes made to the code
pass the test suite and don't introduce any breaking changes for users, and it
uses Continous Deployment (CD) to automatically publish LabGym to PyPI once a
new version is released. 

To automatically run the test suite and deploy new versions, LabGym uses GitHub
Actions, which is a platform that provides free servers that can be used to run
such automated tasks. The tasks to run are configured via `.yml` files in the
`.github/workflows` folder in the repository. For a reference on the
configuration, please refer to <https://docs.github.com/en/actions/quickstart>.

### CI

The CI workflow is defined in `.github/workflows/ci.yml`, and is configured to
run on every Pull Request. Currently, the CI workflow runs the unit test suite
using `nox`, running the `tests()` function in `noxfile.py`. 

Although the test suite is defined using the `pytest` module, `pytest` itself
can only use one version of Python at a time. Since LabGym supports both Python
3.9 and 3.10, it's necessary to test on both versions of Python to ensure that,
for example, a PR doesn't include Python features that are supported on Python
3.10 but not on Python 3.9. `nox` allows us to test both versions by creating a
separate virtual environment for each Python version, then it installs and runs
`pytest` in each environment. For more information, check out the [Nox
documentation](https://nox.thea.codes/en/stable/).

The final part of the CI pipeline is automatic documentation builds, which are
useful when previewing documentation to make sure it gets built correctly. The
documentation builds are triggered using a webhook, which is configured
separately from GitHub Actions. For the most part, you should never need to
touch the webhook configuration, and you can check on the status of
documentation builds at <https://readthedocs.org/projects/labgym/> or by
clicking the ReadTheDocs icon at the bottom of the documentation website.

### CD

The CD workflow is defined in `.github/workflows/python-publish.yml`. The
workflow builds
[wheels](https://packaging.python.org/en/latest/glossary/#term-Wheel) for
LabGym, then uploads them to PyPI. For more information, take a look at
<https://github.com/pypa/gh-action-pypi-publish>.



