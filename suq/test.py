import unittest
import models
import datetime

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
    maxID, max = "Max", models.load_calendar("../calendars/max.ics")
    charlieID, charlie = "Charlie", models.load_calendar("../calendars/charlie.ics")
    hugoID, hugo = "Hugo", models.load_calendar("../calendars/hugo.ics")
    fake_db = {maxID: max, charlieID: charlie, hugoID: hugo}


if __name__ == '__main__':
    unittest.main()
