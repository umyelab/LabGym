import json
from urllib import request

from . import gui


current_version = 2.2
current_version_check = 22.2

try:
    latest_version = list(
        json.loads(request.urlopen("https://pypi.python.org/pypi/LabGym/json").read())[
            "releases"
        ].keys()
    )[-1]
    latest_version_str = list(latest_version)
    latest_version_str.remove(".")
    latest_version_check = latest_version_str[0]
    for i in latest_version_str[1:]:
        latest_version_check += i
    latest_version_check = float(latest_version_check)
    if latest_version_check > current_version_check:
        print(
            "A newer version "
            + "("
            + str(latest_version)
            + ")"
            + ' of LabGym is available. You may upgrade it by "python3 -m pip install --upgrade LabGym".\nFor the details of new changes, check: "https://github.com/umyelab/LabGym".'
        )
except:
    pass


gui.gui()
