$.ajax({
    url: "/fb-app-id",
    type: "GET",
    dataType: "json",
    async: false,
    contentType: "application/json",
    success: function (data, textStatus, jqXHR) {
        if (textStatus == "success") {
            console.log("APP ID IS")
            console.log(data['data'])
            initFB(data['data'])
        }
    }
});
function initFB(appID) {
    window.fbAsyncInit = function () {
        // Initialises facebook api

        FB.init({appId: appID, cookie: true, xfbml: true, status: true, version: 'v2.8'});
        FB
            .AppEvents
            .logPageView();
    };

    (function (d, s, id) {
        var js,
            fjs = d.getElementsByTagName(s)[0];
        if (d.getElementById(id)) {
            return;
        }
        js = d.createElement(s);
        js.id = id;
        js.src = "//connect.facebook.net/en_US/sdk.js";
        fjs
            .parentNode
            .insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
}
