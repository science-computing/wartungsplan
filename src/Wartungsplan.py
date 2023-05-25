#!/usr/bin/env python
# encoding: utf-8

###############################################################################
#                                                                             #
# Wartungspläne CLI Tool                                                      #
#                                                                             #
# plan.py                                                                     #
###############################################################################
#                                                                             #
# Copyright (C) 2016-2022 science + computing ag                              #
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

""" A tool run to open recurring tickets """


import argparse
import datetime
import sys
import logging
import configparser
import smtplib
from email.message import EmailMessage

import dateutil.parser
import icalendar
# under active development, few issues, nothing major
# https://github.com/niccokunzmann/python-recurring-ical-events
import recurring_ical_events

try:
    import pyotrs
except ModuleNotFoundError:
    pass


logger = logging.getLogger(__name__)


class ListStdout:
    """ Lists events to stdout """
    def __init__(self, config):
        _ = config

    def act(self, events, dry_run=False):
        """ List all Jobs in given Date """
        _ = dry_run

        for event in events:
            print(event.get("summary"))
            print(event.get("description"))
            print(event.decoded("dtstart"))
            print(event.decoded("dtend"))
            print('-------------------------')


class SendEmail:
    """ Sends events via email to the configured target"""
    def __init__(self, config):
        self.config = config

    def act(self, events, dry_run=False):
        """ Run the due jobs """
        sender_address = self.config["sender"]
        recipient_address = self.config["recipient"]

        if len(events) <= 0:
            logger.info("No events in the given period")
            return

        # Build Email Messages for each event before sending the mail
        messages = []
        for event in events:
            msg = EmailMessage()
            msg['Subject'] = event.get("summary", "")
            msg['From'] = sender_address
            msg['To'] = recipient_address

            # the DESCRIPTION only contains txt, no HTML
            # HTML body is contained in
            #  DESCRIPTION;ALTREP="data:text/html or
            #  X-ALT-DESC:FMTTYPE=text/html
            # see also
            # https://www.rfc-editor.org/rfc/rfc5545#section-3.2.1
            data = event.get("description", "")

            msg.set_content(data)
            messages.append(msg)
            logger.debug("Email Message created")

        # Check if this is a dry run.
        if dry_run:
            logger.info("This is a Dry run!")
            for msg in messages:
                logger.debug("Sending Email")
                print(msg)
        else:
            logger.info("We are sending the Emails to %s", recipient_address)

            logger.debug("Connecting to %s with port %s",
                         self.config["server"], self.config["port"])
            # Connect to Server with SSL from the beginning of the
            # connection. 'context' is an optional argument and can contain a
            # SSLContext that allows configuring various aspects of the secure
            # connection.
            # Read https://docs.python.org/3/library/ssl.html#ssl-security and
            # https://docs.python.org/3/library/ssl.html#ssl.SSLContext for more
            # information.
            with smtplib.SMTP_SSL(self.config["server"],
                                  self.config["port"]) as smtp:
                logger.info("Connected to: %s", smtp.sock.getpeername())
                logger.info("Connection cypher: %s", smtp.sock.cipher())
                smtp.login(sender_address, self.config["password"])
                for msg in messages:
                    smtp.send_message(msg)
                    logger.info("Email sent")


class OtrsApi():
    """ Open a ticket in OTRS """
    def __init__(self, config):
        self.config = config
        if "pyotrs" not in sys.modules:
            raise ModuleNotFoundError("Install optional dependency pyotrs "
                                      + "(pip install pyotrs)")

    def act(self, events, dry_run=False):
        """ Open a ticket in OTRS for every event in range """

        for event in events:
            new_ticket = pyotrs.Ticket.create_basic(
                                         Title=self.config['tickettitel'],
                                         Queue=self.config.get("queue", "Raw"),
                                         State=self.config.get("state", "new"),
                                         Priority=self.config['priority'],
                                         CustomerUser="root@localhost")
            first_article = pyotrs.Article({"Subject": event.get("summary",""),
                                            "Body":
                                              event.get("description","") +
                                              "\n\n" +
                                              self.config.get("footer", "")
                                            })
            if dry_run:
                logger.info("new_ticket: %s", new_ticket.to_dct())
                logger.info("first_article: %s", first_article.to_dct())
            else:
                client = pyotrs.Client(self.config['server'],
                                       self.config['username'],
                                       self.config['password'])
                logger.info("URL for request %s", client._build_url())

                if not client.session_create():
                    logger.ERROR("Session to OTRS could not be opened")
                    return False

                resp = client.ticket_create(new_ticket, first_article)
                #resp == {u'ArticleID': u'9', u'TicketID': u'7',
                #         u'TicketNumber': u'2016110528000013'}
                logger.info("Reply from OTRS: %s", resp)
        return True


class Wartungsplan:
    """ Builds the events for the given range and allow to call
        into the backend """
    def __init__(self, start_date, end_date, calendar, backend):
        self.calendar = calendar
        self.backend = backend

        # parse start-date
        if not start_date:
            self.start_date = datetime.datetime.today()
        else:
            self.start_date = dateutil.parser.parse(start_date)
        logger.info("Start Date: %s", self.start_date.astimezone())

        # parse end-date
        if not end_date:
            self.end_date = self.start_date + datetime.timedelta(1)
        else:
            self.end_date = dateutil.parser.parse(end_date)
        logger.info("End Date: %s", self.end_date.astimezone())

        # Get all Events from start_date to end_date
        self.events = recurring_ical_events.of(calendar).between(
                          self.start_date.astimezone(),
                          self.end_date.astimezone())
        logger.info("%i Events %s - %s", len(self.events), start_date, end_date)

    def act(self, dry_run=False):
        """ Run the routine to perform the backend action """
        return self.backend.act(self.events, dry_run)


def main():
    """ The plan main program """
    parser = argparse.ArgumentParser()

    parser.add_argument('--config', '-c', default='/etc/plan.conf',
                        help='Directory to different config file. Default ' +
                             'is plan.conf in same Folder as plan.py')
    parser.add_argument('--ics-calendar', '-i', default=None,
                        help='Path to the ics calendar '
                             '(Takes precedence over value in config)')
    # Default is no Output. Only Errors will be output.
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='More v\'s more text')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Don\'t perform any action')
    parser.add_argument('--logfile', '-w', default=None,
                        help='Write log to file')
    parser.add_argument("--start-date", '-s', default=None,
                        help='Start Date e.g. 2023-05-02. Default is todays date')
    parser.add_argument("--end-date", '-e', default=None,
                        help='End Date e.g. 2023-05-03. ' +
                             'Default is start-date + 1 day. ' +
                             '(00:00:00 respectively)')

    # list: List installed jobs
    # send: To call the SendEmail backend
    # This list will grow with more backends
    actions = ['list', 'send', 'otrs']
    parser.add_argument('action', choices=actions)
    args = parser.parse_args()


    # Check if we already have a log handler
    if logger.handlers:
        # Remove all handlers
        for handler in logger.handlers:
            logger.removeHandler(handler)

    logging.basicConfig(filename=args.logfile,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
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
    with open(args.config, encoding = 'utf-8') as conf:
        config.read_file(conf)
        logger.debug("Read config %s", args.config)

    # Get calendar location from argument
    if args.ics_calendar:
        directory = args.ics_calendar
    # Get calendar location from config
    else:
        directory = config["calendar"]["directory"]

    with open(directory, encoding = 'utf-8') as calendar:
        calendar = icalendar.Calendar.from_ical(calendar.read())

    # call the function selected by action
    if args.action == 'list':
        backend = ListStdout(None)
    if args.action == 'send':
        backend = SendEmail(config["mail"])
    if args.action == 'otrs':
        backend = OtrsApi(config["otrs"])

    if not backend:
        raise NameError("Action not found")

    try:
        wartungsplan = Wartungsplan(args.start_date, args.end_date, calendar, backend)

        return wartungsplan.act(args.dry_run)
    except Exception as err:
        raise SystemExit(err) from err


if __name__ == "__main__":
    sys.exit(main())
