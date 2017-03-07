from typing import List, Tuple
from datetime import datetime

from icalendar import Calendar, Event # type: ignore

Break = Tuple[datetime, datetime]

class Event_(object):
    def __init__(self, summary: str, start: datetime, end: datetime):
        self.summary = summary
        self.start = start
        self.end = end

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

def print_calendar(cal: Calendar) -> None:
    for i in events(cal):
        print(i)

"""
compress all the events in the cal to a list of starttime endtime tuples
"""
def cal_to_tuple(cal: Calendar):
    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart, dtend = component.get('dtstart').dt, component.get('dtend').dt
            dtstart = dtstart.replace(tzinfo=None)
            dtend = dtend.replace(tzinfo=None)
            events.append((dtstart, dtend))
    return sorted(events)

def find_freetime(cal: Calendar):
    #combine overlapping events
    events = cal_to_tuple(cal) #events should be sorted by start time
    finalEvents = [events[0]]

    #grab the event you want to merge to the previous event,
    #save its start time to c and its end time to d
    for c, d in events[1:]:

        #grab the most recently added event, and save its
        #start time to a, and end time to b
        a, b = finalEvents[-1]
        if c<=b<d:
            # c<=b<d: a-------b          Ans: [(a,d)]
            #               c---d
            #      =  a---------d
            finalEvents[-1] = a, d
        elif b<c<d:
            # b<c<d: a-------b           Ans: [(a,b),(c,d)]
            #                  c---d
            #      = a-------b c---d
            finalEvents.append((c,d))
        else:
            # c<d<b: a-------b           Ans: [(a,b)]
            #         c---d
            #      = a-------b
            pass


def get_breaks(cal: Calendar) -> List[Break]:
    by_start = sorted(events(cal), key=lambda i: i.start)

    for i in by_start:
        print(i)

if __name__ == "__main__":
    cal = load_calendar("test.ics")
    print_calendar(cal)
    find_freetime(cal)
    get_breaks(cal)
