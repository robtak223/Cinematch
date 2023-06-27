from error import *
from common import *
from recommendation_algo import rec_algo
from flask import Blueprint, request, jsonify
from db_models import *
import json
import random


movies_bp = Blueprint('movies', __name__)
"""
Endpoint for left and right swipes
"""
@movies_bp.route('/movie/swipe', methods=['POST'])
def swipe():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content or 'title' not in content or 'rating' not in content:
        raise APITypeError('Missing information (username, title, or rating)')
    used = content['username']
    title = content['title']
    rating = content['rating']
    # A rating of 1 is a right swipe (want to watch), and 0 is a left swipe (don't want to watch)
    if rating != "1" and rating != "0":
        raise APITypeError('Invalid rating. Must be 0 or 1')
    record = Swipes.query.filter_by(Username=used).filter_by(Title = title).first()
    if record is not None:
        raise APITypeError('Rating already exists')
    new_rate = Swipes()
    new_rate.setup(used, title, rating)
    add_record(new_rate)
    return jsonify(new_rate.serialize())

"""
Endpoint for up swipes
"""
@movies_bp.route('/movie/rate', methods=['POST'])
def rating():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content or 'title' not in content or 'rating' not in content:
        raise APITypeError('Missing information (username, title, or rating)')
    used = content['username']
    title = content['title']
    rating = content['rating']
    record = Up.query.filter_by(Username=used).filter_by(Title = title).first()
    if record is not None:
        raise APITypeError('Rating already exists')
    new_rate = Up()
    new_rate.setup(used, title, rating)
    add_record(new_rate)
    if 'watchlist' in content and content['watchlist'] == "true":
        record = Swipes.query.filter_by(Username=used).filter_by(Title = title).first()
        if record is None:
            raise APIMissingError("Needs to be a movie the user has swiped left or right on")
        delete_record(record)

    return jsonify(new_rate.serialize())

"""
Endpoint for fresh stack of movies
"""
@movies_bp.route('/movie/new', methods=['POST'])
def new_movies():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    seen_movies = get_already_swiped_movies(used)
    if len(seen_movies) > MAX_TRIAL_LEN:
        user_ratings, friend_rate, all_rate = get_rec_algo_info(used)
        titles = rec_algo(NUM_MOVIES, user_ratings, friend_rate, all_rate)
        for i in range(len(titles)):
            if titles[i] == None:
                titles[i] = get_rand(seen_movies)
    else:
        titles = get_popular_movies(seen_movies)
    return_info = get_api_info(titles)
    ret = dict()
    ret['movies'] = return_info
    return jsonify(ret)


"""
Endpoint for single random movie
"""
@movies_bp.route('/movie/random', methods=['POST'])
def random_movie():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'username' not in content:
        raise APITypeError('Missing information (username)')
    used = content['username']
    exitLoop = 0
    while not exitLoop:
        movieID = random.randint(MIN_MOVIE_ID, MAX_MOVIE_ID)
        title = Movies.query.filter_by(ID=movieID).first()
        try:
            info = get_api_info([title.Title])
        except APIExternalError as e:
            print(e, file=open(LOG_FILE, 'a'))
        else:
            exitLoop = 1

    ret = dict()
    ret['movies'] = info
    return jsonify(ret)

"""
Endpoint for info on a movie
"""
@movies_bp.route('/movie/info', methods=['POST'])
def movie_get_info():
    content_type = request.headers.get('Content-Type')
    if (content_type != 'application/json'):
        raise APITypeError('Content type not supported (JSON Required)')
    content = json.loads(request.data)
    if 'title' not in content:
        raise APITypeError('Missing information (title)')
    title = content['title']
    info = get_api_info([title])
    ret = dict()
    ret['movie'] = info
    return jsonify(ret)