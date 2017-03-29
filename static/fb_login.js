function FBlogin() {
    FB.login(function (response) {
        var obj = {
            userID: response.authResponse.userID,
            accessToken: response.authResponse.accessToken,
        };
        var data_json = JSON.stringify(obj);
        $.ajax({
            url: "/API_FB_login",
            type: "POST",
            data: data_json,
            dataType: "json",
            async: false,
            contentType: "application/json",
            success: function (data, textStatus, jqXHR) {
                if (data == "Logged In! Please redirect me to app!") {
                    fetchUserDetail()
                }   
            }
        });
    }, {
        scope: 'public_profile, email, user_friends',
        return_scopes: true
    });
}

function fetchUserDetail() {
    FB.api('/me', {fields: 'name, email, id' }, function (response) {
        console.log(response);
        var obj = {
            userID: response.id,
            userName: response.name,
            email: response.email
        };
        var data_json = JSON.stringify(obj);
        $.ajax({
            url: "/API_FB_login",
            type: "POST",
            data: data_json,
            dataType: "json",
            async: false,
            contentType: "application/json",
            success: function (data, textStatus, jqXHR) {
                if (data == "Logged In! Please redirect me to app!") {
                    location.replace("/app");
                }
            }
        });
    });
}

function checkFBlogin() {
    FB.getLoginStatus(function (response) {
        // If user is already connected to fb, update their info and log them into the server
        if (response.status === 'connected') {
            FBlogin(); //NOTE: TODO: change this to 'fetchUserDetail()' when pushing to prod
        } 
        // Otherwise, make them login. then, when they are logged in, update their info (line 17)
        else if (response.status === 'not_authorized') {
            FBlogin();
            console.log("Please log into this app.")
        } else {
            FBlogin();
            console.log("Please log into this Facebook.")
        }
    });
}