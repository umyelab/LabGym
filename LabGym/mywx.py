"""Provide function to guard from multiple instantiations of wx.App

Public Functions
    App -- Return the wx.App object.
    bring_wxapp_to_foreground -- Bring the wx app to the foreground.

Public Classes
    None

Use
    import mywx
    app = mywx.App()
or
    import mywx
    mywx.App()
instead of
    import wx
    app = wx.App()
for added protection against creating two wx.App objects at once.  

This implementation uses the common approach of using a module-level 
variable to store the value after its initial creation.
This pattern is often referred to as memoization or lazy initialization.

A side benefit of this implementation is that a reference to object
is preserved (as module variable _cached_app), so it doesn't get garbage
collected when used like
    import mywx
    mywx.App()

Note that mywx.App could be implemented as a subclass of wx.App instead 
of a function.  It would use a custom __new__ method to guard against 
creating multiple instances, and a custom __init__ method to guard 
against re-initializing the singleton object.
If a custom OnInit method was desired, the scales would be tipped in
favor of the subclass implementation over the function implementation.

"wx.App is supposed to be used as a singleton.  It doesn't own the 
frames that are created in its OnInit, but instead assumes that it is 
supposed to manage and deliver events to all the windows that exist in 
the application."

"the OnInit is called during the construction of the App (after the
toolkit has been initialized) not during the MainLoop call."
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations
    
# Standard library imports.
import logging
import sys

# Related third party imports.
if sys.platform == 'darwin':  # macOS
    # AppKit is from package pyobjc-framework-Cocoa, "Wrappers for the
    # Cocoa frameworks on macOS".
    from AppKit import NSApp, NSApplication
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
# (none)


logger = logging.getLogger(__name__)

_cached_app = None


def App():
    """Return the wx.App object."""

    global _cached_app
 
    if _cached_app is not None:
        return _cached_app

    # Milestone -- This must be the first time running this function.
    # Construct the app obj, cache it, and return it.

    app = wx.App()
    logger.debug('%s: %r', 'app', app)

    _cached_app = app
    return app


def bring_wxapp_to_foreground() -> None:
    """Bring the wx app to the foreground.

    We want the wx app displayed to the user, not initially obscured by 
    windows from other apps.

    On macOS 12.7, with LabGym started from terminal, I'm seeing:
    *   the registration dialog is displayed, but doesn't have focus
        and is under the windows of the active app (terminology?),
        potentially hidden completely.
    *   a bouncing python rocketship icon in the tray.  The bouncing
        stops when you mouseover the icon.  Also some other actions
        can stop the bouncing or just pause the bouncing... weird.

    I wasn't able to resolve this on macOS using the wx.Dialog object's 
    Raise, SetFocus, and Restore methods.
    Instead, this approach worked for me...
        "Calling NSApp().activateIgnoringOtherApps_(True) via AppKit: 
        This macOS workaround uses the AppKit module to explicitly 
        activate the application, ignoring other running applications.  
        This is typically done after your wxPython application has 
        started and its main window is shown."
    """ 

    if sys.platform == 'darwin':  # macOS
        NSApplication.sharedApplication()
        NSApp().activateIgnoringOtherApps_(True)
