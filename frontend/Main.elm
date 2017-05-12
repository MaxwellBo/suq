module Main exposing (..)

import Dict exposing (Dict)
import Time exposing (Time)
import Date
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Array exposing (Array)
import Maybe

import Requests exposing (..)
import Models exposing (..)

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

init : (Model, Cmd Msg)
init =
  { activeTab = MyCalendar
  , status = "No status"
  , time = 0
  , calendarURLField = ""
  , profile = Profile "" "" ""
  , friendsInfo = []
  , myCalendar = Calendar [] [] [] [] [] [] []
  , hasCalendar = True -- TODO: figure out whether this should this be false by default?
  } !
    [ getProfile
    , getFriendsInfo
    , getMyCalendar
    , Task.perform Tick Time.now
    ]

{--
#########################################################
  UPDATE
#########################################################
--}



update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    ChangeTab tab ->
      { model | activeTab = tab } ! []

    Refresh ->
      model ! [ getProfile, getMyCalendar, getFriendsInfo ]

    Tick time ->
      { model | time = time } ! []

    UpdateCalendarURLField url ->
      { model | calendarURLField  = url } ! []

    GetMyCalendarResponse (Ok data) ->
      { model | myCalendar = data 
      , hasCalendar = True
      } ! []

    GetMyCalendarResponse (Err err) ->
      { model | status = toString err
      , hasCalendar = False 
      } ! []

    GetProfileResponse (Ok data) ->
      { model | profile = data } ! []

    GetProfileResponse (Err err) ->
      { model | status = toString err } ! []

    GetFriendsInfoResponse (Ok data) ->
      { model | friendsInfo = data } ! []

    GetFriendsInfoResponse (Err err) ->
      { model | status = toString err } ! []

    PostCalendarURL ->
      model ! [ postCalendarURL <| model.calendarURLField ]

    PostCalendarURLResponse (Ok data) ->
      { model | status = data } ! [ getMyCalendar ]

    PostCalendarURLResponse (Err err) ->
      { model | status = handleHTTPError err } ! []
      

{--
#########################################################
  MAIN VIEW
#########################################################
--}
view : Model -> Html Msg
view model =
  div
    []
    [ nav [ class "nav has-shadow uq-purple", id "top"]
      [ div [ class "container"]
        [ div [ class "nav-left"]
          [ a [class "nav-item"]
            [img [src "static/images/sync_uq_logo.png", alt "SyncUQ"] []
            ]
          ]
        ]
      ]
    , div [class "tabs is-centered is-large is-hidden-mobile"]
        [ ul []
            [ li [ onClick <| ChangeTab MyCalendar, class <| isActiveTab model MyCalendar] [a [] [text "My Calendar"]]
            , li [ onClick <| ChangeTab Friends, class <| isActiveTab model Friends] [a [] [text "Friends"]]
            , li [ onClick <| ChangeTab WhosFree, class <| isActiveTab model WhosFree] [a [] [text "Who's Free?"]]
            , li [ onClick <| ChangeTab PlaceholderTab, class <| isActiveTab model PlaceholderTab] [a [] [text "Placeholder"]]
            , li [ onClick <| ChangeTab ProfileTab, class <| isActiveTab model ProfileTab] [a [] [text "Profile"]]
            ]
        ]
    , section [ class "section"]
        [ div [ class "container content"]
            [ div [class "content-margin"]
                [ case model.activeTab of
                    MyCalendar -> viewMyCalendar model
                    ProfileTab -> viewProfile model
                    Friends -> viewFriends model
                    WhosFree -> viewWhosFree model
                    PlaceholderTab -> viewPlaceholderTab model
                ]
            ]
        ]

    , div [ class "glue-to-bottom is-hidden-tablet" ]
        [ div [ class "is-mobile is-large columns" ]
          --Each tab is a "column" on mobile, to add a new tab, add a new div with mobile-tab and column class
          [ div [class "mobile-tab column", onClick <| ChangeTab MyCalendar, class <| isActiveTabMobile model MyCalendar] [a [] [i [ class "fa fa-calendar" ] []]]
          , div [class "mobile-tab column", onClick <| ChangeTab Friends, class <| isActiveTabMobile model Friends] [a [] [i [ class "fa fa-users" ] []]]
          , div [class "mobile-tab column", onClick <| ChangeTab WhosFree, class <| isActiveTabMobile model WhosFree] [a [] [i [ class "fa fa-question" ] []]]
          , div [class "mobile-tab column", onClick <| ChangeTab PlaceholderTab, class <| isActiveTabMobile model PlaceholderTab] [a [] [i [ class "fa fa-bell" ] []]]
          , div [class "mobile-tab column", onClick <| ChangeTab ProfileTab, class <| isActiveTabMobile model ProfileTab] [a [] [i [ class "fa fa-user-secret" ] []]]
          ]
        ]
    ]
{--
#########################################################
  TABS
#########################################################
--}
viewMyCalendar : Model -> Html Msg
viewMyCalendar model =
  if model.hasCalendar then
    viewCalendarCards model.myCalendar
  else
    let
      instructions
        = ol []
            [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
            , li [] [ text "Open the side menu and long press the 'Share' button. Then press 'Copy link'" ]
            , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
            ]
    in
      div []
        [ p [class "title title-padding"] [text "Import your Calendar"]
        , div [class "is-hidden-tablet"] 
          [ img [class "mobile-cal-img", src "../static/images/mobile_copy_cal_1.jpg"] []
          , img [class "mobile-cal-img-two", src "../static/images/mobile_copy_cal_2.jpg"] []
          , instructions
          ]
        , div [class "is-hidden-mobile"]
          [ div [ class "crop-height" ] [img [class "desktop-cal-img scale", src "../static/images/desktop_copy_cal.png"] []]
          , instructions
          ]
        , div [] [ text <| model.status ]
        , input [ class "input is-primary input-margin", type_ "text", placeholder "paste timetable link here", onInput UpdateCalendarURLField, value model.calendarURLField ] []
        , button [ class "button is-primary", onClick PostCalendarURL ] [ text "Submit" ]
        , p [] [text "Your link should look like this 'https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w'"]
        ]

viewFriends : Model -> Html Msg
viewFriends model =
    div [] []

viewWhosFree : Model -> Html Msg
viewWhosFree model =
    div []
      [ p [class "title title-padding"] [ text "Who's Free?"]
      ,div []
        (List.map viewFriendInfo model.friendsInfo)
      ]

viewPlaceholderTab : Model -> Html Msg
viewPlaceholderTab model =
  div [] []

-- TODO: Refactor this so that it takes a Profile, instead of the whole model
viewProfile : Model -> Html Msg
viewProfile model =
  div []
    [ div [ class "profile-head" ]
      [ img [ src model.profile.dp, class "dp" ] []
      , div [ class "h1 profile-head-text" ]
        [ text model.profile.name ]
      ]
    , div [ class "profile-body" ]
      [ div [ class "profile-row odd-row" ]
        [ text "Email: ", text model.profile.email ]
      , div [ class "profile-row even-row" ] [ text <| "Local time: " ++ timeFormat model.time ]
      , button [ onClick Refresh, class "refresh button is-medium" ] [ text "Refresh" ]
      ]
    ]

{--
#########################################################
  HELPER FUNCTIONS FOR TABS
#########################################################
--}
viewEventCard : Event -> Html Msg
viewEventCard event =
  let
    -- TODO: Remove this `let` block - these do not need to be re-aliased
    summary = event.summary
    location = event.location
    startTime = event.start
    endTime = event.end
  in
    div [class "event-info-card"]
      [ article [class "media justify-between"]
        [ div [class "media-left"]
          [p [class "event-summary-text"]
            [text summary]
          ,p [class "event-location-text"]
            [text location]
          ]
        , div [class "media-right"]
          [p [class "event-time-text"]
            [text (startTime ++ " - " ++ endTime)]
          ]
        ]
      ]

{--
TODO: Abstract this so it isnt so long
--}
viewCalendarCards : Calendar -> Html Msg
viewCalendarCards calendar =
  let
    pClass = "title title-padding event-card-day"
  in
    div []
      [ p [class pClass] [text "Monday"]
      , div [] (List.map viewEventCard calendar.monday)
      , p [class pClass] [text "Tuesday"]
      , div [] (List.map viewEventCard calendar.tuesday)
      , p [class pClass] [text "Wednesday"]
      , div [] (List.map viewEventCard calendar.wednesday)
      , p [class pClass] [text "Thursday"]
      , div [] (List.map viewEventCard calendar.thursday)
      , p [class pClass] [text "Friday"]
      , div [] (List.map viewEventCard calendar.friday)
      , p [class pClass] [text "Saturday"]
      , div [] (List.map viewEventCard calendar.saturday)
      , p [class pClass] [text "Sunday"]
      , div [] (List.map viewEventCard calendar.sunday)
      ]

viewFriendInfo : FriendInfo -> Html Msg
viewFriendInfo friendInfo =
  let
    background = friendInfo.status ++ "-bg"
  in
    div [class ("friend-info-card " ++ background)]
      [ article [class "media align-center"]
        [ div [class "media-left align-center"]
          [ img [ src friendInfo.dp, class "dp" ] [] ]
        , div [class "media-content"]
            [div [class "content"]
              [ p [class "friend-info-name-text"]
                [ text <| friendInfo.name
                ]
              ]
            ]
        , div [class "media-right"]
            [ i [class "friend-status-text"]
              [ text <| friendInfo.status 
              ]
          , br [] []
          , div [class "friend-status-info-text"]
            [ text <| friendInfo.statusInfo
             ]
           ]
       ]
     ]

timeFormat : Time -> String
timeFormat time =
  let
    pad c = String.padLeft 2 c << toString
    hours = Date.hour << Date.fromTime <| time
    minutes = Date.minute << Date.fromTime <| time
  in
     pad ' ' hours ++ ":" ++ pad '0' minutes

isActiveTab : Model -> Tab -> String
isActiveTab model tab =
  if model.activeTab == tab then
    "is-active tab"
  else
    "tab"
isActiveTabMobile : Model -> Tab -> String
isActiveTabMobile model tab =
  if model.activeTab == tab then
    "is-active-mobile"
  else
    ""
{--
#########################################################
  SUBSCRIPTIONS
#########################################################
--}
subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick

