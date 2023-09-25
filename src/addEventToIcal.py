#!/usr/bin/env python
# encoding: utf-8

###############################################################################
#                                                                             #
# Wartungspläne CLI Tool to convert txt to calendar events                    #
#                                                                             #
# addEventToIcal.py                                                           #
###############################################################################
#                                                                             #
# Copyright (C) 2016-2023 science + computing ag                              #
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

""" A tool that adds events to ical files """

import argparse
import sys
from datetime import datetime, timedelta
from icalendar import Calendar, Event

def load_existing_calendar(calendar_file):
    """ Load an existing calendar or create a new one """
    try:
        with open(calendar_file, 'rb') as file:
            cal = Calendar.from_ical(file.read())
        return cal
    except FileNotFoundError:
        return Calendar()

def add_event(calendar_file, start_date, end_date, repeat_interval, start_time,
              end_time, duration, title, description):
    """ Create a new event and add it to the calendar """
    existing_cal = load_existing_calendar(calendar_file)

    # Parse start and end dates
    start_date = datetime.strptime(start_date, '%Y-%m-%d').astimezone()
    # Only if there is an end
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').astimezone()

    # Parse start and end times
    start_time = datetime.strptime(start_time, '%H:%M').astimezone()
    # Ignore end_time if duration is given
    if duration:
        duration = timedelta(hours=int(duration.split(':')[0]),
                             minutes=int(duration.split(':')[1]))
        end_time = (start_time + duration).time()
    else:
        end_time = datetime.strptime(end_time, '%H:%M').astimezone()

    cal_event = Event()
    cal_event.add('summary', title)
    cal_event.add('dtstart', datetime.combine(start_date, start_time.time()))
    if end_date:
        cal_event.add('dtend', datetime.combine(end_date, end_time.time()))
    cal_event.add('description', description)
    if repeat_interval:
        cal_event.add('rrule', repeat_interval)
    existing_cal.add_component(cal_event)

    # Write the updated calendar data to the file
    with open(calendar_file, 'wb') as file:
        file.write(existing_cal.to_ical())

def main():
    """ Command line argument interface for scriptable use """
    parser = argparse.ArgumentParser(description='Add events to an iCal file.')
    parser.add_argument('calendar_file', help='iCal file to add events to')
    parser.add_argument('--start-date',
                        default=datetime.now().strftime('%Y-%m-%d'),
                        help='Start date in YYYY-MM-DD format. Default is today')
    parser.add_argument('--end-date', default='',
                        help='End date in YYYY-MM-DD format. Default is none')
    parser.add_argument('--rrule', default='RRULE:FREQ=DAILY',
                        help='Interval according to rfc5545 e.g. RRULE:FREQ=DAILY')
    parser.add_argument('--start-time', default='09:00',
                        help='Start time in HH:MM format. Default is 09:00')
    parser.add_argument('--end-time', default='10:00',
                        help='End time in HH:MM format. Default is 10:00')
    parser.add_argument('--duration', default='',
                        help='HH:MM format. If set replaces --end-time')
    parser.add_argument('--title', required=True, help='Event title')

    args = parser.parse_args()

    # Read event description from stdin
    description = sys.stdin.read().strip()

    # Convert the RRULE string to a dictionary if provided
    rrule_property = {}
    if args.rrule:
        rrule_parts = args.rrule.split(';')
        for part in rrule_parts:
            key, value = part.split('=')
            rrule_property[key.lower()] = value

    # Add the event to the calendar
    print(args.calendar_file, args.start_date, args.end_date,
              rrule_property, args.start_time, args.end_time,
              args.duration, args.title, description)
    add_event(args.calendar_file, args.start_date, args.end_date,
              rrule_property, args.start_time, args.end_time,
              args.duration, args.title, description)

if __name__ == '__main__':
    main()
