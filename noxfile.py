'''
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext.

For license issues, please contact:

Dr. Bing Ye
Life Sciences Institute
University of Michigan
210 Washtenaw Avenue, Room 5403
Ann Arbor, MI 48109-2216
USA

Email: bingye@umich.edu
'''

import nox
import platform


nox.options.error_on_missing_interpreters=True

EXTRAS_WX_URL = "https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04"


@nox.session(python=['3.9','3.10'],reuse_venv=True)
def tests(session:nox.Session):
    # prefer wheels globally
    session.env["PIP_PREFER_BINARY"]="1"
    session.env["PIP_NO_CACHE_DIR"]="1"

    # Preinstall a wxPython wheel to avoid building from source
    if platform.system() == "Linux":
        session.install(
            "--only-binary=:all:",
            "-f", EXTRAS_WX_URL,
            "wxPython==4.2.1"
        )

        # Force CPU-only PyTorch stack to avoid large CUDA downloads
        session.install(
            "--no-cache-dir",
            "--index-url", "https://download.pytorch.org/whl/cpu",
            "torch==2.8.0",
            "torchvision==0.23.0",
            "torchaudio==2.8.0",
        )


    # package and test dependencies
    session.install("-e", ".")
    session.install("pytest")
    

    session.run("pytest", "-q")


@nox.session(reuse_venv=True)
def docs(session:nox.Session):
    session.install("-U", "pip", "setuptools", "wheel")
    session.install('-r','docs/requirements.txt')
    session.run('make','-C','docs','clean',external=True)
    session.run('sphinx-autobuild','docs','docs/_build/html')
