#!/usr/bin/env python

import configparser
from exchangelib import Credentials, Account, EWSDateTime
from icalendar import Calendar, Event
from icalendar import vRecur, vText

def convert_to_ical_recur_pattern(exchange_item):
    """Converts Exchange recurring pattern to iCalendar recurrence rules."""
    recurrence = exchange_item.recurrence
    rule = vRecur()

    if recurrence.number:
        rule['COUNT'] = recurrence.number

    if recurrence.start:
        rule['DTSTART'] = recurrence.start

    if recurrence.interval:
        rule['INTERVAL'] = recurrence.interval

    if recurrence.first_day_of_week:
        rule['WKST'] = vText(recurrence.first_day_of_week)

    # Handle more recurrence pattern details as needed

    return rule

# Set up credentials (replace with your own credentials)
config = configparser.ConfigParser()
config.read("exchange.conf")

credentials = Credentials(config['exchange']['user'],
                          config['exchange']['password'])

# Connect to the Exchange server
account = Account(config['exchange']['user'], credentials=credentials, autodiscover=True)

# Define the start and end datetime for which you want to fetch events
start_date = EWSDateTime(2024, 1, 1)
end_date = EWSDateTime(2024, 1, 31)

# Fetch calendar items between start_date and end_date
calendar_items = account.calendar.view(start=start_date, end=end_date)

# Create a new iCalendar object
ical = Calendar()

# Iterate through each calendar item and add it to the iCalendar object
for item in calendar_items:
    event = Event()
    event.add('summary', item.subject)
    event.add('dtstart', item.start)
    event.add('dtend', item.end)
    event.add('description', item.body)

    # Check if it's a recurring event and convert recurrence pattern
    if item.recurrence:
        recurrence_rule = convert_to_ical_recur_pattern(item)
        event.add('rrule', recurrence_rule)

    ical.add_component(event)

# Save the iCalendar object to a file
with open('calendar_events.ics', 'wb') as f:
    f.write(ical.to_ical())

print("Calendar events have been exported to 'calendar_events.ics'")

