module Main exposing (..)

import Time exposing (Time)
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Requests exposing (..)
import Models exposing (..)
import Views exposing (..)


main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



{--
#########################################################
  MODEL
#########################################################
--}

init : ( Model, Cmd Msg )
init =
    { activeTab = MyCalendarTab
    , status = "No status"
    , time = 0
    , calendarURLField = ""
    , profile = Profile "" "" ""
    , settings = Settings False
    , friendsInfo = []
    , whatsDue = []
    , myCalendar = Calendar [] [] [] [] [] [] []
    , hasCalendar =
        True
        -- TODO: figure out whether this should this be false by default?
    , addFriendInfo = []
    }
        ! getState

getState : List (Cmd Msg)
getState = [ getProfile
           , getSettings
           , getFriendsInfo
           , getCalendar
           , getWhatsDue
           , getAddFriendInfo
           , Task.perform Tick Time.now
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
            { model | activeTab = tab } ! []

        Refresh ->
            model ! getState

        Tick time ->
            { model | time = time } ! []

        UpdateCalendarURLField url ->
            { model | calendarURLField = url } ! []

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
            
        PostCalendarURL ->
            model ! [ postCalendarURL <| model.calendarURLField ]

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
