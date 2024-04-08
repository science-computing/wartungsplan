#!/usr/bin/env python
# encoding: utf-8

# A tool to download a calendar from Microsoft Exchange

import argparse
import configparser
import datetime
import logging
import dateutil.parser
import exchangelib
import icalendar


logger = logging.getLogger(__name__)


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
logger.info("Datetime utc now: %s", datetime.datetime.utcnow())
logger.info("Datetime local time now: %s", datetime.datetime.now().astimezone())


# Read Config file with utf-8 encoding (Umlaute ä, ö, ü, ... can be read)
config = configparser.ConfigParser()
with open(args.config, mode='r', encoding='utf-8') as conf:
    config.read_file(conf)
    config = config['exchange']
    logger.debug("Read config %s", args.config)


# prepare credentials for login
credentials = exchangelib.Credentials(config['user'],
                                      config['password'])

xconfig = exchangelib.Configuration(server=config.get('host', 'localhost'),
                                    credentials=credentials)

if not args.test:
    # Connect to the Exchange server
    account = exchangelib.Account(
        primary_smtp_address=config['email'],
        config=xconfig,
        autodiscover=False,
        access_type=exchangelib.DELEGATE,
    )

    # walk calendars
    logger.info("First walk")
    try:
        print(account.root.tree())

        account.root.refresh()
        account.public_folders_root.refresh()
        account.archive_root.refresh()
        
        some_folder = a.root / "Some Folder"
        print(some_folder.parent)
        print(some_folder.parent.parent.parent)
        # Returns the root of the folder structure, at any level. Same as Account.root
        print(some_folder.root)
        print(some_folder.children)  # A generator of child folders
        print(some_folder.absolute)  # Returns the absolute path, as a string
        # A generator returning all subfolders at arbitrary depth this level
        some_folder.walk()


        logger.info("Found the following calendars:")
        for item in account.folders[exchangelib.folders.Calendar]:
            logger.info(item.name)
    except Exception as e:
        logger.error(e, exc_info=e)

    logger.info("Second walk")
    try:

        for cal_folder in account.calendar.children:
            if -1 !=str(cal_folder).find('Test'):
                myCalendar=cal_folder
                break
        
        for item in myCalendar.all():
            print(item.subject)


        for cal_folder in account.calendar.children:
            logger.info(cal_folder.name)
            if -1 != str(cal_folder).find(config.get('calendar', 'Calendar')):
                logger.info("Found configured calendar")
                myCalendar=cal_folder
    except Exception as e:
        logger.error(e, exc_info=e)

if args.start_date:
    start = dateutil.parser.parse(args.start_date)
else:
    start = datetime.datetime.today().astimezone()
if args.end_date:
    end = dateutil.parser.parse(args.end_date)
else:
    end = start + datetime.timedelta(days=7)

logger.debug("Start date is: %s", start)
logger.debug("End date is: %s", end)

# exchangelib.Account.calendar.all() can not be used because it doesn't expand
# recurring events. exchangelib.CalendarItem['recurrence'] and
# icalendar.Event['rrule'] are not in any way compatible or translate
# meaningfully.
if not args.test:
    calendar_items = account.calendar.view(start=start, end=end)
else:
    calendar_items = [exchangelib.CalendarItem(subject="foo1", start=start, end=end),
                      exchangelib.CalendarItem(subject="foo2", start=start, end=end),
                      exchangelib.CalendarItem(subject="bar1", start=start, end=end)]
logger.info("Number of items in calendar: %i", len(calendar_items))

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
