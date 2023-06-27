from recommendation_algo import rec_algo

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

# Default ratio unit test
def test_default_ratio():
    k = 10
    user_movie_ratings = {17: 1, 3:-1, 4: 1}
    friend_movie_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}]
    all_user_ratings = [{17: 1, 7: 2, 0: -1}, {4: 1, 3: 1, 0: 3, 100: -7}, {17: 1, 3:-1, 4: 1, 9:1}, {17: 1, 3:-1, 4: 1}]
    recommendation = rec_algo(k, user_movie_ratings, friend_movie_ratings, all_user_ratings)
    print(recommendation)
    assert(None in recommendation)

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


if __name__ == "__main__":
    test_friend_recommendations()
    test_friendless_user()
    test_no_overlap()
    test_default_ratio()
