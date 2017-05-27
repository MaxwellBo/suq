function onDeviceReady() {
    if (navigator.connection.type == Connection.NONE) {
        navigator.notification.alert('An internet connection is required to continue');
    } else {
        window.open("http://syncuq.com", "_system");
    }
}
document.addEventListener("deviceready", onDeviceReady, false);