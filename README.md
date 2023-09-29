# Wartungsplan #

A tool to extract events from an ical file by day or day range and perform an
action per event like sending an email or opening a ticket.

![wartungsplan](https://github.com/science-computing/wartungsplan/assets/2771054/ee0f788d-7c62-4321-9a78-1dc076aa36fd)

## Requirements

 - Python 3.8

## Installation instructions ##

    # prepare the python virtual env
    python3 -m venv venv
    # enter the venv
    source venv/bin/activate
    # install Wartungsplan
    pip install wartungsplan


## Events from icalendar ##

An icalendar file stored in local filesystem or localy mounted.
Can be edited with Thunderbird or even Outlook with an established
UI with all posible features of the `Recurrence Rule`
(https://www.rfc-editor.org/rfc/rfc5545#section-3.3.10).

The first Tuesday every month:

	RRULE:FREQ=MONTHLY;BYDAY=1TU

The config file:

    [calendar]
    #Directory to ics file. Calendar only needs to be readable.
    directory = /media/shareX/Wartungspläne.ics

The direcotry options only allows paths within the file system.
To include remote calendars mount a share or download the calendar file. The
calendar is not modified so does not have to be synched back.
Systemd can download e.g. using curl.
For type=oneshot ExecStart commands are executed sequentially
if commands fail the entire unit fails.


### Event headers ###

The calendar events may have in the configuration file defined headers that
substitute the predefined values.

    [headers]
    # Configure here the available (allowed) headers with their
    # default value
    X-Priority = 3
    X-TicketID =
    To = tom@peekabooav.de
    X-Custom-2 = hehehehehe
    # For OTRS
    tickettitel = Titel
    queue = Queueebene1::Queueebene2
    state = New
    priority = 1 very low

Events headers are the first few lines up until an empty line or a line that
does not match "^[A-Za-z0-9-]*: .*$".

    To: email@example.com

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

### A scriptable tool to create events ###

Part of the package is a script `addEventToIcal.py` that helps migration from
e.g. a cronjob oriented way or any repository or list of definition or
recurring tasks.

It reads the event body from STDIN and takes arguments to add events to an
existing calendar or create a new one. Since the body is what comes from STDIN
the first lines of the input can be headers.

    usage: addEventToIcal [-h] [--start-date START_DATE] [--end-date END_DATE]
                    [--rrule RRULE] [--start-time START_TIME] [--end-time END_TIME]
                    [--duration DURATION] --title TITLE calendar_file

    Add events to an iCal file.

    positional arguments:
      calendar_file         iCal file to add events to

    options:
      -h, --help            show this help message and exit
      --start-date START_DATE
                            Start date in YYYY-MM-DD format. Default is today
      --end-date END_DATE   End date in YYYY-MM-DD format. Default is none
      --rrule RRULE         Interval according to rfc5545 e.g. RRULE:FREQ=DAILY
      --start-time START_TIME
                            Start time in HH:MM format. Default is 09:00
      --end-time END_TIME   End time in HH:MM format. Default is 10:00
      --duration DURATION   HH:MM format. If set replaces --end-time
      --title TITLE         Event title

#### Rrule ####

A quarterly rule coudl look the following two ways. The first will run every
three months on the 28th, which could be a weekend. The second will take place
every twelve weeks on Thursdays. And the third example - every three months on
the first Monday:

    FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=28
    FREQ=WEEKLY;INTERVAL=12;BYDAY=TH
    FREQ=MONTHLY;INTERVAL=3;BYDAY=1MO


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

```
$ Wartungsplan -h
usage: Wartungsplan [-h] [--config CONFIG] [--ics-calendar ICS_CALENDAR]
                    [--verbose] [--dry-run] [--logfile LOGFILE]
                    [--start-date START_DATE] [--end-date END_DATE]
                    {version,list,send,otrs}

positional arguments:
  {version,list,send,otrs}
                        Just print the version or select the desired action.

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
```

## Contact ##

In case you want or need to contact us in private because you don't want the
entire world to know, security related issues ... or to just say "Hello":

felix.bauer@eviden.com
christian.habrom@eviden.com
