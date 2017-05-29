module Models exposing (..)

import Http
import Navigation
import Time exposing (Time)


type Msg
    = ChangeTab Tab
    | UrlChange Navigation.Location
    | Refresh
    | Tick Time
    | UpdateCalendarURLField String
    | UpdateSearchField String
    | UpdateIncognitoCheckbox Bool
    | PostCalendarURL
    | PostFriendRequest AddFriendInfoPiece
    | PostRemoveFriendRequest AddFriendInfoPiece
    | DeleteCalendar
    | OpenViewSharedBreaks FriendInfo
    | CloseViewSharedBreaks
    | GetCalendarResponse (Result Http.Error Calendar)
    | PostCalendarResponse (Result Http.Error Calendar)
    | GetPostFriendRequestResponse (Result Http.Error String)
    | GetProfileResponse (Result Http.Error Profile)
    | GetFriendsInfoResponse (Result Http.Error FriendsInfo)
    | GetWhatsDueResponse (Result Http.Error WhatsDue)
    | GetAddFriendInfoResponse (Result Http.Error AddFriendInfo)
    | GetSettingsResponse (Result Http.Error Settings)
    | PostSettingsResponse (Result Http.Error Settings)
    | DeleteCalendarResponse (Result Http.Error ())


type Tab
    = TimetableTab
    | FriendsTab
    | WhosFreeTab
    | WhatsDueTab
    | ProfileTab


{-| {"summary":"lecture", "start":"10:00", "end":"11:00"}
-}
type alias Event =
    { summary : String
    , location : String
    , start : String
    , end : String
    }


{-| FIXME: Called a timetable now
-}
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
    }


type alias Settings =
    { incognito : Bool }


{-|
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
    , breaks : Breaks
    }


type alias Break =
    { start : String
    , end : String
    , day : String
    }


type alias Breaks =
    List Break


type alias FriendsInfo =
    List FriendInfo


type alias APIError =
    { code : Int
    , message : String
    }


type alias WhatsDue =
    List Piece


type alias Piece =
    { subject : String
    , description : String
    , date : String
    , weighting : String
    , completed : Bool
    }


type alias AddFriendInfo =
    List AddFriendInfoPiece


type alias AddFriendInfoPiece =
    { name : String
    , fbId : String
    , dp : String
    , status : String
    }


{-| TODO: Arrange the order of these fields so it matches that in in `init`
-}
type alias Model =
    { activeTab : Tab
    , history : List Navigation.Location
    , status : String
    , time : Time
    , calendarURLField : String
    , searchField : String
    , profile : Profile
    , settings : Settings
    , friendsInfo : Maybe FriendsInfo
    , whatsDue : Maybe WhatsDue
    , breaksPopup : Maybe FriendInfo
    , myCalendar : Maybe Calendar
    , hasUploadedCalendar : Bool
    , addFriendInfo : Maybe AddFriendInfo
    , friendRequestResponse : String
    }
