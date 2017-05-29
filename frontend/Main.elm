module Main exposing (..)

import Debug
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


locationToTab : Navigation.Location -> Tab
locationToTab location =
    let
        routeParser =
            Url.oneOf
                [ Url.map TimetableTab <| Url.s "timetable"
                , Url.map FriendsTab <| Url.s "friends"
                , Url.map WhosFreeTab <| Url.s "whos-free"
                , Url.map WhatsDueTab <| Url.s "whats-due"
                , Url.map ProfileTab <| Url.s "profile"
                ]
    in
        Maybe.withDefault TimetableTab <| Url.parseHash routeParser location



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
    , profile = Profile "" ""
    , settings = Settings False
    , friendsInfo = Nothing
    , whatsDue = Nothing
    , myCalendar = Nothing
    , hasUploadedCalendar =
        True
        -- until proven guilty
    , addFriendInfo = Nothing
    , friendRequestResponse = ""
    }
        ! (initState ++ refreshState)


initState : List (Cmd Msg)
initState =
    [ getWhatsDue
    , Task.perform Tick Time.now
    ]


refreshState : List (Cmd Msg)
refreshState =
    [ getCalendar
    , getAddFriendInfo
    , getFriendsInfo
    , getProfile
    , getSettings
    ]



{--
#########################################################
  UPDATE
#########################################################
--}


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeTab tab ->
            -- FIXME: ChangeTab shouldn't exist. Nav should be handled by href
            let
                cmds =
                    if tab /= model.activeTab then
                        case tab of
                            TimetableTab ->
                                [ Navigation.newUrl "#timetable", getCalendar ]

                            FriendsTab ->
                                [ Navigation.newUrl "#friends", getAddFriendInfo ]

                            WhosFreeTab ->
                                [ Navigation.newUrl "#whos-free", getFriendsInfo ]

                            WhatsDueTab ->
                                [ Navigation.newUrl "#whats-due" ]

                            ProfileTab ->
                                [ Navigation.newUrl "#profile", getProfile, getSettings ]
                    else
                        case tab of
                            TimetableTab ->
                                [ getCalendar ]

                            FriendsTab ->
                                [ getAddFriendInfo ]

                            WhosFreeTab ->
                                [ getFriendsInfo ]

                            WhatsDueTab ->
                                []

                            ProfileTab ->
                                [ getProfile, getSettings ]
            in
                model ! cmds

        UrlChange location ->
            { model
                | history = location :: model.history
                , activeTab = locationToTab location
            }
                ! []

        Refresh ->
            model ! refreshState

        Tick time ->
            { model | time = time } ! []

        UpdateCalendarURLField url ->
            { model | calendarURLField = url } ! []

        UpdateSearchField string ->
            { model | searchField = string } ! []

        UpdateIncognitoCheckbox value ->
            let
                settings_ =
                    model.settings

                model_ =
                    { model | settings = { settings_ | incognito = value } }

                -- update the model
            in
                model_ ! [ postSettings <| model_.settings ]

        -- send the updated model
        PostCalendarResponse (Ok data) ->
            { model
                | myCalendar = Just data
                , hasUploadedCalendar = True
            }
                ! [ getFriendsInfo, getWhatsDue ]

        PostCalendarResponse (Err err) ->
            { model
                | status = Debug.log "DEBUG: " <| toString err
                , myCalendar = Nothing
                , hasUploadedCalendar = False
            }
                ! []

        GetCalendarResponse (Ok data) ->
            { model
                | myCalendar = Just data
                , hasUploadedCalendar = True
            }
                ! []

        GetCalendarResponse (Err err) ->
            { model
                | status = Debug.log "DEBUG: " <| toString err
                , myCalendar = Nothing
                , hasUploadedCalendar = False
            }
                ! []

        GetProfileResponse (Ok data) ->
            { model | profile = data } ! []

        GetProfileResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        GetFriendsInfoResponse (Ok data) ->
            { model | friendsInfo = Just data } ! []

        GetFriendsInfoResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        GetWhatsDueResponse (Ok data) ->
            { model | whatsDue = Just data } ! []

        GetWhatsDueResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        GetAddFriendInfoResponse (Ok data) ->
            { model | addFriendInfo = Just data } ! []

        GetAddFriendInfoResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        GetPostFriendRequestResponse (Ok data) ->
            { model | friendRequestResponse = toString data } ! [ getAddFriendInfo, getFriendsInfo ]

        GetPostFriendRequestResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        PostCalendarURL ->
            model ! [ postCalendarURL <| model.calendarURLField ]

        PostFriendRequest friend ->
            model ! [ postFriendRequest <| friend ]

        PostRemoveFriendRequest friend ->
            model ! [ postRemoveFriendRequest <| friend ]

        DeleteCalendar ->
            model ! [ deleteCalendar ]

        GetSettingsResponse (Ok data) ->
            { model | settings = data } ! []

        GetSettingsResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        PostSettingsResponse (Ok data) ->
            { model | settings = data } ! [ getFriendsInfo ]

        PostSettingsResponse (Err err) ->
            { model | status = Debug.log "DEBUG: " <| toString err } ! []

        DeleteCalendarResponse _ ->
            model ! refreshState



{--
#########################################################
  SUBSCRIPTIONS
#########################################################
--}


subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick
