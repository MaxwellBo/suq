__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
import sys
import logging
from typing import *
from datetime import datetime, timezone, timedelta

# Libraries
from flask import Flask, flash, jsonify, request, render_template, session, redirect, url_for, send_from_directory, json  # type: ignore
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user  # type: ignore

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

logging.basicConfig(level=logging.DEBUG)

#############
### SETUP ###
#############

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    logging.info("Creating the database")
    db.create_all()
    db.session.commit()

@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error: APIException) -> Response:
    """
    Transforms custom APIExceptions into API error responses.

    See http://flask.pocoo.org/docs/0.12/patterns/apierrors/ for more details.
    """
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response


@app.after_request
def add_header(response: Response) -> Response:
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@login_manager.user_loader
def load_user(id: str):
    """
    This callback is used to reload the user object from the user ID stored in the session. 
    It should take the unicode ID of a user, and return the corresponding user object.
    It should return None(not raise an exception) if the ID is not valid.
    """
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

def redirect_url() -> Response:
    """
    TODO
    """
    return request.args.get('next') or \
        request.referrer or \
        url_for('index')


@app.route('/check-login')
@login_required
def check_login() -> Response:
    """
    TODO
    """
    return redirect(redirect_url())


@app.route('/logout')
def logout() -> Response:
    """
    Logs a user out.
    """
    logout_user()
    return redirect(url_for('login'))

######################
### REST ENDPOINTS ###
######################

@app.route('/whats-due', methods=['GET'])
@login_required
def whats_due() -> Response:
    """
    Grabs the upcoming assessment infomation for the current user.
    """

    if current_user.calendar_data is None:
        raise NotFound(message="Calendar not yet added")

    return ok(current_user.whats_due)


@app.route('/fb-friends', methods=['POST', 'GET'])
@login_required
def fb_friends() -> Response:
    """
    POST: Updates the user's fb friend list.

    GET: Grabs the user's fb friend list from the db, finds out whether the user
    has added that friend in the app (and vice versa), returns this information.
    """
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
        return ok("Friends added")
    else:
        all_users = User.query.all()
        friends_info = []
        for user in all_users:
            if ((user.fb_user_id != None) and (user.fb_user_id != current_user.fb_user_id)):
                friend_info = {
                    'name': user.username,
                    'fbId': user.fb_user_id,
                    'dp': user.profile_picture,
                    # TODO implement this function
                    'requestStatus': get_request_status(current_user.fb_user_id, user.fb_user_id)
                }
                friends_info.append(friend_info)
                logging.info(f"Found current user: {current_user.username}'s facebook friend: {user.username}")
        logging.info(f"Found add friend info: {friends_info}")
        sort_weight = {
            "Friends": 1,
            "Accept": 2,
            "Pending": 3,
            "Not Added": 4,
        }
        sorted_list = sorted(
            friends_info, key=lambda x: sort_weight[x['requestStatus']])
        return ok(sorted_list)


@app.route('/add-friend', methods=['POST'])
@login_required
def add_friend() -> Response:
    """
    Accepts 1 json field 'friendId'
    Checks if friend is in our db. If not, error
    Then checks if friend request already exists. If so, error.
    Then adds new friend request.
    """
    friend_fb_id = request.json['friendId']
    logging.info(f"{current_user.fb_user_id} added user {friend_fb_id} ")
    friend_user = User.query.filter_by(fb_user_id=friend_fb_id).first()
    if friend_user is None:
        return ok("Error: friend id not registered!")
    else:
        existing_request = HasFriend.query.filter_by(
            fb_id=current_user.fb_user_id, friend_fb_id=friend_fb_id).first()
        if (existing_request != None):
            if (request.json['remove'] == True):
                HasFriend.query.filter_by(
                    fb_id=current_user.fb_user_id, friend_fb_id=friend_fb_id).delete()
                db.session.commit()
                return ok("Friend Removed!")
            else:
                return ok("Friend already added!")
        else:
            if (request.json['remove'] == True):
                return ok("Friend not added!")
            new_friend_connection = HasFriend(
                fb_id=current_user.fb_user_id, friend_fb_id=friend_fb_id)
            db.session.add(new_friend_connection)
            db.session.commit()
            return created("Friend request succeeded!")


@app.route('/breaks', methods=['POST'])
@login_required
def breaks() -> Response:
    """
    TODO
    """
    logging.debug(dir(request))
    logging.debug(request.json)
    group_members: Set[User] = { User.query.filter_by(fb_user_id=friend_id).first() 
        for friend_id in request.json["friendIds"] }

    if not all(current_user in i.confirmed_friends for i in group_members):
        raise Forbidden(message=("Not all of the Facebook accounts corresponding to the Facebook IDs"
            " specified in the request to this endpoint are friends of the current user's"
            " Facebook account"))

    group_members.add(current_user)

    return ok(get_remaining_shared_breaks_this_week(group_members))


@app.route('/calendar', methods=['GET', 'POST', 'DELETE'])
@login_required
def calendar() -> Response:
    """
    GET:  Extracts this weeks subjects from the calendar for the logged in user

    POST: Provides the server with a URL to the logged in user's calendar stored
            at UQ Timetable planner

    DELETE: Deletes the cached calendar URl and data
    """
    if request.method == 'GET':
        if (current_user.calendar_data is None):
            raise NotFound(message="Calendar not yet added")

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

        return created(current_user.timetable)
    else:
        current_user.remove_calendar()
        db.session.flush()
        db.session.commit()
        return no_content()


@app.route('/profile', methods=['GET'])
@login_required
def profile() -> Response:
    """
    Retrieves basic profile information for the logged in user
    """
    return ok({"name": current_user.username,
               "dp": current_user.profile_picture,
               "calURL": current_user.calendar_url})


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings() -> Response:
    """
    GET: Grabs the current settings that the user has set in their profile menu.

    POST: Updates user settings
    """
    def make_settings_response(current_user: User) -> Response:
        return ok({"incognito": current_user.incognito})

    if request.method == 'GET':
        return make_settings_response(current_user)
    else:
        try:
            current_user.incognito = request.json['incognito']
            logging.info(f"Changed {current_user.username}'s incognito setting to {current_user.incognito}")
            db.session.flush()
            db.session.commit()
        except:
            pass

        return make_settings_response(current_user)

@app.route('/status', methods=['GET', 'POST'])
@login_required
def status() -> Response:
    """
    GET: Grabs the current check-in statues for the user

    POST: Updates check-in statuses
    """
    # TODO: Implement the frontend consumer code for this, using the same state
    # synchronization scheme as ussed in `/settings`
    def make_status_response(user: User) -> Response:
        return ok({"atUni": user.at_uni,
                   "onBreak": user.on_break
                   })

    if request.method == 'GET':
        return make_status_response(current_user)
    else:

        # FIXME: Ugly code
        try:
            if request.json['atUni']:
                current_user.check_in()
            else:
                current_user.check_out()
        except:
            pass

        try:
            if request.json['onBreak']:
                current_user.begin_break()
            else:
                current_user.end_break()
        except:
            pass
        
        db.session.flush()
        db.session.commit()

        return make_status_response(current_user)


@app.route('/statuses', methods=['GET'])
@login_required
def statuses() -> Response:
    """
    Grabs the who's free information of each of the current users confirmed friends.
    Sorts this information, and sends to the front end.
    """
    confirmed_friends = current_user.confirmed_friends
    logging.debug(confirmed_friends)
    sort_weight = {
        "Free": 1,
        "Busy": 2,
        "Starting": 3,
        "Finished": 4,
        "Unavailable": 5,
        "Unknown": 6
    }
    list_user_info = [user.availability(current_user)
                      for user in confirmed_friends]
    sorted_list = sorted(
        list_user_info, key=lambda x: sort_weight[x['status']])
    complete_list = [current_user.availability(current_user)] + sorted_list
    return ok(complete_list)


@app.route('/fb-login', methods=['POST'])
def fb_login() -> Response:
    """
    Uses the JSON passed to us from the frontend to either 'log in' a user, 
    or register them if they do not exist.
    """
    logging.info("Commenced Facebook login procedure")
    user_id = request.json['userID']
    existing_user = User.query.filter_by(fb_user_id=user_id).first()

    if existing_user is None:
        access_token = request.json['accessToken']
        logging.info("The login request was for a new user, creating new user")

        new_user = User(username="unknown", email="unknown",
                        fb_user_id=user_id, fb_access_token=access_token)
        logging.info(f"User made, user_id = {user_id}, access_token = {access_token}")
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)
        logging.info("The user is now logged in")
    else:
        logging.info("The user already exists")

        try:
            username = request.json['userName']
            # in case they've changer their name on facebook since they
            # registered
            logging.info(f"Updating user with name {existing_user.username} to {username}")
            existing_user.username = username
        except KeyError as e:
            logging.error(f"Login field 'userName' is empty, error: {e}")

        try:
            email = request.json['email']
            # in case they've changed their email since they registered
            logging.info(f"Updating user with email {existing_user.email} to {email}")
            existing_user.email = email
        except KeyError as e:
            logging.error(f"Login field 'email' is empty, error: {e}")

        try:
            access_token = request.json['accessToken']
            logging.info("Adding new accessToken")

            # update their accessToken with the one supplied
            existing_user.fb_access_token = access_token
        except KeyError as e:
            logging.error(f"Login field 'accessToken' is empty, error: {e}")

        logging.info("Logging in user")
        login_user(existing_user, remember=True)
        logging.info("User logged in")

    db.session.flush()
    db.session.commit()
    # FIXME: Is this functional? Otherwise it should just be an `ok()`
    return ok("Logged user in")

@app.route('/fb-app-id', methods=['GET'])
def fb_app_id() -> Response:
    """
    TODO
    """
    app_id = os.environ.get('FB_APP_ID', '1091049127696748')
    return ok(app_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"Running app on port {port}")
    app.run(host='0.0.0.0', port=port)
