"""Provide functions to obtain, store, and forward registration info.

"Public" Functions
    is_registered() -> bool
        Return True if registration data is stored.

    register() -> None
        Get reg info from user, store reginfo locally, and send to receiver.

    get_reginfo_from_file() -> dict | None
        Load registration info from file, and return reginfo.

Example 1
    import registration

    if not registration.is_registered():
        # Get reg info from user, store reginfo locally.  Also, send
        # reginfo to central receiver via central_logger (unless
        # central_logger's disabled attribute is True).
        registration.register()

Example 2
    import registration

    reginfo = registration.get_reginfo_from_file()

    # if user has skipped registration (with checked "Don't ask again")
    # but that was selected in some different (earlier?) installation,
    # then expire or void the "skip-henceforth" behavior.
    skip_pass_void = (reginfo is not None
        and reginfo.get('name') == 'skip'
        and packaging.version.parse(version)
            != packaging.version.parse(reginfo.get('version'))
        )

    # if not registration.is_registered():
    if not registration.is_registered() or skip_pass_void:
        # Get reg info from user, store reginfo locally.  Also, send
        # reginfo to central receiver via central_logger (unless
        # central_logger's disabled attribute is True).
        registration.register()

Strengths
    *   Input text fields are validated as not-empty before acceptance.
    *   On macOS, displays form on foreground/top, instead of hidden
        below other windows.

Weaknesses
    *   This module file is long.  It should be refactored into a
        package with smaller module files.

"Private" Functions
    These functions are implementation details and should not be relied
    upon by external code, as they might change without notice in future
    versions.
    By convention they are named with a single leading underscore ("_")
    to indicate to other programmers that they are intended for private
    or internal use.

    _get_reginfo_from_form() -> dict | None
        Display a reg form, get user input, and return reginfo.

    _store_reginfo_to_file(reginfo: dict) -> None
        Store registration info to file in user's LabGym config directory.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
from datetime import datetime
import getpass
import logging
from pathlib import Path
import platform
import sys
import textwrap
import uuid
from zoneinfo import ZoneInfo

# Related third party imports.
# pylint: disable=wrong-import-position
if sys.platform == 'darwin':  # macOS
# pylint: enable=wrong-import-position
    # AppKit is from package pyobjc-framework-Cocoa, "Wrappers for the
    # Cocoa frameworks on macOS".
    from AppKit import NSApp, NSApplication
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version
import yaml  # PyYAML, YAML parser and emitter for Python

# Local application/library specific imports.
from LabGym import __version__ as version
from LabGym import central_logging
from LabGym import config


logger = logging.getLogger(__name__)


# class NotEmptyValidator(wx.PyValidator):
class NotEmptyValidator(wx.Validator):
    """Validate that a text control contains content.

    (class purpose and functionality, and optionally its attributes and methods)
    """
    def __init__(self):
        wx.Validator.__init__(self)

    def Clone(self):  # pylint: disable=invalid-name
        return NotEmptyValidator()

    def Validate(self, parent):  # pylint: disable=invalid-name
        text_control = self.GetWindow()

        # .strip() removes leading/trailing whitespace
        text = text_control.GetValue().strip()

        if not text:
            # the string is empty after stripping whitespace
            wx.MessageBox("This field cannot be empty.",
                "Error", wx.OK | wx.ICON_ERROR)
            text_control.SetFocus()
            return False

        # Milepost -- text is not empty
        return True

    def TransferToWindow(self):  # pylint: disable=invalid-name
        return True # We don't modify the window's value

    def TransferFromWindow(self):  # pylint: disable=invalid-name
        return True # We don't modify the validator's associated value


class RegFormDialog(wx.Dialog):
    """Make a registration form dialog.

    (class purpose and functionality, and optionally its attributes and methods)
    """
    def __init__(self, parent):
        # Why label with "User Group Registration" instead of, say,
        # "Software Registration"?  Because this label suggests that
        # registration is in the user's interest and the user
        # community's interest.
        title = "LabGym User Group Registration"

        header = textwrap.dedent("""
            Please register to be enrolled in the LabGym User Group.

            The LabGym User Group promotes engagement between new users,
            experienced users, and developers, leading to improvements
            in user experience, including better features, better
            implementation, and better installation.
            """).strip()

        super().__init__(parent, title=title)

        # Create string input fields
        my_validator = NotEmptyValidator()  # do we need three separate?
        self.input_name = wx.TextCtrl(self, validator=my_validator)
        self.input_affiliation = wx.TextCtrl(self, validator=my_validator)
        self.input_email = wx.TextCtrl(self, validator=my_validator)

        # Create buttons
        self.register_button = wx.Button(self, wx.ID_OK, "Register")
        fontsize = self.register_button.GetFont().GetPointSize()
        logger.debug('%s: %r', 'fontsize + 2', fontsize + 2)
        font = wx.Font(fontsize + 2,
            wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.register_button.SetFont(font)
        self.skip_button = wx.Button(self, wx.ID_CANCEL, "Skip for now")

        # Create the checkbox
        self.my_checkbox = wx.CheckBox(self,
            label='Remember my choice, don\'t ask me again')

        # Create sizers for layout.
        # Buttons and checkbox will go in the same FlexGridSizer as the
        # text input fields.
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.FlexGridSizer(6, 2, 1, 1)  # rows, cols, vgap, hgap

        # Allow col 0 to be shrinkable (even though proportion is 0 for items)
        # This allows it to shrink to the size of its content
        input_sizer.AddGrowableCol(0)

        text = wx.StaticText(self, label=header)
        main_sizer.Add(text,
            0,  # proportion (int).  0 means the item won't expand
                # beyond its minimal size.

            # border on all sides, and align left
            wx.ALL | wx.LEFT,

            10,  # width (in pixels) of the borders specified
            )

        # Add input fields with labels to the input sizer
        input_sizer.Add(wx.StaticText(self, label="Name:"),
            0, wx.ALL | wx.EXPAND, 5)
        input_sizer.Add(self.input_name,
            1, wx.EXPAND)
        input_sizer.Add(wx.StaticText(self, label="Affiliation:"),
            0, wx.ALL | wx.EXPAND, 5)
        input_sizer.Add(self.input_affiliation,
            1, wx.EXPAND)
        input_sizer.Add(wx.StaticText(self, label="Email Address:"),
            0, wx.ALL | wx.EXPAND, 5)
        input_sizer.Add(self.input_email,
            1, wx.EXPAND)

        # Add a row of dummy empty spacer items
        input_sizer.Add((0,10), 0)  # add a fixed-height spacer of 10 pixels
        input_sizer.AddSpacer(0)  # leave this cell blank

        # Add buttons to the sizer
        input_sizer.Add(self.register_button, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        input_sizer.Add(self.skip_button, 0, wx.ALL, 5)
        # Add a dummy empty spacer item
        input_sizer.AddSpacer(0)  # leave this cell blank
        input_sizer.Add(self.my_checkbox,
            0, wx.LEFT | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # Add sizers to main sizer
        main_sizer.Add(input_sizer, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(main_sizer)

    def GetInputValues(self, alt=None) -> dict | None:
        """Return a dict containing the dialog object's input values.

        If alt-behavior specified as 'skip', then return a dict of dummy val.
        """
        if alt is None:
            result = {
                'name': self.input_name.GetValue(),
                'affiliation': self.input_affiliation.GetValue(),
                'email': self.input_email.GetValue(),
                }
        elif alt == 'skip':
            result = {
                'name': 'skip',
                'affiliation': 'skip',
                'email': 'skip',
                }
        else:
            # bad usage...
            logger.warning('%s: %r', 'Unexpected!  alt', alt)
            result = {}
        return result

    def bring_to_foreground(self) -> None:
        """Bring the window to the foreground.

        We want the form window displayed to the user.

        On macOS 12.7, with app started from terminal, I'm seeing:
        *   the registration dialog is displayed, but doesn't have focus
            and is under the windows of the active app (terminology?),
            potentially hidden completely.
        *   a bouncing python rocketship icon in the tray.  The bouncing
            stops when you mouseover the icon.  Also some other actions
            can stop the bouncing or just pause the bouncing... weird.

        I wasn't able to resolve this on macOS using the wx.Dialog
        object's Raise, SetFocus, and Restore methods.
        Instead, ...
            "Calling NSApp().activateIgnoringOtherApps_(True) via
            AppKit: This macOS workaround uses the AppKit module to
            explicitly activate the application, ignoring other running
            applications.  This is typically done after your wxPython
            application has started and its main window is shown."
        """

        if sys.platform == 'darwin':  # macOS
            NSApplication.sharedApplication()
            NSApp().activateIgnoringOtherApps_(True)


def _get_reginfo_from_form() -> dict | None:
    """Display a reg form, get user input, and return reginfo.

    Notes
    *   In wxPython, the ShowModal() method displays a dialog window in
        a modal fashion. This means it:

        o   Blocks Interaction: The dialog takes over the application's
            focus, preventing the user from interacting with any other
            windows in the application until the dialog is closed.

        o   Requires User Response: The user must explicitly close the
            modal dialog before returning to the main application workflow.

        o   Returns a Value: The ShowModal() method returns a value
            (e.g., wx.ID_OK, wx.ID_CANCEL) indicating how the user
            closed the dialog (e.g., by clicking "OK" or "Cancel").

        In simpler terms, using ShowModal() is like presenting a
        mandatory popup that demands the user's attention and a decision
        before they can continue using the application.

        This differs from the Show() method, which displays a dialog in
        a modeless fashion. A modeless dialog allows the user to
        interact with other application windows while it's open.
    """

    # Create a wx.App instance.
    app = wx.App()

    with RegFormDialog(None) as dlg:
        logger.debug('%s -- %s', 'Milestone ShowModal', 'calling...')
        dlg.bring_to_foreground()
        if dlg.ShowModal() == wx.ID_OK:
            logger.debug('%s -- %s', 'Milestone ShowModal', 'returned')
            logger.debug('User pressed [Register]')
            # pylint: disable-next=redefined-outer-name
            reginfo = dlg.GetInputValues()
        else:
            logger.debug('%s -- %s', 'Milestone ShowModal', 'returned')
            logger.debug('User pressed [Skip]')

            if dlg.my_checkbox.GetValue():
                logger.debug('Checked')
                reginfo = dlg.GetInputValues('skip')
            else:
                logger.debug('Unchecked')
                reginfo = None

    logger.debug('%s: %r', 'reginfo', reginfo)
    return reginfo


def register(central_logger=None) -> None:
    """Get reg info from user, store reginfo locally, and send to receiver.

    1.  Get reg info from user.
    2.  Add info from a survey of context.
    3.  Store reginfo locally.
    4.  Send reginfo to central receiver via central_logger (unless
        central_logger's disabled attribute is True).

    In production use, central_logger is not passed in, central_logger is
    obtained by calling central_logging.get_central_logger.

    For development and testing, central_logger may be overridden by the
    caller, like
        registration.register(central_logger=logging.getLogger('Local Logger'))

    (I'm ambivalent on this... central_logger could be made a required arg,
    and then no need to obtain it independently from inside this function.)
    """
    if central_logger is None:
        central_logger = central_logging.get_central_logger()

    # pylint: disable-next=redefined-outer-name
    reginfo = _get_reginfo_from_form()
    logger.debug('%s: %r', 'reginfo', reginfo)

    if reginfo is None:
        return

    # update reginfo dict with supplemental info from a survey of context
    reginfo.update({
        'schema': 'reginfo 2025-07-10',
        'username': getpass.getuser(),

        'datetime': datetime.now(ZoneInfo('US/Eastern')).strftime(
            '%Y-%m-%dT%H:%M:%S%z'),
        'uuid': str(uuid.uuid4()),

        'platform': platform.platform(),
        'node': platform.node(),
        'version': version,  # LabGym version
        })

    try:
        _store_reginfo_to_file(reginfo)
        reginfo.update({'status': 'saved to regfile'})
    except Exception as e:
        reginfo.update({'status': 'unable to save to regfile'})

    central_logger.info(reginfo)


# pylint: disable-next=redefined-outer-name
def _store_reginfo_to_file(reginfo: dict) -> None:
    """Store registration info to file in user's LabGym config directory.

    Save/store/stow/write reginfo dict to ~/.labgym/registration.yaml.
    Or more accurately, <configdir>/registration.yaml.

    Notes to developer
    *   Consider pros/cons of saving in a more opaque form.
        zip-file instead of yaml?  with '.done' extension instead of
        '.zip' so it looks like a flag-file instead of a discardable
        backup.
    *   Re naming the reciprocal functions, write/read?, store/recall?
        backup, dump, put, save, store, stow, write
        get, load, read, recall, restore
    """

    # Get all of the values needed from config.get_config().
    configdir: Path = config.get_config()['configdir']

    # ensure configdir exists
    configdir.mkdir(parents=True, exist_ok=True)

    # write reginfo file
    regfile = configdir.joinpath('registration.yaml')
    with open(regfile, 'w', encoding='utf-8') as f:
        yaml.dump(reginfo, f, default_flow_style=False)


def get_reginfo_from_file() -> dict | None:
    """Load registration info from file, and return reginfo."""

    # Get all of the values needed from config.get_config().
    configdir: Path = config.get_config()['configdir']

    # read reginfo file
    regfile = configdir.joinpath('registration.yaml')

    try:
        with open(regfile, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
    except Exception:
        result = None

    return result


def is_registered() -> bool:
    """Return True if there is a readable regfile."""
    return not get_reginfo_from_file() is None


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s\t%(levelname)s\t%(module)s:%(lineno)d\t%(message)s'
        )

    reginfo = _get_reginfo_from_form()
    logger.debug('%s: %r', 'reginfo', reginfo)
