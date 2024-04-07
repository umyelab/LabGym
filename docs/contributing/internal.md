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
   Package Index (PyPI). For more information, see [CI/CD Pipeline](#ci-cd-pipeline).

9. After verifying that the deployment is successful, merge the release PR
   into `master`.

## CI/CD Pipeline


