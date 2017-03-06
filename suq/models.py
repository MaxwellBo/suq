from icalendar import Calendar, Event

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        cal = Calendar.from_ical(f.read())
        return cal

def print_calendar(cal: Calendar) -> None:
    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart, dtend = component.get('dtstart'), component.get('dtend')
            # ^ http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
            print("summary: ", component.get('summary'))
            print("dtstart: ", type(dtstart.dt), dtstart.dt)
            print("dtend:   ", type(dtend.dt), dtend.dt)
            # print("dtstamp: ", component.get('dtstamp').dt)
            # Don't know what this last one is or whether it's useful

if __name__ == "__main__":
    cal = load_calendar("test.ics")
    print_calendar(cal)
