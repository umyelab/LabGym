"""Provide functions to obtain and send registration info.

"Public" Functions
    is_registered -- Return True if registration data is stored.

    register --
        Get reg info from user, store reginfo locally, and send to receiver.

    get_reginfo_from_file --
        Load registration info from file, and return reginfo.

"Private" Functions
These functions are implementation details and should not be relied upon 
by external code, as they might change without notice in future versions.
    _get_reginfo_from_form --
        Display a reg form, get user input, and return reginfo.

    _store_reginfo_to_file -- ...


Example
    if not registration.is_registered():
        # Get reg info from user, store reginfo locally.  Also, send 
        # reginfo to central receiver via central_logger (unless
        # central_logger's disabled attribute is True).
        registration.register()
"""

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



class RegForm(wx.Frame):
    # def __init__(self, parent, title):
    def __init__(self):
        # super(RegForm, self).__init__(parent, title=title, size=(300, 200))
        wx.Frame.__init__(self, None, wx.ID_ANY, title='My Form')

        # Create a panel
        # self.panel?  Will I need access to it later?
        panel = wx.Panel(self, wx.ID_ANY)

        # Create sizers for layout.
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.GridSizer(3, 2, 5, 5)  # Rows, Cols, VGap, HGap
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Why label with "User Group Registration" instead of, say, 
        # "Software Registration"?  Because this label suggests that 
        # registration is in the user's interest and the user 
        # community's interest.  ("Free Very Valuable User Group 
        # Registration" seems too much though.)
        text = wx.StaticText(panel, label="LabGym User Group Registration")
        main_sizer.Add(text, 0, wx.ALL | wx.CENTER, 10)

        # Create string input fields
        self.text_name = wx.TextCtrl(panel)
        self.text_affiliation = wx.TextCtrl(panel)
        self.text_email = wx.TextCtrl(panel)

        # Create buttons
        register_button = wx.Button(panel, label="Register")
        register_button.Bind(wx.EVT_BUTTON, self.on_register)
        skip_button = wx.Button(panel, label="Skip")
        skip_button.Bind(wx.EVT_BUTTON, self.on_skip)

        # Add input fields to the input sizer
        input_sizer.Add(wx.StaticText(panel, label="Name:"), 
            0, wx.ALIGN_CENTER_VERTICAL)
        input_sizer.Add(self.text_name, 1, wx.EXPAND)

        input_sizer.Add(wx.StaticText(panel, label="Affiliation:"), 
            0, wx.ALIGN_CENTER_VERTICAL)
        input_sizer.Add(self.text_affiliation, 1, wx.EXPAND)

        input_sizer.Add(wx.StaticText(panel, label="Email address:"), 
            0, wx.ALIGN_CENTER_VERTICAL)
        input_sizer.Add(self.text_email, 1, wx.EXPAND)

        # Add buttons to the button sizer
        button_sizer.Add(register_button, 0, wx.ALL | wx.CENTER, 5)
        button_sizer.Add(skip_button, 0, wx.ALL | wx.CENTER, 5)

        # Add sizers to main sizer
        main_sizer.Add(input_sizer, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)
        self.Center()
        self.Show()

    def on_register(self, event):
        # validate data entry... or message and return without closing

        reginfo = {
            'name': self.text_name.GetValue(),
            'affiliation': self.text_affiliation.GetValue(),
            'email': self.text_email.GetValue(),
            }

        reginfo.update({
            'schema': 'reginfo 2025-07-10',
            'username': getpass.getuser(),
            })

        logger.info('%s: %r', 'reginfo', reginfo)

        central_logger = central_logging.get_central_logger()
        central_logger.info(reginfo)

        self.Close() # Close this window when Register is clicked

    def on_skip(self, event):
        self.Close() # Close this window when Skip is clicked


def _get_reginfo_from_form() -> dict | None:
    """Display a reg form, get user input, and return reginfo.


    ---
    Display a reg form, store reginfo locally, and send to receiver.

    Display a LabGym registration form, whose onSubmit method (a) stores 
    reginfo locally, and (b) sends reginfo via the central_logger to a 
    central receiver.

    Notes
    *   The registration info is stored in ~/.labgym/registration.yaml
        (or opts.configdir/registration.yaml?)
    """

    app = wx.PySimpleApp()
    logger.debug('%s -- %s', 'RegForm().Show()', 'calling...')
    frame = RegForm().Show()
    logger.debug('%s -- %s', 'RegForm().Show()', 'returned')
    logger.debug('%s -- %s', 'app.MainLoop()', 'calling...')
    app.MainLoop()
    logger.debug('%s -- %s', 'app.MainLoop()', 'calling...')

    # can I still access the objects after MainLoop returns?
    logger.debug('%s: %r', 'frame', frame)
    logger.debug('%s: %r', 'dir(frame)', dir(frame))
    

    # result = {
    #     'schema': 'reginfo 2025-07-10',
    #     'username': getpass.getuser(),
    #     'name': 'James Stewart',
    #     # 'rank': 'Brigadier General',
    #     # 'serial number': 'O-433210',
    #     'affiliation': 'US Army Air Forces, Air Force Reserve',
    #     'email': '',
    #     }
    # 
    # return result


def register() -> None:
    """Get reg info from user, store reginfo locally, and send to receiver.

    Get reg info from user, store reginfo locally.  Also, send 
    reginfo to central receiver via central_logger (unless
    central_logger's disabled attribute is True).
    """
    reginfo = _get_reginfo_from_form()
    logger.debug('%s: %r', 'reginfo', reginfo)

    if reginfo is None:
        return

    _store_reginfo_to_file(reginfo)
    central_logger.info(reginfo)


def _store_reginfo_to_file(reginfo: dict) -> None:
    # TODO
    return
    

def get_reginfo_from_file() -> dict | None:
    """Load registration info from file, and return reginfo."""

    # TODO
    result = None

    return result


def is_registered() -> bool:
    """Return True if registration data is stored."""
    return not get_reginfo_from_file() == None


if __name__ == '__main__':
    # logger.error('Milepost alfa (e)')
    # logger.warning('Milepost alfa (w)')
    # logger.info('Milepost alfa (i)')
    # logger.debug('Milepost alfa (d)')
    #
    # # this isn't honored... maybe logging config already performed by an import.
    # logging.basicConfig(level=logging.DEBUG)
    # # logging.getLogger().setLevel(logging.DEBUG)
    # print('Milepost')
    #
    # logger.error('Milepost bravo (e)')
    # logger.warning('Milepost bravo (w)')
    # # WHY ARE THESE NOT PRODUCING?
    # logger.info('Milepost bravo (i)')
    # logger.debug('Milepost bravo (d)')
    #
    # print('Milepost Z -- %s: %r\n' % ('dir(logger)', dir(logger)))
    #
    # print(f'Milepost E -- root logger level: {logging.getLogger().level}')
    # print(f'Milepost E -- this logger level: {logger.level}')
    # print(f'Milepost E -- this logger effectivelevel: {logger.getEffectiveLevel()}')
    # print(f'Milepost E -- this logger disabled flag: {logger.disabled}')
    # print(f'Milepost E -- this logger propagate flag: {logger.propagate}')
    # print(f'Milepost E -- this logger hasHandlers(): {logger.hasHandlers()}')
    # print(f'Milepost E -- this logger filters: {logger.filters}')
    #
    # sys.exit('intentional abend')

    logging.basicConfig(level=logging.DEBUG)

    _get_reginfo_from_form()

    # app = wx.PySimpleApp()
    # frame = RegForm().Show()
    # app.MainLoop()
