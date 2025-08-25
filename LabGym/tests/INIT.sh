# INIT -- Define ERROR, IS_VENV functions.  Define PYFILES.
#
# Usage
#     source INIT.sh

ERROR () { printf "ERROR: %s\n" "$*" >& 2; }

IS_VENV () { [ -n "$VIRTUAL_ENV+1" ]; }  # works in sh, bash, and zsh
    
PYFILES=$(cd .. && echo *.py)
# printf "%s: %s\n" "\$PYFILES" "$PYFILES"

return
# if return failed, then this script is being executed in its own shell
ERROR "bad usage -- source $0 instead of executing it in its own shell"
exit 1
