from email_validator import validate_email, EmailNotValidError
from error import *
from common import *
from flask import Blueprint, request, jsonify
from db_models import *
from recommendation_algo import rec_algo
import json



users_bp = Blueprint('users', __name__)
"""
Endpoint for login
"""
@users_bp.route('/user/login', methods=['POST'])
def login():
    content_type = request.headers.get('Content-Type')
    # ensure json data is passed in
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    
    # Raise an error if mandatory fields are missing
    if 'username' not in content or 'password' not in content:
        raise APITypeError('Missing information (username or password)')
    used = content['username']
    password = content['password']
    hashed_pass = hash(str(password))
    # Check and ensure user does not already exist and that password matches
    user = Users.query.filter_by(Username=used).first()
    if user is None:
        raise APINotFoundError('Username not found')
    if user.Pass != hashed_pass:
        raise APIAuthError('Incorrect Password')
    
    
    
    seen_movies = get_already_swiped_movies(used)
    if used == "cinematchtester":
        titles = POPULAR_MOVIES_100
    elif used == "default":
        titles = TEST_MOVIES
    elif 'movies' in content:
        titles = content['movies']
    elif len(seen_movies) > MAX_TRIAL_LEN:
        user_ratings, friend_rate, all_rate = get_rec_algo_info(used)
        titles = rec_algo(NUM_MOVIES, user_ratings, friend_rate, all_rate)
        for i in range(len(titles)):
            if titles[i] == None:
                titles[i] = get_rand(seen_movies)
    else:
        titles = get_popular_movies(seen_movies)
    return_info = dict()
    #Get pending friend requests
    friend_requests = []
    req_obj = Requests.query.filter_by(Destination=used)
    for req in req_obj:
        src = req.Source
        friend_requests.append(src)
    friends = get_friends(used)
    groups = get_groups_info(used)
    return_info["movies"] = get_api_info(titles)
    return_info["requests"] = friend_requests
    return_info["username"] = used
    return_info["name"] = user.FullName
    return_info["friends"] = friends
    return_info["groups"] = groups
    return_info['instance'] = data_logger.get_rec()
    return jsonify(return_info)


"""
Endpoint for creating user
"""
@users_bp.route('/user/add', methods=['POST'])
def add_user():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content or 'password' not in content or 'name' not in content or 'email' not in content:
        raise APITypeError('Missing information (username, password, email, or name)')
    used = content['username']
    password = content['password']
    nam = content['name']
    email = content['email']
    user = Users.query.filter_by(Username=used).first()
    if user is not None:
        raise APIAuthError('Account already associated with that username')
    user = Users.query.filter_by(Email=email).first()
    if user is not None:
        raise APIAuthError('Account already associated with that email')
    try:
        v = validate_email(email)
    except EmailNotValidError as e:
        raise APIAuthError('Email is not properly formatted')
    new_user = Users()
    hashed_pass = hash(password)
    new_user.setup(used, hashed_pass, nam, email)
    add_record(new_user)
    return jsonify(new_user.serialize())


"""
Endpoint for deleting user
"""
@users_bp.route('/user/delete', methods=['POST'])
def del_user():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    user = Users.query.filter_by(Username=used).first()

    # Ensure user exists
    if user is None:
        raise APIAuthError('No account associated with that username')
    delete_record(user)

    # Delete all pending requests and existing friends
    pending_requests = Requests.query.filter_by(Source=used)
    for req in pending_requests:
        delete_record(req)
    pending_requests = Requests.query.filter_by(Destination=used)
    for req in pending_requests:
        delete_record(req)
    friends_list = Friends.query.filter_by(Username1=used)
    for friend in friends_list:
        delete_record(friend)
    friends_list = Friends.query.filter_by(Username2=used)
    for friend in friends_list:
        delete_record(friend)
    swipes_list = Swipes.query.filter_by(Username=used)
    for swipe in swipes_list:
        delete_record(swipe)
    rating_list = Up.query.filter_by(Username=used)
    for rating in rating_list:
        delete_record(rating)
    group_list = Groups.query.filter_by(Username=used)
    for group in group_list:
        delete_record(group)
    response = {"message": "success"}
    return jsonify(response), 200

"""
Endpoint for getting the watchlist
"""
@users_bp.route('/user/watchlist', methods=['POST'])
def watchlist():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    user = Users.query.filter_by(Username=used).first()

    # Ensure user exists
    if user is None:
        raise APIAuthError('No account associated with that username')

    movies_g = []
    movies_b = []
    swipe_obj = Swipes.query.filter_by(Username=used)
    for swipe in swipe_obj:
        if swipe.Rating == 1:
            movies_g.append(swipe.Title)
        else:
            movies_b.append(swipe.Title)
    ret = dict()
    ret['right'] = movies_g
    ret['left'] = movies_b
    return jsonify(ret)

"""
Endpoint for refreshing info
"""
@users_bp.route('/user/refresh', methods=['POST'])
def user_refresh():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    user = Users.query.filter_by(Username=used).first()
    if user is None:
        raise APINotFoundError("Username does not exist")
    return_info = dict()
    #Get pending friend requests
    friend_requests = []
    req_obj = Requests.query.filter_by(Destination=used)
    for req in req_obj:
        src = req.Source
        friend_requests.append(src)
    friends = get_friends(used)
    groups = get_groups_info(used)
    return_info["requests"] = friend_requests
    return_info["username"] = used
    return_info["name"] = user.FullName
    return_info["friends"] = friends
    return_info["groups"] = groups
    return jsonify(return_info)

"""
Endpoint for sending password reset code
"""
@users_bp.route('/user/password/change', methods=['POST'])
def change_password():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content or 'code' not in content:
        raise APITypeError('Missing information (username, code)')
    used = content['username']
    code = content['code']
    user = Users.query.filter_by(Username=used).first()
    if user is None:
        raise APINotFoundError("Username does not exist")
    email = user.Email

    send_change_password_email(code, email, user.FullName)
    response = {"message": "success"}
    return jsonify(response), 200

"""
Endpoint for setting new password
"""
@users_bp.route('/user/password/set', methods=['POST'])
def set_password():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content or 'password' not in content:
        raise APITypeError('Missing information (username, code)')
    used = content['username']
    password = content['password']
    user = Users.query.filter_by(Username=used).first()
    if user is None:
        raise APINotFoundError("Username does not exist")
    hashed_pass = hash(str(password))
    user.Pass = hashed_pass
    db.session.commit()
    response = {"message": "success"}
    return jsonify(response), 200