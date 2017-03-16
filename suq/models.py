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
UserID = str

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(10))
    FBuserID = db.Column('fb_user_id',db.String(32))
    FBAccessToken = db.Column('fb_access_token', db.String(128))
    email = db.Column('email',db.String(50),unique=True , index=True)
    registered_on = db.Column('registered_on' , db.DateTime)

    def __init__(self , username ,password , email, FBuserID, FBAccessToken):
        logging.warning("Creating user")
        self.username = username
        self.password = self.psw_to_md5(password) #Hash password
        self.email = email
        self.FBuserID = FBuserID
        self.FBAccessToken = FBAccessToken
        self.registered_on = datetime.utcnow()
        logging.warning("Creating user with properties Name: %s, Password: %s, Email: %s, Time: %s" % (self.username, self.password, self.email, self.registered_on))
    
    @classmethod
    def psw_to_md5(self, str_psw):
        import hashlib
        if str_psw == None:
            return None
        else:
            m = hashlib.md5(str_psw.encode(encoding='utf-8'))
            return m.hexdigest()

class CalDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    calendar = db.Column(db.LargeBinary())

    def __init__(self, name: str, calendar: str) -> None:
        self.username = name
        self.calendar = calendar

    def __repr__(self):
        return '<Name %r>' % self.name


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

def get_events(cal: Calendar) -> List[Event_]:
    # http://icalendar.readthedocs.io/en/latest/_modules/icalendar/prop.html#vDDDTypes
    return [ Event_(i.get('summary'), i.get('dtstart').dt, i.get('dtend').dt)\
    for i in cal.walk() if i.name == "VEVENT" ]

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

if __name__ == "__main__":
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
