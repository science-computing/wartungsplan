#!/usr/bin/env python

import configparser
from exchangelib import Configuration, Credentials, Account, EWSDateTime, DELEGATE, IMPERSONATION, EWSTimeZone
from icalendar import Calendar, Event
import datetime

# Set up credentials (replace with your own credentials)
config = configparser.ConfigParser()
config.read("exchange.conf")

credentials = Credentials(config['exchange']['user'],
                          config['exchange']['password'])

xconfig = Configuration(server=config['exchange']['host'], credentials=credentials)

# Connect to the Exchange server
account = Account(
    primary_smtp_address=config['exchange']['email'],
    config=xconfig,
    autodiscover=False,
    access_type=DELEGATE,
)

# Define the start and end datetime for which you want to fetch events
start_date = datetime.datetime.strptime('2024-01-01', '%Y-%m-%d')
end_date = datetime.datetime.strptime('2024-01-31', '%Y-%m-%d')

tz = EWSTimeZone.localzone()
tz_start = EWSDateTime.from_datetime(start_date).astimezone(tz)
tz_end =   EWSDateTime.from_datetime(end_date).astimezone(tz)

# Fetch calendar items between start_date and end_date
calendar_items = account.calendar.view(start=tz_start, end=tz_end)

# Create a new iCalendar object
ical = Calendar()

# Iterate through each calendar item and add it to the iCalendar object
for item in calendar_items:
    event = Event()
    event.add('summary', item.subject)
    event.add('dtstart', item.start)
    event.add('dtend', item.end)
    event.add('description', item.body)
    
    # Add more properties as needed, such as location, attendees, etc.
    
    ical.add_component(event)

# Save the iCalendar object to a file
with open('calendar_events.ics', 'wb') as f:
    f.write(ical.to_ical())

print("Calendar events have been exported to 'calendar_events.ics'")

