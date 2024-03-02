# Contributing

Thank you for contributing to LabGym! This guide is meant to be used by anyone
who wishes to make contributions to LabGym. 

```{toctree}
setup
developing
docs
```

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
