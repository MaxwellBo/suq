from icalendar import Calendar, Event
import datetime

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        cal = Calendar.from_ical(f.read())
        return cal

def print_calendar(cal: Calendar) -> None:
    for component in cal.walk():
        if component.name == "VEVENT":
            print_event(component)

def print_event(event: Event) -> None:
    dtstart, dtend = event.get('dtstart').dt, event.get('dtend').dt
    # ^ http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    #print("summary: ", event.get('summary'))
    #print("dtstart: ", type(dtstart.dt), dtstart.dt)
    #print("dtend:   ", type(dtend.dt), dtend.dt)
    # print("dtstamp: ", componentevent.get('dtstamp').dt)
    # Don't know what this last one is or whether it's useful

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
        


if __name__ == "__main__":
    cal = load_calendar("test.ics")
    find_freetime(cal)

