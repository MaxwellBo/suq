import Dict exposing (Dict)
import Time exposing (Time)
import Date
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode
import Array exposing (Array)

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
type Tab
  = MyCalendar
  | Friends
  | WhosFree
  | PlaceholderTab
  | Profile

{--
Calendar Example
"monday": [{"summary":"lecture", "start":"10:00", "end":"11:00"}
          , {"summary":"tute", "start":"12:00", "end":"13:00"}
          ]

"tuesday": [{"summary":"lecture", "start":"10:00", "end":"11:00"}
           , {"summary":"tute", "start":"12:00", "end":"13:00"}
           ]

"wednesday": [{"summary":"lecture", "start":"10:00", "end":"11:00"}
             , {"summary":"tute", "start":"12:00", "end":"13:00"}
             ]

"friday" : []
"saturday" : []
"sunday" : []
--}
type alias Event = Dict String String
type alias Calendar = Dict String (List Event)
type alias Profile = Dict String String
type alias FriendsBreaks = Dict String (List Time)

{-
FriendInfo Example
name: "Charlie Groves"
dp: "graph.facebook.com/1827612378/images"
status: "Free"
statusInfo: "until 3pm"
-}
type alias FriendInfo = Dict String String
type alias FriendsInfo = List FriendInfo

type alias APIError =
  { code : Int
  , message : String
  }

type alias Model =
  { activeTab : Tab
  , status : String
  , hasCalendar : Bool
  , time : Time
  , calendarURLField : String
  , profile : Profile
  , friendsBreaks : FriendsBreaks
  , friendsInfo : FriendsInfo
  , myCalendar : Calendar
  }

init : (Model, Cmd Msg)
init =
  { activeTab = MyCalendar
  , status = "No status"
  , time = 0
  , calendarURLField = ""
  , profile = Dict.empty
  , friendsBreaks = Dict.empty
  , friendsInfo = []
  , myCalendar = Dict.empty
  , hasCalendar = True
  } !
    [ getProfile
    , getFriendsInfo
    , getMyCalendar
    , Task.perform Tick Time.now
    ]


mockFriendsBreaks : FriendsBreaks
mockFriendsBreaks = Dict.fromList [ ("Hugo", [100.0]), ("Charlie", [200.0])]

{--
#########################################################
  UPDATE
#########################################################
--}
type Msg
  = ChangeTab Tab
  | Refresh
  | Tick Time
  | UpdateCalendarURLField String
  | GetMyCalendarResponse (Result Http.Error Calendar)
  | GetProfileResponse (Result Http.Error Profile)
  | GetFriendsInfoResponse (Result Http.Error FriendsInfo)
  | GetFriendBreaksResponse (Result Http.Error FriendsBreaks)
  | PostCalendarURL
  | PostCalendarURLResponse (Result Http.Error String)



update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    ChangeTab tab ->
      { model | activeTab = tab } ! []

    Refresh ->
      model ! [ getProfile, getFriendsBreaks, getFriendsInfo, getMyCalendar ]

    Tick time ->
      { model | time = time } ! []

    UpdateCalendarURLField url ->
      { model | calendarURLField  = url } ! []

    GetMyCalendarResponse (Ok data) ->
      { model | myCalendar = data 
      , hasCalendar = True} ! []

    GetMyCalendarResponse (Err err) ->
      { model | status = toString err
      , hasCalendar = False} ! []

    GetProfileResponse (Ok data) ->
      { model | profile = data } ! []

    GetProfileResponse (Err err) ->
      { model | status = toString err } ! []

    GetFriendsInfoResponse (Ok data) ->
      { model | friendsInfo = data } ! []

    GetFriendsInfoResponse (Err err) ->
      { model | status = toString err } ! []

    GetFriendBreaksResponse (Ok data) ->
      { model | friendsBreaks = data } ! []

    GetFriendBreaksResponse (Err err) ->
      { model | status = toString err } ! []

    PostCalendarURL ->
      model ! [ postCalendarURL <| model.calendarURLField ]

    PostCalendarURLResponse (Ok data) ->
      { model | status = data } ! []

    PostCalendarURLResponse (Err err) ->
      { model | status = handleHTTPError err } ! []


-- http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Error
-- http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Response
handleHTTPError : Http.Error -> String
handleHTTPError response =
  let
    decodeError : Decoder APIError
    decodeError =
      Decode.at ["error"] <| Decode.map2 APIError
        (Decode.field "code" Decode.int)
        (Decode.field "message" Decode.string)

    formatError : Int -> String -> String -> String
    formatError code mx my =
      "CODE - { "
      ++ (toString <| code)
      ++ " }     MESSAGE - { "
      ++ mx ++ " | " ++ my ++ " }"
  in
    case response of
      Http.BadUrl string -> string
      Http.Timeout -> "Timeout"
      Http.NetworkError -> "Network Error"
      Http.BadPayload error response -> error
      Http.BadStatus response ->
        case Decode.decodeString decodeError response.body of
          (Ok apiError) -> 
            formatError response.status.code response.status.message apiError.message          
          (Err parsingErrorMessage) -> 
            formatError response.status.code response.status.message parsingErrorMessage


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
            [img [src "static/images/syncuqlogo.png", alt "SyncUQ"] []
            ]
          ]
        ]
      ]
    , div [class "tabs is-centered is-large is-hidden-mobile"]
        [ ul []
            [li [ onClick <| ChangeTab MyCalendar, class <| isActiveTab model MyCalendar] [a [] [text "My Calendar"]]
            ,li [ onClick <| ChangeTab Friends, class <| isActiveTab model Friends] [a [] [text "Friends"]]
            ,li [ onClick <| ChangeTab WhosFree, class <| isActiveTab model WhosFree] [a [] [text "Who's Free?"]]
            ,li [ onClick <| ChangeTab PlaceholderTab, class <| isActiveTab model PlaceholderTab] [a [] [text "Placeholder"]]
            ,li [ onClick <| ChangeTab Profile, class <| isActiveTab model Profile] [a [] [text "Profile"]]
            ]
        ]
    , section [ class "section"]
        [ div [ class "container content"]
            [ div [class "content-margin"]
                [ case model.activeTab of
                    MyCalendar -> viewMyCalendar model
                    Profile -> viewProfile model
                    Friends -> viewFriends model
                    WhosFree -> viewWhosFree model
                    PlaceholderTab -> viewPlaceholderTab model
                ]
            ]
        ]

    , div [class "glue-to-bottom is-hidden-tablet"]
        [div [class "is-mobile is-large columns"]
          [
            --Each tab is a "column" on mobile, to add a new tab, add a new div with mobile-tab and column class
            div [class "mobile-tab column", onClick <| ChangeTab MyCalendar, class <| isActiveTabMobile model MyCalendar] [a [] [i [ class "fa fa-calendar" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab Friends, class <| isActiveTabMobile model Friends] [a [] [i [ class "fa fa-users" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab WhosFree, class <| isActiveTabMobile model WhosFree] [a [] [i [ class "fa fa-question" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab PlaceholderTab, class <| isActiveTabMobile model PlaceholderTab] [a [] [i [ class "fa fa-bell" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab Profile, class <| isActiveTabMobile model Profile] [a [] [i [ class "fa fa-user-secret" ] []]]
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
    div []
      [ p [class "title title-padding"] [text "Import your Calendar"]
      , div [class "is-hidden-tablet"] 
        [ img [class "mobile-cal-img", src "../static/images/mobileCopyCal1.jpg"] []
        , img [class "mobile-cal-img-two", src "../static/images/mobileCopyCal2.jpg"] []
        , ol []
          [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
          , li [] [ text "Open the side menu and long press the 'Share' button. Then press 'Copy link'" ]
          , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
          ]
        ]
      , div [class "is-hidden-mobile"]
        [ div [ class "crop-height" ] [img [class "desktop-cal-img scale", src "../static/images/desktopCopyCal.png"] []]
        , ol []
          [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
          , li [] [ text "Right click the 'Share' button at the top right of the screen. Then press 'Copy link'" ]
          , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
          ]
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

viewProfile : Model -> Html Msg
viewProfile model =
  div []
    [ div [ class "profile-head" ]
      [ case Dict.get "dp" model.profile of
          Just dpUrl -> img [ src dpUrl, class "dp" ] []
          Nothing -> img [ src "../static/images/default_dp.jpg" ] []
      , div [ class "h1 profile-head-text" ]
        [ text <| case Dict.get "name" model.profile of
                    Just name -> name
                    Nothing -> "No Name Mcgee"
        ]
      ]
    , div [ class "profile-body" ]
      [ div [ class "profile-row odd-row" ]
        [ text "Email: ", text <| case Dict.get "email" model.profile of
                    Just email -> email
                    Nothing -> "No email specified"
        ]
      , div [ class "profile-row even-row" ]
        [
          button [ onClick Refresh, class "refresh button is-medium" ] [ text "Refresh" ]
        ]
      , div [ class "profile-row odd-row" ] [ text "Placeholder" ]
      , div [ class "profile-row even-row" ] [ text "Placeholder" ]
      , div [ class "profile-row odd-row" ] [ text "Placeholder" ]
      , div [ class "profile-row even-row" ] [ text "Placeholder" ]
    ]
    , div [] [ text <| model.status ]
    , div [] [ text <| timeFormat model.time ]
    ]

{--
#########################################################
  HELPER FUNCTIONS FOR TABS
#########################################################
--}
viewEventCard : Event -> Html Msg
viewEventCard event =
  let
    summary = case Dict.get "summary" event of
            Just summary -> summary
            Nothing -> "Event"
    startTime = case Dict.get "start" event of
            Just start -> start
            Nothing -> "Unknown Start Time"
    endTime = case Dict.get "end" event of
            Just end -> end
            Nothing -> "Unknown End Time"
  in
    div [class "event-info-card"]
      [ article [class "media"]
        [ div [class "media-left"]
          [p [class "event-summary-text"]
            [text summary]
          ]
        , div [class "media-right"]
          [p [class "event-time-text"]
            [text (startTime ++ "-" ++ endTime)]
          ]
        ]
      ]

{--
TODO: Abstract this so it isnt so long
--}
viewCalendarCards : Calendar -> Html Msg
viewCalendarCards calendar =
  let
    mondayEvents = case Dict.get "monday" calendar of
            Just events -> events
            Nothing -> []

    tuesdayEvents = case Dict.get "tuesday" calendar of
            Just events -> events
            Nothing -> []

    wednesdayEvents = case Dict.get "wednesday" calendar of
            Just events -> events
            Nothing -> []

    thursdayEvents = case Dict.get "thursday" calendar of
            Just events -> events
            Nothing -> []

    fridayEvents = case Dict.get "friday" calendar of
            Just events -> events
            Nothing -> []

    saturdayEvents = case Dict.get "saturday" calendar of
            Just events -> events
            Nothing -> []
    sundayEvents = case Dict.get "sunday" calendar of
            Just events -> events
            Nothing -> []
  in
    div []
      [ p [class "title title-padding"] [text "Monday"]
      , div [] (List.map viewEventCard mondayEvents)
      , p [class "title title-padding"] [text "Tuesday"]
      , div [] (List.map viewEventCard tuesdayEvents)
      , p [class "title title-padding"] [text "Wednesday"]
      , div [] (List.map viewEventCard wednesdayEvents)
      , p [class "title title-padding"] [text "Thursday"]
      , div [] (List.map viewEventCard thursdayEvents)
      , p [class "title title-padding"] [text "Friday"]
      , div [] (List.map viewEventCard fridayEvents)
      , p [class "title title-padding"] [text "Saturday"]
      , div [] (List.map viewEventCard saturdayEvents)
      , p [class "title title-padding"] [text "Sunday"]
      , div [] (List.map viewEventCard sundayEvents)
      ]
viewFriendInfo : FriendInfo -> Html Msg
viewFriendInfo friendInfo =
  let
    background = case Dict.get "status" friendInfo of
            Just status -> (status ++ "-bg")
            Nothing -> ""
  in
    div [class ("friend-info-card " ++ background)]
      [ article [class "media"]
        [ figure [class "media-left"]
          [p []
            [ case Dict.get "dp" friendInfo of
              Just dpUrl -> img [ src dpUrl, class "dp" ] []
              Nothing -> img [ src "../static/images/default_dp.jpg", class "dp" ] []
            ]
          ]
        , div [class "media-content"]
            [div [class "content"]
              [ p [class "friend-info-name-text"]
                [
                 text <| case Dict.get "name" friendInfo of
                     Just name -> name
                     Nothing -> "No Name Mcgee"

                ]
                , hr [class "thin-hr"] []
              ]
            ]
        , div [class "media-right"]
            [ i [class "friend-status-text"]
              [ text <| case Dict.get "status" friendInfo of
                     Just status -> status
                     Nothing -> "Unknown"
              ]
          , br [] []
          , div [class "friend-status-info-text"]
            [ text <| case Dict.get "statusInfo" friendInfo of
                   Just statusInfo -> statusInfo
                   Nothing -> "Unknown"
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

viewFriendsBreaks : FriendsBreaks -> Html Msg
viewFriendsBreaks dict =
  let
    entry (name, breaks) = div [] [ text name, text <| toString breaks ]
  in
    div [] (List.map entry <| Dict.toList dict)

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


{--
#########################################################
  HTTP
#########################################################
--}

getMyCalendar : Cmd Msg
getMyCalendar =
  let
    endpoint = "/weeks_events"

    decoder : Decode.Decoder Calendar
    decoder = Decode.at ["data"] <| Decode.dict (Decode.list (Decode.dict Decode.string))
  in
    Http.send GetMyCalendarResponse <| (Http.get endpoint decoder)

getProfile : Cmd Msg
getProfile =
  let
    endpoint = "/profile"

    decoder : Decode.Decoder Profile
    decoder = Decode.at ["data"] <| Decode.dict Decode.string
  in
    Http.send GetProfileResponse <| (Http.get endpoint decoder)

getFriendsInfo : Cmd Msg
getFriendsInfo =
  let
    endpoint = "/sample_friends_info"

    decoder : Decode.Decoder FriendsInfo
    decoder = Decode.at ["data"] <| Decode.list (Decode.dict Decode.string)
  in
    Http.send GetFriendsInfoResponse <| (Http.get endpoint decoder)

getFriendsBreaks : Cmd Msg
getFriendsBreaks =
  let
    endpoint = "/friends_breaks"

    decoder : Decode.Decoder FriendsBreaks
    decoder = Decode.at ["data"] <| Decode.dict (Decode.list Decode.float)
  in
    Http.send GetFriendBreaksResponse <| (Http.get endpoint decoder)

postCalendarURL : String -> Cmd Msg
postCalendarURL url =
  let
    endpoint = "/calendar"
    body = Http.jsonBody
        << Encode.object
        <| [ ("url", Encode.string url) ]

    decoder = Decode.at ["data"] <| Decode.string
  in
    Http.send PostCalendarURLResponse <| (Http.post endpoint body decoder)


