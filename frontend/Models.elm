module Models exposing (..)

import Http

import Time exposing (Time)

type Msg
  = ChangeTab Tab
  | Refresh
  | Tick Time
  | UpdateCalendarURLField String
  | GetMyCalendarResponse (Result Http.Error Calendar)
  | GetProfileResponse (Result Http.Error Profile)
  | GetFriendsInfoResponse (Result Http.Error FriendsInfo)
  | PostCalendarURL
  | PostCalendarURLResponse (Result Http.Error String)

-- TODO: Change all these to have Tab at the end
type Tab
  = MyCalendar
  | Friends
  | WhosFree
  | PlaceholderTab
  | ProfileTab

-- {"summary":"lecture", "start":"10:00", "end":"11:00"}
type alias Event = 
  { summary : String
  , location : String
  , start : String
  , end : String
  }

type alias Calendar = 
  { monday : List Event
  , tuesday : List Event
  , wednesday : List Event
  , thursday : List Event
  , friday : List Event
  , saturday : List Event
  , sunday : List Event
  }

type alias Profile = 
  { dp : String
  , name : String
  , email : String
  }

{-
FriendInfo Example
dp: "graph.facebook.com/1827612378/images"
name: "Charlie Groves"
status: "Free"
statusInfo: "until 3pm"
-}
type alias FriendInfo = 
  { dp : String
  , name : String
  , status : String
  , statusInfo : String
  }
type alias FriendsInfo = List FriendInfo

type alias APIError =
  { code : Int
  , message : String
  }

-- TODO: Arrange the order of these fields so it matches that in in `init`
type alias Model =
  { activeTab : Tab
  , status : String
  , hasCalendar : Bool
  , time : Time
  , calendarURLField : String
  , profile : Profile
  , friendsInfo : FriendsInfo
  , myCalendar : Calendar
  }