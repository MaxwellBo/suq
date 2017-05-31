__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import logging
from itertools import *
import urllib.request
from typing import List, Dict, Any, Optional, Iterable, Set, cast
from datetime import datetime, timezone, timedelta, date
from collections import deque

# Libraries
import flask_login
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy # type: ignore
from icalendar import Calendar, Event # type: ignore

# Imports
from backend.middleware import *

#################
### CONSTANTS ###
#################

BRISBANE_TIME_ZONE = timezone(timedelta(hours=10))

###############
### GLOBALS ###
###############

db = SQLAlchemy()
"""
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue
"""

########################
### BUSINESS OBJECTS ###
########################

class Period(object):
    """
    An abstract class representing the concept of a period of time
    """
    
    def __init__(self, start: datetime, end: datetime) -> None:
        self.start = start
        self.end = end

    def __contains__(self, instant: datetime) -> bool:
        return self.start <= instant <= self.end


class Break(Period):
    """
    A concrete class representing the period of time between two events

    NOTE: This adds some presentation logic onto Period, which it extends, mostly
        unchanged
    """

    @property
    def is_short(self) -> bool:
        duration_in_minutes = (self.end - self.start).total_seconds() // 60
        return duration_in_minutes < 15

    @property
    def is_overnight(self) -> bool:
        return self.start.date() != self.end.date()

    def to_dict(self) -> dict:

        DAY_NAMES = [ "Monday", "Tuesday", "Wednesday", "Thursday", 
                            "Friday", "Saturday", "Sunday" ] 

        start_string = str(self.start.strftime('%H:%M'))
        end_string = str(self.end.strftime('%H:%M'))
        day = DAY_NAMES[self.start.weekday()]
        return { "start": start_string, "end": end_string, "day": day }

    def __repr__(self) -> str:
        return f"Break({repr(self.start)}, {repr(self.end)})"

class Event_(Period):
    """
    A concrete class representing an event that occured at a certain location
    for a period of time

    NOTE: The name `Event_` was chosen so that it did not shadow the `icalendar`
        class `Event`
    """

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
    _profile_picture = db.Column('profile_picture',  db.String(512)) # FIXME: Remove
    email           = db.Column('email',            db.String(128))
    registered_on   = db.Column('registered_on',    db.DateTime)
    calendar_url    = db.Column('calendar_url',     db.String(512))
    calendar_data   = db.Column('calendar_data',    db.LargeBinary())
    incognito       = db.Column('incognito',        db.Boolean())
    # checked_in_at = db.Column('checkedInAt'), db.datetime()???, nullable=true )
    # on_break_at = db.Column('onBreakAt'), db.datetime()????, nullable=true)
    # TODO: Add these fields

    def __init__(self, username: str, email: str, fb_user_id: str, fb_access_token: str) -> None:
        logging.info("Creating user")
        self.username = username
        self.email = email
        self.fb_user_id = fb_user_id
        self.fb_access_token = fb_access_token
        self.calendar_url = ""
        self.calendar_data = None
        self.registered_on = datetime.utcnow()
        self.incognito = False
        self.checked_in_at: Optional[datetime] = None # NOTE: Not mapped to the DB at the moment
        self.on_break_at: Optional[datetime] = None   # NOTE: Not mapped to the DB at the moment

        logging.info("Creating user with the following properties"
                        + f": Name: {self.username}"
                        + f", Email: {self.email}, Time: {self.registered_on}")


    def add_calendar(self, url: str) -> None:
        """
        Downloads the calendar stored at the provided and URL, and loads the binary
        into the database

        This method also

            1) Attempts to correct common user mistakes associated with URL input
            2) Throws errors if the request, or the calendar data, or the calendar
            is invalid
        """
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
    def profile_picture(self) -> str:
        if self.fb_user_id is not None:
            return f"https://graph.facebook.com/{self.fb_user_id}/picture" 
            # add '?type=large' to the end of this link to get a larger photo
        else:
            return ""

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
        """
        Finds out the users current status
        One of 7 possible status's
        Unknown, Unavailable, Finished, Starting, Busy, Free, Unknown
        """
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
        if all(i.end < now for i in user_events):
            finished_time = sorted(
                user_events, key=lambda i: i.end)[-1].end.strftime('%H:%M')
            return { **user_details, **make_user_status("Finished", f"Finished uni at {finished_time}") }

        # Case 4: User has not started uni for the day
        if all(now < i.start for i in user_events):
            start_time = sorted(
                user_events, key=lambda i: i.start)[0].start.strftime('%H:%M')
            return { **user_details, **make_user_status("Starting", f"Uni starts at {start_time}")}

        busy_event = self.current_event
        break_event = self.current_break

        # Case 5: User is on a break at uni
        if break_event is not None and not break_event.is_short:
            busy_at_time = break_event.end.strftime('%H:%M')
            return { **user_details, **make_user_status("Free", f"until {busy_at_time}")}

        # Case 6: User is on a short break
        if busy_event is None and break_event is not None and break_event.is_short:
            # XXX: Here be dragons: Mutates context for the next condition to catch
            #                       AND DOES NOT RETURN
            # We're free to perform the index on [0] here because short breaks
            # only get created when there's events ahead of us
            busy_event = sorted([ i for i in user_events
                if now < i.start ], key=lambda i: i.start)[0]

        # Case 7: User is busy at uni
        if busy_event is not None:
            time_free = busy_event.end.strftime('%H:%M')
            return { **user_details, **make_user_status("Busy", f"Free at {time_free}")}


        logging.debug(("Status blew up: calendar_data: {}, user_events: {}"
                       "busy_event: {} break_event: {}").format(
                           type(self.calendar_data), user_events, busy_event, break_event))

        # Case 8: Something went wrong
        return { **user_details, **make_user_status("Unknown", "???")}
        
    def availability(self, friend: User) -> Dict[str, Any]:
        """
        Returns the user's current status and a list of "sync"'d breaks between
        the user and the friend parameter
        """
        if self.calendar_data is not None and friend.calendar_data is not None:
            breaks = get_shared_breaks({self, friend})[:10]
            return { **self.status, "breaks": [ i.to_dict() for i in breaks ] }		
        
        return { **self.status, "breaks": [] }

    @property
    def confirmed_friends(self) -> List[User]:
        """
        Finds the current user's confirmed friends.
        """
        confirmed_friends = []
        for friend in HasFriend.query.filter_by(fb_id=self.fb_user_id).all():
            logging.info(f"Checking whether fb id {friend.friend_fb_id} is friends with {self.username}")

            # Find whether the friend has added the user
            if HasFriend.query.filter_by(fb_id=friend.friend_fb_id, friend_fb_id=friend.fb_id).first() != None:
                logging.info(f"{self.username} is a confirmed friend of fb_id {friend.friend_fb_id}")
                confirmed_friends.append(User.query.filter_by(fb_user_id=friend.friend_fb_id).first())
        return confirmed_friends

    def check_in(self) -> None:
        now = datetime.now(BRISBANE_TIME_ZONE)
        self.checked_in_at = now

    def check_out(self) -> None: 
        self.checked_in_at = None

    @property
    def at_uni(self) -> bool:
        """
        Whether the uni has checked in as "at uni" today
        """
        if self.checked_in_at is None:
            return False
        else:
            return self.checked_in_at.date() == datetime.today().date()

    def begin_break(self) -> None:
        now = datetime.now(BRISBANE_TIME_ZONE)
        self.on_break_at = now

    def end_break(self) -> None: 
        self.on_break_at = None

    @property
    def on_break(self) -> bool:
        """
        Whether the user has recently checked in as "on a break"
        """

        if self.on_break_at is None:
            return False
        else:
            now = datetime.now(BRISBANE_TIME_ZONE)
            return self.on_break_at >= now - timedelta(hours=2)
  
class HasFriend(db.Model):
    """
    A uni-directional friendship relation. 

    The user associated with the "id" field wishes to be friends with the user
    associated with the "friend_id".

    A unidirectional relation constitutes a friend request in the
    direciton of the "friend_id" user and a pending request from the "id" user.
    Denying this request deletes this table entry.

    A bidirectional relation constitutes a confirmed friendship.
    """
    __tablename__ = "HasFriend"
    fb_id        = db.Column('fb_id',         db.String(128),
                            nullable = False, primary_key = True)
    friend_fb_id = db.Column('friend_fb_id',  db.String(128),
                            nullable = False, primary_key = True)

    def __init__(self, fb_id: str, friend_fb_id: str) -> None:
        logging.info("Establishing friendship")
        self.fb_id = fb_id
        self.friend_fb_id = friend_fb_id
        logging.info("Friendship created")


######################
### BUSINESS LOGIC ###
######################

def get_events(cal: Calendar) -> List[Event_]:
    """
    Given a calendar, extracts all porcelain `Event_`s and throws away all
    other information
    """
    # http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    events = [ Event_(i.get('summary'),i.get('location'), i.get('dtstart').dt, i.get('dtend').dt)\
    for i in cal.walk() if i.name == "VEVENT" ]

    # This is probably not necessary, and it should be the duty for downstream
    # consumers of this method to maintain their own preconditions
    # BUT we're forcing the sorting of this just in case a downstream consumer
    # makes assumptions about the order of the calendar
    return sorted(events, key=lambda i: i.start)


def get_datetime_of_week_start(original: datetime) -> datetime:
    """
    Given a date, returns the most recent sunday of that date, at the time 11:59pm

    Eg. If given the datetime "monday 21st of march, 2pm" it will return 
    "Sunday 20th march, 11:59pm".
    """
    days_ahead = original.isoweekday()
    original_ = original - timedelta(days=days_ahead)
    return original_.replace(hour=23, minute=59)

def get_breaks(events: List[Event_]) -> List[Break]:
    """
    Given a list of events, returns a list of breaks between these events that:
        1) Aren't overnight
        2) Aren't "short"
    """

    by_start = deque(sorted(events, key=lambda i: i.start))

    breaks: List[Break] = []

    while True:
        # If we've run out of gaps between two events to find
        if len(by_start) < 2:
            return [i for i in breaks if not i.is_short and not i.is_overnight]

        subject = by_start.popleft()

        if any(subject.end in i for i in by_start):
            continue
        else:
            # Only subjects with "exposed" outer-ends
            # get to create a break to the next event
            breaks.append(Break(subject.end, by_start[0].start))

def weeks_events_to_dictionary(events: List[Event_]) -> Dict[str, List[dict]]:
    """
    Takes a week of events, and turns it into a jsonify-able dictionary.
    """

    CALENDAR_FIELD_NAMES = [ "monday", "tuesday", "wednesday", "thursday", 
                            "friday", "saturday", "sunday" ] 
    # FIXME: This might be already a part of datetime

    week_events: Dict[str, List[Any]] = dict((i, []) for i in CALENDAR_FIELD_NAMES)

    for event in events:
        if (event.end.weekday() == event.start.weekday()):
            week_events.get(CALENDAR_FIELD_NAMES[event.start.weekday()]).append(event.to_dict())
    return week_events


def get_this_weeks_events(instant: datetime, events: List[Event_]) -> List[Event_]:
    """
    Given a date, and a list of events, returns the list of events from 
    the week (Sunday -> Sunday).
    """
    week_start = get_datetime_of_week_start(instant)
    week_end = week_start + timedelta(days=7)
    return [ i for i in events if i.start in Period(week_start, week_end) ]

def get_todays_events(instant: datetime, events: List[Event_]) -> List[Event_]:
    """
    TODO
    """
    day_start = instant.replace(hour=0, minute=0)
    day_end = day_start + timedelta(hours=23, minutes=59)
    return [ i for i in events if i.start in Period(day_start, day_end) ]

def cull_past_breaks(events: List[Break]) -> List[Break]:
    """
    Removes breaks before the current time
    """
     # Here be dragons: This is hardcoded to Brisbane's timezone
    now = datetime.now(BRISBANE_TIME_ZONE)

    return sorted([i for i in events if now < i.end], key=lambda i: i.start)


def get_shared_breaks(group_members: Set[User]) -> List[Break]:
    """
    Finds common breaks between a group of users.
    """
    def concat(xs: Iterable[Iterable[Any]]) -> Iterable[Any]:
        return list(chain.from_iterable(xs))

    merged_calendars = cast(List[Event_], concat(
        user.events for user in group_members))
    return cull_past_breaks(get_breaks(merged_calendars))


def get_remaining_shared_breaks_this_week(group_members: Set[User]) -> List[Break]:
    """
    Finds this weeks remaining common breaks between a group of users
    """
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


# FIXME: Make 'request_status' an enum: https://docs.python.org/3/library/enum.html
def get_request_status(user_id: str, friend_id: str) -> str:
    """
    Takes the current user id, and a supposed friend id.
    Returns 1 of 3 cases
    "Not Added" - the user and friend have not sent each other a friend request
    "Pending" - the user has sent the friend a friend request, but they have not replied
    "Accept" - the friend has sent a user a friend request, the user has not accepted
    "Friends" - the user and friend are friends.
    """
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

