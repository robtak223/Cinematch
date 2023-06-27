from error import *
from common import *
from flask import Blueprint, request, jsonify
from db_models import *
import json

friends_bp = Blueprint('friends', __name__)

"""
Endpoint for sending a friend request
"""
@friends_bp.route('/friends/add', methods=['POST'])
def friend_request():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username1' not in content or 'username2' not in content:
        raise APITypeError('Missing information (usernames)')
    # username1 is the sending username, username2 is the receiving username
    user1 = content['username1']
    user2 = content['username2']
    if user1 == user2:
        raise APITypeError('Cannot add yourself as a friend.')
    usera = Users.query.filter_by(Username=user1).first()
    userb = Users.query.filter_by(Username=user2).first()
    if usera is None or userb is None:
        raise APIMissingError("Username does not exist")
    frienda = Friends.query.filter_by(Username1=user1).filter_by(Username2=user2).first()
    friendb = Friends.query.filter_by(Username1=user2).filter_by(Username2=user1).first()
    if frienda is not None or friendb is not None:
        raise APIMissingError("Users are already friends")
    new_req = Requests()
    new_req.setup(user1, user2)
    add_record(new_req)
    return jsonify(new_req.serialize())

"""
Endpoint for confirming a received friend request.
"""
@friends_bp.route('/friends/confirm', methods=['POST'])
def confirm_request():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username1' not in content or 'username2' not in content:
        raise APITypeError('Missing information (usernames)')
    user1 = content['username1']
    user2 = content['username2']
    req = Requests.query.filter_by(Source=user1, Destination=user2).first()
    if req is None:
        raise APIMissingError('No matching friend request')
    delete_record(req)
    new_friend = Friends()
    new_friend.setup(user1, user2)
    add_record(new_friend)
    return jsonify(new_friend.serialize())

"""
Endpoint for rejecting a friend request
"""

@friends_bp.route('/friends/reject', methods=['POST'])
def reject_request():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username1' not in content or 'username2' not in content:
        raise APITypeError('Missing information (usernames)')
    user1 = content['username1']
    user2 = content['username2']
    req = Requests.query.filter_by(Source=user1, Destination=user2).first()
    if req is None:
        raise APIMissingError('No matching friend request')
    delete_record(req)
    response = {"message": "success"}
    return jsonify(response), 200

"""
Endpoint for removing a friend
"""

@friends_bp.route('/friends/remove', methods=['POST'])
def remove_friend():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username1' not in content or 'username2' not in content:
        raise APITypeError('Missing information (usernames)')
    user1 = content['username1']
    user2 = content['username2']
    frienda = Friends.query.filter_by(Username1=user1).filter_by(Username2=user2).first()
    friendb = Friends.query.filter_by(Username1=user2).filter_by(Username2=user1).first()
    if frienda is None and friendb is None:
        raise APIMissingError("Users are not friends")
    elif frienda is not None:
        delete_record(frienda)
    else:
        delete_record(friendb)
    response = {"message": "success"}
    return jsonify(response), 200