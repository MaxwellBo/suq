from itertools import *

from typing import List, Tuple, Dict, NewType
from datetime import datetime, timezone, timedelta

from icalendar import Calendar, Event # type: ignore

UserID = str

class Period(object):
    def __init__(self, start: datetime, end: datetime) -> None:
        self.start = start
        self.end = end

    def __contains__(self, instant: datetime) -> bool:
        return self.start <= instant <= self.end

    def __str__(self) -> str:
        return f"{self.start} | {self.end}"


class Break(Period):
    pass

class Event_(Period):
    def __init__(self, summary: str, start: datetime, end: datetime) -> None:
        super().__init__(start=start, end=end)
        self.summary = summary

    def __str__(self) -> str:
        return f"{self.summary} | {self.start} | {self.end}"

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        return Calendar.from_ical(f.read())

def events(cal: Calendar) -> List[Event_]:
    # http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    return [ Event_(i.get('summary'), i.get('dtstart').dt, i.get('dtend').dt)\
    for i in cal.walk() if i.name == "VEVENT" ]

def get_breaks(cal: Calendar) -> List[Break]:
    by_start = sorted(events(cal), key=lambda i: i.start)
    by_end = sorted(events(cal), key=lambda i: i.end)

    breaks = []
    for start_event in by_start:
        # Stop caring about events that have no bearing on whether we have a break or not
        # Predicate: if you start later than the event we're testing, you get to stay
        remove_past = list(filter(lambda i: start_event.end < i.start, by_end))

        if len(remove_past) == 0:
            break
        elif start_event.end in remove_past[0]:
            continue
        else:
            breaks.append(Break(start_event.end, remove_past[0].start))

    def is_short_break(x: Break) -> bool:
        duration_in_minutes = (x.end - x.start).total_seconds() // 60
        return duration_in_minutes < 15

    def is_overnight(x: Break) -> bool:
        return x.start.date() != x.end.date()

    return [ i for i in breaks if not is_short_break(i) and not is_overnight(i) ]


def get_breaks_now(user: UserID, friends_to_calendar: Dict[UserID, Calendar])-> Dict[UserID, Break]:

    collector = {}

    for (friend, calendar) in friends_to_calendar.items():
        if user == friend:
            # Don't check our own breaks
            continue

        get_current_breaks = [ i for i in get_breaks(calendar)\
            if datetime.now(timezone(timedelta(hours=10))) in i ]

        if len(get_current_breaks) != 0:
            assert(len(get_current_breaks) == 1)
            collector[friend] = get_current_breaks[0]

    return collector

if __name__ == "__main__":
    maxID, max = "Max", load_calendar("../calendars/max.ics")
    charlieID, charlie = "Charlie", load_calendar("../calendars/charlie.ics")
    hugoID, hugo = "Hugo", load_calendar("../calendars/hugo.ics")

    fake_db = { maxID: max, charlieID: charlie, hugoID: hugo }

    # for i in get_breaks(max):
    #     print(i.start, i.end)

    # print("-------------------------")

    # for i in get_breaks(charlie):
    #     print(i.start, i.end)

    breaks = get_breaks_now(maxID, fake_db)

    for (friendID, brk) in breaks.items():
        print(f"{friendID} has break starting at {brk.start} and ending at {brk.end}")
