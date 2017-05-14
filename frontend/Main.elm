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
           , getMyCalendar
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

        GetMyCalendarResponse (Ok data) ->
            { model
                | myCalendar = data
                , hasCalendar = True
            }
                ! []

        GetMyCalendarResponse (Err err) ->
            { model
                | status = toString err
                , hasCalendar = False
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

        PostCalendarURLResponse (Ok data) ->
            { model | status = data } ! [ getMyCalendar ]

        PostCalendarURLResponse (Err err) ->
            { model | status = handleHTTPError err } ! []

        GetPostSettingsResponse (Ok data) ->
            { model | settings = data } ! []

        GetPostSettingsResponse (Err err) ->
            { model | status = handleHTTPError err } ! []

view : Model -> Html Msg
view model =
    div
        []
        [ nav [ class "nav has-shadow uq-purple", id "top" ]
            [ div [ class "container" ]
                [ div [ class "nav-left" ]
                    [ a [ class "nav-item" ]
                        [ img [ src "static/images/sync_uq_logo.png", alt "SyncUQ" ] []
                        ]
                    ]
                ]
            ]
        , div [ class "tabs is-centered is-large is-hidden-mobile" ]
            [ ul []
                [ li [ onClick <| ChangeTab MyCalendarTab, class <| isActiveTab model MyCalendarTab ] [ a [] [ text "My Calendar" ] ]
                , li [ onClick <| ChangeTab FriendsTab, class <| isActiveTab model FriendsTab ] [ a [] [ text "Friends" ] ]
                , li [ onClick <| ChangeTab WhosFreeTab, class <| isActiveTab model WhosFreeTab ] [ a [] [ text "Who's Free?" ] ]
                , li [ onClick <| ChangeTab WhatsDueTab, class <| isActiveTab model WhatsDueTab ] [ a [] [ text "What's Due?" ] ]
                , li [ onClick <| ChangeTab ProfileTab, class <| isActiveTab model ProfileTab ] [ a [] [ text "Profile" ] ]
                ]
            ]
        , section [ class "section" ]
            [ div [ class "container content" ]
                [ div [ class "content-margin" ]
                    [ case model.activeTab of
                        MyCalendarTab ->
                            viewMyCalendar model

                        FriendsTab ->
                            viewFriends model

                        WhosFreeTab ->
                            viewWhosFree model

                        WhatsDueTab ->
                            viewWhatsDueTab model

                        ProfileTab ->
                            viewProfile model
                    ]
                ]
            ]
        , div [ class "glue-to-bottom is-hidden-tablet" ]
            [ div [ class "is-mobile is-large columns" ]
                --Each tab is a "column" on mobile, to add a new tab, add a new div with mobile-tab and column class
                [ div [ class "mobile-tab column", onClick <| ChangeTab MyCalendarTab, class <| isActiveTabMobile model MyCalendarTab ] [ a [] [ i [ class "fa fa-calendar" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab FriendsTab, class <| isActiveTabMobile model FriendsTab ] [ a [] [ i [ class "fa fa-users" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab WhosFreeTab, class <| isActiveTabMobile model WhosFreeTab ] [ a [] [ i [ class "fa fa-question" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab WhatsDueTab, class <| isActiveTabMobile model WhatsDueTab ] [ a [] [ i [ class "fa fa-bell" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab ProfileTab, class <| isActiveTabMobile model ProfileTab ] [ a [] [ i [ class "fa fa-user-secret" ] [] ] ]
                ]
            ]
        ]


{--
#########################################################
  SUBSCRIPTIONS
#########################################################
--}


subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick
