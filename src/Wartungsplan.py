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
import re
import importlib.metadata
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


class Backend:
    """ Interface for Wartungsplan backends """
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        logger.debug("Create backend %s", type(self).__name__)

    def act(self, events):
        """ Walks over events splits headers from text, calls subclass
            implementation to apply headers and possibly prepare an action
            and finally perform the in subclass implemented action. """
        # e.g. for the email backend actions_data contains the msg objects
        actions_data = []

        for event in events:
            # the DESCRIPTION only contains txt, no HTML
            # HTML body is contained in
            #  DESCRIPTION;ALTREP="data:text/html or
            #  X-ALT-DESC:FMTTYPE=text/html
            # see also
            # https://www.rfc-editor.org/rfc/rfc5545#section-3.2.1
            data = str(event.get("description", ""))

            headers,text = self._split_message(data)
            pre_action_object = self._prepare_event(headers, text, event)
            actions_data.append(self._apply_headers(headers, event,
                                                    pre_action_object))
        self._perform_action(actions_data)

    def _prepare_event(self, headers, text, event):
        """ Implemented in the subclass. """
        _ = headers, event
        return text

    def _apply_headers(self, headers, event, pre_action_object):
        """ Possibly implemented in the subclass. """
        _ = headers, event
        return pre_action_object

    def _perform_action(self, actions_data):
        """ Implemented in the subclass. """
        raise NotImplementedError("Subclass should implement this")

    def _split_message(self, data):
        """ Returns touple (headers, text) """
        header = ["[headers]"]
        text = []
        header_re = re.compile(r'^[A-Za-z0-9-]*: .*$')
        header_part = True
        for line in data.strip('\r').split('\n'): #strip('\r').
            if header_part and '=' in line:
                logger.warning('This is likely a mistake: ' +
                               '"=" found but ":" expected for header keys')
            if header_part and header_re.match(line):
                logger.debug("Header LINE: %s", line)
                header.append(line)
            else:
                logger.debug("Message LINE: %s", line)
                header_part = False
                text.append(line)

        logger.debug("Number of lines: %d header, %d text", len(header),
                     len(text))
        headers = configparser.ConfigParser()
        headers.read_string("\n".join(header))

        # log headers
        for key in headers:
            logger.debug("Header: %s: %s", key, headers[key])

        return headers["headers"], '\n'.join(text)


class ListStdout(Backend):
    """ Lists events to stdout """
    def __init__(self, config, dry_run):
        _ = config
        super().__init__(config, dry_run)

    def _prepare_event(self, headers, text, event):
        text = [str(event.get("summary")),
                str(event.get("description")),
                str(event.decoded("dtstart")),
                str(event.decoded("dtend")),
                '-------------------------']
        logger.debug("Event content: %s", text)
        return '\n'.join(text)

    def _perform_action(self, actions_data):
        """ List all Jobs in given Date """
        for data in actions_data:
            print(data)


class SendEmail(Backend):
    """ Sends events via email to the configured target"""
    def _prepare_event(self, headers, text, event):
        sender_address = self.config["mail"]["sender"]
        recipient_address = self.config["mail"]["recipient"]

        msg = EmailMessage()
        msg['Subject'] = str(event['summary'])
        msg['From'] = sender_address
        msg['To'] = recipient_address

        msg.set_content(text)
        logger.debug("Email Message created")

        return msg

    def _apply_headers(self, headers, event, pre_action_object):
        # add all configured allowed headers
        msg = pre_action_object
        for confheader in self.config["headers"].keys():
            if msg[confheader]:
                logger.debug("Delete already set header \"%s\"", confheader)
                del msg[confheader]
            msg[confheader] = headers.get(confheader,
                                          self.config["headers"][confheader])
        return msg

    def _perform_action(self, actions_data):
        sender_address = self.config["mail"]["sender"]
        recipient_address = self.config["mail"]["recipient"]

        # Check if this is a dry run.
        messages = actions_data
        if self.dry_run:
            logger.info("This is a Dry run!")
            for msg in messages:
                logger.debug("Sending Email")
                print(msg)
        else:
            logger.info("We are sending the Emails to %s", recipient_address)

            logger.debug("Connecting to %s with port %s",
                         self.config["mail"]["server"],
                         self.config["mail"]["port"])
            # Connect to Server with SSL from the beginning of the
            # connection. 'context' is an optional argument and can contain a
            # SSLContext that allows configuring various aspects of the secure
            # connection.
            # Read https://docs.python.org/3/library/ssl.html#ssl-security and
            # https://docs.python.org/3/library/ssl.html#ssl.SSLContext for more
            # information.
            with smtplib.SMTP_SSL(self.config["mail"]["server"],
                                  self.config["mail"]["port"]) as smtp:
                logger.info("Connected to: %s", smtp.sock.getpeername())
                logger.info("Connection cypher: %s", smtp.sock.cipher())
                smtp.login(sender_address, self.config["mail"]["password"])
                for msg in messages:
                    smtp.send_message(msg)
                    logger.info("Email sent")


class OtrsApi(Backend):
    """ Open a ticket in OTRS """
    def __init__(self, config, dry_run):
        super().__init__(config, dry_run)
        if "pyotrs" not in sys.modules:
            raise ModuleNotFoundError("Install optional dependency pyotrs "
                                      + "(pip install pyotrs)")

    def _prepare_event(self, headers, text, event):
        options = {
        "title" : str(event['summary']),
        'queue' : self.config['otrs'].get('queue', 'Queueebene1::Queueebene2'),
        'state' : self.config['otrs'].get('state', 'New'),
        'priority' : self.config['otrs'].get('priority', '1 very low'),
        'customUser' : self.config['otrs'].get('customUser', 'root@localhost')}

        if 'headers' in self.config:
            for confheader in self.config['headers'].keys():
                options[confheader] = headers.get(confheader,
                                                  self.config["headers"][confheader])

        new_ticket = pyotrs.Ticket.create_basic(
                                     Title=options["title"],
                                     Queue=options["queue"],
                                     State=options["state"],
                                     Priority=options["priority"],
                                     CustomerUser=options["customUser"])
        first_article = pyotrs.Article({'Subject': options['title'],
                                        "Body":
                                          text +
                                          "\n\n" +
                                          self.config.get("footer", "")
                                        })
        return (new_ticket, first_article)

    def _perform_action(self, actions_data):
        """ Open a ticket in OTRS for every event in range """
        for event in actions_data:
            (new_ticket, first_article) = event
            if self.dry_run:
                logger.info("new_ticket: %s", new_ticket.to_dct())
                logger.info("first_article: %s", first_article.to_dct())
            else:
                client = pyotrs.Client(self.config['otrs']['server'],
                                       self.config['otrs']['username'],
                                       self.config['otrs']['password'])

                logger.info("Opening connection to OTRS")
                if not client.session_create():
                    logger.error("Session to OTRS could not be opened")
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
        logger.info("%i Events in time range %s - %s", len(self.events),
                    start_date, end_date)

        if len(self.events) <= 0:
            logger.info("No events in the given period")
            return

    def run_backend(self):
        """ Run the routine to perform the backend action """
        return self.backend.act(self.events)


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
    actions = ['version', 'list', 'send', 'otrs']
    parser.add_argument('action', choices=actions, help="Just print the version "\
                        "or select the desired action.")
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

    # print version and exit
    version = importlib.metadata.version('Wartungsplan')
    logger.debug('Wartungsplan version %s', version)
    if args.action == 'version':
        print("Wartungsplan", version)
        sys.exit(0)

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
        logger.debug("Read config %s", args.config)

    # Get calendar location from argument
    if args.ics_calendar:
        calendarfile = args.ics_calendar
    # Get calendar location from config
    else:
        calendarfile = config["calendar"]["calendarfile"]

    with open(calendarfile, mode='r', encoding='utf-8') as calendar:
        calendar = icalendar.Calendar.from_ical(calendar.read())
        logger.debug("Read calendar file %s", calendarfile)

    # call the function selected by action
    if args.action == 'list':
        backend = ListStdout(None, args.dry_run)
    if args.action == 'send':
        backend = SendEmail({"mail":config["mail"],
                             "headers":config["headers"]}, args.dry_run)
    if args.action == 'otrs':
        backend = OtrsApi({"otrs":config["otrs"],
                           "headers":config["headers"]}, args.dry_run)

    if not backend:
        raise NameError("Action not found")

    try:
        wartungsplan = Wartungsplan(args.start_date, args.end_date, calendar, backend)

        return wartungsplan.run_backend()
    except Exception as err:
        raise SystemExit(err) from err


if __name__ == "__main__":
    sys.exit(main())
