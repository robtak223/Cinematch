# File Created by John Kuszmaul, Cinematch Co-Founder
# Feb. 7, 2023
# Cinematch

import random
import math

ALGO_LOG_FILE = "logs/algo.txt"

# Returns the k top movies for a user 
# May return less than k movies if not enough found.
# user_movie_ratings -- a dictionary containing movies as keys and ratings as values. Positive and negative denote good and bad ratings
# friends_movie_ratings -- a list of dictionaries  containing the recommendations of the user's friends
# All_user_ratings, a list of the ratins of all users, in the order of their ids
# ratio: a list of the probability at which types of movies should be returned (should add up to 1). The types of movies are:
#      - Random popular movies
#      - Movies that friends have liked
#      - Movies that the algorithm thinks this user will like (i.e., movies that rate similarly to movies that the user liked).
def rec_algo(k, user_movie_ratings, friends_movie_ratings, all_user_ratings, ratio=[0.2, 0.3, 0.5]):
    total_weight = ratio[0] + ratio[1] + ratio[2]
    if total_weight < 0.9:
        print("Sum of input ratios too low: ", total_weight, file=open(ALGO_LOG_FILE, 'a'))
        
    movies_already_rated = {} # Includes movies already rated and movies about to be recommended
    movie_recs = [] # The ultimate list of movies returned

    # We want to display movies that their friends liked.
    for movie in user_movie_ratings:
        movies_already_rated[movie] = True
    movies_friends_like = find_friends_fav_movies(movies_already_rated, friends_movie_ratings)

    # We want to display movies that similar users liked.
    similar_movies = get_movies_from_most_similar_user(user_movie_ratings, all_user_ratings, movies_already_rated)
    more_similar_users = True
    
    while len(movie_recs) < k:
        ran = random.uniform(0, total_weight)
        if ran < ratio[0]:
            movie_recs.append(None)
        elif ran < ratio[0] + ratio[1]:
            if len(movies_friends_like) > 0:
                if movies_friends_like[0][0] not in movie_recs:
                    friends_movie = movies_friends_like.pop()[0]
                    movie_recs.append(friends_movie)
                    movies_already_rated[friends_movie] = True
                else:
                    movies_friends_like.pop()
        else:
            if len(similar_movies) > 0:
                if similar_movies[0] not in movie_recs:
                    movie_recs.append(similar_movies[0])
                    movies_already_rated[similar_movies.pop()] = True
                else:
                    similar_movies.pop()
            elif more_similar_users:
                similar_movies = get_movies_from_most_similar_user(user_movie_ratings, all_user_ratings, movies_already_rated)
                if len(similar_movies) == 0:
                    more_similar_users = False

    return movie_recs

# Returns a list of movies that a similar user liked.
# @param user_movie_ratings: a dictionary with movies as keys and the user's ratings as values.
# @param all_user_ratings: a list containing dictionaries of each user's ratings.
# @param movies_already_rated: a list of movies that cannot be returned (e.g., because they are already rated by the user).
# Effects: Does not modify input parameters.
def get_movies_from_most_similar_user(user_movie_ratings, all_user_ratings, movies_already_rated):
    similar_user = most_similar_user(user_movie_ratings, all_user_ratings, movies_already_rated)[0]
    similar_movies = []
    if similar_user is not None:
        for movie in all_user_ratings[similar_user]:
            if movie not in movies_already_rated and all_user_ratings[similar_user][movie] > 0:
                similar_movies.append(movie)
    return similar_movies

# Returns a list of (movie, num_likes) pairs of all movies liked by friends, in decreasing order of how many friends like them.
# Doesn't consider how may friends disliked the movie.
# @param movies_already_rated: a dictionary containing movies that the user has already swiped on; these will not be returned.
# @param friends_movie_ratings: a list of dictionaries, each of which corresponds to the ratings of one particular friend.
# Effects: No parameters are modified.
def find_friends_fav_movies(movies_already_rated, friends_movie_ratings):
    # We want to display movies that their friends liked.    
    movies_friends_like = {}
    # This dictionary stores the total number of friends that liked the movie. Discards friends' negative ratings.
    for movies_specific_friend_likes in friends_movie_ratings:
        for movie in movies_specific_friend_likes:
            rating = movies_specific_friend_likes[movie]
            if movie not in movies_already_rated and rating > 0:
                if movie not in movies_friends_like:
                    movies_friends_like[movie] = 0
                movies_friends_like[movie] += rating
    movies_friends_like = list(movies_friends_like.items())
    movies_friends_like.sort(reverse=True, key = lambda x: x[1])
    return movies_friends_like

# Returns a similarity score between user 1 and user 2 given their ratings of movies, as well as the number of movies they have both rated.
# @parameters: two dictionaries of user ratings
def user_similarity_score(user_one_ratings, user_two_ratings):
    total_similarity = 0
    common_movies = 0
    for movie in user_one_ratings:
        if movie in user_two_ratings:
            total_similarity += user_one_ratings[movie] * user_two_ratings[movie] # dot product
            common_movies += 1
    if common_movies == 0:
        average_similarity = 0
    else:
        average_similarity = total_similarity/common_movies * (1 - 1/(2 * math.sqrt(common_movies))) # 1 - standard deviation of n coin flips, where n is the number of common movies
    return average_similarity, common_movies # Maximize average similarity but also common movies

# Returns the idx of the user with the highest user similarity score to user 1
# If the return value is not None, None, then it is a (user_id, movie) pair of a user that has liked some movie not in movies_already_rated.
# user_ratings -- the ratings of user 1
# all_user_ratings -- the ratings of all users (may include user 1)
def most_similar_user(user_ratings, all_user_ratings, movies_already_rated):
    similarity_scores = []
    for i in range(len(all_user_ratings)):
        similarity_scores.append((i, user_similarity_score(user_ratings, all_user_ratings[i]))) # A list of (index, (average_similarity, total_common_movies))
    similarity_scores.sort(key = lambda x: x[1][0], reverse=True) # sort by similarity score
    while len(similarity_scores) > 0:
        # We make sure that this max_similarity_user likes a move that user 1 hasn't rated yet
        max_id = similarity_scores[0][0]
        for movie in all_user_ratings[max_id]:
            if movie not in movies_already_rated and all_user_ratings[max_id][movie] > 0:
                return max_id, movie
        similarity_scores.pop(0)
    return None, None
        

