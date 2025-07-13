"""Provide functions to obtain and forward registration info.

"Public" Functions
    is_registered() -> bool
        Return True if registration data is stored.

    register() -> None
        Get reg info from user, store reginfo locally, and send to receiver.

    get_reginfo_from_file() -> dict | None
        Load registration info from file, and return reginfo.

Example
    import registration

    if not registration.is_registered():
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

Notes
    ...

"Private" Functions
These functions are implementation details and should not be relied upon 
by external code, as they might change without notice in future versions.
By convention they are named with a single leading underscore ("_") to 
indicate to other programmers that they are intended for private or 
internal use.
    _get_reginfo_from_form(variant='dialog w/o frame') -> dict | None
        Display a reg form, get user input, and return reginfo.

    _store_reginfo_to_file(reginfo: dict) -> None
        ...

Should these classes be considered private?  I'm not seeing a public use case.
    RegFormDialog(wx.Dialog)
    NotEmptyValidator(wx.PyValidator)
    RegFrame(wx.Frame)
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import getpass
import logging
import platform
import sys
import textwrap

# Related third party imports.
if sys.platform == 'darwin':  # macOS
    # AppKit is from pyobjc-framework-Cocoa, "Wrappers for the Cocoa
    # frameworks on macOS"
    from AppKit import NSApp, NSApplication
import wx  # Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
import central_logging


logger = logging.getLogger(__name__)


class NotEmptyValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)

    def Clone(self):
        return NotEmptyValidator()

    def Validate(self, parent):
        text_control = self.GetWindow()

        # .strip() removes leading/trailing whitespace
        text = text_control.GetValue().strip() 

        if not text: 
            # the string is empty after stripping whitespace
            wx.MessageBox("This field cannot be empty.", 
                "Error", wx.OK | wx.ICON_ERROR)
            text_control.SetFocus()
            return False
        else:
            return True

    def TransferToWindow(self):
        return True # We don't modify the window's value

    def TransferFromWindow(self):
        return True # We don't modify the validator's associated value


class RegFormDialog(wx.Dialog):
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
        self.skip_button = wx.Button(self, wx.ID_CANCEL, "Skip")

        # Create sizers for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.GridSizer(3, 2, 1, 1)  # rows, cols, vgap, hgap
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        text = wx.StaticText(self, label=header)
        main_sizer.Add(text, 
            0,  # proportion (int).  0 means the item won't expand
                # beyond its minimal size.

            # # border on all sides, align left, and expand
            # # wx.ALL | wx.EXPAND | wx.LEFT,  
            # border on all sides, and align left
            wx.ALL | wx.LEFT,  

            10,  # width (in pixels) of the border specified by the
                 # border flags
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

        # Add buttons to the button sizer
        button_sizer.Add(self.register_button, 0, wx.ALL, 5)
        button_sizer.Add(self.skip_button, 0, wx.ALL, 5)

        # Add sizers to main sizer
        main_sizer.Add(input_sizer, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(button_sizer, 
            0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizerAndFit(main_sizer)

    def GetInputValues(self) -> dict | None:
        result = {
            'name': self.input_name.GetValue(), 
            'affiliation': self.input_affiliation.GetValue(),
            'email': self.input_email.GetValue(),
            }
        return result

    def bring_to_foreground(self):
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


class RegFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(400, 300))
        panel = wx.Panel(self)
        btn = wx.Button(panel, label="Open Dialog")
        btn.Bind(wx.EVT_BUTTON, self.OnOpenDialog)

    def OnOpenDialog(self, event):
        # Using 'with' statement for automatic destruction
        with RegFormDialog(self) as dlg: 
            if dlg.ShowModal() == wx.ID_OK:
                reginfo = dlg.GetInputValues()
                logger.info('%s: %r', 'reginfo', reginfo)
            else:
                print("Dialog cancelled")


def _get_reginfo_from_form(variant='dialog w/o frame') -> dict | None:
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

    assert variant in ['dialog w/o frame', 'dialog w/ frame']

    # Create a wx.App instance.
    app = wx.App()

    if variant == 'dialog w/ frame':
        # Create and show the main frame. 
        logger.debug('%s -- %s', 'RegFrame()', 'calling...')
        frame = RegFrame(None, "Registration Frame")
        logger.debug('%s -- %s', 'RegFrame()', 'returned')
        logger.debug('%s -- %s', 'frame.Show()', 'calling...')
        frame.Show()
        logger.debug('%s -- %s', 'frame.Show()', 'returned')
   
        # Start the main event loop.
        logger.debug('%s -- %s', 'app.MainLoop()', 'calling...')
        app.MainLoop()
        logger.debug('%s -- %s', 'app.MainLoop()', 'returned')

        return reginfo

    assert variant == 'dialog w/o frame'
    with RegFormDialog(None) as dlg: 
        logger.debug('%s -- %s', 'Milestone ShowModal', 'calling...')
        dlg.bring_to_foreground()
        if dlg.ShowModal() == wx.ID_OK:
            logger.debug('%s -- %s', 'Milestone ShowModal', 'returned')
            logger.debug('User pressed [Register]')
            reginfo = dlg.GetInputValues()
        else:
            logger.debug('%s -- %s', 'Milestone ShowModal', 'returned')
            logger.debug('User pressed [Skip]')
            reginfo = None

    logger.debug('%s: %r', 'reginfo', reginfo)
    return reginfo


def register() -> None:
    """Get reg info from user, store reginfo locally, and send to receiver.

    Get reg info from user, add info from a survey of context, and 
    1.  Store reginfo locally.  
    2.  Send reginfo to central receiver via central_logger (unless
        central_logger's disabled attribute is True).

(draft)...
    Display a reg form, store reginfo locally, and send to receiver.

    Display a LabGym registration form, whose onSubmit method (a) stores 
    reginfo locally, and (b) sends reginfo via the central_logger to a 
    central receiver.
    ---
(draft?)
    Notes
    *   The registration info is stored in ~/.labgym/registration.yaml
        (or opts.configdir/registration.yaml?)
    ---
    """
    reginfo = _get_reginfo_from_form()
    logger.debug('%s: %r', 'reginfo', reginfo)

    if reginfo is None:
        return

    # update reginfo dict with supplemental info
    reginfo.update({
        'schema': 'reginfo 2025-07-10',
        'username': getpass.getuser(),
        # date
        # computer os
        # LabGym version
        })

    # 1.  Store reginfo locally.  
    _store_reginfo_to_file(reginfo)

    # 2.  Send reginfo to central receiver via central_logger (unless
    #     central_logger's disabled attribute is True).
    central_logger.info(reginfo)


def _store_reginfo_to_file(reginfo: dict) -> None:
    # TODO -- Implement.
    return
    

def get_reginfo_from_file() -> dict | None:
    """Load registration info from file, and return reginfo."""

    # TODO -- Implement.
    result = None

    return result


def is_registered() -> bool:
    """Return True if registration data is stored."""
    return not get_reginfo_from_file() == None


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s\t%(levelname)s\t%(module)s:%(lineno)d\t%(message)s'
        )

    # demo 
    variant = 'dialog w/o frame'  # default
    # variant = 'dialog w/ frame'

    reginfo = _get_reginfo_from_form(variant=variant)
    logger.debug('%s: %r', 'reginfo', reginfo)
