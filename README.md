# Wartungsplan #

A tool to extract events from an ical file by day or day range and perform an
action per event like sending an email or opening a ticket.

## Requirements

 - Python 3.8

## Installation instructions ##

    # prepare the python virtual env
    python3 -m venv venv
    # enter the venv
    source venv/bin/activate
    # install dependecies
    pip install -r requirements.txt
    # install Wartungsplan
    pip install .
    # run the test suite
    test/test.py


## Events from icalendar ##

An icalendar file stored in local filesystem or localy mounted.
Can be edited with Thunderbird or even Outlook with an established
UI with all posible features of the `Recurrence Rule`
(https://www.rfc-editor.org/rfc/rfc5545#section-3.3.10).

	RRULE:FREQ=MONTHLY;BYDAY=1TU

The config file:

    [calendar]
    #Directory to ics file. Calendar only needs to be readable.
    directory = /media/shareX/Wartungspläne.ics

### Mode of operation ###

You would create several calendar files according to your need and run them
regularly using cron or systemd.

The calendars are split first of all by backend then by partition (the group
of people you want to give access).

 - E-Mail notification
 - Ticketing system

Then for example four calendars for four responsibilities (teams):

 - Client machine tasks
 - Server related tasks
 - Network
 - Public facing servers
 - Internal servers
 - Database servers

Another aproach could be to separate by duration (to run Wartungsplan daily,
weekly, monthly):

 - Tasks to finish the same day
 - That week
 - That month

If you already have different queues set up in your ticketing system you can
also start from there.

Be careful to not have more calendars than events ;-) 60 events per calender is
not too much, having to include 12 calenders in Outlook is a disaster, always.

The calendar files are on the local file system, a network share or otherwise
synchronized/transported.

### Microsoft Outlook ###

It is strongly recommended to explicitly sync the calendar back to its source:

    Send / Receive -> Send all


## Mail ##

The config file:

    [mail]
    server = smtp.example.com
    port = 465
    password = kCHvJeUy4Gd2XgsXXYFqUtjk
    sender = tom_jones@example.com
    recipient = michael_jackson@example.com

## OTRS ##

Install optional depenency:
    pip install pyotrs

The config file:

    [otrs]
    server = http://localhost
    webservicename = AutomaticTicketCreationForRecurringTasks
    username = restapiuser
    password = AiX3sheeIyahf8aaQuah2wio
    tickettitel = Titel
    queue = Queueebene1::Queueebene2
    state = New
    priority = 1 very low
    footer = Ticket automatically created by Wartungsplan

# Examples

    usage: Wartungsplan [-h] [--config CONFIG] [--ics-calendar ICS_CALENDAR]
                        [--verbose] [--dry-run] [--logfile LOGFILE]
                        [--start-date START_DATE] [--end-date END_DATE]
                        {list,send,otrs}

    positional arguments:
      {list,send,otrs}

    options:
      -h, --help            show this help message and exit
      --config CONFIG, -c CONFIG
                            Directory to different config file. Default is
                            plan.conf in same Folder as plan.py
      --ics-calendar ICS_CALENDAR, -i ICS_CALENDAR
                            Path to the ics calendar (Takes precedence over value
                            in config)
      --verbose, -v         More v's more text
      --dry-run, -d         Don't perform any action
      --logfile LOGFILE, -w LOGFILE
                            Write log to file
      --start-date START_DATE, -s START_DATE
                            Start Date e.g. 2023-05-02. Default is todays date
      --end-date END_DATE, -e END_DATE
                            End Date e.g. 2023-05-03. Default is start-date + 1
                            day. (00:00:00 respectively)

## Contact ##

In case you want or need to contact us in private because you don't want the
entire world to know, security related issues ... or to just say "Hello":

felix.bauer@eviden.com
christian.habrom@eviden.com
