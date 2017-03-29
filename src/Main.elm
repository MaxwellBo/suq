import Dict exposing (Dict)
import Time exposing (Time)
import Date
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


main =
  Html.program
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }



-- MODEL

type Tab
  = Import
  | Friends
  | Profile

type alias Profile = Dict String String

type alias FriendsBreaks = Dict String (List Time)

{-
FriendInfo Example
name: "Charlie Groves"
profileURL: "graph.facebook.com/1827612378/images"
status: "Free"
statusInfo: "until 3pm"
-}
type alias FriendInfo = 
  { name: String
  , profileURL: String
  , status: String
  , statusInfo: String
  }
type alias Model =
  { activeTab : Tab
  , status : String
  , time : Time
  , calendarURLField : String
  , profile : Profile
  , friendsBreaks : FriendsBreaks
  }

init : (Model, Cmd Msg)
init =
  { activeTab = Import
  , status = "No status"
  , time = 0
  , calendarURLField = ""
  , profile = Dict.empty
  , friendsBreaks = Dict.empty
  } !
    [ getProfile
    , Task.perform Tick Time.now
    ]


mockFriendsBreaks : FriendsBreaks
mockFriendsBreaks = Dict.fromList [ ("Hugo", [100.0]), ("Charlie", [200.0])]


-- UPDATE

type Msg
  = ChangeTab Tab
  | Refresh
  | Tick Time
  | UpdateCalendarURLField String
  | GetProfileResponse (Result Http.Error Profile)
  | GetFriendBreaksResponse (Result Http.Error FriendsBreaks)
  | PostCalendarURL
  | PostCalendarURLResponse (Result Http.Error ())



update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    ChangeTab tab ->
      { model | activeTab = tab } ! []

    Refresh ->
      model ! [ getProfile, getFriendsBreaks ]

    Tick time ->
      { model | time = time } ! []

    UpdateCalendarURLField url ->
      { model | calendarURLField  = url } ! []

    GetProfileResponse (Ok data) ->
      { model | profile = data } ! []

    GetProfileResponse (Err err) ->
      { model | status = toString err } ! []

    GetFriendBreaksResponse (Ok data) ->
      { model | friendsBreaks = data } ! []

    GetFriendBreaksResponse (Err err) ->
      { model | status = toString err } ! []

    PostCalendarURL ->
      model ! [ postCalendarURL <| model.calendarURLField ]

    PostCalendarURLResponse _ ->
      model ! []

-- VIEW

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
    , div [class "tabs is-centered is-large is-hidden-touch"]
        [ ul []
            [li [ onClick <| ChangeTab Import, class <| isActiveTab model Import] [a [] [text "My Calendar"]]
            ,li [ onClick <| ChangeTab Friends, class <| isActiveTab model Friends] [a [] [text "Friends"]]
            ,li [ onClick <| ChangeTab Profile, class <| isActiveTab model Profile] [a [] [text "Profile"]]
            ]
        ]
    , section [ class "section"]
        [ div [ class "container content"]
            [case model.activeTab of
              Import -> viewImport model
              Profile -> viewProfile model
              Friends -> viewFriends model
            ]
        ]

    , div [class "glue-to-bottom is-hidden-desktop"]
        [div [class "is-mobile is-large columns"]
          [
            div [class "mobile-tab column", onClick <| ChangeTab Import, class <| isActiveTabMobile model Import] [a [] [i [ class "fa fa-calendar" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab Friends, class <| isActiveTabMobile model Friends] [a [] [i [ class "fa fa-users" ] []]]
            ,div [class "mobile-tab column", onClick <| ChangeTab Profile, class <| isActiveTabMobile model Profile] [a [] [i [ class "fa fa-user-secret" ] []]]
          
          ]
        ]
    ]

viewImport : Model -> Html Msg
viewImport model =
  div []
    [ text "Steps to import your calendar"
    , ol []
      [ li [] [ text "Log in to UQ Timetable Planner and navigate to the calendar you want" ]
      , li [] [ text "Right click the 'ICAL' button in the top right hand corner of the screen, and select 'Copy link address'" ]
      , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
      ]
    , input [ type_ "text", placeholder "Name", onInput UpdateCalendarURLField, value model.calendarURLField ] []
    , button [ onClick PostCalendarURL ] [ text "Submit" ]
    ]

viewProfile : Model -> Html Msg
viewProfile model =
  div []
    [ button [ onClick Refresh ] [ text "Refresh" ]
    , br [] []
    , div [] [ text <| model.status ]
    , div [] [ text <| timeFormat model.time ]
    , case Dict.get "dp" model.profile of
        Just dpUrl -> img [ src dpUrl ] []
        Nothing -> img [ src "../static/images/default_dp.jpg" ] []
    , div [] [ text <| toString model.profile ]
    ]

viewFriends : Model -> Html Msg
viewFriends model =
    viewFriendsBreaks mockFriendsBreaks

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

-- SUBSCRIPTIONS

subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick



-- HTTP

getProfile : Cmd Msg
getProfile =
  let
    endpoint = "/profile"

    decoder : Decode.Decoder Profile
    decoder = Decode.at ["data"] <| Decode.dict Decode.string
  in
    Http.send GetProfileResponse <| (Http.get endpoint decoder)

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
    decoder = Decode.succeed ()
  in
    Http.send PostCalendarURLResponse <| (Http.post endpoint body decoder)


