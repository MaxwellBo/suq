window.fbAsyncInit = function() {
// Initialises facebook api    
FB.init({
    appId      : '1091049127696748',
    cookie     : true,
    xfbml      : true,
    version    : 'v2.8'
});
FB.AppEvents.logPageView();   
// Checks for login
FB.getLoginStatus(function(response) {
    statusChangeCallback(response);
    if (response.status === 'connected') {
    } else {
        FB.login();
    }
});
};

(function(d, s, id){
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) {return;}
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);


}(document, 'script', 'facebook-jssdk'));