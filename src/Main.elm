import Dict exposing (Dict)
import Time exposing (Time)
import Date
import Task
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode


main =
  Html.program
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }



-- MODEL

type alias Profile = Dict String String

type alias FriendsBreaks = Dict String (List Time)

type alias Model =
  { status : String
  , time : Time
  , calendarURLField : String
  , profile : Profile
  , friendsBreaks : FriendsBreaks
  }

init : (Model, Cmd Msg)
init =
  { status = "No status"
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
  = Refresh
  | Tick Time
  | UpdateCalendarURLField String
  | GetProfileResponse (Result Http.Error Profile)
  | GetFriendBreaksResponse (Result Http.Error FriendsBreaks)
  | PostCalendarURL
  | PostCalendarURLResponse (Result Http.Error ())



update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
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
    [ div [class "tabs is-centered is-large"]
        [ ul []
            [li [] [a [] [text "My Calendar"]]
            ,li [] [a [] [text "Friends"]]
            ,li [] [a [] [text "Who's Free?"]]
            ,li [] [a [] [text "Groups"]]
            ,li [class "is-active"] [a [] [text "Profile"]]
            ]
        ]
    , button [ onClick Refresh ] [ text "Refresh" ]
    , br [] []
    , div [] [ text <| model.status ]
    , div [] [ text <| timeFormat model.time ]
    , case Dict.get "dp" model.profile of
        Just dpUrl -> img [ src dpUrl ] []
        Nothing -> img [ src "../static/images/default_dp.jpg" ]
    , div [] [ text <| toString model.profile ]
    , input [ type_ "text", placeholder "Name", onInput UpdateCalendarURLField
            , value model.calendarURLField ] []
    , button [ onClick PostCalendarURL ] [ text "Update calendar URL" ]
    , viewFriendsBreaks mockFriendsBreaks
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



-- SUBSCRIPTIONS

subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every Time.minute Tick



-- HTTP

getProfile : Cmd Msg
getProfile =
  let
    url = "/profile"

    decoder : Decode.Decoder Profile
    decoder = Decode.at ["data"] <| Decode.dict Decode.string
  in
    Http.send GetProfileResponse <| (Http.get url decoder)

getFriendsBreaks : Cmd Msg
getFriendsBreaks =
  let
    url = "/friends_breaks"

    decoder : Decode.Decoder FriendsBreaks
    decoder = Decode.at ["data"] <| Decode.dict (Decode.list Decode.float)
  in
    Http.send GetFriendBreaksResponse <| (Http.get url decoder)

postCalendarURL : String -> Cmd Msg
postCalendarURL url =
  let
    url = "/calendar"
    body =  Http.emptyBody -- TODO: Do something with the URL here
    decoder = Decode.succeed ()
  in
    Http.send PostCalendarURLResponse <| (Http.post url body decoder)


