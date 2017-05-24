module Main exposing (..)

import Time exposing (Time)
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import UrlParser as Url
import Navigation

import Requests exposing (..)
import Models exposing (..)
import Views exposing (..)


{--
#########################################################
  ROUTING
#########################################################
--}

-- FIXME: Type signatures for these values and functions

main =
    Navigation.program UrlChange
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }

routeParser =
  Url.oneOf
    [ Url.map MyCalendarTab <| Url.s "calendar"
    , Url.map FriendsTab <| Url.s "friends"
    , Url.map WhosFreeTab <| Url.s "whos-free"
    , Url.map WhatsDueTab <| Url.s "whats-due"
    , Url.map ProfileTab <| Url.s "profile"
    ]

locationToTab location = 
  Maybe.withDefault MyCalendarTab <| Url.parseHash routeParser location



{--
#########################################################
  MODEL
#########################################################
--}

init : Navigation.Location -> ( Model, Cmd Msg )
init location =
    { activeTab = locationToTab location
    , history = [ location ]
    , status = "No status"
    , time = 0
    , calendarURLField = ""
    , searchField = ""
    , profile = Profile "" "" ""
    , settings = Settings False
    , friendsInfo = []
    , whatsDue = []
    , myCalendar = Calendar [] [] [] [] [] [] []
    , hasCalendar =
        True
        -- TODO: figure out whether this should this be false by default?
    , addFriendInfo = []
    , addFriendFbId = ""
    , friendRequestResponse = ""
    }
        ! initState

initState : List (Cmd Msg)
initState = [ getWhatsDue
            , Task.perform Tick Time.now
            ]

refreshState : List (Cmd Msg)
refreshState = [ getProfile
               , getSettings
               , getFriendsInfo
               , getCalendar
               , getAddFriendInfo
               ]

{--
#########################################################
  UPDATE
#########################################################
--}


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeTab tab -> -- FIXME: ChangeTab shouldn't exist. Nav should be handled by href
          let
            tab_ = case tab of
              MyCalendarTab -> "#calendar"
              FriendsTab -> "#friends"
              WhosFreeTab -> "#whos-free"
              WhatsDueTab -> "#whats-due"
              ProfileTab -> "#profile"
          in 
            model ! [ Navigation.newUrl <| tab_ ]

        UrlChange location ->
            { model | history = location :: model.history
                    , activeTab = locationToTab location } ! []

        Refresh ->
            model ! refreshState

        Tick time ->
            { model | time = time } ! refreshState

        UpdateCalendarURLField url ->
            { model | calendarURLField = url } ! []

        UpdateSearchField string ->
            { model | searchField = string }
                ! []

        UpdateIncognitoCheckbox value ->
            let
                settings_ = model.settings
                model_ = { model | settings = { settings_ | incognito = value } } -- update the model
            in
                model_ ! [ postSettings <| model_.settings ] -- send the updated model
        
        GetPostCalendarResponse (Ok data) ->
            { model
                | myCalendar = data
                , hasCalendar = True
            }
                ! [ getFriendsInfo, getWhatsDue ]

        GetPostCalendarResponse (Err err) ->
            { model
                | status = toString err
                , hasCalendar = False
                , myCalendar = Calendar [] [] [] [] [] [] []
            }
                ! []

        GetProfileResponse (Ok data) ->
            { model | profile = data } ! []

        GetProfileResponse (Err err) ->
            { model | status = toString err } ! []

        GetFriendsInfoResponse (Ok data) ->
            { model | friendsInfo = data } ! []

        GetFriendsInfoResponse (Err err) ->
            { model | status = toString err } ! []

        GetWhatsDueResponse (Ok data) ->
            { model | whatsDue = data } ! []
        
        GetWhatsDueResponse (Err err) ->
            { model | status = toString err } ! []

        GetAddFriendInfoResponse (Ok data) ->
            { model | addFriendInfo = data } ! []
        
        GetAddFriendInfoResponse (Err err) ->
            { model | status = toString err } ! []

        GetPostFriendRequestResponse (Ok data) ->
            { model | friendRequestResponse = toString data } ! [getAddFriendInfo, getFriendsInfo]
        
        GetPostFriendRequestResponse (Err err) ->
            { model | status = toString err } ! []
    
        PostCalendarURL ->
            model ! [ postCalendarURL <| model.calendarURLField ]
        
        PostFriendRequest fbId ->
            { model | addFriendFbId = fbId } ! [ postFriendRequest <| fbId]

        PostRemoveFriendRequest fbId ->
            { model | addFriendFbId = fbId } ! [ postRemoveFriendRequest <| fbId]

        DeleteCalendar -> 
            model ! [ deleteCalendar ] 

        GetPostSettingsResponse (Ok data) ->
            { model | settings = data } ! []

        GetPostSettingsResponse (Err err) ->
            { model | status = handleHTTPError err } ! []

        DeleteCalendarResponse _ ->
            model ! [ getCalendar ]



{--
#########################################################
  SUBSCRIPTIONS
#########################################################
--}


subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick
