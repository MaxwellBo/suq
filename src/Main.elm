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
import Maybe

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
            ,li [ onClick <| ChangeTab ProfileTab, class <| isActiveTab model ProfileTab] [a [] [text "Profile"]]
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

    , div [class "glue-to-bottom is-hidden-tablet"]
        [div [class "is-mobile is-large columns"]
          [
            --Each tab is a "column" on mobile, to add a new tab, add a new div with mobile-tab and column class
            div [class "mobile-tab column", onClick <| ChangeTab MyCalendar, class <| isActiveTabMobile model MyCalendar] [a [] [i [ class "fa fa-calendar" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab Friends, class <| isActiveTabMobile model Friends] [a [] [i [ class "fa fa-users" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab WhosFree, class <| isActiveTabMobile model WhosFree] [a [] [i [ class "fa fa-question" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab PlaceholderTab, class <| isActiveTabMobile model PlaceholderTab] [a [] [i [ class "fa fa-bell" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab ProfileTab, class <| isActiveTabMobile model ProfileTab] [a [] [i [ class "fa fa-user-secret" ] []]]
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


{--
#########################################################
  HTTP
#########################################################
--}

getMyCalendar : Cmd Msg
getMyCalendar =
  let
    endpoint = "/weeks-events"

    eventDecoder : Decoder Event
    eventDecoder = Decode.map4 Event
      (Decode.field "summary" Decode.string)
      (Decode.field "location" Decode.string)
      (Decode.field "start" Decode.string)
      (Decode.field "summary" Decode.string)

    decoder : Decoder Calendar
    decoder = Decode.at ["data"] <|
      Decode.map7 Calendar 
        (Decode.field "monday" (Decode.list eventDecoder))
        (Decode.field "tuesday" (Decode.list eventDecoder))
        (Decode.field "wednesday" (Decode.list eventDecoder))
        (Decode.field "thursday" (Decode.list eventDecoder))
        (Decode.field "friday" (Decode.list eventDecoder))
        (Decode.field "saturday" (Decode.list eventDecoder))
        (Decode.field "sunday" (Decode.list eventDecoder))
  in
    Http.send GetMyCalendarResponse <| (Http.get endpoint decoder)

getProfile : Cmd Msg
getProfile =
  let
    endpoint = "/profile"

    decoder : Decoder Profile
    decoder = Decode.at ["data"] <|
      Decode.map3 Profile
        (Decode.field "dp" Decode.string)
        (Decode.field "name" Decode.string)
        (Decode.field "email" Decode.string)
  in
    Http.send GetProfileResponse <| (Http.get endpoint decoder)

getFriendsInfo : Cmd Msg
getFriendsInfo =
  let
    endpoint = "/all-users-info"

    friendInfoDecoder : Decoder FriendInfo
    friendInfoDecoder = Decode.map4 FriendInfo
        (Decode.field "dp" Decode.string)
        (Decode.field "name" Decode.string)
        (Decode.field "status" Decode.string)
        (Decode.field "statusInfo" Decode.string)

    decoder : Decode.Decoder FriendsInfo
    decoder = Decode.at ["data"] <| 
      Decode.list friendInfoDecoder
  in
    Http.send GetFriendsInfoResponse <| (Http.get endpoint decoder)

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


