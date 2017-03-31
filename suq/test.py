import unittest
import models
import datetime
import urllib.request

class TestGetDatetimeOfWeekStart(unittest.TestCase):

    def test_sunday(self):
        sunday = datetime.datetime(2017, 3, 26, 12, 25, 00)
        expected = datetime.datetime(2017, 3, 19, 23, 59, 00)
        result = models.get_datetime_of_weekStart(sunday)
        self.assertTrue(result == expected)
    
    def test_monday(self):
        monday = datetime.datetime(2017, 3, 27, 12, 25, 00)
        expected = datetime.datetime(2017, 3, 26, 23, 59, 00)
        result = models.get_datetime_of_weekStart(monday)
        self.assertTrue(result == expected)

    def test_wednesday(self):
        wednesday = datetime.datetime(2017, 4, 14, 12, 25, 00)
        expected = datetime.datetime(2017, 4, 9, 23, 59, 00)
        result = models.get_datetime_of_weekStart(wednesday)
        self.assertTrue(result == expected)

class TestGetWeeksEvents(unittest.TestCase):
    def test_broken_ical(self):
        try:
            brokenCal = models.load_calendar("../calendars/broken.ics")
            brokenEvents = models.get_events(brokenCal)
            todaysDate = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10)))
            events = models.get_this_weeks_events(todaysDate, events)
            eventsDict = models.weeks_events_to_dictionary(events)
        except:
            return True
    def test_working_url_cal(self):
        response = urllib.request.urlopen("https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics")
        data = response.read()
        cal = models.load_calendar_from_data(data)
        events = models.get_events(cal)
        todays_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10)))
        events = models.get_this_weeks_events(todays_date, events)
        events_dict = models.weeks_events_to_dictionary(events)
        print(events_dict)
        return True

    def test_is_valid_calendar(self):
        response = urllib.request.urlopen("https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics") #valid ical
        data = response.read()
        self.assertTrue(models.is_valid_calendar(data))
        response = urllib.request.urlopen("https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w") #http page, not ical
        data = response.read()
        self.assertFalse(models.is_valid_calendar(data))
    
if __name__ == '__main__':
    unittest.main()
