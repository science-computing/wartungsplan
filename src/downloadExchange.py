#!/usr/bin/env python
# encoding: utf-8


###############################################################################
#                                                                             #
# Wartungspläne CLI Tool to convert txt to calendar events                    #
#                                                                             #
# downloadExchange.py                                                         #
###############################################################################
#                                                                             #
# Copyright (C) 2016-2024 science + computing ag                              #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or (at       #
# your option) any later version.                                             #
#                                                                             #
# This program is distributed in the hope that it will be useful, but         #
# WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU           #
# General Public License for more details.                                    #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

"""
A tool to download a calendar from Microsoft Exchange
"""

import argparse
import configparser
import datetime
import logging
import sys
import dateutil.parser
import exchangelib
import icalendar

logger = logging.getLogger(__name__)


def download(config, start_date=None, end_date=None, dry_run=False):
    # prepare credentials for login
    credentials = exchangelib.Credentials(config['user'],
                                          config['password'])

    xconfig = exchangelib.Configuration(server=config.get('host', 'localhost'),
                                        credentials=credentials)

    if not dry_run:
        # Connect to the Exchange server
        account = exchangelib.Account(
            primary_smtp_address=config['email'],
            config=xconfig,
            autodiscover=False,
            access_type=exchangelib.DELEGATE,
        )

        selected_calendar = None
        if config.get('calendar', None):
            # walk calendars
            logger.debug("Walk calendars")
            for cal_folder in account.calendar.children:
                logger.debug(dir(cal_folder))
                logger.debug("Found calendar: %s", cal_folder)
                if str(cal_folder) == "Calendar (%s)" % config.get('calendar', 'Calendar'):
                    logger.info("Found calendar: %s", cal_folder)
                    selected_calendar = cal_folder
            if not selected_calendar:
                raise FileNotFoundError(f"Calendar NOT FOUND: \"{cal_folder}\"")
        else:
            # use default calendar
            selected_calendar = account.calendar


    if start_date:
        start = dateutil.parser.parse(start_date)
    else:
        start = datetime.datetime.today()

    if end_date:
        end = dateutil.parser.parse(end_date)
    else:
        end = start + datetime.timedelta(days=7)

    # tzinfo object must be compatible with exchangelib
    # https://github.com/ecederstrand/exchangelib/issues/1076
    if dry_run:
        tz = exchangelib.EWSTimeZone.localzone()
    else:
        tz = account.default_timezone

    start = exchangelib.EWSDateTime.from_datetime(start).astimezone(tz)
    end = exchangelib.EWSDateTime.from_datetime(end).astimezone(tz)

    logger.debug("Start date is: %s", start)
    logger.debug("End date is: %s", end)

    # exchangelib.Account.calendar.all() can not be used because it doesn't expand
    # recurring events. exchangelib.CalendarItem['recurrence'] and
    # icalendar.Event['rrule'] are not in any way compatible or translate
    # meaningfully.
    if not dry_run:
        calendar_items = selected_calendar.view(start=start, end=end)
    else:
        calendar_items = [exchangelib.CalendarItem(subject="foo1", start=start, end=end),
                          exchangelib.CalendarItem(subject="foo2", start=start, end=end),
                          exchangelib.CalendarItem(subject="bar1", start=start, end=end)]

    # Create a new iCalendar object
    ical = icalendar.Calendar()

    # Iterate through each calendar item and add it to the iCalendar object
    # ATTENTION!! Only summary, start, end, and description are copied
    for item in calendar_items:
        logger.debug("Read item: %s, %s, %s", item.subject, item.start, item.end)
        event = icalendar.Event()
        event.add('summary', item.subject)
        event.add('dtstart', item.start)
        event.add('dtend', item.end)
        event.add('description', item.body)
        # Add more properties as needed, such as location, attendees, etc.

        ical.add_component(event)

    # Save the iCalendar object to a file
    with open(config.get('outfile', 'calendar_events.ics'), 'wb') as f:
        f.write(ical.to_ical())

    logger.info("Calendar events have been exported to %s",
                config.get('outfile', 'calendar_events.ics'))


def main():
    """ Command line arguments for interactive or scriptable use """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='./exchange.conf',
                        help='Absolute or relative path to configuration file.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='More v\'s more text')
    parser.add_argument('-s', '--start-date', default=None,
                        help='Start Date e.g. 2023-05-02. Default is todays date')
    parser.add_argument('-e', '--end-date', default=None,
                        help='End Date e.g. 2023-05-03. ' +
                             'Default is start-date + 7 days. ' +
                             '(00:00:00 respectively)')
    parser.add_argument('-t', '--test', action='store_true',
                        help='No Exchange server? Run script on dummy data!')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.ERROR)

    if args.verbose == 1:
        logger.setLevel(logging.INFO)
        logger.info("Loglevel INFO")
    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
        logger.info("Loglevel DEBUG")
    logger.debug("Parsed args: %s", args)

    # log system settings
    logger.info("Datetime utc now: %s", datetime.datetime.now(tz=datetime.timezone.utc))
    logger.info("Datetime local time now: %s", datetime.datetime.now().astimezone())


    # Read Config file with utf-8 encoding (Umlaute ä, ö, ü, ... can be read)
    config = configparser.ConfigParser()
    if args.test:
        config = {'user': 'foo', 'password': 'foo$'}
        return download(config, args.start_date, args.end_date, dry_run=True)
    else:
        with open(args.config, mode='r', encoding='utf-8') as conf:
            config.read_file(conf)
            config = config['exchange']
            logger.debug("Read config %s", args.config)

        return download(config, args.start_date, args.end_date)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        raise SystemExit(err) from err
