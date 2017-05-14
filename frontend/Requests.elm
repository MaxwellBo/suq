module Requests exposing (..)

import Http
import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode
import Models exposing (..)


getMyCalendar : Cmd Msg
getMyCalendar =
    let
        endpoint =
            "/calendar"

        eventDecoder : Decoder Event
        eventDecoder =
            Decode.map4 Event
                (Decode.field "summary" Decode.string)
                (Decode.field "location" Decode.string)
                (Decode.field "start" Decode.string)
                (Decode.field "summary" Decode.string)

        decoder : Decoder Calendar
        decoder =
            Decode.at [ "data" ] <|
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
        Http.send PostCalendarURLResponse <| (Http.post endpoint body decoder)


getProfile : Cmd Msg
getProfile =
    let
        endpoint =
            "/profile"

        decoder : Decoder Profile
        decoder =
            Decode.at [ "data" ] <|
                Decode.map3 Profile
                    (Decode.field "dp" Decode.string)
                    (Decode.field "name" Decode.string)
                    (Decode.field "email" Decode.string)
    in
        Http.send GetProfileResponse <| (Http.get endpoint decoder)


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
        Http.send GetPostSettingsResponse <| (Http.get endpoint settingsDecoder)


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
        Http.send GetPostSettingsResponse <| (Http.post endpoint body settingsDecoder)


getFriendsInfo : Cmd Msg
getFriendsInfo =
    let
        endpoint =
            "/all-users-info"

        friendInfoDecoder : Decoder FriendInfo
        friendInfoDecoder =
            Decode.map4 FriendInfo
                (Decode.field "dp" Decode.string)
                (Decode.field "name" Decode.string)
                (Decode.field "status" Decode.string)
                (Decode.field "statusInfo" Decode.string)

        decoder : Decode.Decoder FriendsInfo
        decoder =
            Decode.at [ "data" ] <|
                Decode.list friendInfoDecoder
    in
        Http.send GetFriendsInfoResponse <| (Http.get endpoint decoder)

getWhatsDue : Cmd Msg
getWhatsDue =
    let
        endpoint =
            "/whats-due"

        pieceDecoder : Decoder Piece
        pieceDecoder =
            Decode.map4 Piece
                (Decode.field "subject" Decode.string)
                (Decode.field "description" Decode.string)
                (Decode.field "date" Decode.string)
                (Decode.field "weighting" Decode.string)

        decoder : Decode.Decoder WhatsDue
        decoder =
            Decode.at [ "data" ] <|
                Decode.list pieceDecoder
    in
        Http.send GetWhatsDueResponse <| (Http.get endpoint decoder)


-- http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Error
-- http://package.elm-lang.org/packages/elm-lang/http/1.0.0/Http#Response
getAddFriendInfo : Cmd Msg
getAddFriendInfo =
    let
        endpoint =
            "/fb-friends"

        pieceDecoder : Decoder AddFriendInfoPiece
        pieceDecoder =
            Decode.map4 AddFriendInfoPiece
                (Decode.field "name" Decode.string)
                (Decode.field "fbId" Decode.string)
                (Decode.field "picture" Decode.string)
                (Decode.field "requestStatus" Decode.string)

        decoder : Decode.Decoder AddFriendInfo
        decoder =
            Decode.at [ "data" ] <|
                Decode.list pieceDecoder
    in
        Http.send GetAddFriendInfoResponse <| (Http.get endpoint decoder)


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
            "CODE - { "
                ++ (toString <| code)
                ++ " }     MESSAGE - { "
                ++ mx
                ++ " | "
                ++ my
                ++ " }"
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
