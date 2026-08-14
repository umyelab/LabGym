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
nox.options.reuse_existing_virtualenvs=False

EXTRAS_WX_URL = "https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04"

# macOS Python 3.9 (wxPython ~4.2.x / Cocoa) can abort during interpreter
# teardown when repeated real-wx.App lifecycle modules are alphabetically
# interleaved with the rest of the native-importing suite. Isolate those
# modules in a separate pytest process for Darwin+3.9 only; they are not
# skipped. Add any future test module that creates/manages a real wx.App
# fixture to this list.
MACOS39_REAL_APP_TEST_FILES = (
	"LabGym/tests/test_categorizer_class_mismatch.py",
	"LabGym/tests/test_diagnostics_cm_colors.py",
	"LabGym/tests/test_interactive_results_checkbox.py",
	"LabGym/tests/test_triage_guards.py",
	"LabGym/tests/test_mywx.py",
	"LabGym/tests/test_registration.py",
	"LabGym/tests/test_userdata_survey.py",
)


@nox.session(python=['3.9','3.10'])
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
			"torch==2.8.0+cpu",
			"torchvision==0.23.0+cpu",
			"torchaudio==2.8.0+cpu",
		)
	elif platform.system() == "Darwin":
		# Keep the macOS GUI stack on the version family that completes CI cleanly.
		session.install(
			"--only-binary=:all:",
			"wxPython==4.2.4",
			"pyobjc-framework-Cocoa==11.1",
		)
	elif platform.system() == "Windows":
		# Verified Windows CPU family; editable install below enforces numpy<=1.26.4
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

	# Darwin + Python 3.9: isolate real-wx.App lifecycle modules in process 1.
	session_python = str(session.python)
	if platform.system() == "Darwin" and (
		session_python == "3.9" or session_python.startswith("3.9.")
	):
		session.run("pytest", "-q", *MACOS39_REAL_APP_TEST_FILES)
		ignore_args = [f"--ignore={path}" for path in MACOS39_REAL_APP_TEST_FILES]
		session.run(
			"pytest",
			"-q",
			"LabGym/tests",
			*ignore_args,
			"tests/test_load.py",
			"tests/test_main.py",
		)
	else:
		session.run("pytest", "-q")


@nox.session(reuse_venv=True)
def docs(session:nox.Session):
	session.install("-U", "pip", "setuptools", "wheel")
	session.install('-r','docs/requirements.txt')
	session.run('make','-C','docs','clean',external=True)
	session.run('sphinx-autobuild','docs','docs/_build/html')
