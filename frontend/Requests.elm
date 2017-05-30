module Requests exposing (..)

import Http
import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode
import Models exposing (..)


{-| http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http
-}
put : String -> Http.Body -> Http.Request ()
put url body =
    Http.request
        { method = "PUT"
        , headers = []
        , url = url
        , body = body
        , expect = Http.expectStringResponse (\_ -> Ok ())
        , timeout = Nothing
        , withCredentials = False
        }


{-| http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http
-}
delete : String -> Http.Body -> Http.Request ()
delete url body =
    Http.request
        { method = "DELETE"
        , headers = []
        , url = url
        , body = body
        , expect = Http.expectStringResponse (\_ -> Ok ())
        , timeout = Nothing
        , withCredentials = False
        }

decodeNullableString : Decoder String
decodeNullableString =
    Decode.oneOf [ Decode.string, Decode.null "Unknown" ]

eventDecoder : Decoder Event
eventDecoder =
    Decode.map4 Event
        (Decode.field "summary" decodeNullableString)
        (Decode.field "location" decodeNullableString)
        (Decode.field "start" decodeNullableString)
        (Decode.field "end" decodeNullableString)


calendarDecoder : Decoder Calendar
calendarDecoder =
    Decode.at [ "data" ] <|
        Decode.map7 Calendar
            (Decode.field "monday" (Decode.list eventDecoder))
            (Decode.field "tuesday" (Decode.list eventDecoder))
            (Decode.field "wednesday" (Decode.list eventDecoder))
            (Decode.field "thursday" (Decode.list eventDecoder))
            (Decode.field "friday" (Decode.list eventDecoder))
            (Decode.field "saturday" (Decode.list eventDecoder))
            (Decode.field "sunday" (Decode.list eventDecoder))


getCalendar : Cmd Msg
getCalendar =
    let
        endpoint =
            "/calendar"
    in
        Http.send GetCalendarResponse <| Http.get endpoint calendarDecoder


postCalendarURL : String -> Cmd Msg
postCalendarURL url =
    let
        endpoint =
            "/calendar"

        body =
            Http.jsonBody
                << Encode.object
            <|
                [ ( "url", Encode.string url ) ]

        decoder =
            Decode.at [ "data" ] <| Decode.string
    in
        Http.send PostCalendarResponse <| Http.post endpoint body calendarDecoder


postFriendRequest : AddFriendInfoPiece -> Cmd Msg
postFriendRequest friend =
    let
        endpoint =
            "/add-friend"

        body =
            Http.jsonBody
                << Encode.object
            <|
                [ ( "friendId", Encode.string friend.fbId )
                , ( "remove", Encode.bool False )
                ]

        decoder =
            Decode.at [ "data" ] <| Decode.string
    in
        Http.send GetPostFriendRequestResponse <| Http.post endpoint body decoder


postRemoveFriendRequest : AddFriendInfoPiece -> Cmd Msg
postRemoveFriendRequest friend =
    let
        endpoint =
            "/add-friend"

        body =
            Http.jsonBody
                << Encode.object
            <|
                [ ( "friendId", Encode.string friend.fbId )
                , ( "remove", Encode.bool True )
                ]

        decoder =
            Decode.at [ "data" ] <| Decode.string
    in
        Http.send GetPostFriendRequestResponse <| Http.post endpoint body decoder


deleteCalendar : Cmd Msg
deleteCalendar =
    let
        endpoint =
            "/calendar"
    in
        Http.send DeleteCalendarResponse <| delete endpoint Http.emptyBody


getProfile : Cmd Msg
getProfile =
    let
        endpoint =
            "/profile"

        decoder : Decoder Profile
        decoder =
            Decode.at [ "data" ] <|
                Decode.map2 Profile
                    (Decode.field "dp" Decode.string)
                    (Decode.field "name" Decode.string)
    in
        Http.send GetProfileResponse <| Http.get endpoint decoder


settingsDecoder : Decoder Settings
settingsDecoder =
    Decode.at [ "data" ] <|
        Decode.map Settings
            (Decode.field "incognito" Decode.bool)


getSettings : Cmd Msg
getSettings =
    let
        endpoint =
            "/settings"
    in
        Http.send GetSettingsResponse <| Http.get endpoint settingsDecoder


postSettings : Settings -> Cmd Msg
postSettings settings =
    let
        endpoint =
            "/settings"

        body =
            Http.jsonBody
                << Encode.object
            <|
                [ ( "incognito", Encode.bool settings.incognito ) ]
    in
        Http.send PostSettingsResponse <| Http.post endpoint body settingsDecoder


getFriendsInfo : Cmd Msg
getFriendsInfo =
    let
        endpoint =
            "/statuses"

        breakDecoder : Decoder Break
        breakDecoder =
            Decode.map3 Break
                (Decode.field "start" Decode.string)
                (Decode.field "end" Decode.string)
                (Decode.field "day" Decode.string)

        friendInfoDecoder : Decoder FriendInfo
        friendInfoDecoder =
            Decode.map5 FriendInfo
                (Decode.field "dp" Decode.string)
                (Decode.field "name" Decode.string)
                (Decode.field "status" Decode.string)
                (Decode.field "statusInfo" Decode.string)
                (Decode.field "breaks" (Decode.list breakDecoder))

        decoder : Decode.Decoder FriendsInfo
        decoder =
            Decode.at [ "data" ] <|
                Decode.list friendInfoDecoder
    in
        Http.send GetFriendsInfoResponse <| Http.get endpoint decoder


getWhatsDue : Cmd Msg
getWhatsDue =
    let
        endpoint =
            "/whats-due"

        pieceDecoder : Decoder Piece
        pieceDecoder =
            Decode.map5 Piece
                (Decode.field "subject" Decode.string)
                (Decode.field "description" Decode.string)
                (Decode.field "date" Decode.string)
                (Decode.field "weighting" Decode.string)
                (Decode.field "completed" Decode.bool)

        decoder : Decode.Decoder WhatsDue
        decoder =
            Decode.at [ "data" ] <|
                Decode.list pieceDecoder
    in
        Http.send GetWhatsDueResponse <| Http.get endpoint decoder


getAddFriendInfo : Cmd Msg
getAddFriendInfo =
    let
        endpoint =
            "/fb-friends"

        pieceDecoder : Decoder AddFriendInfoPiece
        pieceDecoder =
            Decode.map4 AddFriendInfoPiece
                (Decode.field "name" decodeNullableString)
                (Decode.field "fbId" decodeNullableString)
                (Decode.field "dp" Decode.string)
                (Decode.field "requestStatus" Decode.string)

        decoder : Decode.Decoder AddFriendInfo
        decoder =
            Decode.at [ "data" ] <|
                Decode.list pieceDecoder
    in
        Http.send GetAddFriendInfoResponse <| Http.get endpoint decoder


{-| http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Error
http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Response
-}
handleHTTPError : Http.Error -> String
handleHTTPError response =
    let
        decodeError : Decoder APIError
        decodeError =
            Decode.at [ "error" ] <|
                Decode.map2 APIError
                    (Decode.field "code" Decode.int)
                    (Decode.field "message" Decode.string)

        formatError : Int -> String -> String -> String
        formatError code mx my =
            "uhhhhhHhhhhh the '"
                ++ "["
                ++ (toString <| code)
                ++ "]"
                ++ " "
                ++ mx
                ++ ","
                ++ " "
                ++ my
                ++ " machine broke"
    in
        case response of
            Http.BadUrl string ->
                string

            Http.Timeout ->
                "Timeout"

            Http.NetworkError ->
                "Network Error"

            Http.BadPayload error response ->
                error

            Http.BadStatus response ->
                case Decode.decodeString decodeError response.body of
                    Ok apiError ->
                        formatError response.status.code response.status.message apiError.message

                    Err parsingErrorMessage ->
                        formatError response.status.code response.status.message parsingErrorMessage
