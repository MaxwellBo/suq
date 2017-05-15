__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
import sys
import logging
from typing import *
from datetime import datetime, timezone, timedelta

# Libraries
from flask import Flask, flash, jsonify, request, render_template, session, redirect, url_for, send_from_directory, json # type: ignore
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user # type: ignore
from sqlalchemy import create_engine

# Imports
from backend.responses import *
from backend.models import *
from flask_migrate import Migrate

###############
### GLOBALS ###
###############

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:////tmp/flask_app.db')
app.config["SECRET_KEY"] = "ITSASECRET"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in"
login_manager.login_message_category = "info"
engine = create_engine('sqlite://', echo=False) # type: ignore
### FIXME: Is this actually used anywhere ^

logging.basicConfig(level=logging.DEBUG)

#############
### SETUP ###
#############

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue

db.init_app(app)
migrate = Migrate(app,db)

with app.app_context():
    logging.info(".Creating the database")
    db.create_all()
    db.session.commit()

"""
Transforms custom APIExceptions into API error responses.

See http://flask.pocoo.org/docs/0.12/patterns/apierrors/ for more details.
"""
@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error: Any) -> Response:
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

"""
Add headers to both force latest IE rendering engine or Chrome Frame,
and also to cache the rendered page for 10 minutes.
"""
@app.after_request
def add_header(response: Response) -> Response:
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


########################
### HELPER FUNCTIONS ###
########################

"""
Returns whether user is already registered
"""
# FIXME: Do we need this?
def query_user(username: str) -> bool:
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    return False

"""
Returns whether a facebook user has logged in before.
"""
def query_fb_user(fb_user_id: str) -> bool:
    return bool(User.query.filter_by(fb_user_id=fb_user_id).first())

"""
TODO
"""
def redirect_url() -> Response:
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')


"""
FIXME: Do we even need this?
"""
@login_manager.user_loader
def load_user(id: str):
    if id is None:
        return None
    try:
        user = User.query.get(int(id))
    except:
        return None
    return user


########################
### STATIC ENDPOINTS ###
########################

@app.route('/', methods=['GET'])
def index() -> Response:
    return app.send_static_file("index.html")

@app.route('/app', methods=['GET'])
@login_required
def frontend() -> Response:
    return app.send_static_file("app.html")

@app.route('/whatsdue', methods=['GET','POST'])
def whatsdue() -> Response:
    if request.method == 'GET':
        return render_template("whatsdue.html")
    else:
        subjects = [ request.form[f"subject{i}"] for i in range(1, 6) ]
        data = get_whats_due(set(subjects))
        return jsonify(data)

@app.route('/login', methods=['GET'])
def login() -> Response:
    if current_user.is_authenticated:
        logging.info("User at login page is logged in")
    else:
        logging.info("User at login page is not logged in")
    return render_template("login.html")


#################
### REDIRECTS ###
#################

@app.route('/check-login')
@login_required
def check_login() -> Response:
    return redirect(redirect_url())

"""
Logs a user out.
"""
@app.route('/logout')
def logout() -> Response:
    logout_user()
    return redirect(url_for('login'))

######################
### REST ENDPOINTS ###
######################

# XXX: Feel free to change the name if it's too similiar to the static endpoint
@app.route('/whats-due', methods=['GET'])
@login_required
def whats_due() -> Response:
    return ok(current_user.whats_due)

@app.route('/fb-friends', methods=['POST','GET'])
@login_required
def fb_friends() -> Response:
    if request.method == 'POST':
        friends_list_dict = request.json['friends']
        friends_list = []
        for friend in friends_list_dict:
            friends_list.append(friend['id'])
        logging.info("Updating user friends")
        friends_list_string = ",".join(friends_list)
        current_user.fb_friends = friends_list_string.encode()
        db.session.flush()
        db.session.commit()
        logging.info("Update Succeeded")
        print(current_user.fb_friends)
        return ok("Friends added")
    else:
        user_friends_fbid = current_user.fb_friends.decode().split(',')
        friends_info = []
        for fb_id in user_friends_fbid:
            print(f"User {current_user.username}: Attempting to find user id {fb_id} in our db")
            friend_user = User.query.filter_by(fb_user_id=fb_id).first()
            if (friend_user != None):
                friends_info = {
                    'name':friend_user.username, 
                    'fbId': fb_id,
                    'picture': friend_user.profile_picture,
                    'requestStatus': get_request_status(current_user.fb_user_id,fb_id) #TODO implement this function
                }
                print(f"Found current user: {current_user.username}'s facebook friend: {friend_user.username}")
        print(f"Found add friend info: {friends_info}")
        return ok([friends_info])
        """
        Grabs user info from fb_id's in user_friends
        Grabs SUQ friend status
        eg.
        [
            {
                name: "John Doe"
                fb_id: 32525234523432
                picture: "fb_picture_url"
                request-status: "Pending" (user has sent john a friend request)
            },{
                name: "John Doe"
                fb_id: 32525234523432
                picture: "fb_picture_url"
                request-status: "accept" (john has sent user a friend request)
            },{
                name: "John Doe"
                fb_id: 32525234523432
                picture: "fb_picture_url"
                request-status: "Not Added" (no friend requests so far)
            },{
                name: "John Doe"
                fb_id: 32525234523432
                picture: "fb_picture_url"
                friend-status: "Friends" (Confirmed friends)
            },
        ]
        """

"""
Accepts 1 json field 'friendId'
Checks if friend is in our db. If not, error
Then checks if friend request already exists. If so, error.
Then adds new friend request.
"""
@app.route('/add-friend', methods=['POST'])
@login_required
def add_friend() -> Response:
    friend_fb_id = request.json['friendId']
    friend_user = User.query.filter_by(friend_fb_id=friend_fb_id).first()
    if friend_user is None:
        return ok("Error: friend id not registered!")
    else:
        existing_request = HasFriend.query.filter_by(fb_id=current_user.fb_user_id, friend_fb_id=friend_fb_id).first()
        if (existing_request != None):
            return ok("Friend already added!")
        else:
            new_friend_connection = HasFriend(fb_id=current_user.fb_user_id, friend_fb_id=friend_fb_id)
            db.session.add(new_friend_connection)
            db.session.commit()
            return created("Friend request succeeded!")

@app.route('/breaks')
@login_required
def breaks() -> Response:
    ids = request.json["friendIds"]

    # TODO:
    # 1. Verify that every id in `ids` is a friend of the current user (for security)
    # 2. Get the table entry associated with each id (use a list comprehension)
    # 3. Verify that the `current_user` is in that comprehended list
    # 4. pass that onto... 

    group_members: List[User] = [] # should be the comprehended list
    return ok(get_remaining_shared_breaks_this_week(group_members))
    

"""
GET:  Extracts this weeks subjects from the calendar for the logged in user
POST: Provides the server with a URL to the logged in user's calendar stored
        at UQ Timetable planner
"""
@app.route('/calendar', methods=['GET', 'POST', 'DELETE'])
@login_required
def calendar() -> Response:
    if request.method == 'GET':
        if (current_user.calendar_data is None):
            return ok("Calendar not yet added!")

        return ok(current_user.timetable)
    elif request.method == 'POST':
        cal_url = request.json['url']
        logging.info("Received calendar from {cal_url}")

        """
        Verifies that a URL is in fact a URL to a timetableplanner calendar
        """
        def is_url_valid(url: str) -> bool:
            must_contain = ['/share/', 'timetableplanner.app.uq.edu.au']
            return all(string in url for string in must_contain)

        if not is_url_valid(cal_url):
            raise InternalServerError(message="Invalid URL")

        try:
            current_user.add_calendar(cal_url)
        except:
            raise InternalServerError(message="Invalid Calendar")

        # FIXME: Do we need this db.session stuff?
        # Charlie: Yes, current_user is updating their cal, we need to commit that
        # Shouldn't it be in `.add_calendar` then? Or does it have to be in the
        # top level function due to race condition shenanigan stuff
        db.session.flush()
        db.session.commit()

        logging.info(f"Updated calendar {current_user.calendar_url}")

        return created()
    else:
        current_user.remove_calendar()
        return no_content()

"""
Retrieves basic profile information for the logged in user
"""
@app.route('/profile', methods=['GET'])
@login_required
def profile() -> Response:
    return ok({"name": current_user.username, 
                "dp": current_user.profile_picture, 
                "email": current_user.email,
                "calURL": current_user.calendar_url})


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings() -> Response:

    def make_settings_response(current_user: User) -> Response:
        return ok({"incognito": current_user.incognito})


    if request.method == 'GET':
        return make_settings_response(current_user)
    else:
        try:
            current_user.incognito = request.json['incognito']
            logging.info(f"Changed {current_user.username}'s incognito setting to {current_user.incognito}")
        except:
            pass
        
        return make_settings_response(current_user)


# TODO: https://github.com/MaxwellBo/suq_backend/issues/8
@app.route('/all-users-info', methods=['GET'])
@login_required
def all_users_info() -> Response:
    list_of_all_users = User.query.all()
    logging.info(list_of_all_users)
    return ok([user.availability(current_user) for user in list_of_all_users])


"""
Uses the JSON passed to us from the frontend to either 'log in' a user, 
or register them if they do not exist.
"""
@app.route('/fb-login', methods=['POST'])
def fb_login() -> Response:
    logging.info("Commenced Facebook login procedure")
    user_id = request.json['userID']
    existing_user = User.query.filter_by(fb_user_id=user_id).first()

    if existing_user is None:
        access_token = request.json['accessToken']
        logging.info("The login request was for a new user, creating new user")

        new_user = User(username=None, email=None, fb_user_id=user_id, fb_access_token=access_token)
        logging.info(f"User made, user_id = {user_id}, access_token = {access_token}")
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)
        logging.info("The user is now logged in")
    else:
        logging.info("The user already exists")

        try:
            username = request.json['userName']
            email = request.json['email']

            logging.info(f"Updating user with name {existing_user.username} to {username}")
            logging.info(f"Updating user with email {existing_user.email} to {email}")

            existing_user.username = username # in case they've changer their name on facebook since they registered
            existing_user.email = email # in case they've changed their email since they registered
        except KeyError as e:
            logging.error(f"The JSON was malformed, causing the following KeyError: {e}")

        try:
            access_token = request.json['accessToken']
            logging.info("Adding new accessToken")

            existing_user.fb_access_token = access_token #update their accessToken with the one supplied
        except KeyError as e:
            logging.error(f"The JSON was malformed, causing the following KeyError {e}")

        logging.info("Logging in user")
        login_user(existing_user, remember=True)
        logging.info("User logged in")

    db.session.flush()
    db.session.commit()
    # FIXME: Is this functional? Otherwise it should just be an `ok()`
    return ok("Logged user in")

if __name__ == '__main__':
    logging.info("Running app")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
