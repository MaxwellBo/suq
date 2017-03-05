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
            print("summary: ", component.get('summary'))
            print("dtstart: ", component.get('dtstart'))
            print("dtend:   ", component.get('dtend'))
            print("dtstamp: ", component.get('dtstamp'))

if __name__ == "__main__":
    cal = load_calendar("test.ics")
    print_calendar(cal)
