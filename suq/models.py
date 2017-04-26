__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
from itertools import *
from typing import List, Tuple, Dict
from datetime import datetime, timezone, timedelta
from collections import deque
import logging
# Libraries
from icalendar import Calendar, Event # type: ignore
from flask_sqlalchemy import SQLAlchemy
import flask_login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.request
import re
from bs4 import BeautifulSoup # TODO: Does BeautifulSoup block?

### TYPE ALIASES ###

UserID = str

### GLOBALS ###

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column('id', db.Integer, primary_key=True)
    # TODO: Make all variable and column names lower_snake_case
    username = db.Column('username', db.String(128))
    password = db.Column('password' , db.String(128))
    FBuserID = db.Column('fb_user_id',db.String(64))
    FBAccessToken = db.Column('fb_access_token', db.String(512))
    profilePicture= db.Column('profile_picture',db.String(512))
    email = db.Column('email',db.String(128))
    registeredOn = db.Column('registeredOn' , db.DateTime)
    calendarURL = db.Column('calendarURL' , db.String(512))
    calendarData = db.Column('calendarData',db.LargeBinary())
    incognito = db.Column('incognito', db.Boolean())

    def __init__(self , username ,password , email, FBuserID, FBAccessToken):
        logging.warning("Creating user")
        self.username = username
        if password != None:
            self.set_password(password)
        else:
            self.password = ""
        self.email = email
        self.FBuserID = FBuserID
        self.FBAccessToken = FBAccessToken
        if self.FBuserID != None:
            # FIXME: Use fstring here
            self.profilePicture = "http://graph.facebook.com/"+self.FBuserID+"/picture" #add '?type=large' to the end of this link to get a larger photo
        else:
            self.profilePicture = ""
        self.calendarURL = ""
        self.calendarData = None
        self.registeredOn = datetime.utcnow()
        self.incognito = False
        logging.warning("Creating user with properties Name: %s, Password: %s, Email: %s, Time: %s" % (self.username, self.password, self.email, self.registeredOn))

    def add_calendar(self, cal_url: str) -> bool:
        if ".ics" not in cal_url: 
            cal_url = cal_url + '.ics' #append the .ics to the end of the share cal
        if "w" == cal_url[0]: #User copied across the webcal:// instead of https://
            cal_url = "https://" + cal_url[9:]
        elif "t" == cal_url[0]: #User didnt copy across the https://
            cal_url = "https://" + cal_url
        response = urllib.request.urlopen(cal_url)
        data = response.read()
        if is_valid_calendar(data):
            self.calendarURL = cal_url
            logging.warning("Calendar Added %s" % (data.decode('utf-8')))
            self.calendarData = data
            return True
        else:
            return False

    def set_password(self, password):
        self.password = generate_password_hash(password) #Hash password
    
    def check_password(self, password):
        return check_password_hash(password)


"""
class HasFriend(db.Model):
    __tablename__ = "HasFriend"
    friend_id1 = db.Column('id', db.Integer, db.ForeignKey("Users.id"), nullable = False, primary_key = True)
    friend_id2 = db.Column('friend_id', db.Integer, db.ForeignKey("Users.id"), nullable = False, primary_key = True)

    def __init__(self, friend1, friend2):
        logging.warning("Establishing friendship")
        self.friend_id1 = friend1
        self.friend_id2 = friend2
        logging.warning("Friendship created")
"""
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
    def __init__(self, summary: str, location: str, start: datetime, end: datetime) -> None:
        super().__init__(start=start, end=end)
        self.summary = summary
        self.location = location
    def to_dict(self) -> dict:
        start_string = str(self.start.strftime('%H:%M'))
        end_string = str(self.end.strftime('%H:%M'))
        summary_string = str(self.summary)
        location = str(self.location)
        return {"summary": summary_string, "location":location, "start": start_string, "end": end_string}
    def __str__(self) -> str:
        return f"{self.summary} | {self.start} | {self.end}"

# http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
def load_calendar(filename: str) -> Calendar:
    with open(filename, "r") as f:
        # http://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python
        return Calendar.from_ical(f.read())

def load_calendar_from_data(calData) -> Calendar:
    return Calendar.from_ical(calData)

def get_events(cal: Calendar) -> List[Event_]:
    # http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    return [ Event_(i.get('summary'),i.get('location'), i.get('dtstart').dt, i.get('dtend').dt)\
    for i in cal.walk() if i.name == "VEVENT" ]

def is_valid_calendar(data) -> bool:
    try:
        cal = load_calendar_from_data(data)
        events = get_events(cal)
        todays_date = datetime.now(timezone(timedelta(hours=10)))
        events = get_this_weeks_events(todays_date, events)
        eventsDict = weeks_events_to_dictionary(events)
    except:
        return False
    return True
"""
Takes: a date
Returns: the most recent sunday of that date, at the time 11:59pm
Eg. give it "monday 21st of march, 2pm" it will return "Sunday 20th march, 11:59pm
"""
def get_datetime_of_weekStart(dToriginal: datetime) -> datetime:
    daysAhead =dToriginal.isoweekday()
    hoursInADay = 24
    dToriginal = dToriginal - timedelta(hours=(hoursInADay*daysAhead))
    dToriginal = dToriginal.replace(hour=23, minute=59)
    return dToriginal
    
def get_breaks(events: List[Event_]) -> List[Break]:

    def is_short_break(x: Break) -> bool:
        duration_in_minutes = (x.end - x.start).total_seconds() // 60
        return duration_in_minutes < 15

    def is_overnight(x: Break) -> bool:
        return x.start.date() != x.end.date()

    by_start = deque(sorted(events, key=lambda i: i.start))

    breaks = []

    while True:
        # If we've run out of gaps between two events to find
        if len(by_start) < 2:
            return [i for i in breaks if not is_short_break(i) and not is_overnight(i)]

        subject = by_start.popleft()

        if any(subject.end in i for i in by_start):
            continue
        else:
            # Only subjects with "exposed" outer-ends
            # get to create a break to the next event
            breaks.append(Break(subject.end, by_start[0].start))
"""
Takes a week of events, and turns it into a jsonify-able dictionary
"""
def weeks_events_to_dictionary(events: List[Event_]):
    days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    weekEvents = {days[0]:[], days[1]: [], days[2]: [], days[3]: [], days[4]: [], days[5]: [], days[6]: []}
    for event in events:
        if (event.end.isoweekday() == event.start.isoweekday()):
            weekEvents.get(days[event.start.isoweekday()]).append(event.to_dict())
    return weekEvents


"""
Takes: A date, a list of events
Returns: The list of events from the week (Sunday -> Sunday) 
"""
def get_this_weeks_events(date: datetime, events: List[Event_]) -> List[Event_]:
    weekStartTime = get_datetime_of_weekStart(date)
    events = cull_events_before_date(weekStartTime, events)
    hoursInAWeek = 7 * 24
    weekEndTime = weekStartTime + timedelta(hours=hoursInAWeek)
    events = cull_events_after_date(weekEndTime, events)
    return events

def get_todays_events(date: datetime, events: List[Event_]) -> List[Event_]:
    day_start_time = date.replace(hour=1, minute=0)
    events = cull_events_before_date(day_start_time, events)
    day_end_time = date.replace(hour=23, minute=59)
    events = cull_events_after_date(day_end_time, events)
    return events
"""
Removes events before a certain date
"""
def cull_events_before_date(date: datetime, events: List[Event_]) -> List[Event_]:
    return sorted([i for i in events if date < i.end], key=lambda i: i.start)

"""
Removes events after a certain date
"""
def cull_events_after_date(date: datetime, events: List[Event_]) -> List[Event_]:
    return sorted([i for i in events if date > i.end], key=lambda i: i.start)

def cull_past_breaks(breaks: List[Break]) -> List[Break]:
     # Here be dragons: This is hardcoded to Brisbane's timezone
    now = datetime.now(timezone(timedelta(hours=10)))

    # Sorting it again to defend against bad breaks lists
    return sorted([i for i in breaks if now < i.end], key=lambda i: i.start)



def get_friends_current_and_future_breaks(user: UserID,
    friends_to_calendar: Dict[UserID, Calendar])-> Dict[UserID, Break]:

    collector = {}

    for (friend, calendar) in friends_to_calendar.items():
        if user == friend:
            # Don't check our own breaks
            continue

        future_and_current_breaks =\
            cull_past_breaks(
                get_breaks(
                    get_events(
                        calendar))) # mfw Python isn't Haskell

        if len(future_and_current_breaks) != 0:
            collector[friend] = future_and_current_breaks[0]

    return collector

def get_group_current_and_future_breaks(group_members: List[UserID],
    members_to_calendar: Dict[UserID, Calendar]) -> List[Break]:

    def concat(xs):
        return list(chain.from_iterable(xs))

    events = concat(get_events(calendar)\
                    for (userID, calendar) in members_to_calendar.items()\
                    if userID in group_members)

    return cull_past_breaks(get_breaks(events))

def get_test_calendar_events() -> List[Event_]:
    charlie = load_calendar("calendars/charlie.ics")
    events = get_events(charlie)
    return events

def is_url_valid(url: str) -> bool:
    must_contain = ['/share/', 'timetableplanner.app.uq.edu.au']
    return all(string in url for string in must_contain)
"""
Takes a time and list of events,
Returns the event that the time is inside of, or None, if the time is not 
inside any Event
"""
def get_event_user_is_at(date: datetime, events: List[Event_]) -> Event_:
    for event in events:
        if (event.start < date) and (event.end > date):
            return event
    return None

def get_break_user_is_on(date: datetime, events: List[Event_]) -> Break:
    breaks = get_breaks(events)
    for user_break in breaks:
        if (user_break.start < date) and (user_break.end > date):
            return user_break
    return None

# TODO: Desperately need to clean this up
def get_user_status(user: User):

    user_details = { "name" : user.username, "dp": user.profilePicture}

    def make_user_status(status, status_info):
        return { "status": status, "statusInfo": status_info }

    # Case 1: User is Incognito
    if user.incognito:
        return { **user_details, **make_user_status("Unavailable", "No Uni Today") }
    # Case 2: User has no Calendar
    if user.calendarData is None:
        return { **user_details, **make_user_status("Unknown", "User has no calendar") }

    user_calendar = load_calendar_from_data(user.calendarData)
    # FIXME:                   extract UTC+10 timezone into some sort of constant
    todays_date = datetime.now(timezone(timedelta(hours=10)))
    user_events = get_todays_events(todays_date, get_events(user_calendar))

    # Case 3: User does not have uni today
    if user_events == []:
        return { **user_details, **make_user_status("Unavailable", "No uni today") }

    # Case 4: User has finished uni for the day 
    if user_events[-1].end < todaysDate:
        finished_time = user_events[-1].end.strftime('%H:%M')
        return { **user_details, **make_user_status("Finished", f"Finished uni at {finished_time}") }

    # Case 5: User has not started uni for the day
    if user_events[0].start > todaysDate:
        start_time = user_events[0].start.strftime('%H:%M')
        return { **user_details, **make_user_status("Starting", f"Uni starts at {start_time}")}

    # Case 6: User is busy at uni
    busy_event = get_event_user_is_at(todays_date, user_events)
    if  busy_event is not None:
        time_free = busy_event.end.strftime('%H:%M')
        return { **user_details, **make_user_status("Busy", f"Free at {time_free}")}

    # Case 7: User is on a break at uni
    break_event = get_break_user_is_on(todays_date,user_events)
    if break_event is not None:
        busy_at_time = break_event.end.strftime('%H:%M')
        return { **user_details, **make_user_status("Free", f"until {busy_at_time}")}
    # Case 8: Something went wrong
    return { **user_details, **make_user_status("Unknown", "???")}

"""
Takes a list of course codes, finds their course profile id nums, parses
uq's php thing, then returns the coming assessment in an array.

Returns data, an array of string arrays
"""
def get_whats_due(subjects):
    courseUrl = 'https://www.uq.edu.au/study/course.html?course_code='
    assessmentUrl = 'https://www.courses.uq.edu.au/student_section_report' +\
        '.php?report=assessment&profileIds='
    coursesID = []
    for course in subjects:
        course = course.upper()
        try: 
            response = urllib.request.urlopen(courseUrl+course)
            html = response.read().decode('utf-8')
        except:
            continue #just ignore it if it fails lmao
        try: 
            profile_id_regex = re.compile('profileId=\d*')
            profile_id = profile_id_regex.search(html).group()
            if profile_id != None:
                profile_id = profile_id[10:] #Strip the 'profileID='
                coursesID.append(profile_id)
        except:
            continue #once again. heck it.
    courses = ",".join(coursesID)
    data = []
    response = urllib.request.urlopen(assessmentUrl + courses)
    html = response.read().decode('utf-8')
    html = re.sub('<br />', ' ', html)
    soup = BeautifulSoup(html,"html5lib")
    table = soup.find('table', attrs={'class':'tblborder'})
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    data.pop(0)
    return data
        

# TODO: Get rid of this
if __name__ == "__main__":
    url = "https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics"
    response = urllib.request.urlopen(url)
    data = response.read()
    user_calendar = load_calendar_from_data(data)
    user_events = get_events(user_calendar)
    todaysDate = datetime.now(timezone(timedelta(hours=10)))
    user_events = get_todays_events(todaysDate, user_events)
    print(get_user_status())
    """
    maxID, max = "Max", load_calendar("../calendars/max.ics")
    charlieID, charlie = "Charlie", load_calendar("../calendars/charlie.ics")
    hugoID, hugo = "Hugo", load_calendar("../calendars/hugo.ics")

    fake_db = { maxID: max, charlieID: charlie, hugoID: hugo }

    group_breaks = get_group_current_and_future_breaks([maxID, charlieID, hugoID], fake_db)
    for i in group_breaks:
        print(f"The group has break starting at {i.start} and ending at {i.end}")

    friends_breaks = get_friends_current_and_future_breaks(maxID, fake_db)
    for (friendID, brk) in friends_breaks.items():
        print(f"{friendID} has break starting at {brk.start} and ending at {brk.end}")
    """
