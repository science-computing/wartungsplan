#!/usr/bin/env python
# encoding: utf-8

###############################################################################
#                                                                             #
# Test suite Wartungspläne CLI Tool                                           #
#                                                                             #
# test.py                                                                     #
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

""" Test suite for a tool than opens recurring tickets """

import logging
import os
import sys
import unittest
import icalendar
import tempfile

# Add Wartungsplan to PYTHONPATH
TESTSDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(TESTSDIR))

from src import Wartungsplan
from src import addEventToIcal


# pylint: disable=invalid-name
# pylint: disable=protected-access


class DummyBackend:
    """ Dummy backedn that does noghting """
    def __init__(self, _):
        pass

    def act(self, events):
        """ The action that should be performed
        here nothing """
        return len(events)


class TestWartungsplan(unittest.TestCase):
    """ Test the Wartungsplan class """
    @classmethod
    def setUpClass(cls):
        """ Set up common test case resources. """
        cls.tests_data_dir = os.path.join(TESTSDIR, "test-data")
        cls.b = DummyBackend(None)

    def test_one_event_with_empty_subject(self):
        """ The test data calendar has one non standard event
        because it diesn't have a subject """
        p = os.path.join(self.tests_data_dir, "Empty-Event-2023-05-01.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-05-01", "2023-05-02", cal, self.b)
            self.assertEqual(wp.run_backend(), 1)
            wp = Wartungsplan.Wartungsplan("2023-05-02", "2023-05-03", cal, self.b)
            self.assertEqual(wp.run_backend(), 0)

    def test_every_second_tuesday(self):
        """ One event that takes place every second tuesday of the month """
        p = os.path.join(self.tests_data_dir, "Every2ndTuesday-2023-05-02.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-05-02", "2023-05-03", cal, self.b)
            self.assertEqual(wp.run_backend(), 1)
            wp = Wartungsplan.Wartungsplan("2023-05-02", "2023-06-06", cal, self.b)
            self.assertEqual(wp.run_backend(), 2)

    def test_every_day_with_html(self):
        """ This calendar has an event thats description contains html.
        This is not within the initial standard and is implemented differently
        for calendar clients which is why for now we don't use it. Also
        because input validation would be an issue. """
        p = os.path.join(self.tests_data_dir, "EveryDayWithHeavyHTML.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-05-05", "2023-05-06", cal, self.b)
            self.assertEqual(wp.run_backend(), 1)
            wp = Wartungsplan.Wartungsplan("2023-06-01", "2023-07-01", cal, self.b)
            self.assertEqual(wp.run_backend(), 30)

    def test_bangkok_timezone(self):
        """ With this test we avoid regression of an error we made handling
        timezones. While in Bangkok it's the next day we (UTC+2) have a
        different date. """
        p = os.path.join(self.tests_data_dir, "TimezoneBangkok3rdOr4th-05-2023.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-05-03", None, cal, self.b)
            self.assertEqual(wp.run_backend(), 1)
            wp = Wartungsplan.Wartungsplan("2023-05-04", None, cal, self.b)
            self.assertEqual(wp.run_backend(), 0)

    def test_every_day_except_one(self):
        """ The calendar file has one event that takes place every day except
        the 26.09.2023 to make sure this is handeled correctly. """
        p = os.path.join(self.tests_data_dir, "EveryDayExcept-2023-09-26.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-09-26", None, cal, self.b)
            self.assertEqual(wp.run_backend(), 0)
            wp = Wartungsplan.Wartungsplan("2023-09-30", None, cal, self.b)
            self.assertEqual(wp.run_backend(), 1)

    def test_with_outlook_calendar(self):
        """ oh fuck """
        p = os.path.join(self.tests_data_dir, "OutlookCalendar-2023-10-06.ics")
        with open(p, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-10-06", None, cal, self.b)
            self.assertTrue('ö' in wp.events[0]["summary"])
            self.assertEqual(wp.run_backend(), 1)
            wp = Wartungsplan.Wartungsplan("2023-10-07", None, cal, self.b)
            self.assertEqual(wp.run_backend(), 3)


class TestSendEmail(unittest.TestCase):
    """ Test the SendEmail backend """
    def test_split_message(self):
        """ Test the split_message function """
        body = """To: test@example.com
        X-Priority: 1 (Highest)

        Kind creature,"""
        b = Wartungsplan.SendEmail("")
        header,text = b._split_message(body)
        self.assertEqual(header["To"], "test@example.com")
        self.assertEqual(len(text.split('\n')), 3)

    def test_invalid_header(self):
        """ Check if a header gets passed throught to the email message
        if it is not declared in the config as a accepted header. """
        config = {"mail":{"sender":"","recipient":""},
                  "headers":{"X-Priority":None}}
        b = Wartungsplan.SendEmail(config)

        body = """X-Priority: 1 (Highest)
X-INVALID: yes

Kind creature,"""
        header,text = b._split_message(body)

        event = {"summary":""}
        pre_action_object = b._prepare_event(header,text,event)
        msg = b._apply_headers(header, event, pre_action_object)

        self.assertEqual(msg["X-Priority"], "1 (Highest)")
        self.assertFalse('X-INVALID' in msg.keys())
        self.assertEqual(len(text.split('\n')), 2)


class TestOtrsApi(unittest.TestCase):
    """ Test the OtrsApi Backend """
    def test_split_message(self):
        """ Test the split_message function """
        body = """Queue: Ops5
        Priority: high

        Kind creature,"""
        b = Wartungsplan.OtrsApi("", False)
        header,text = b._split_message(body)
        self.assertEqual(header["Queue"], "Ops5")
        self.assertEqual(len(text.split('\n')), 3)

    def test_config_option_priority(self):
        """ Test how config options get replaces by headers """
        config = {'otrs':{
                      'queue':'q1:q2',
                      'tickettitel':'Title',
                      'priority':'high',
                      'customUser':'Tom'},
                  }
        b = Wartungsplan.OtrsApi(config, True)

        # config value
        body = ''
        header,text = b._split_message(body)
        event = {'summary':'One '}
        ticket, article = b._prepare_event(header,text,event)
        ticket = ticket.to_dct()
        article = article.to_dct()
        t1 = {'Ticket': {'Title': 'One ', 'Queue': 'q1:q2', 'State': 'New',
                         'Priority': 'high', 'CustomerUser': 'Tom'}}
        a1 = {'Subject': 'One ', 'Body': '\n\n'}
        self.assertEqual(ticket, t1)
        self.assertEqual(article, a1)

        # header config
        config['headers'] = {'queue':'q3:q4'}
        body = ''
        header,text = b._split_message(body)
        event = {'summary':'One '}
        ticket, article = b._prepare_event(header,text,event)
        ticket = ticket.to_dct()
        article = article.to_dct()
        t1 = {'Ticket': {'Title': 'One ', 'Queue': 'q3:q4', 'State': 'New',
                         'Priority': 'high', 'CustomerUser': 'Tom'}}
        a1 = {'Subject': 'One ', 'Body': '\n\n'}
        self.assertEqual(ticket, t1)
        self.assertEqual(article, a1)

        # header in event
        body = 'queue: q5:q6'
        header,text = b._split_message(body)
        event = {'summary':'One '}
        ticket, article = b._prepare_event(header,text,event)
        ticket = ticket.to_dct()
        article = article.to_dct()
        t1 = {'Ticket': {'Title': 'One ', 'Queue': 'q5:q6', 'State': 'New',
                         'Priority': 'high', 'CustomerUser': 'Tom'}}
        a1 = {'Subject': 'One ', 'Body': '\n\n'}
        self.assertEqual(ticket, t1)
        self.assertEqual(article, a1)


class TestAddEventToIcal(unittest.TestCase):
    """ Test tool to add event or create new calendar """
    @classmethod
    def setUpClass(cls):
        """ Set up common test case resources. """
        cls.tests_data_dir = os.path.join(TESTSDIR, "test-data")
        cls.b = DummyBackend(None)

    def test_create_daily_event(self):
        """ Test inserting a daily event """
        _, calendar_file = tempfile.mkstemp()
        os.unlink(calendar_file)
        addEventToIcal.add_event(calendar_file, '2023-09-25', '',
                                 'FREQ=DAILY', '11:00', '', '0:20',
                                 'Test1', 'Here we go again')
        addEventToIcal.add_event(calendar_file, '2023-09-25', '',
                                 'FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;', '11:00',
                                 '', '0:20', 'Test4', 'H3r3 w3 g0 again')
        with open(calendar_file, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-09-25", "2023-09-26", cal, self.b)
            self.assertEqual(wp.run_backend(), 2)
            wp = Wartungsplan.Wartungsplan("2023-09-26", "2023-09-27", cal, self.b)
            self.assertEqual(wp.run_backend(), 2)
            wp = Wartungsplan.Wartungsplan("2023-09-30", "2023-10-01", cal, self.b)
            self.assertEqual(wp.run_backend(), 1)
        os.unlink(calendar_file)

    def test_create_weekly_event(self):
        """ Test inserting more weekly events """
        _, calendar_file = tempfile.mkstemp()
        os.unlink(calendar_file)
        addEventToIcal.add_event(calendar_file, '2023-09-25', '',
                                 'FREQ=WEEKLY', '11:00', '', '0:20',
                                 'Test2', 'Here we go again')
        addEventToIcal.add_event(calendar_file, '2023-09-25', '',
                                 'FREQ=WEEKLY', '11:20', '', '0:20',
                                 'Test3', 'Here we go again')
        with open(calendar_file, encoding='utf-8') as c:
            cal = icalendar.Calendar.from_ical(c.read())
            wp = Wartungsplan.Wartungsplan("2023-09-25", "2023-09-26", cal, self.b)
            self.assertEqual(wp.run_backend(), 2)
            wp = Wartungsplan.Wartungsplan("2023-09-26", "2023-09-27", cal, self.b)
            self.assertEqual(wp.run_backend(), 0)
            wp = Wartungsplan.Wartungsplan("2023-10-02", "2023-10-03", cal, self.b)
            self.assertEqual(wp.run_backend(), 2)
        os.unlink(calendar_file)

    def test_string_to_rrule(self):
        """ Test value separation """
        rrules = [
            ('FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=28',
             {'freq': 'MONTHLY', 'interval': '3', 'bymonthday': '28'}),
            ('FREQ=WEEKLY;;INTERVAL=12;BYDAY=TH,MO',
             {'freq': 'WEEKLY', 'interval': '12', 'byday': ['TH', 'MO']}),
            (';FREQ=DAILY;;',
             {'freq': 'DAILY'}),
            (';',
             {}),
            ('Hello',
             {}),
            ('',
             {}),
        ]
        for text, parsed  in rrules:
            self.assertEqual(parsed, addEventToIcal.string_to_rrule(text))


if __name__ == '__main__':
    logging.disable(logging.ERROR)

    unittest.main()
