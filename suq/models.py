from icalendar import Calendar, Event
from typing import List, Tuple
from datetime import datetime

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        cal = Calendar.from_ical(f.read())
        return cal

def print_calendar(cal: Calendar) -> None:
    for i in events(cal):
        print_event(i)

def print_event(event: Event) -> None:
    dtstart, dtend = event.get('dtstart'), event.get('dtend')
    # ^ http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    print("summary: ", event.get('summary'))
    print("dtstart: ", type(dtstart.dt), dtstart.dt)
    print("dtend:   ", type(dtend.dt), dtend.dt)
    # print("dtstamp: ", componentevent.get('dtstamp').dt)
    # Don't know what this last one is or whether it's useful

def events(cal: Calendar):
    return [ i for i in cal.walk() if i.name == "VEVENT" ]

Break = Tuple[datetime, datetime]

def get_breaks(cal: Calendar) -> List[Break]:
    pass

if __name__ == "__main__":
    cal = load_calendar("test.ics")
    print_calendar(cal)
