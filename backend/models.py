__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import logging
import re
import urllib.request
from itertools import *
from typing import List, Tuple, Dict, Any, Optional, Iterable, Set, cast
from datetime import datetime, timezone, timedelta, date
from collections import deque

# Libraries
import flask_login
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy # type: ignore

from icalendar import Calendar, Event # type: ignore
from bs4 import BeautifulSoup # type: ignore


#################
### CONSTANTS ###
#################

BRISBANE_TIME_ZONE = timezone(timedelta(hours=10))

###############
### GLOBALS ###
###############

db = SQLAlchemy()

########################
### BUSINESS OBJECTS ###
########################

"""
An abstract class representing the concept of a period of time
"""
class Period(object):
    def __init__(self, start: datetime, end: datetime) -> None:
        self.start = start
        self.end = end

    def __contains__(self, instant: datetime) -> bool:
        return self.start <= instant <= self.end


"""
A concrete class representing the period of time between two events

NOTE: This adds some presentation logic onto Period, which it extends, mostly
      unchanged
"""
class Break(Period):
    def to_dict(self) -> dict:
        start_string = str(self.start.strftime('%H:%M'))
        end_string = str(self.end.strftime('%H:%M'))
        return { "start": start_string, "end": end_string }

    def __repr__(self) -> str:
        return f"Break({repr(self.start)}, {repr(self.end)})"

"""
A concrete class representing an event that occured at a certain location
for a period of time

NOTE: The name `Event_` was chosen so that it did not shadow the `icalendar`
      class `Event`
"""
class Event_(Period):
    def __init__(self, summary: str, location: str, start: datetime, end: datetime) -> None:
        super().__init__(start=start, end=end)
        self.summary = summary
        self.location = location

    def to_dict(self) -> dict:
        start_string = str(self.start.strftime('%H:%M'))
        end_string = str(self.end.strftime('%H:%M'))
        return { "summary": self.summary, "location": self.location, "start": start_string, "end": end_string } 

    def __repr__(self) -> str:
        return f"Event_({repr(self.summary)}, {repr(self.location)}, {repr(self.start)}, {repr(self.end)})"

##############
### TABLES ###
##############

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id              = db.Column('id',               db.Integer,         primary_key=True)
    username        = db.Column('username',         db.String(128)) # FIXME: Should be "name"
    fb_user_id      = db.Column('fb_user_id',       db.String(128))
    fb_access_token = db.Column('fb_access_token',  db.String(512))
    fb_friends      = db.Column('fb_friends',       db.LargeBinary())
    profile_picture = db.Column('profile_picture',  db.String(512))
    email           = db.Column('email',            db.String(128))
    registered_on   = db.Column('registered_on',    db.DateTime)
    calendar_url    = db.Column('calendar_url',     db.String(512))
    calendar_data   = db.Column('calendar_data',    db.LargeBinary())
    incognito       = db.Column('incognito',        db.Boolean())
    # checked_in_at = db.Column('checkedInAt'), db.datetime()???, nullable=true )
    # TODO: Add this field

    def __init__(self, username: str, email: str, fb_user_id: str, fb_access_token: str) -> None:
        logging.warning("Creating user")
        self.username = username
        self.email = email
        self.fb_user_id = fb_user_id
        self.fb_access_token = fb_access_token

        if self.fb_user_id is not None:
            self.profile_picture = f"http://graph.facebook.com/{self.fb_user_id}/picture" 
            # add '?type=large' to the end of this link to get a larger photo
        else:
            self.profile_picture = ""

        self.calendar_url = ""
        self.calendar_data = None
        self.registered_on = datetime.utcnow()
        self.incognito = False
        # self.checked_in_at = None
        # TODO: ^ uncomment me once the DB column has been added
        logging.warning("Creating user with the following properties"
                        + f": Name: {self.username}"
                        + f", Email: {self.email}, Time: {self.registered_on}")


    """
    Downloads the calendar stored at the provided and URL, and loads the binary
    into the database

    This method also

        1) Attempts to correct common user mistakes associated with URL input
        2) Throws errors if the request, or the calendar data, or the calendar
           is invalid
    """
    def add_calendar(self, url: str) -> None:
        if ".ics" not in url: 
            url = url + '.ics' # append the .ics to the end of the share cal
        if "w" == url[0]: # User copied across the webcal:// instead of https://
            url = f"https://{url[9:]}"
        elif "t" == url[0]: # User didnt copy across the https://
            url = f"https://{url}"

        response = urllib.request.urlopen(url)
        data = response.read()

        try:        
            Calendar.from_ical(data) # XXX: Throws exceptions when data is invalid
            self.calendar_url = url
            self.calendar_data = data
            logging.info(f"Calendar added")
        except Exception as e:
            logging.error(f"An invalid calendar was found when {url} was followed: {e}")
            raise e

    def remove_calendar(self) -> None:
        self.calendar_url = ""
        self.calendar_data = None
    
    @property
    def breaks(self) -> List[Break]:
        return get_breaks(self.events)

    @property
    def calendar(self) -> Calendar:
        logging.debug(f"Type of calendar_data is {type(self.calendar_data)}")
        return Calendar.from_ical(self.calendar_data)

    @property
    def events(self) -> List[Event_]:
        return get_events(self.calendar)

    @property
    def subjects(self) -> Set[str]:
        return set([event.summary.split(' ')[0] for event in self.events])
        
    @property
    def timetable(self) -> Dict[str, List[dict]]:
        now = datetime.now(BRISBANE_TIME_ZONE)
        user_events = get_this_weeks_events(now, self.events)
        events_dict = weeks_events_to_dictionary(user_events)
        return events_dict

    @property
    def current_event(self) -> Optional[Event_]:
        now = datetime.now(BRISBANE_TIME_ZONE)

        for event in self.events:
            if now in event:
                return event
        
        return None

    @property
    def current_break(self) -> Optional[Break]:
        now = datetime.now(BRISBANE_TIME_ZONE)

        for brk in self.breaks:
            if now in brk:
                return brk
        
        return None    
        
    @property
    def whats_due(self) -> List[Dict[str, str]]:
        return get_whats_due(self.subjects)

    @property
    def status(self) -> Dict[str, str]: 

        user_details = { "name" : self.username, "dp": self.profile_picture }

        def make_user_status(status: str, status_info: str) -> Dict[str, str]: 
            return { "status": status, "statusInfo": status_info }

        # TODO: Add additional information here if we know for sure that a
        # User is at uni today, not just that their timetable said so

        # Case 1: User has no Calendar
        if self.calendar_data is None:
            return { **user_details, **make_user_status("Unknown", "User has no calendar") }

        now = datetime.now(BRISBANE_TIME_ZONE)
        user_events = get_todays_events(now, self.events)

        # Case 2: User does not have uni today
        if user_events == [] or self.incognito: 
            return { **user_details, **make_user_status("Unavailable", "No uni today") }

        # Case 3: User has finished uni for the day 
        if user_events[-1].end < now:
            finished_time = user_events[-1].end.strftime('%H:%M')
            return { **user_details, **make_user_status("Finished", f"Finished uni at {finished_time}") }

        # Case 4: User has not started uni for the day
        if user_events[0].start > now:
            start_time = user_events[0].start.strftime('%H:%M')
            return { **user_details, **make_user_status("Starting", f"Uni starts at {start_time}")}

        # Case 5: User is busy at uni
        busy_event = self.current_event
        if busy_event is not None:
            time_free = busy_event.end.strftime('%H:%M')
            return { **user_details, **make_user_status("Busy", f"Free at {time_free}")}

        # Case 6: User is on a break at uni
        break_event = self.current_break
        if break_event is not None:
            busy_at_time = break_event.end.strftime('%H:%M')
            return { **user_details, **make_user_status("Free", f"until {busy_at_time}")}
        # Case 7: Something went wrong
        return { **user_details, **make_user_status("Unknown", "???")}
        
    def availability(self, friend) -> Dict[str, str]:
        if self.calendar_data is not None and friend.calendar_data is not None:
            breaks = get_shared_breaks([self, friend])[:10]
            return { **self.status, "breaks": [ i.to_dict() for i in breaks ] }		
        
        return { **self.status, "breaks": [] }
    def get_confirmed_friends(self):
        confirmed_friends = []
        for friend in HasFriend.query.filter_by(fb_id=self.fb_user_id).all():
            print(f"Checking whether fb id {friend.friend_fb_id} is friends with {self.username}")

            #Find whehter the friend has added the user
            if HasFriend.query.filter_by(fb_id=friend.friend_fb_id, friend_fb_id=friend.fb_id).first() != None:
                print(f"{self.username} is a confirmed friend of fb_id {friend.friend_fb_id}")
                confirmed_friends.append(User.query.filter_by(fb_user_id=friend.friend_fb_id).first())
        return confirmed_friends

    def check_in(self) -> None:
        # now = datetime.now(BRISBANE_TIME_ZONE)
        # self.checked_in_at = now
        pass

    def check_out(self) -> None: 
        # self.checked_in_at = None
        pass

    @property
    def at_uni(self) -> bool:
        # if self.checked_in_at is None:
        #     return False
        # else:
        #     return self.checked_in_at.date() == datetime.today().date()

        # TODO: v delete me when uncommenting the above block v
        return False
  
"""
A uni-directional friendship relation. 

The user associated with the "id" field wishes to be friends with the user
associated with the "friend_id".

A unidirectional relation constitutes a friend request in the
direciton of the "friend_id" user and a pending request from the "id" user.
Denying this request deletes this table entry.

A bidirectional relation constitutes a confirmed friendship.
"""
class HasFriend(db.Model):
    __tablename__ = "HasFriend"
    fb_id        = db.Column('fb_id',         db.String(128),
                            nullable = False, primary_key = True)
    friend_fb_id = db.Column('friend_fb_id',  db.String(128),
                            nullable = False, primary_key = True)

    def __init__(self, fb_id: str, friend_fb_id: str) -> None:
        logging.warning("Establishing friendship")
        self.fb_id = fb_id
        self.friend_fb_id = friend_fb_id
        logging.warning("Friendship created")


######################
### BUSINESS LOGIC ###
######################

"""
Given a calendar, extracts all porcelain `Event_`s and throws away all
other information
"""
def get_events(cal: Calendar) -> List[Event_]:
    # http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    return [ Event_(i.get('summary'),i.get('location'), i.get('dtstart').dt, i.get('dtend').dt)\
    for i in cal.walk() if i.name == "VEVENT" ]


"""
Given a date, returns the most recent sunday of that date, at the time 11:59pm

Eg. If given the datetime "monday 21st of march, 2pm" it will return 
"Sunday 20th march, 11:59pm".
"""
def get_datetime_of_week_start(original: datetime) -> datetime:
    days_ahead = original.isoweekday()
    original_ = original - timedelta(days=days_ahead)
    return original_.replace(hour=23, minute=59)

"""
Given a list of events, returns a list of breaks between these events that:
    1) Aren't overnight
    2) Aren't "short"
"""
def get_breaks(events: List[Event_]) -> List[Break]:

    def is_short_break(x: Break) -> bool:
        duration_in_minutes = (x.end - x.start).total_seconds() // 60
        return duration_in_minutes < 15

    def is_overnight(x: Break) -> bool:
        return x.start.date() != x.end.date()

    by_start = deque(sorted(events, key=lambda i: i.start))

    breaks: List[Break] = []

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
Takes a week of events, and turns it into a jsonify-able dictionary.
"""
def weeks_events_to_dictionary(events: List[Event_]) -> Dict[str, List[dict]]:
    days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    week_events: Dict[str, List[Any]] = dict((i, []) for i in days)

    for event in events:
        if (event.end.isoweekday() == event.start.isoweekday()):
            week_events.get(days[event.start.isoweekday()]).append(event.to_dict())
    return week_events


"""
Given a date, and a list of events, returns the list of events from 
the week (Sunday -> Sunday).
"""
def get_this_weeks_events(instant: datetime, events: List[Event_]) -> List[Event_]:
    week_start = get_datetime_of_week_start(instant)
    week_end = week_start + timedelta(days=7)
    return [ i for i in events if i.start in Period(week_start, week_end) ]

def get_todays_events(instant: datetime, events: List[Event_]) -> List[Event_]:
    day_start = instant.replace(hour=0, minute=0)
    day_end = day_start + timedelta(hours=23, minutes=59)
    return [ i for i in events if i.start in Period(day_start, day_end) ]

"""
Removes breaks before the current time
"""
def cull_past_breaks(events: List[Break]) -> List[Break]:
     # Here be dragons: This is hardcoded to Brisbane's timezone
    now = datetime.now(BRISBANE_TIME_ZONE)

    return sorted([i for i in events if now < i.end], key=lambda i: i.start)


def get_shared_breaks(group_members: List[User]) -> List[Break]:
    def concat(xs: Iterable[Iterable[Any]]) -> Iterable[Any]:
        return list(chain.from_iterable(xs))

    merged_calendars = cast(List[Event_], concat(
        user.events for user in group_members))
    return cull_past_breaks(get_breaks(merged_calendars))


def get_remaining_shared_breaks_this_week(group_members: List[User]) -> List[Break]:
    # So, the Mypy type checker treats `List` as invariant, meaning we
    # can't give a `List[B]` to a function that expects a `List[A]` if
    # B is a subclass of A.
    # So we have to cast it in to the function...

    # FIXME: Get rid of these casts when Van Rossum figures out how to write a
    #        proper type system
    breaks = cast(List[Event_], get_shared_breaks(group_members))
    now = datetime.now(BRISBANE_TIME_ZONE)

    ### ... and out.
    return cast(List[Break], get_this_weeks_events(now, breaks))


"""
Takes a list of course codes, finds their course profile id numbers, parses
UQ's PHP gateway, then returns the coming assessment.
"""
def get_whats_due(subjects: Set[str]) -> List[Dict[str, str]]:
    course_url = 'https://www.uq.edu.au/study/course.html?course_code='
    assessment_url = 'https://www.courses.uq.edu.au/student_section_report' +\
        '.php?report=assessment&profileIds='

    courses_id = []
    for course in subjects:
        try:
            response = urllib.request.urlopen(course_url + course.upper())
            html = response.read().decode('utf-8')
        except:
            continue  # Ignore in the case of failure
        try:
            profile_id_regex = re.compile('profileId=\d*')
            profile_id = profile_id_regex.search(html).group()
            if profile_id != None:
                # Slice to strip the 'profileID='
                courses_id.append(profile_id[10:])
        except:
            continue  # Ignore in the case of failure

    courses = ",".join(courses_id)
    response = urllib.request.urlopen(assessment_url + courses)
    html = response.read().decode('utf-8')
    html = re.sub('<br />', ' ', html)

    soup = BeautifulSoup(html, "html5lib")
    table = soup.find('table', attrs={'class': 'tblborder'})
    rows = table.find_all('tr')[1:]  # ignore the top row of the table

    data = []
    for row in rows:
        cols = [ ele.text.strip() for ele in row.find_all('td') ]

        subject = cols[0].split(" ")[0] # Strip out irrelevant BS about the subject
        date = cols[2]

        # Some dates are ranges. We only care about the end
        if " - " in date:
            _, date = date.split(" - ")

        now = datetime.now(BRISBANE_TIME_ZONE)

        def try_parsing_date(xs: str) -> Optional[datetime]:
            # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
            # Gotta hand it to UQ for being totally inconsistent
            for fmt in ("%d %b %Y: %H:%M", "%d %b %Y : %H:%M", "%d %b %y %H:%M"):
                try:
                    return datetime.strptime(xs, fmt).replace(tzinfo=BRISBANE_TIME_ZONE)
                except ValueError:
                    pass

            return None

        due = try_parsing_date(date)

        if due and due < now:
            logging.info(f"Culling assessment due on {due}")
            continue # Don't add if it's passed deadline

        # Otherwise, add it regardless
        data.append({"subject": subject, "description": cols[1],
                     "date": cols[2], "weighting": cols[3]})

    return data
    
"""
Takes the current user id, and a supposed friend id.
Returns 1 of 3 cases
"Not Added" - the user and friend have not sent each other a friend request
"Pending" - the user has sent the friend a friend request, but they have not replied
"Accept" - the friend has sent a user a friend request, the user has not accepted
"Friends" - the user and friend are friends.
"""
def get_request_status(user_id, friend_id):
    if HasFriend.query.filter_by(fb_id=user_id, friend_fb_id=friend_id).first() != None:
        # I realise this could be a ternary but trust me this is neater.
        if HasFriend.query.filter_by(fb_id=friend_id, friend_fb_id=user_id).first() != None:
            result = "Friends"
        else:
            result = "Pending"
    else:
        if HasFriend.query.filter_by(fb_id=friend_id, friend_fb_id=user_id).first() != None:
            result = "Accept"
        else:
            result = "Not Added"

    logging.info(f"user {user_id} has the status: '{result}' with user {friend_id}")
    return result

# TODO: Move this to tests
if __name__ == "__main__":
    url = "https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w.ics"
    response = urllib.request.urlopen(url)
    data = response.read()
    user_calendar = Calendar.from_ical(data)
    user_events = get_events(user_calendar)
    todays_date = datetime.now(BRISBANE_TIME_ZONE)
    user_events = get_todays_events(todays_date, user_events)
