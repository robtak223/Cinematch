from conftest import fake_user, test_client
from recommendation_algo import rec_algo
import pytest

def pytest_configure():
    pytest.pid = 0
# Ensure add user works
def test_add_user(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['name'] = fake_user.FullName
    user_data['username'] = fake_user.Username
    user_data['password'] = fake_user.Pass
    user_data['email'] = fake_user.Email
    response = test_client.post('/user/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    user_data['name'] = fake_user2.FullName
    user_data['username'] = fake_user2.Username
    user_data['password'] = fake_user2.Pass
    user_data['email'] = fake_user2.Email
    response = test_client.post('/user/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# Ensure duplicate username fails
def test_bad_user(test_client, fake_user):
    user_data = dict()
    # Duplicate username
    user_data['name'] = "Unique name"
    user_data['username'] = fake_user.Username
    user_data['password'] = fake_user.Pass
    user_data['email'] = "unique.email@gmail.com"
    response = test_client.post('/user/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 403
    # Missing name
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['password'] = fake_user.Pass
    user_data['email'] = "unique.email@gmail.com"
    response = test_client.post('/user/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

# Ensure login works
def test_login_user(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['password'] = fake_user.Pass
    response = test_client.post('/user/login', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['movies']) > 0 



# Ensure bad password and bad username fail
def test_bad_login(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['password'] = "WrongPassword"
    response = test_client.post('/user/login', json=user_data,
        content_type='application/json')
    assert response.status_code == 403
    user_data['username'] = "NonexistentUsername"
    user_data['password'] = "1234"
    response = test_client.post('/user/login', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

# Ensure adding a friend works
def test_new_friend(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = fake_user2.Username
    response = test_client.post('/friends/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# Ensure usernames that dont exist fail
def test_bad_friend(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = "username that doesn't exist"
    response = test_client.post('/friends/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

# Ensure rejection works, double rejection fails
def test_reject_request(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = fake_user2.Username
    response = test_client.post('/friends/reject', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    response = test_client.post('/friends/reject', json=user_data,
        content_type='application/json')
    assert response.status_code == 404
    response = test_client.post('/friends/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# ensure confirming a reuquest that doesn't exist fails
def test_bad_confirm_friend(test_client, fake_user, fake_user2):
    user_data = dict()
    # Request exists between users, but must be inputted in the correct order
    user_data['username1'] = fake_user2.Username
    user_data['username2'] = fake_user.Username
    response = test_client.post('/friends/confirm', json=user_data,
        content_type='application/json')
    assert response.status_code == 404
    user_data['username1'] = fake_user.Username
    user_data['username2'] = "username that doesn't exist"
    response = test_client.post('/friends/confirm', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

#ensure confirming a request succeeds
def test_confirm_friend(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = fake_user2.Username
    response = test_client.post('/friends/confirm', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = fake_user2.Username
    response = test_client.post('/friends/add', json=user_data,
        content_type='application/json')
    assert response.status_code == 404


# Test the swiping endpoint 
def test_swipe(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['title'] = "Star Wars"
    user_data['rating'] = "1"
    response = test_client.post('/movie/swipe', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    user_data['title'] = "Jurassic Park"
    user_data['rating'] = "1"
    response = test_client.post('/movie/swipe', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    user_data['username'] = fake_user2.Username
    user_data['title'] = "Jurassic Park"
    user_data['rating'] = "1"
    response = test_client.post('/movie/swipe', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# Test swipe endpoint for repeat entry and bad rating
def test_bad_swipe(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['title'] = "Star Wars"
    user_data['rating'] = "2"
    response = test_client.post('/movie/swipe', json=user_data,
        content_type='application/json')
    assert response.status_code == 404
    user_data['rating'] = "1"
    response = test_client.post('/movie/swipe', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

# the fake users are friends. Fake user1 liked star wars, it should be recommended to fake user2.
def test_popular_movies(test_client, fake_user2):
    user_data = dict()
    user_data['username'] = fake_user2.Username
    user_data['password'] = fake_user2.Pass
    response = test_client.post('/user/login', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['movies']) == 10
    
# Ensure the viewed endpoint works
def test_viewed(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['title'] = "Jaws"
    user_data['rating'] = "1"
    response = test_client.post('/movie/rate', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

def test_bad_view(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    user_data['title'] = "Jaws"
    user_data['rating'] = "2"
    response = test_client.post('/movie/rate', json=user_data,
        content_type='application/json')
    assert response.status_code == 404
    user_data['rating'] = "1"
    response = test_client.post('/movie/rate', json=user_data,
        content_type='application/json')
    assert response.status_code == 404


# Test that new stack of movies does not contain previously swiped on movies
def test_new_movies(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    response = test_client.post('/movie/new', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    for movie in data['movies']:
        if movie['title'] == "Jurassic Park":
            assert 1 == 0
    return




# Jurasssic Park should be recommended to this group since both users liked it
def test_create_delete_group(test_client, fake_user, fake_user2):
    user_data = dict()
    members = []
    members.append(fake_user.Username)
    members.append(fake_user2.Username)
    user_data['name'] = 'test'
    user_data['members'] = members
    user_data['leader'] = fake_user.Username
    response = test_client.post('/group/new', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['movies'][0]['title'] == "Jurassic Park"
    pytest.pid = data['groupid']


def test_bad_group(test_client, fake_user):
    user_data = []
    user_data.append(fake_user.Username)
    response = test_client.post('/group/new', json=user_data,
        content_type='application/json')
    assert response.status_code == 404


def test_refresh_group(test_client, fake_user):
    user_data = dict()
    user_data['username'] = fake_user.Username
    response = test_client.post('/group/refresh', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1

def test_delete_group(test_client):
    user_data = dict()
    user_data['groupid'] = pytest.pid
    response = test_client.post('/group/delete', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# Remove friend works and double remove fails
def test_remove_friend(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username1'] = fake_user.Username
    user_data['username2'] = fake_user2.Username
    response = test_client.post('/friends/remove', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    response = test_client.post('/friends/remove', json=user_data,
        content_type='application/json')
    assert response.status_code == 404

# Ensure delete user works
def test_delete_user(test_client, fake_user, fake_user2):
    user_data = dict()
    user_data['username'] = fake_user.Username
    response = test_client.post('/user/delete', json=user_data,
        content_type='application/json')
    assert response.status_code == 200
    user_data['username'] = fake_user2.Username
    response = test_client.post('/user/delete', json=user_data,
        content_type='application/json')
    assert response.status_code == 200

# A unit test
def test_friend_recommendations():
    k = 3
    user_movie_ratings = {17: 1, 3:-1, 4: 1}
    friend_movie_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}]
    all_user_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}, {17: 1, 3:-1, 4: 1, 9:1}, {17: 1, 3:-1, 4: 1}]
    recommendation = rec_algo(k, user_movie_ratings, friend_movie_ratings, all_user_ratings, [0, 0.5, 0.5])
    assert(len(recommendation) == 3)
    assert(0 in recommendation)
    assert(7 in recommendation)
    assert(9 in recommendation)    

# A friendless user unit test
def test_friendless_user():
    k = 1
    user_movie_ratings = {17: 1, 3:-1, 4: 1}
    friend_movie_ratings = []
    all_user_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}, {17: 1, 3:-1, 4: 1, 9:1}, {17: 1, 3:-1, 4: 1}]
    recommendation = rec_algo(k, user_movie_ratings, friend_movie_ratings, all_user_ratings, [0, 0, 1])
    assert(recommendation == [9])

# Users with no overlapping movies unit test
def test_no_overlap():
    k = 1
    user_movie_ratings = {17: 1, 3:-1, 4: 1}
    friend_movie_ratings = []
    all_user_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}, {17: 1, 3:-1, 4: 1, 9:1}, {17: 1, 3:-1, 4: 1}, {20:1}]
    recommendation = rec_algo(k, user_movie_ratings, friend_movie_ratings, all_user_ratings, [0, 0, 1])
    assert(recommendation == [9])



