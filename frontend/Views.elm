module Views exposing (..)

import Time exposing (Time)
import Date
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Models exposing (..)
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
            (List.map viewAddFriendCard model.addFriendInfo)
        , div [] [text <| model.friendRequestResponse]
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
        [ p [ class "title title-padding " ] [ text "What's Due?" ]
        , div []
            (List.map viewPiece model.whatsDue)
        ]

-- HACK FIXME
-- TODO: Make this different from events so we don't confuse the user
-- Everything looks wonky and stupid too
viewPiece : Piece -> Html Msg
viewPiece piece =
    div [ class "piece-card" ]
        [ article [ class "media justify-between" ]
            [ div [ class "media-left" ]
                [ p [ class "event-summary-text" ]
                    [ text piece.subject ]
                , p [ class "event-location-text" ]
                    [ text piece.description ]
                ]
            , div [ class "media-right" ]
                [ p [ class "event-time-text" ]
                    [ text (piece.date ++ " - " ++ piece.weighting) ]
                ]
            ]
        ]

viewAddFriendCard : AddFriendInfoPiece -> Html Msg
viewAddFriendCard addFriendInfo =
    let
        actionButton = getActionButton addFriendInfo.status addFriendInfo.fbId
    in
        div [ class "friend-info-card add-friend-card add-friend-bg" ]
            [ article [ class "media align-center" ]
                [ div [ class "media-left align-center" ]
                    [ img [ src addFriendInfo.dp, class "dp" ] [] ]
                , div [ class "media-content" ]
                    [ div [ class "content" ]
                        [ p [ class "friend-info-name-text" ]
                            [ text <| addFriendInfo.name
                            ]
                        ]
                    ]
                , div [ class "media-right" ]
                    [ actionButton
                    ]
                ]
            ]

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
            -- [ text "Email: ", text model.profile.email ] TODO: Uncomment this line after the presentation
                [ text "Email: ", text "CENSORED FOR PRESENTATION" ]
            , div [ class "profile-row even-row" ] [ text <| "Local time: " ++ timeFormat model.time ]
            , div [ class "profile-row odd-row" ] [ text <| "Incognito:  ", checkbox "" model.settings.incognito UpdateIncognitoCheckbox ]
            , button [ onClick Refresh, class "refresh button is-medium" ] [ text "Refresh" ]
            , button [ onClick DeleteCalendar, class "button is-medium" ] [ text "Drop Calendar" ]
            , a [ class "button is-medium" ] [ text "Logout" ]
            ]
        ]



{--
#########################################################
  HELPER FUNCTIONS FOR TABS
#########################################################
--}

getActionButton : String -> String -> Html Msg
getActionButton status fbid =
    case status of
        "Friends" -> div [] 
                        [ p [class "info-box-friends floated"] [ span [class "tag is-success is-medium"] [text "Friends" ]]
                        , button [ onClick (PostRemoveFriendRequest <| fbid), class "button is-danger floated" ] [ span [class "icon"] [i [ class "fa fa-times"] [] ] ]
                        ]
        "Pending" -> div [] 
                        [ p [class "info-box-pending floated"] [span [class "tag is-info is-medium"] [text "pending" ]]
                        , button [ onClick (PostRemoveFriendRequest <| fbid), class "button is-danger floated" ] [ span [class "icon"] [i [ class "fa fa-times"] [] ] ]
                        ]        
        "Accept" -> button [ onClick (PostFriendRequest <| fbid), class "button is-info" ] [ text "Accept Request" ]
        "Not Added" -> button [ onClick (PostFriendRequest  <| fbid), class "button is-info" ] [ text "Add Friend" ]
        status -> div [] []


viewEventCard : Event -> Html Msg
viewEventCard event =
    div [ class "event-info-card" ]
        [ article [ class "media justify-between" ]
            [ div [ class "media-left" ]
                [ p [ class "event-summary-text" ]
                    [ text event.summary ]
                , p [ class "event-location-text" ]
                    [ text event.location ]
                ]
            , div [ class "media-right" ]
                [ p [ class "event-time-text" ]
                    [ text (event.start ++ " - " ++ event.end) ]
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
