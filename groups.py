from error import *
from common import *
from flask import Blueprint, request, jsonify
from db_models import *
import json

groups_bp = Blueprint('groups', __name__)

"""
Endpoint for creating a group and getting recommended movies
"""
@groups_bp.route('/group/new', methods=['POST'])
def add_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'name' not in content or 'members' not in content or len(content['members']) < 2:
        raise APITypeError('At least two members and a name required to create a group')
    for used in content['members']:
        user = Users.query.filter_by(Username=used).first()
        if user is None:
            raise APINotFoundError('Username not found')
    
    movies = dict()
    titles = []
    group_obj = Groups.query.order_by(Groups.GroupID.desc()).first()
    groupID = 1
    if group_obj:
        groupID = group_obj.GroupID + 2
    leader = content['leader']
    name = content['name']
    for user in content['members']:
        new_group = Groups()
        new_group.setup(user, groupID, leader, name)
        add_record(new_group)
    for user in content['members']:
        req = Swipes.query.filter_by(Username=user)
        for rating in req:
            if rating.Rating == 1:
                if rating.Title in movies:
                    movies[rating.Title] += 1
                else:
                    movies[rating.Title] = 1
    most_common_movies = sorted(movies, key=movies.get)
    most_common_movies.reverse()
    for movie in most_common_movies:
        if len(titles) < NUM_GROUP_MOVIES:
            titles.append(movie)
        else:
            break
    return_info = get_api_info(titles)
    for obj in return_info:
        obj['likes'] = movies[obj['title']]
    ret = dict()
    ret['name'] = name
    ret['members'] = content['members']
    ret['movies'] = return_info
    ret['groupid'] = groupID
    return jsonify(ret)

"""
Endpoint for getting the groups for a user
"""
@groups_bp.route('/group/refresh', methods=['POST'])
def refresh_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    user = Users.query.filter_by(Username=used).first()
    if user is None:
        raise APINotFoundError('Username not found')
    ret = get_groups_info(used)
    return ret

"""
Endpoint for deleting a group
"""
@groups_bp.route('/group/delete', methods=['POST'])
def delete_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'groupid' not in content:
        raise APITypeError('Missing information (id)')
    gid = content['groupid']
    users = Groups.query.filter_by(GroupID=gid)
    if not users.first():
        raise APINotFoundError("group id doesn't exist")
    for user in users:
        delete_record(user)
    response = {"message": "success"}
    return jsonify(response), 200


@groups_bp.route('/group/remove', methods=['POST'])
def remove_member_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'groupid' not in content or 'username' not in content:
        raise APITypeError('Missing information (id, username)')
    gid = content['groupid']
    used = content['username']
    users = Groups.query.filter_by(GroupID=gid)
    if not users.first():
        raise APINotFoundError("group id doesn't exist")
    for user in users:
        if user.Username == used:
            delete_record(user)
            break
    movies = dict()
    titles = []
    users = Groups.query.filter_by(GroupID=gid)
    for user in users:
        req = Swipes.query.filter_by(Username=user.Username)
        for rating in req:
            if rating.Rating == 1:
                if rating.Title in movies:
                    movies[rating.Title] += 1
                else:
                    movies[rating.Title] = 1
    most_common_movies = sorted(movies, key=movies.get)
    most_common_movies.reverse()
    for movie in most_common_movies:
        if len(titles) < NUM_GROUP_MOVIES:
            titles.append(movie)
        else:
            break
    return_info = get_api_info(titles)
    for obj in return_info:
        obj['likes'] = movies[obj['title']]
    ret = dict()
    ret['movies'] = return_info
    return jsonify(ret)

@groups_bp.route('/group/add', methods=['POST'])
def add_member_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'groupid' not in content or 'username' not in content:
        raise APITypeError('Missing information (id, username)')
    gid = content['groupid']
    used = content['username']
    users = Groups.query.filter_by(GroupID=gid)
    user_info = users.first()
    if not user_info:
        raise APINotFoundError("group id doesn't exist")
    new = Groups()
    new.setup(used, user_info.GroupID, user_info.Leader, user_info.Name)
    add_record(new)
    movies = dict()
    titles = []
    users = Groups.query.filter_by(GroupID=gid)
    for user in users:
        req = Swipes.query.filter_by(Username=user.Username)
        for rating in req:
            if rating.Rating == 1:
                if rating.Title in movies:
                    movies[rating.Title] += 1
                else:
                    movies[rating.Title] = 1
    most_common_movies = sorted(movies, key=movies.get)
    most_common_movies.reverse()
    for movie in most_common_movies:
        if len(titles) < NUM_GROUP_MOVIES:
            titles.append(movie)
        else:
            break
    return_info = get_api_info(titles)
    for obj in return_info:
        obj['likes'] = movies[obj['title']]
    ret = dict()
    ret['movies'] = return_info
    return jsonify(ret)


@groups_bp.route('/group/info', methods=['POST', 'GET'])
def get_group():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'groupid' not in content:
        raise APITypeError('Missing information (id)')
    gid = content['groupid']
    group = Groups.query.filter_by(GroupID=gid).first()
    new = dict()
    curr = group.Name
    new['name'] = curr
    curr = group.GroupID
    members = []
    people = Groups.query.filter_by(GroupID=curr)
    for person in people:
        new['leader'] = person.Leader
        members.append(person.Username)
    new['members'] = members
    movies = dict()
    titles = []
    for user in members:
        req = Swipes.query.filter_by(Username=user)
        for rating in req:
            if rating.Rating == 1:
                if rating.Title in movies:
                    movies[rating.Title] += 1
                else:
                    movies[rating.Title] = 1
    most_common_movies = sorted(movies, key=movies.get)
    most_common_movies.reverse()
    for movie in most_common_movies:
        if len(titles) < NUM_GROUP_MOVIES:
            titles.append(movie)
        else:
            break
    info = get_api_info(titles)
    for obj in info:
        obj['likes'] = movies[obj['title']]
    new['movies'] = info
    new['groupid'] = curr
    return jsonify(new)