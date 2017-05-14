module Views exposing (..)

import Time exposing (Time)
import Date
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Models exposing (..)

viewMyCalendar : Model -> Html Msg
viewMyCalendar model =
    if model.hasCalendar then
        viewCalendarCards model.myCalendar
    else
        let
            instructions =
                ol []
                    [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
                    , li [] [ text "Open the side menu and long press the 'Share' button. Then press 'Copy link'" ]
                    , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
                    ]
        in
            div []
                [ p [ class "title title-padding" ] [ text "Import your Calendar" ]
                , div [ class "is-hidden-tablet" ]
                    [ img [ class "mobile-cal-img", src "../static/images/mobile_copy_cal_1.jpg" ] []
                    , img [ class "mobile-cal-img-two", src "../static/images/mobile_copy_cal_2.jpg" ] []
                    , instructions
                    ]
                , div [ class "is-hidden-mobile" ]
                    [ div [ class "crop-height" ] [ img [ class "desktop-cal-img scale", src "../static/images/desktop_copy_cal.png" ] [] ]
                    , instructions
                    ]
                , div [] [ text <| model.status ]
                , input [ class "input is-primary input-margin", type_ "text", placeholder "Paste timetable link here", onInput UpdateCalendarURLField, value model.calendarURLField ] []
                , button [ class "button is-primary", onClick PostCalendarURL ] [ text "Submit" ]
                , p [] [ text "Your link should look like this 'https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w'" ]
                ]


viewFriends : Model -> Html Msg
viewFriends model =
    div []
        [ p [ class "title title-padding" ] [ text "Add Friends" ]
        , div []
            (List.map viewFriendPiece model.addFriendInfo)
        , div [] [text <| model.status]
        ]


viewWhosFree : Model -> Html Msg
viewWhosFree model =
    div []
        [ p [ class "title title-padding" ] [ text "Who's Free?" ]
        , div []
            (List.map viewFriendInfo model.friendsInfo)
        ]


viewWhatsDueTab : Model -> Html Msg
viewWhatsDueTab model =
    div []
        [ p [ class "title title-padding" ] [ text "What's Due?" ]
        , div []
            (List.map viewPiece model.whatsDue)
        ]

viewPiece : Piece -> Html Msg
viewPiece piece =
    div [] [ text <| toString piece ]

viewFriendPiece : AddFriendInfoPiece -> Html Msg
viewFriendPiece piece =
    div [] [ text <| toString piece ]

checkbox : String -> Bool -> (Bool -> Msg) -> Html Msg
checkbox name state update =
  label
    [ style [("padding", "20px")]
    ]
    [ input [ type_ "checkbox", onCheck update, checked state ] []
    , text name
    ]

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
            , div [ class "profile-row odd-row" ] [ text <| "Incognito:  ", checkbox "" model.settings.incognito UpdateIncognitoCheckbox ]
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
        summary =
            event.summary

        location =
            event.location

        startTime =
            event.start

        endTime =
            event.end
    in
        div [ class "event-info-card" ]
            [ article [ class "media justify-between" ]
                [ div [ class "media-left" ]
                    [ p [ class "event-summary-text" ]
                        [ text summary ]
                    , p [ class "event-location-text" ]
                        [ text location ]
                    ]
                , div [ class "media-right" ]
                    [ p [ class "event-time-text" ]
                        [ text (startTime ++ " - " ++ endTime) ]
                    ]
                ]
            ]



{--
TODO: Abstract this so it isnt so long
--}


viewCalendarCards : Calendar -> Html Msg
viewCalendarCards calendar =
    let
        pClass =
            "title title-padding event-card-day"
    in
        div []
            [ p [ class pClass ] [ text "Monday" ]
            , div [] (List.map viewEventCard calendar.monday)
            , p [ class pClass ] [ text "Tuesday" ]
            , div [] (List.map viewEventCard calendar.tuesday)
            , p [ class pClass ] [ text "Wednesday" ]
            , div [] (List.map viewEventCard calendar.wednesday)
            , p [ class pClass ] [ text "Thursday" ]
            , div [] (List.map viewEventCard calendar.thursday)
            , p [ class pClass ] [ text "Friday" ]
            , div [] (List.map viewEventCard calendar.friday)
            , p [ class pClass ] [ text "Saturday" ]
            , div [] (List.map viewEventCard calendar.saturday)
            , p [ class pClass ] [ text "Sunday" ]
            , div [] (List.map viewEventCard calendar.sunday)
            ]


viewFriendInfo : FriendInfo -> Html Msg
viewFriendInfo friendInfo =
    let
        background =
            friendInfo.status ++ "-bg"
    in
        div [ class ("friend-info-card " ++ background) ]
            [ article [ class "media align-center" ]
                [ div [ class "media-left align-center" ]
                    [ img [ src friendInfo.dp, class "dp" ] [] ]
                , div [ class "media-content" ]
                    [ div [ class "content" ]
                        [ p [ class "friend-info-name-text" ]
                            [ text <| friendInfo.name
                            ]
                        ]
                    ]
                , div [ class "media-right" ]
                    [ i [ class "friend-status-text" ]
                        [ text <| friendInfo.status
                        ]
                    , br [] []
                    , div [ class "friend-status-info-text" ]
                        [ text <| friendInfo.statusInfo
                        ]
                    ]
                ]
            ]


timeFormat : Time -> String
timeFormat time =
    let
        pad c =
            String.padLeft 2 c << toString

        hours =
            Date.hour << Date.fromTime <| time

        minutes =
            Date.minute << Date.fromTime <| time
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