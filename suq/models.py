from itertools import *

from typing import List, Tuple
from datetime import datetime

from icalendar import Calendar, Event # type: ignore

Break = Tuple[datetime, datetime]

class Event_(object):
    def __init__(self, summary: str, start: datetime, end: datetime) -> None:
        self.summary = summary
        self.start = start
        self.end = end

    def __contains__(self, instant: datetime):
        return self.start <= instant <= self.end

    def __str__(self):
        return f"{self.summary} | {self.start} | {self.end}"

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        cal = Calendar.from_ical(f.read())
        return cal

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
        remove_past = list(filter(lambda i: start_event.end < i.start, by_end))

        if len(remove_past) == 0:
            break
        elif start_event.end in remove_past[0]:
            continue
        else:
            breaks.append((start_event.end, remove_past[0].start))

    def is_short_break(x: Break) -> bool:
        start, finish = x
        duration_in_minutes = (finish - start).total_seconds() // 60
        return duration_in_minutes < 15

    def is_overnight(x: Break) -> bool:
        start, finish = x # TODO: Figure out whether I can pattern match in argslists
        return start.date() != finish.date()

    breaks = [ i for i in breaks if not is_short_break(i) and not is_overnight(i) ]

    return breaks

if __name__ == "__main__":
    cal = load_calendar("test.ics")

    for (start, finish) in get_breaks(cal):
        print(start, finish)

