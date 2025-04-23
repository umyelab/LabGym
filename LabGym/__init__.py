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
import logging.config
import os

# related third party imports
import yaml

# Log the load of this module (by the module loader, on first import).
# Create the log record manually, because logging isn't configured yet.
records = [logging.LogRecord(
    level=logging.DEBUG, msg='loading %s', args=(__file__),
    lineno=28, exc_info=None, name=__name__, pathname=__file__,
    )]




__version__='2.8.1'



# Configure logging per logging.yaml
configfile = os.path.join(os.path.dirname(__file__), 'logging.yaml')
try:
    with open(configfile) as f:
        config = yaml.safe_load(f)

    # print(f'config: {config!r}')
    records.append(logging.LogRecord(
        level=logging.DEBUG,
        msg='%s: %r', args=('config', config),
        lineno=47, exc_info=None, name=__name__, pathname=__file__,
        ))

    logging.config.dictConfig(config)
except:
    records.append(logging.LogRecord(
        level=logging.WARNING,
        msg='trouble configuring logging from configfile (%s)',
        args=(configfile),
        lineno=55, exc_info=None, name=__name__, pathname=__file__,
        ))

    logging.basicConfig(level=logging.DEBUG)

# Now that logging is configured, handle the manually created log records.
logger = logging.getLogger(__name__)
for record in records:
    if record.levelno >= logger.getEffectiveLevel():
        logger.handle(record)
