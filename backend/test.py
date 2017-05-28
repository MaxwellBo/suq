__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

import unittest
from models import *
import datetime
import urllib.request

class TestGetDatetimeOfWeekStart(unittest.TestCase):
    def test_sunday(self) -> None:
        sunday = datetime.datetime(2017, 3, 26, 12, 25, 00)
        expected = datetime.datetime(2017, 3, 19, 23, 59, 00)
        result = get_datetime_of_week_start(sunday)
        self.assertEqual(result, expected)
    
    def test_monday(self) -> None:
        monday = datetime.datetime(2017, 3, 27, 12, 25, 00)
        expected = datetime.datetime(2017, 3, 26, 23, 59, 00)
        result = get_datetime_of_week_start(monday)
        self.assertEqual(result, expected)

    def test_wednesday(self) -> None:
        wednesday = datetime.datetime(2017, 4, 14, 12, 25, 00)
        expected = datetime.datetime(2017, 4, 9, 23, 59, 00)
        result = get_datetime_of_week_start(wednesday)
        self.assertEqual(result, expected)

class TestCalendarParsing(unittest.TestCase):
    me = User("parsing", "email", "fb_user_id", "fb_access_token")

    def test_broken_ical(self):
        with open("./calendars/broken.ics") as f:

            # Just cram it in
            self.me.calendar_data = f.read()

            # Try and access the calendar
            try:
                self.me.calendar
                self.fail(msg="Did not throw an exception")
            except:
                pass
    
# https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics
class TestCalendarRetrieval(unittest.TestCase):

    me = User("retrieval", "email", "fb_user_id", "fb_access_token")

    def test_invalid_calendar_url(self):
        try:
            self.me.add_calendar("www.GARBAGEURL.com")
            self.fail(msg="Did not throw an exception")
        except:
            pass

    def test_get_valid_calendar(self):

        CALENDAR_URL = "https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics"
        self.me.add_calendar(
            "https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics")

        self.assertIsNotNone(self.me.calendar_data)

    def test_subjects(self):
        subjects = self.me.subjects
        self.assertIn("CSSE3002", subjects)
        self.assertIn("COMS3200", subjects)
        self.assertIn("INFS3202", subjects)



class TestWhatsDue(unittest.TestCase):
    def test_simple(self) -> None:
        pass

if __name__ == '__main__':
    unittest.main()
