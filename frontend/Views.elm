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
                    [ a [ class "nav-item", href "/app" ]
                        [ img [ src "static/images/sync_uq_logo.png", alt "SyncUQ" ] []
                        ]
                    ]
                ]
            ]
        , div [ class "tabs is-centered is-large is-hidden-mobile" ]
            [ ul []
                [ li [ onClick <| ChangeTab TimetableTab, class <| isActiveTab model TimetableTab ] [ a [] [ text "Timetable" ] ]
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
                        TimetableTab ->
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
                [ div [ class "mobile-tab column", onClick <| ChangeTab TimetableTab, class <| isActiveTabMobile model TimetableTab ] [ a [] [ i [ class "fa fa-calendar" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab FriendsTab, class <| isActiveTabMobile model FriendsTab ] [ a [] [ i [ class "fa fa-users" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab WhosFreeTab, class <| isActiveTabMobile model WhosFreeTab ] [ a [] [ i [ class "fa fa-question" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab WhatsDueTab, class <| isActiveTabMobile model WhatsDueTab ] [ a [] [ i [ class "fa fa-bell" ] [] ] ]
                , div [ class "mobile-tab column", onClick <| ChangeTab ProfileTab, class <| isActiveTabMobile model ProfileTab ] [ a [] [ i [ class "fa fa-user-secret" ] [] ] ]
                ]
            ]
        ]


viewMyCalendar : Model -> Html Msg
viewMyCalendar model =
    if model.hasUploadedCalendar then
        case model.myCalendar of
            Just myCalendar ->
                viewCalendarCards myCalendar

            Nothing ->
                viewLoading
    else
        viewUploadCalendar model


viewUploadCalendar : Model -> Html Msg
viewUploadCalendar model =
    div []
        [ p [ class "title title-padding" ] [ text "Import your Calendar" ]
        , div [ class "is-hidden-tablet" ]
            [ img [ class "mobile-cal-img info-img", src "../static/images/mobile_copy_cal_1.jpg" ] []
            , img [ class "mobile-cal-img-two info-img", src "../static/images/mobile_copy_cal_2.jpg" ] []
            , ol []
                [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
                , li [] [ text "Open the side menu and long press the 'Share' button. Then press 'Copy link'" ]
                , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
                ]
            ]
        , div [ class "is-hidden-mobile" ]
            [ div [ class "crop-height" ] [ img [ class "desktop-cal-img scale info-img", src "../static/images/desktop_copy_cal.png" ] [] ]
            , ol []
                [ li [] [ text "Log in to UQ Timetable Planner and navigate to the saved calendar you want" ]
                , li [] [ text "Right click the 'Share' button at the top right of the screen. Then press 'Copy link'" ]
                , li [] [ text "Paste the link into the field below, and click 'Submit'" ]
                ]
            ]
        , input [ class "input is-primary input-margin", type_ "text", placeholder "Paste timetable link here", onInput UpdateCalendarURLField, value model.calendarURLField ] []
        , button [ class "button is-primary", onClick PostCalendarURL ] [ text "Submit" ]
        , p [] [ text "Your link should look like this 'https://timetableplanner.app.uq.edu.au/share/NFpehMDzBlmaglRIg1z32w'" ]
        ]


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


viewFriends : Model -> Html Msg
viewFriends model =
    let
        friends =
            case model.addFriendInfo of
                Just addFriendInfo ->
                    addFriendInfo
                        |> List.filter (\x -> String.contains (String.toLower model.searchField) (String.toLower x.name))
                        |> List.map viewAddFriendCard

                Nothing ->
                    [ viewLoading ]
    in
        div []
            [ p [ class "title title-padding" ] [ text "Add Friends" ]
            , div [ class "friend-search" ]
                [ input [ class "input is-primary friend-search-input", Html.Attributes.placeholder "Search", value model.searchField, onInput UpdateSearchField ] []
                ]
            , div [] friends
            , div [] [ text <| model.friendRequestResponse ]
            ]


viewWhosFree : Model -> Html Msg
viewWhosFree model =
    div []
        [ p [ class "title title-padding" ] [ text "Who's Free?" ]
        , div []
            (case model.friendsInfo of
                Just friendsInfo ->
                    (List.map viewFriendInfo friendsInfo)

                Nothing ->
                    [ viewLoading ]
            )
        ]


viewWhatsDueTab : Model -> Html Msg
viewWhatsDueTab model =
    if model.hasUploadedCalendar then
        div []
            [ p [ class "title title-padding " ] [ text "What's Due?" ]
            , div []
                (case model.whatsDue of
                    Just whatsDue ->
                        whatsDue 
                            |> List.filter (\x -> not <| x.completed)
                            |> List.map viewPiece

                    Nothing ->
                        [ viewLoading ]
                )
            ]
    else
        viewUploadCalendar model



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
                [ p [ class "event-weight-text" ]
                    [ text (piece.weighting) ]
                , p [ class "event-time-text" ]
                    [ text (piece.date) ]
                ]
            ]
        ]


viewAddFriendCard : AddFriendInfoPiece -> Html Msg
viewAddFriendCard friend =
    div [ class "friend-info-card add-friend-card add-friend-bg" ]
        [ article [ class "media align-center" ]
            [ div [ class "media-left align-center" ]
                [ img [ src friend.dp, class "dp" ] [] ]
            , div [ class "media-content" ]
                [ div [ class "content" ]
                    [ p [ class "friend-info-name-text" ]
                        [ text <| friend.name
                        ]
                    ]
                ]
            , div [ class "media-right" ]
                [ viewActionButton friend
                ]
            ]
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
            [ div [ class "profile-row even-row" ]
                [ p [ class "profile-setting-desc" ] [ text <| "Local time: " ++ timeFormat model.time ]
                ]
            , div [ class "profile-row odd-row incognito-checkbox" ]
                [ p [ class "profile-setting-desc" ] [ text <| "Incognito:  " ]
                , checkbox "" model.settings.incognito UpdateIncognitoCheckbox
                ]
            , div [ class "profile-button-container" ]
                [ button [ onClick Refresh, class " profile-button refresh button is-info is-medium" ] [ text "Refresh" ]
                , button [ onClick DeleteCalendar, class "profile-button button is-danger is-medium" ] [ text "Drop Calendar" ]
                ]
            , div [ class "logout-wrapper" ] [ a [ href "/logout", class "profile-logout-button button is-primary is-medium" ] [ text "Logout" ] ]
            ]
        ]



{--
#########################################################
  HELPER FUNCTIONS FOR TABS
#########################################################
--}


checkbox : String -> Bool -> (Bool -> Msg) -> Html Msg
checkbox name state update =
    label
        [ class "switch" ]
        [ input [ type_ "checkbox", onCheck update, checked state ] []
        , text name
        , div [ class "slider" ] []
        ]


viewLoading : Html Msg
viewLoading =
    div [ id "loading" ]
        [ div [ class "sk-folding-cube" ]
            [ div [ class "sk-cube1 sk-cube" ] []
            , div [ class "sk-cube2 sk-cube" ] []
            , div [ class "sk-cube4 sk-cube" ] []
            , div [ class "sk-cube3 sk-cube" ] []
            ]
        ]


viewActionButton : AddFriendInfoPiece -> Html Msg
viewActionButton friend =
    case friend.status of
        -- FIXME: These shouldn't be strings, but members of a "RequestStatus" union type
        "Friends" ->
            div []
                [ p [ class "info-box-friends floated" ] [ span [ class "tag is-success is-medium" ] [ text "Friends" ] ]
                , button [ onClick <| PostRemoveFriendRequest friend, class "button is-danger floated" ] [ span [ class "icon" ] [ i [ class "fa fa-times" ] [] ] ]
                ]

        "Pending" ->
            div []
                [ p [ class "info-box-pending floated" ] [ span [ class "tag is-info is-medium" ] [ text "Pending" ] ]
                , button [ onClick <| PostRemoveFriendRequest friend, class "button is-danger floated" ] [ span [ class "icon" ] [ i [ class "fa fa-times" ] [] ] ]
                ]

        "Accept" ->
            button [ onClick <| PostFriendRequest friend, class "button is-info" ] [ text "Accept Request" ]

        "Not Added" ->
            button [ onClick <| PostFriendRequest friend, class "button is-info" ] [ text "Add Friend" ]

        _ ->
            div [] []


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
