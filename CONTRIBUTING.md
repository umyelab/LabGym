# How to Contribute

Thanks for contributing to LabGym! This guide is mainly intended for members of the Bing Ye Lab at the U-M Life Sciences Institute, but these instructions will work for others
as long as you create a fork of this repository and follow along from there. 

 - [Getting Set Up to Contribute](#getting-set-up-to-contribute)
 - [Adding a New Feature](#adding-a-new-feature)
 - [Collaborating on a Pull Request](#collaborating-on-a-pull-request)
 - [Submitting a Bug Fix](#submitting-a-bug-fix)

## Getting Set Up to Contribute

1. Install Git from [https://git-scm.com/downloads](https://git-scm.com/downloads), then issue the following commands to properly configure Git.
```bash
git config --global user.name "First Last"
git config --global user.email "name@example.com"
git config --global core.editor editorname
```

2. Clone the repository. If you're using a fork of LabGym, replace the URL with that of your fork.
```bash
git clone https://github.com/umyelab/LabGym.git
```

## Adding a New Feature

1. Switch to the master branch and pull the most recent changes from `origin/master`
```bash
git checkout master
git pull
```

2. Create a new branch and switch to it. Replace `add-new-feature` with a short name that describes the feature you want to add; for example,
`feature/add-preprocessing-module`.
```bash
git branch feature/add-new-feature
git checkout feature/add-new-feature
# OR
git checkout -b feature/add-new-feature
```

3. Make your changes, commiting individual steps along the way. Please follow [these guidelines](https://cbea.ms/git-commit/) to write properly formatted commit messages.
Note that most of the time, a subject line is all that is needed. 

4. Push your branch to GitHub. The `-u` flag is important because it enables you to track changes made to your branch by other people.
```bash
git push -u origin feature/add-new-feature
```

5. Go to LabGym on GitHub ([https://github.com/umyelab/LabGym](https://github.com/umyelab/LabGym)) and click the orange banner to submit a Pull Request. Make sure to
write a description of the exact changes you made and why they are relevant. If your changes are accepted, they will be merged into `master`, and you can safely delete
`feature/add-new-feature` on your local repository.

## Collaborating on a Pull Request

To test out and modify code in a pull request authored by someone else, do the following:

1. If you're collaborating on this pull request for the first time, fetch the upstream branch and switch to it. 
```bash
git fetch origin branch-name
git checkout branch-name
```
Otherwise, pull the latest changes. 
```bash
git checkout branch-name
git pull
```

2. Test out the code. If you need to make edits, follow the same commit guidelines as in [Adding a New Feature](#adding-a-new-feature).

3. Once your changes are ready, then push them back to GitHub.
```bash
git push
```

## Submitting a Bug Fix

To submit a bug fix, follow the same instructions as in [Adding a New Feature](#adding-a-new-feature), but name your branch `bugfix/fix-this-bug` or `hotfix/fix-this-bug` instead. 
