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

# standard library imports
import logging

# Log the load of this module (by the module loader, on first import).
# Create the log record manually, because logging isn't configured yet.
logrecords = [logging.LogRecord(
    level=logging.DEBUG, msg='loading %s', args=(__file__),
    lineno=24, exc_info=None, name=__name__, pathname=__file__,
    )]

# local application/library specific imports
import LabGym.mylogging as mylogging


# Configure logging, and append any new log records to logrecords.
try:
    mylogging.config(logrecords, myname=__name__)
except:
    logrecords.append(logging.LogRecord(
        level=logging.WARNING,
        msg='trouble configuring logging', args=None,
        lineno=42, exc_info=None, name=__name__, pathname=__file__,
        ))

    logging.basicConfig(level=logging.DEBUG)

# Now that logging is configured, handle the manually created log records.
handle = logging.getLogger().handle  # the root logger's handle method
for logrecord in logrecords:
    # get the effectivelevel of the logger to which the record was attributed
    effectivelevel = logging.getLogger(logrecord.name).getEffectiveLevel()
    if logrecord.levelno >= effectivelevel:
        handle(logrecord)


__version__='2.8.1'
