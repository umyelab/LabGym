import json
from urllib import request

from packaging import version

from . import gui
from . import __version__


current_version = version.parse(__version__)
pypi_json = json.loads(
    request.urlopen("https://pypi.python.org/pypi/LabGym/json").read()
)
latest_version = version.parse(pypi_json["info"]["version"])

if latest_version > current_version:
    print(
        f"You are using LabGym {current_version}, but version {latest_version} is available."
    )
    print(
        "Consider upgrading LabGym by using the command 'python3 -m pip install --upgrade LabGym'."
    )
    print("For the details of new changes, check https://github.com/umyelab/LabGym.\n")


gui.gui()
