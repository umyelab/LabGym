"""
Provide functions for flagging user data that is located internal to LabGym.

Public functions
    Specialized Functions
        survey
        assert_userdata_dirs_are_separate
        offer_to_mkdir_userdata_dirs
        advise_on_internal_userdata_dirs
        warn_on_orphaned_userdata

    General-purpose Functions
        is_path_under(path1: str|Path, path2: str|Path) -> bool
        is_path_equivalent(path1: str|Path, path2: str|Path) -> bool
        resolve(path1: str|Path) -> str
        dict2str(arg: dict, hanging_indent: str=' '*16) -> str
        get_list_of_subdirs(parent_dir: str|Path) -> List[str]
        open_in_browser

Public classes: None

Design issues
*   Why is the user-facing text using the term "folder" instead of "dir"
    or "directory"?
    As Gemini says,
        When authoring dialog text for display to the user, "folder" is
        generally the better terminology for a general audience using a
        graphical user interface (GUI), while "directory" is appropriate
        for technical users or command-line interfaces (CLI). The
        abbreviation "dir" should be avoided in user-facing text.

*   Why sometimes use a webbrowser instead of only dialog text?
    Because
    +   The user can't select and copy the wx.Dialog text into a 
        clipboard (observed on MacOS).  
    +   A wx.Dialog disappears when LabGym is quit.  By displaying 
        instructions in a separate app, they can still be referenced 
        after LabGym is quit.
    +   Formatting... It's more efficient to write content in html 
        instead of hand-formatting text for a wx.Dialog.
    There are other possible approaches... prepare the instructions in
    html, then use html2text library to get formatted text from the 
    html, and display that in a wx.Dialog.

The path args for the functions in this module should be absolute
(full) paths, not relative (partial) paths.  That's the assumption
during development.  If that assumption is violated, are unintended
consequences possible?
Instead of answering that question, implement guards.
(1) Enforce with asserts?
        assert Path(arg).is_absolute()
(2) Or, enforce with asserts in the Specialized functions, but not the
    General-purpose functions?
(3) Or, guard by decorating selected functions, instead of individually
    adding the right mix of assert statements to function bodies.
For now, choosing (2).

The survey function has an early-exit capability, for demonstration
purposes.  If LabGym is started with
    --enable userdata_survey_exit
then survey will call sys.exit('Exiting early') instead of returning.

Design with paths as strings, or, paths as pathlib.Path objects?
Since the paths are configured as strings, assume the calls from outside
this module pass strings, and inside this module, developer is free to
use pathlib where convenient.
In other words, for public functions, support string path args, and
optionally, extend to support Path object args.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import webbrowser

# Related third party imports.
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
from LabGym import config, mywx


logger = logging.getLogger(__name__)

def is_path_under(path1: str|Path, path2: str|Path) -> bool:
    """Return True if path2 is under path1."""

    p1 = Path(path1).resolve()
    p2 = Path(path2).resolve()
    return p1 in p2.parents


def is_path_equivalent(path1: str|Path, path2: str|Path) -> bool:
    """Return True if path1 & path2 are equivalent."""

    # if they both exist, are they the same?
    if Path(path1).exists() and Path(path2).exists():
        return Path(path1).samefile(Path(path2))

    # if neither exists, are the strings of the resolved paths the same?
    if not Path(path1).exists() and not Path(path2).exists():
        return resolve(path1) == resolve(path2)

    # At this point, one exists and the other doesn't, therefore False
    return False


def resolve(path1: str|Path) -> str:
    """Return a string representation of the resolved string or Path obj."""

    return str(Path(path1).resolve())


def dict2str(arg: dict, hanging_indent: str=' '*16) -> str:
    """Return a string representation of the dict, with a hanging indent.

    Return '' if the dict is empty.

    Why the hanging indent?  So that it can be tuned to avoid fouling
    the left-alignment when used inside a multiline string that will be
    dedented.
    """

    result = ('\n' + hanging_indent).join(
        [f'{key}: {value}' for key, value in arg.items()]
        )

    return result


def get_list_of_subdirs(parent_dir: str|Path) -> List[str]:
    """Return a sorted list of strings of the names of the child dirs.

    ... excluding __pycache__.
    If parent_dir is not an existing dir, then return an empty list.
    """

    parent_path = Path(parent_dir)

    if parent_path.is_dir():
        result = [str(item) for item in parent_path.iterdir()
            if str(item) not in ['__init__', '__init__.py', '__pycache__']
            and (parent_path / item).is_dir()]
    else:
        result = []

    result.sort()
    return result


def open_html_in_browser(html_content):
    """
    Creates a temporary HTML file with the provided content and opens it 
    in a new web browser window.
    """
    # Use NamedTemporaryFile to ensure the file is eventually deleted by the OS
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
        f.write(html_content)
        file_path = f.name
    
    # Create a file URL for the browser
    url = 'file://' + os.path.abspath(file_path)
    
    # Open the URL in a new browser window (new=1) or a new tab (new=2)
    # The default is to try opening in a new window/tab if possible.
    webbrowser.open(url, new=1) 
    
    # Note: The temporary file will not be automatically deleted 
    # as long as the Python script is running. You might need to 
    # manually delete it after the browser is closed or when your 
    # application exits if you need immediate cleanup.


def assert_userdata_dirs_are_separate(
        detectors_dir: str, models_dir: str) -> None:
    """Verify the separation of configuration's userdata dirs.

    If not separate, then display an error message, then sys.exit().

    Enforce an expectation that the detectors_dir and models_dir are
    separate, and do not have a "direct, lineal relationshop", where one
    is under the other.

    Also, enforce the expectation that the path args are absolute (full).
    """

    assert Path(detectors_dir).is_absolute()
    assert Path(models_dir).is_absolute()

    if (is_path_equivalent(detectors_dir, models_dir)
            or is_path_under(detectors_dir, models_dir)
            or is_path_under(models_dir, detectors_dir)):

        # fatal configuration error
        title = 'LabGym Configuration Error'
        msg = textwrap.dedent(f"""\
            LabGym Configuration Error
                The detectors folder is specified by config or defaults as 
                    {detectors_dir!r}
                    which resolves to 
                    {resolve(detectors_dir)!r}
                The models folder is specified by config or defaults as 
                    {models_dir!r}
                    which resolves to 
                    {resolve(models_dir)!r}

            The userdata folders must be separate.
            """)

        logger.error('%s', msg)

        # Show the error msg with an OK_Dialog.
        with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
            mywx.bring_wxapp_to_foreground()

            result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
            logger.debug('%s: %r', 'result', result)

            sys.exit('Bad configuration')


def offer_to_mkdir_userdata_dirs(
        labgym_dir: str, detectors_dir: str, models_dir: str) -> None:
    """Offer to attempt to mkdir userdata dirs if they are external.

    If there are any userdata dirs that
        (a) are defined in the LabGym configuration to be external to
            the LabGym sw directory,
        (b) don't already exist.
    then offer to attempt to mkdir them.

    Note that the attempts to mkdir can fail and raise an exception for
    several reasons, including insufficient permissions, or parent dir
    of the target dir doesn't exist.

    Also, enforce the expectation that the path args are absolute (full).
    """
    assert Path(labgym_dir).is_absolute()
    assert Path(detectors_dir).is_absolute()
    assert Path(models_dir).is_absolute()

    mkdir_targets = {}

    if (not is_path_under(labgym_dir, detectors_dir)
            and not os.path.isdir(detectors_dir)):
        mkdir_targets.update({'detectors': detectors_dir})
    if (not is_path_under(labgym_dir, models_dir)
            and not os.path.isdir(models_dir)):
        mkdir_targets.update({'models': models_dir})

    if mkdir_targets:
        title = 'LabGym Configuration: make folders?'
        msg = textwrap.dedent(f"""\
            These folders are specified by your LabGym configuration, but
            they don't exist yet.
                {dict2str(mkdir_targets)}

            Try to create them?
            """)
            # 64-char ruler -----------------------------------------------!
        logger.debug('%s:\n%s', 'msg', msg)

        with mywx.OK_Cancel_Dialog(None, title=title, msg=msg) as dlg:
            mywx.bring_wxapp_to_foreground()

            result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
            logger.debug('%s: %r', 'result', result)

            if result == wx.ID_OK:
                 for value in mkdir_targets.values():
                      # Deliberately using os.mkdir instead of os.makedirs.
                      # to avoid unintentionally creating a mistake with
                      # multiple levels...
                      os.mkdir(value)


def get_instructions(folder, name, labgym_configfile):
    """Return html <li> element of instructions for a folder inside LabGym.
    
    If there are userdata subfolders, then extra instructions will be
    given to back them up and move them.
    """

    example_new_config_value = f'"{str(Path.home())}/LabGym_{name}"'

    list_of_subdirs = get_list_of_subdirs(folder)
    if len(list_of_subdirs) > 0:
        result = f"""
        <li>Move {name} userdata.
        <ol type="a">
        <li>
        Define "{name}" as a folder somewhere OUTSIDE of the LabGym folder.  
        For example, in the LabGym config toml-file, which might be this
        <br><code>&nbsp;&nbsp;&nbsp;&nbsp;
            {labgym_configfile}
        </code><br>
        specify like (as an example)
        <br><code>&nbsp;&nbsp;&nbsp;&nbsp;
            {name} = {example_new_config_value}
        </code><br>
        (use forward slash "/" inside the toml-file, even on Windows)
        </li>
        <li>
        Ensure the newly specified folder exists.
        </li>
        <li>
        The old, internal {name} folder (LabGym/{name}) contains 
        {len(list_of_subdirs)} subfolders of user data.
        <br>(i) Back them up, 
        <br>(ii) move them into the new {name} folder.  
            (If you just copy them, and leave the originals in the old 
            location, then they will be noticed later as "orphaned" data.
        </li>
        </ol></li>
        """
    else:
        # the internal userdata dir has no userdata to preserve.
        result = f"""
        <li>Move {name} userdata subfolders.
        <ol type="a">
        <li>
        Define "{name}" as a folder somewhere OUTSIDE of the LabGym folder.  
        For example, in LabGym config toml-file
        <br><code>&nbsp;&nbsp;&nbsp;&nbsp;
            {labgym_configfile}
        </code><br>
        specify like (as an example)
        <br><code>&nbsp;&nbsp;&nbsp;&nbsp;
            {name} = {example_new_config_value}
        </code><br>
        (use forward slash "/" inside the toml-file, even on Windows)
        </li>
        <li>
        Ensure the newly specified folder exists.
        </li>

        <li>
        The old, internal detectors (LabGym/{name}) contains no 
        subfolders of user data.
        </li>
        </ol></li>
        """

    return result


def advise_on_internal_userdata_dirs(
        labgym_dir: str, detectors_dir: str, models_dir: str) -> None:
    """...

    Also, enforce the expectation that the path args are absolute (full).
    """

    assert Path(labgym_dir).is_absolute()
    assert Path(detectors_dir).is_absolute()
    assert Path(models_dir).is_absolute()

    # One or both userdata dirs is internal, that is, under labgym_dir.
    assert (is_path_under(labgym_dir, detectors_dir) or
            is_path_under(labgym_dir, models_dir))

    # Get all of the values needed from config.get_config().
    labgym_configfile: str = str(config.get_config()['configfile'])

    title = 'LabGym Configuration: internal userdata dirs'

    # Prepare the dialog message.
    msg = textwrap.dedent("""\
        Your LabGym configuration (or the configuration defaults) 
        presently define userdata folders as located within the LabGym 
        folder.  
        This arrangement is now deprecated.  
        It's better that the userdata folders are located external to 
        the LabGym folder.  

        Intructions are being displayed in a webbrowser page "LabGym
        Configuration Instructions".
        Please follow the instructions to make the recommended changes, 
        Quit this session of LabGym,
        then restart LabGym.

        Quit LabGym Now?  (press OK)
        To carry on with the existing configuration, press Cancel.
        """)
        # 64-char ruler -----------------------------------------------!

    # Prepare the instructions in html.
    instructions_html_body = ''

    if is_path_under(labgym_dir, detectors_dir):
        instructions_html_body += get_instructions(
            detectors_dir, 'detectors', labgym_configfile)

    if is_path_under(labgym_dir, models_dir):
        instructions_html_body += get_instructions(
            models_dir, 'models', labgym_configfile)
            
    # <style>
    #     body { background-color: lightblue; text-align: center; }
    #     h1 { color: white; }
    #     p { color: navy; font-size: 20px; }
    # </style>
    instructions_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LabGym Configuration Instructions</title>
        </head>
        <body>
            <h1>LabGym Configuration Instructions</h1>
            <ol>
                {instructions_html_body}
            </ol>
            (Close this page when instructions are completed.)
        </body>
    """

    alt_instructions_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LabGym Configuration Instructions</title>
        </head>
        <body>
            <h1>LabGym Configuration Instructions</h1>
            <ol>
                {instructions_html_body}
            </ol>
        </body>
    """

    open_html_in_browser(instructions_html)

    logger.debug('%s:\n%s', 'msg', msg)

    with mywx.OK_Cancel_Dialog(None, title=title, msg=msg) as dlg:
        mywx.bring_wxapp_to_foreground()

        result = dlg.ShowModal()
        logger.debug('%s: %r', 'result', result)

        if result == wx.ID_OK:
            sys.exit('User pressed OK to quit')
        else:
            logger.debug('%s', 'User pressed Cancel, or dismissed the dialog')

    # (begin of alt) --------
    import html2text
    altmsg = textwrap.dedent("""\
        Your LabGym configuration (or the configuration defaults) 
        presently define userdata folders as located within the LabGym 
        folder.  
        This arrangement is now deprecated.  
        It's better that the userdata folders are located external to 
        the LabGym folder.
        """)
        # 64-char ruler -----------------------------------------------!

    altmsg += """
        """

    altmsg += html2text.html2text(alt_instructions_html)

    """
        Intructions are being displayed in a webbrowser page "LabGym
        Configuration Instructions".
        Please follow the instructions to make the recommended changes, 
        Quit this session of LabGym,
        then restart LabGym.
        """

    altmsg += textwrap.dedent("""\
        Quit LabGym Now?  (press OK)
        To carry on with the existing configuration, press Cancel.
        """)
        # 64-char ruler -----------------------------------------------!
    #----

    with mywx.OK_Cancel_Dialog(None, title=title, msg=altmsg) as dlg:
        mywx.bring_wxapp_to_foreground()

        result = dlg.ShowModal()
        logger.debug('%s: %r', 'result', result)

        if result == wx.ID_OK:
            sys.exit('User pressed OK to quit')
        else:
            logger.debug('%s', 'User pressed Cancel, or dismissed the dialog')
    # (end of alt) -------- 


def warn_on_orphaned_userdata(
        labgym_dir: str, detectors_dir: str, models_dir: str) -> None:
    """...

    Also, enforce the expectation that the path args are absolute (full).
    """

    assert Path(labgym_dir).is_absolute()
    assert Path(detectors_dir).is_absolute()
    assert Path(models_dir).is_absolute()

    title = 'title...'
    msg = 'msg...'

    logger.debug('%s:\n%s', 'msg', msg)

    with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
        mywx.bring_wxapp_to_foreground()

        result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
        logger.debug('%s: %r', 'result', result)


def survey(
    labgym_dir: str,
    detectors_dir: str,
    models_dir: str,
    ) -> None:
    """Display guidance if userdata dirs are within the LabGym tree.

    1.  Verify the separation of configuration's userdata dirs.
        If bad (not separate),
        then display an error message, then sys.exit().

    2.  Check for user data dirs that are external, but don't exist.
        If any, offer to attempt mkdir.

    3.  If any userdata dirs are configured as located within the
        LabGym tree, then advise user to resolve.
        Otherwise, the userdata dirs are already configured as
        external.  Warn about any orphaned data still sitting in
        traditional internal locations.

    Also, enforce the expectation that the path args are absolute (full).
    """

    assert Path(labgym_dir).is_absolute()
    assert Path(detectors_dir).is_absolute()
    assert Path(models_dir).is_absolute()

    """

    # Get all of the values needed from config.get_config().
    enable_userdata_survey_exit: bool = config.get_config(
        )['enable'].get('userdata_survey_exit', False)

    logger.debug('%s: %r', 'labgym_dir', labgym_dir)
    logger.debug('%s: %r', 'detectors_dir', detectors_dir)
    logger.debug('%s: %r', 'models_dir', models_dir)

    # 1.  Verify the separation of configuration's userdata dirs.
    #     If bad (not separate),
    #     then display an error message, then sys.exit().
    assert_userdata_dirs_are_separate(detectors_dir, models_dir)

    # At this point, the configured detectors_dir models_dir are not in
    # fundamental conflict, at least.

    # 2.  Check for user data dirs that are external, but don't exist.
    #     If any, offer to attempt mkdir.
    offer_to_mkdir_userdata_dirs(labgym_dir, detectors_dir, models_dir)

    # 3.  If any userdata dirs are configured as located within the
    #     LabGym tree, then advise user to resolve.
    #     Otherwise, the userdata dirs are already configured as
    #     external.  Warn about any orphaned data still sitting in
    #     traditional internal locations.
    if (is_path_under(labgym_dir, detectors_dir) or
            is_path_under(labgym_dir, models_dir)):
        # one or more userdata dirs are configured as located internal.
        advise_on_internal_userdata_dirs(labgym_dir, detectors_dir, models_dir)
    else:
        # all userdata dirs are configured as located external.
        warn_on_orphaned_userdata(labgym_dir, detectors_dir, models_dir)

    if enable_userdata_survey_exit:
        sys.exit(f'Exiting early.'
            f'  enable_userdata_survey_exit: {enable_userdata_survey_exit}')
