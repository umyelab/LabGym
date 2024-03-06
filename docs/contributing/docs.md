# Adding Documentation

LabGym uses Sphinx to generate our documentation website. Sphinx is a tool
that converts text-based formats (e.g. reStructuredText, Markdown) into HTML,
allowing us to easily write documentation. Sphinx supports extensions, which
add functionality to the documentation. Here is a list of the extensions that
the LabGym docs use:

 - `MyST-Parser`: Adds support for Markdown to HTML conversion
 - `sphinx-autobuild`: Provides live-reload server for development, enabling
   automatic re-rendering of documentation when files are changed
 - `furo`: An HTML theme for the documentation
 - `sphinx-copybutton`: Adds a button to copy-paste code blocks
 - `sphinx-inline-tabs`: Adds support for tab environments

## Main Workflow

To install Sphinx and the above extensions, enter your development virtual
environment, then use the following command.

```console
$ python -m pip install -r docs/requirements.txt
```

After installing the documentation dependencies, the workflow looks like this:

1. Start the live-reload server.

   ```console
   $ nox -s docs
   ```

   Navigate to `127.0.0.1:8000` in your browser as instructed by the server
   output.

   ```{note}
   This command uses `nox` to start the `sphinx-autobuild` server. To see how
   it works, look at `noxfile.py` in the project root.
   ```

2. Switch to your text editor, make some changes to the documentation, then 
   save your changes.

3. Switch back to the browser window, then examine your changes.

4. Repeat steps 2-3 until you're satisfied. If you need to close the 
   documentation server, hit `Ctrl+C` in your terminal.

For a reference on Markdown syntax and features in Sphinx, please look at
the [Furo docs](https://pradyunsg.me/furo/), especially the "Markup 
Reference" and "Kitchen Sink" tabs.

## Publishing Your Changes

All documentation is included as a part of LabGym's Git repository, which
means that publishing the documentation is as simple as opening a Pull Request!

If your Pull Request is merged into `master`, then it will be reflected on
<https://labgym.readthedocs.io> within a few minutes. Note that you might have
to use the version switcher in the bottom corner to switch from `stable` to
`latest`, because `stable` points to the latest versioned release of LabGym,
while `latest` points to the latest commit on `master`.

## Notes About Documentation Configuration

 - You might notice that the documentation dependencies are specified in a
   `requirements.txt` file instead of LabGym's `pyproject.toml`. This is
   because ReadTheDocs.io requires that we use the `requirements.txt` format.

 - The `requirements.txt` file contains pinned versions of all documentation
   dependencies and sub-dependencies. If it is ever required to update the
   documentation dependencies, you can ignore the comment at the top of the
   file and replace the contents of the file with the following:

   ```
   sphinx>=7.2.6
   sphinx-autobuild>=2021.3.14
   sphinx-copybutton>=0.5.2
   myst-parser>=2.0.0
   furo>=2023.9.10
   sphinx-inline-tabs>=2023.4.21
   ```
   ````{note}
   Replacing the `requirements.txt` with the contents above will not pin
   the sub-dependencies of the main dependencies, which could cause a
   problem because documentation builds would no longer be reproducible 
   (i.e. ReadTheDocs could use a different version of the sub-dependencies,
   causing the documentation to look different than it does on your local
   machine).

   The current `requirements.txt` was generated using the 
   [`PDM`](https://pdm-project.org/latest/) tool with the 
   following command:

   ```
   pdm export --no-default -dG docs -f requirements --no-hashes > docs/requirements.txt
   ```
   There might be a way to generate this file without using PDM, but
   research needs to be done on this to integrate it into the LabGym
   workflow.
   ````
