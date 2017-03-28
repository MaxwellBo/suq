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

type alias SampleData = List String

type alias FriendsBreaks = Dict String (List Time)

type alias Model =
  { status : String
  , time : Time
  , sampleData : SampleData
  , friendsBreaks : FriendsBreaks
  }

init : (Model, Cmd Msg)
init =
  { status = "No status"
  , time = 0
  , sampleData = [""]
  , friendsBreaks = Dict.empty
  } !
    [ getSampleData
    , getFriendsBreaks
    , Task.perform Tick Time.now
    ]


mockFriendsBreaks : FriendsBreaks
mockFriendsBreaks = Dict.fromList [ ("Hugo", [100.0]), ("Charlie", [200.0])]


-- UPDATE

type Msg
  = Refresh
  | Tick Time
  | RetrievedSampleData (Result Http.Error SampleData)
  | RetrievedFriendsBreaks (Result Http.Error FriendsBreaks)


update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    Refresh ->
      model ! [ getSampleData, getFriendsBreaks ]

    Tick time ->
      { model | time = time } ! []

    RetrievedSampleData (Ok data) ->
      { model | sampleData = data } ! []

    RetrievedSampleData (Err _) ->
      { model | status = "Something broke with the sampleData" } ! []

    RetrievedFriendsBreaks (Ok data) ->
      { model | friendsBreaks = data } ! []

    RetrievedFriendsBreaks (Err _) ->
      { model | status = "Something broke with the friendsBreaks" } ! []

-- VIEW

view : Model -> Html Msg
view model =
  div []
    [ button [ onClick Refresh ] [ text "Refresh" ]
    , br [] []
    , div [] [ text <| model.status ]
    , div [] [ text <| timeFormat model.time ]
    , div [] [ text <| toString model.sampleData ]
    , viewFriendsBreaks mockFriendsBreaks
    ]

timeFormat : Time -> String
timeFormat time =
  let
    pad c =  String.padLeft 2 c << toString
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

getSampleData : Cmd Msg
getSampleData =
  let
    url = "http://syncuq-stage.herokuapp.com/ok"

    decoder : Decode.Decoder SampleData
    decoder = Decode.at ["data"] <| Decode.list Decode.string
  in
    Http.send RetrievedSampleData <| (Http.get url decoder)

getFriendsBreaks : Cmd Msg
getFriendsBreaks =
  let
    url = "http://syncuq-stage.herokuapp.com/friends_breaks"

    decoder : Decode.Decoder FriendsBreaks
    decoder = Decode.at ["ok"] <| Decode.dict (Decode.list Decode.float)
  in
    Http.send RetrievedFriendsBreaks <| (Http.get url decoder)

