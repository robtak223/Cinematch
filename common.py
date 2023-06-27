import hashlib
from error import *
from db_models import Swipes, Users, Up, Friends, Groups, Movie2
import requests
from sqlalchemy import or_
from flask_mail import Message
from database import *
import random


"""
This file contains constants and some functions that are used in the endpoints and database connections.
"""

API_KEY = "fd67b62d9133871480c39d445df66ec3"
SEARCH_URL_STRING = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query="
DETAIL_URL_STRING = f"https://api.themoviedb.org/3/movie/"
DETAIL_URL_END = f"?api_key={API_KEY}"
CINEMATCH_EMAIL = "cinematchapp@gmail.com"
NUM_MOVIES = 10
NUM_TRIAL_MOVIES = 10
MAX_TRIAL_LEN = 30
NUM_GROUP_MOVIES = 10
PROD_DB_STRING = "mysql://admin:cinematch@database-1.chogn2wbsjgc.us-east-1.rds.amazonaws.com:3306/main"
PROD = 1
DEV = 0
LOG_FILE = "logs/log.txt"
MIN_MOVIE_ID = 107939
MAX_MOVIE_ID = 452408
MIN_ID_POP = 458347
MAX_ID_POP = 748402
TEST_MOVIES = ["Star Wars", "Spiderman", "Finding Nemo", "Jaws", "Top Gun", "Cars"]
SALT = "gn2wbS"

# Hash a password
def hash(passw):
    new = passw+SALT
    val = hashlib.sha256(new.encode('utf-8')).hexdigest()
    return val

# Delete from the database and commit
def delete_record(record):
    db.session.delete(record)
    db.session.commit()

# Add to the database and commit
def add_record(record):
    db.session.add(record)
    db.session.commit()

"""
Gets movie details from TMDB API for each movie title passed in
"""
def get_api_info(movies) -> list:
    info_dict = None
    ret = []
    for movie in movies:
        new = dict()
        move = movie
        if ' ' in movie:
            movie = movie.split(' ')
            movie = '+'.join(movie)
        query = SEARCH_URL_STRING + movie
        try:
            res = requests.get(query)
        except:
            raise APIExternalError(f"Request failed for movie {movie}")
        info_dict = res.json()
        if 'results' not in info_dict or info_dict['results'] == None or len(info_dict['results']) == 0:
            raise APIExternalError(f"No results for movie: {movie}")
        new['title'] = move
        new['overview'] = info_dict['results'][0]['overview']
        new['poster_path'] = info_dict['results'][0]['poster_path']
        new['release_date'] = info_dict['results'][0]['release_date']
        new['rating'] = info_dict['results'][0]['vote_average']
        ide = info_dict['results'][0]['id']
        query = DETAIL_URL_STRING + str(ide) + DETAIL_URL_END
        try:
            res = requests.get(query)
        except:
            raise APIExternalError(f"Request failed for movie {movie}")
        info_dict = res.json()
        genre_list = []
        for id_name_pair in info_dict['genres']:
            genre_list.append(id_name_pair['name'])
        new['genre'] = genre_list
        ret.append(new)
    return ret


"""
Return a list of groups for the given user
"""

def get_groups_info(used):
    groups = []
    group_obj = Groups.query.filter_by(Username=used)
    for group in group_obj:
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
        groups.append(new)
    return groups

"""
The following two functions collect all the information needed by the recommendation algorithm
"""
def get_rec_algo_info(used):
    # Retrieve the user's ratings
    user_ratings = dict()
    urate_obj = Swipes.query.filter_by(Username=used)
    for obj in urate_obj:
        user_ratings[obj.Title] = 2 * obj.Rating - 1
    urate_obj = Up.query.filter_by(Username=used)
    for obj in urate_obj:
        user_ratings[obj.Title] = 2 * obj.Rating - 1
    
    #retrieve their friends ratings
    friend_rate = []
    friend_obj = Friends.query.filter(or_(Friends.Username1==used, Friends.Username2==used))
    for userb in friend_obj:
        movies = dict()
        userw = userb.Username1
        if userw == used:
            userw = userb.Username2
        req = Swipes.query.filter_by(Username=userw)
        for rating in req:
            movies[rating.Title] = 2 * rating.Rating - 1
        req = Up.query.filter_by(Username=userw)
        for rating in req:
            movies[rating.Title] = 2 * rating.Rating - 1
        friend_rate.append(movies)
    #Retrieve all ratings
    all_rate = []
    user_obj = Users.query.all()
    for userb in user_obj:
        movies = dict()
        userw = userb.Username
        req = Swipes.query.filter_by(Username=userw)
        for rating in req:
            movies[rating.Title] = 2 * rating.Rating - 1
        req = Up.query.filter_by(Username=userw)
        for rating in req:
            movies[rating.Title] = 2 * rating.Rating - 1
        all_rate.append(movies)
    return user_ratings, friend_rate, all_rate

def get_friends(used):
    # Retrieve the user's ratings
    friends = []
    friend_obj = Friends.query.filter_by(Username1=used)
    for friend in friend_obj:
        friends.append(friend.Username2)
    friend_obj = Friends.query.filter_by(Username2=used)
    for friend in friend_obj:
        friends.append(friend.Username1)
    
    return friends

def send_change_password_email(code, email, name):
    msg = Message(
        subject="Change Your Password",
        sender=CINEMATCH_EMAIL,
        recipients=[email]
        )
    msg.body = f"Hello {name},\n\nPlease enter this code in the app:  {code}\n"
    mail.send(msg)


# Returns a list of movies the user has already swiped upon
def get_already_swiped_movies(used):
    # Retrieve the user's ratings
    movies = []
    viewed_obj = Up.query.filter_by(Username=used)
    for movie in viewed_obj:
        movies.append(movie.Title)
    swipe_obj = Swipes.query.filter_by(Username=used)
    for swipe in swipe_obj:
        movies.append(swipe.Title)
    return movies

# Returns NUM_TRIAL_MOVIES random movies from the below list of the 1000 most popular movies of all time.
def get_popular_movies(seen):
    movies = []
    seen = set(seen)
    nums = list(range(1, len(POPULAR_MOVIES_100))) 
    random.shuffle(nums)
    i = 0
    while i < len(POPULAR_MOVIES_100) and len(movies) < NUM_TRIAL_MOVIES:
        if POPULAR_MOVIES_100[nums[i]] not in seen:
            movies.append(POPULAR_MOVIES_100[nums[i]])
        i += 1
    return movies

def get_pop(seen):
    movies = []
    seen = set(seen)
    nums2 = list(range(1, len(POPULAR_MOVIES)))
    random.shuffle(nums2)
    i = 0
    while i < len(POPULAR_MOVIES) and len(movies) < NUM_TRIAL_MOVIES:
        if POPULAR_MOVIES[nums2[i]] not in seen:
            movies.append(POPULAR_MOVIES[nums2[i]])
        i += 1
    return movies


def get_rand(seen):
    
    exitd = 0
    movie = None
    while not exitd:
        num = random.uniform(0,1)
        if num < 0.5:
            ide = random.randint(0,1000)
        elif num < 0.9:
            ide = random.randint(1001, 5000)
        elif num < 0.99:
            ide = random.randint(5001, 10000)
        else:
            ide = random.randint(10001, 200000)
        ide += MIN_ID_POP
        title = Movie2.query.filter_by(ID=ide).first()
        if title.Title not in seen:
            exitd = 1
            movie = title.Title
    return movie
                


POPULAR_MOVIES = ['The Shawshank Redemption', 'The Dark Knight', 'Inception', 'Fight Club', 'Forrest Gump', 'Pulp Fiction', 'The Matrix', 'The Lord of the Rings: The Fellowship of the Ring', 'The Godfather', 'Interstellar', 'The Lord of the Rings: The Return of the King', 'The Dark Knight Rises', 'The Lord of the Rings: The Two Towers', 'Se7en', 'Django Unchained', 'Gladiator', 'Batman Begins', 'Inglourious Basterds', 'The Silence of the Lambs', 'The Wolf of Wall Street', 'Saving Private Ryan', 'The Avengers', 'Star Wars: Episode IV - A New Hope', "Schindler's List", 'The Prestige', 'The Departed', 'Shutter Island', 'Avatar', 'Joker', 'The Green Mile', 'Star Wars: Episode V - The Empire Strikes Back', 'The Godfather Part II', 'Memento', 'Back to the Future', 'Titanic', 'Guardians of the Galaxy', 'Goodfellas', 'Léon: The Professional', 'American Beauty', 'Avengers: Endgame', 'Pirates of the Caribbean: The Curse of the Black Pearl', 'American History X', 'V for Vendetta', 'WALL·E', 'Kill Bill: Vol. 1', 'Terminator 2: Judgment Day', 'Avengers: Infinity War', 'The Truman Show', 'The Usual Suspects', 'The Lion King', 'Iron Man', 'Star Wars: Episode VI - Return of the Jedi', 'Up', 'Finding Nemo', 'Deadpool', 'Braveheart', 'The Shining', 'Reservoir Dogs', 'Eternal Sunshine of the Spotless Mind', "One Flew Over the Cuckoo's Nest", 'Mad Max: Fury Road', 'Toy Story', 'Catch Me If You Can', 'Jurassic Park', 'The Sixth Sense', 'Gone Girl', 'Good Will Hunting', 'No Country for Old Men', 'Raiders of the Lost Ark', 'A Beautiful Mind', 'Star Wars: Episode VII - The Force Awakens', 'The Hunger Games', 'Monsters, Inc.', 'Die Hard', 'Alien', 'Harry Potter and the Deathly Hallows: Part 2', 'Whiplash', 'The Terminator', 'Avengers: Age of Ultron', 'The Intouchables', 'The Martian', 'Snatch', 'Iron Man 3', 'Thor', 'Captain America: The Winter Soldier', 'Captain America: The First Avenger', 'Scarface', 'Slumdog Millionaire', 'Requiem for a Dream', 'Taxi Driver', 'Toy Story 3', 'The Pianist', 'A Clockwork Orange', 'The Hobbit: An Unexpected Journey', 'Gravity', 'Parasite', '300', 'Spider-Man', 'Iron Man 2', 'The Grand Budapest Hotel', 'The Big Lebowski', 'The Revenant', 'Star Wars: Episode I - The Phantom Menace', 'Donnie Darko', 'Star Wars: Episode III - Revenge of the Sith', '12 Angry Men', 'Captain America: Civil War', "Harry Potter and the Sorcerer's Stone", 'The Hangover', 'Black Panther', 'Gran Torino', 'The Imitation Game', 'Black Swan', 'Blade Runner', 'Man of Steel', 'Spider-Man: No Way Home', 'Spirited Away', 'Logan', 'Sin City', 'I Am Legend', 'The Good, the Bad and the Ugly', 'Kill Bill: Vol. 2', 'Thor: Ragnarok', 'City of God', 'Indiana Jones and the Last Crusade', 'Amélie', 'Once Upon a Time in Hollywood', 'Doctor Strange', 'Ratatouille', 'How to Train Your Dragon', 'The Incredibles', 'Full Metal Jacket', 'Prisoners', "Pirates of the Caribbean: Dead Man's Chest", 'Inside Out', 'Aliens', 'Star Wars: Episode II - Attack of the Clones', 'X-Men: Days of Future Past', 'Silver Linings Playbook', 'The Social Network', 'Knives Out', '12 Years a Slave', 'Arrival', 'Batman v Superman: Dawn of Justice', 'Skyfall', 'Life Is Beautiful', 'X-Men: First Class', 'Trainspotting', 'Guardians of the Galaxy Vol. 2', 'Million Dollar Baby', 'Suicide Squad', 'Thor: The Dark World', 'Edge of Tomorrow', 'Shrek', 'District 9', "The King's Speech", 'Fargo', 'Ant-Man', 'The Batman', 'World War Z', 'Psycho', 'Kingsman: The Secret Service', '2001: A Space Odyssey', 'Apocalypse Now', "Pan's Labyrinth", 'The Hunger Games: Catching Fire', 'Dunkirk', 'The Hobbit: The Desolation of Smaug', 'Now You See Me', 'Spider-Man: Homecoming', 'Wonder Woman', 'Heat', 'Casino Royale', 'The Amazing Spider-Man', 'Spider-Man 2', 'The Curious Case of Benjamin Button', "Pirates of the Caribbean: At World's End", 'Dune', 'Drive', 'John Wick', 'Jurassic World', 'Rogue One: A Star Wars Story', 'Harry Potter and the Chamber of Secrets', 'Harry Potter and the Prisoner of Azkaban', 'Transformers', 'Groundhog Day', 'Sherlock Holmes', 'American Psycho', 'Star Wars: Episode VIII - The Last Jedi', 'Birdman or (The Unexpected Virtue of Ignorance)', 'The Bourne Ultimatum', 'Harry Potter and the Goblet of Fire', 'Life of Pi', 'Frozen', 'Into the Wild', 'Get Out', 'Her', '12 Monkeys', 'Ted', 'X-Men', 'Argo', 'Prometheus', 'Jaws', 'The Hateful Eight', 'Taken', '1917', 'Star Trek', 'La La Land', 'Cast Away', 'The Matrix Reloaded', 'Spider-Man 3', 'Home Alone', 'There Will Be Blood', 'Deadpool 2', 'Harry Potter and the Order of the Phoenix', 'Superbad', 'Blade Runner 2049', 'Rocky', 'Lock, Stock and Two Smoking Barrels', 'Toy Story 2', 'Oldboy', 'L.A. Confidential', 'Zombieland', "Ocean's Eleven", 'Limitless', 'Looper', 'The Notebook', 'Independence Day', 'Men in Black', 'Casablanca', 'Captain Marvel', 'Kick-Ass', '21 Jump Street', 'Shaun of the Dead', 'The Kashmir Files', 'Nightcrawler', 'Harry Potter and the Deathly Hallows: Part 1', 'It', 'Minority Report', 'Watchmen', 'Blood Diamond', 'The Great Gatsby', 'Harry Potter and the Half-Blood Prince', 'X2: X-Men United', 'Baby Driver', 'Despicable Me', 'Ex Machina', 'Zodiac', 'The Bourne Identity', 'Top Gun: Maverick', "Don't Look Up", 'I, Robot', 'Bohemian Rhapsody', 'Spider-Man: Into the Spider-Verse', 'Monty Python and the Holy Grail', 'Troy', 'The Hobbit: The Battle of the Five Armies', 'Back to the Future Part II', 'A Quiet Place', 'Hacksaw Ridge', 'Pirates of the Caribbean: On Stranger Tides', 'Rise of the Planet of the Apes', 'Oblivion', 'Juno', 'Crazy, Stupid, Love.', 'Casino', 'Source Code', '500 Days of Summer', 'The Pursuit of Happyness', 'Coco', 'X-Men: The Last Stand', 'Rain Man', 'The Perks of Being a Wallflower', 'Tenet', 'The Matrix Revolutions', 'Three Billboards Outside Ebbing, Missouri', 'The Conjuring', 'Hot Fuzz', 'X-Men Origins: Wolverine', 'Split', 'Zootopia', 'Pacific Rim', 'The Hangover Part II', 'Green Book', 'The Amazing Spider-Man 2', 'Children of Men', 'Spider-Man: Far from Home', 'Mr. & Mrs. Smith', 'Lucy', 'Fury', 'Dead Poets Society', 'Love Actually', 'The Incredible Hulk', 'Edward Scissorhands', 'Indiana Jones and the Temple of Doom', 'Rear Window', 'Mission: Impossible - Ghost Protocol', 'The Butterfly Effect', 'American Sniper', 'Venom', 'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb', 'Dallas Buyers Club', 'Charlie and the Chocolate Factory', 'Ice Age', 'Hancock', 'Little Miss Sunshine', 'Star Trek Into Darkness', 'Rush', 'American Hustle', 'Aquaman', 'Fantastic Beasts and Where to Find Them', 'Kung Fu Panda', 'The Fifth Element', 'Warrior', 'The Maze Runner', 'Spotlight', 'Shrek 2', 'The Wolverine', 'Big Hero 6', 'The Girl with the Dragon Tattoo', 'The Bourne Supremacy', 'Captain Phillips', 'The Terminal', 'Twilight', "It's a Wonderful Life", 'Divergent', 'The Help', 'Top Gun', 'The Hunger Games: Mockingjay - Part 1', 'Mystic River', 'Tangled', 'Lost in Translation', 'Sherlock Holmes: A Game of Shadows', 'Indiana Jones and the Kingdom of the Crystal Skull', 'Star Wars: Episode IX - The Rise of Skywalker', 'Beauty and the Beast', 'The Theory of Everything', 'Justice League', "We're the Millers", 'The Hurt Locker', 'The Day After Tomorrow', 'War of the Worlds', 'Back to the Future Part III', 'Horrible Bosses', 'Quantum of Solace', 'Elysium', 'Gangs of New York', 'The Last Samurai', 'Dawn of the Planet of the Apes', 'John Wick: Chapter 2', 'Spectre', 'Citizen Kane', 'Ready Player One', 'The 40-Year-Old Virgin', 'Big Fish', 'Training Day', 'X-Men: Apocalypse', 'The Big Short', 'Sicario', 'Crash', 'In Bruges', 'The Da Vinci Code', 'The Mummy', 'Scott Pilgrim vs. the World', 'Mission: Impossible', 'The Thing', 'Moneyball', 'Armageddon', 'The Princess Bride', 'American Gangster', 'Cars', 'Wreck-It Ralph', 'Midnight in Paris', 'Predator', 'Doctor Strange in the Multiverse of Madness', 'Saw', 'Aladdin', 'The Devil Wears Prada', 'King Kong', 'The Shape of Water', 'Room', 'The Cabin in the Woods', 'Tropic Thunder', 'The Lost World: Jurassic Park', 'Unbreakable', 'Ghostbusters', 'Alice in Wonderland', '28 Days Later', 'Platoon', 'Godzilla', 'Brave', 'This Is the End', 'In Time', 'Borat', 'Ant-Man and the Wasp', 'Unforgiven', 'E.T. the Extra-Terrestrial', 'Passengers', 'The Exorcist', 'Transformers: Dark of the Moon', 'American Pie', 'Madagascar', 'No Time to Die', 'Collateral', 'Stand by Me', 'Transformers: Revenge of the Fallen', 'Bruce Almighty', 'Live Free or Die Hard', 'Ford v Ferrari', 'The Breakfast Club', 'Vertigo', "Zack Snyder's Justice League", 'Despicable Me 2', '3 Idiots', 'The Chronicles of Narnia: The Lion, the Witch and the Wardrobe', 'The Wizard of Oz', 'Amadeus', 'Cloverfield', 'Life of Brian', 'Terminator 3: Rise of the Machines', 'The Game', "Howl's Moving Castle", 'The Godfather Part III', 'Black Hawk Down', 'Jojo Rabbit', 'Princess Mononoke', 'Fast & Furious 6', 'The Irishman', 'Easy A', 'The Town', 'The Machinist', "Ocean's Twelve", 'Furious 7', 'Wanted', 'The Mask', 'Everything Everywhere All at Once', 'Shang-Chi and the Legend of the Ten Rings', 'Mean Girls', 'The Lives of Others', 'Die Hard with a Vengeance', 'A Star Is Born', 'The Fast and the Furious', 'Dumb and Dumber', 'Jumanji: Welcome to the Jungle', 'Black Widow', 'Fast Five', '22 Jump Street', 'Batman', 'Face/Off', 'The Fault in Our Stars', '2012', '127 Hours', 'Men in Black II', 'Maleficent', 'Free Guy', 'Mission: Impossible - Rogue Nation', 'The Equalizer', "The Devil's Advocate", 'Inside Man', 'The Illusionist', 'Friends with Benefits', 'The Italian Job', 'The Fighter', 'Knocked Up', 'Sweeney Todd: The Demon Barber of Fleet Street', 'The Others', 'Home Alone 2: Lost in New York', 'Speed', 'Signs', 'Men in Black 3', 'Man on Fire', 'Yes Man', 'Die Hard 2', 'The Aviator', 'Snowpiercer', 'Monsters University', 'Sleepy Hollow', 'Terminator Salvation', 'Glass Onion', "Ferris Bueller's Day Off", 'Cloud Atlas', 'Brokeback Mountain', 'Moon', 'Anchorman: The Legend of Ron Burgundy', 'The Suicide Squad', 'Mission: Impossible III', 'The Lego Movie', 'Mulholland Drive', '50 First Dates', 'Wedding Crashers', 'About Time', 'Flight', 'Downfall', 'Hotel Rwanda', 'Raging Bull', 'John Wick: Chapter 3 - Parabellum', 'Boyhood', 'Super 8', 'Night at the Museum', 'Once Upon a Time in America', 'The Ring', 'Jackie Brown', 'Scream', 'Solo: A Star Wars Story', 'Moonrise Kingdom', 'Jumanji', 'Constantine', 'The Gentlemen', "Ocean's Thirteen", 'Bird Box', '10 Things I Hate About You', 'Thor: Love and Thunder', 'Eternals', 'Shazam!', 'The Expendables', 'Eyes Wide Shut', 'Seven Samurai', 'Mission: Impossible II', 'The Nightmare Before Christmas', 'Due Date', 'My Neighbor Totoro', 'Jack Reacher', 'Moana', 'Pineapple Express', 'True Grit', 'The Rock', 'The Deer Hunter', 'How to Train Your Dragon 2', 'TRON: Legacy', 'Being John Malkovich', 'Meet the Parents', 'Mission: Impossible - Fallout', 'Midsommar', 'The Blind Side', 'National Treasure', 'Up in the Air', 'Soul', 'Shooter', 'Click', 'Burn After Reading', 'The Interview', 'Pearl Harbor', 'Kingsman: The Golden Circle', 'Total Recall', 'The Nice Guys', 'The Hunger Games: Mockingjay - Part 2', 'The Hunt', 'Real Steel', 'Equilibrium', '10 Cloverfield Lane', 'The Simpsons Movie', 'The Proposal', 'Hellboy', 'Annihilation', '50/50', 'Les Misérables', 'Once Upon a Time in the West', 'Fantastic Four', 'Pretty Woman', 'Hereditary', 'The Mummy Returns', 'North by Northwest', 'Chinatown', 'Interview with the Vampire: The Vampire Chronicles', 'Jurassic Park III', 'Hugo', 'Kong: Skull Island', 'The Book of Eli', 'Fifty Shades of Grey', 'The Secret Life of Walter Mitty', 'Bullet Train', 'Jurassic World: Fallen Kingdom', 'Lord of War', 'Hitch', 'From Dusk Till Dawn', 'Notting Hill', 'Avatar: The Way of Water', 'The Hangover Part III', 'Pirates of the Caribbean: Dead Men Tell No Tales', 'Gone with the Wind', 'Marriage Story', 'To Kill a Mockingbird', 'The Island', 'Salt', 'Transformers: Age of Extinction', 'The Mist', '3:10 to Yuma', 'O Brother, Where Art Thou?', 'Apocalypto', 'Lucky Number Slevin', 'Magnolia', "There's Something About Mary", 'The Man from U.N.C.L.E.', 'Neighbors', 'Before Sunrise', 'Bridge of Spies', 'The Untouchables', 'Liar Liar', 'Beauty and the Beast', 'Deja Vu', 'The Dictator', 'Insidious', 'Shrek the Third', 'Moonlight', 'Donnie Brasco', 'RED', 'School of Rock', 'A.I. Artificial Intelligence', 'Pitch Perfect', 'Beetlejuice', 'Taken 2', 'Jumper', 'The Expendables 2', 'Batman Returns', 'The Wrestler', 'Us', 'Gattaca', 'Ace Ventura: Pet Detective', 'The Transporter', 'Public Enemies', 'Babel', 'Contagion', 'Seven Pounds', 'Zero Dark Thirty', 'The Bourne Legacy', '300: Rise of an Empire', 'Con Air', 'Scent of a Woman', 'Alien³', 'Incredibles 2', 'As Good as It Gets', 'Pride & Prejudice', 'Law Abiding Citizen', 'Step Brothers', 'Starship Troopers', 'The Accountant', 'The Fugitive', 'Apollo 13', 'Insomnia', 'Lady Bird', 'The Holiday', 'Now You See Me 2', 'Serenity', "A Bug's Life", 'Angels & Demons', 'Lawrence of Arabia', '8 Mile', 'The Royal Tenenbaums', 'Death Proof', 'Bridesmaids', 'Mulan', 'Kung Fu Panda 2', 'Kingdom of Heaven', 'Prince of Persia: The Sands of Time', 'Snow White and the Huntsman', 'Lone Survivor', 'Fast & Furious', 'Uncut Gems', "Hachi: A Dog's Tale", 'Fantastic Beasts: The Crimes of Grindelwald', 'Forgetting Sarah Marshall', 'Manchester by the Sea', 'Creed', 'Moulin Rouge!', 'The Greatest Showman', 'Fear and Loathing in Las Vegas', 'The Twilight Saga: New Moon', 'Predestination', 'Green Lantern', 'Alien: Covenant', "The World's End", 'Nocturnal Animals', 'Halloween', 'Superman Returns', 'Clash of the Titans', 'Red Notice', 'Elf', 'Atonement', 'Panic Room', 'Grease', 'Ice Age: The Meltdown', 'Gone in 60 Seconds', 'Call Me by Your Name', 'Grave of the Fireflies', 'Finding Dory', 'Terminator Genisys', "Don't Breathe", '28 Weeks Later', 'Olympus Has Fallen', 'Almost Famous', 'The Jungle Book', 'The Goonies', 'Corpse Bride', 'Blade', 'Hannibal', 'The Patriot', 'Dredd', 'Contact', 'Sully', '1408', '2 Fast 2 Furious', 'Zoolander', 'Red Dragon', 'Your Name.', 'The Fast and the Furious: Tokyo Drift', 'The Conjuring 2', 'Gone Baby Gone', 'The Graduate', 'Kick-Ass 2', 'John Carter', 'Hellboy II: The Golden Army', 'Resident Evil', 'Stardust', 'Meet the Fockers', 'Rush Hour', 'Alita: Battle Angel', 'Underworld', 'Wonder Woman 1984', 'The Other Guys', 'It Chapter Two', 'The Place Beyond the Pines', 'Phone Booth', 'Rango', 'Road to Perdition', 'Crouching Tiger, Hidden Dragon', 'Robin Hood', 'The Menu', 'Mrs. Doubtfire', 'Vanilla Sky', 'Jerry Maguire', 'Dances with Wolves', 'Office Space', 'Bad Boys', 'Aladdin', 'Van Helsing', 'The Witch', 'Dark Shadows', 'Megamind', 'Hulk', 'Some Like It Hot', 'BlacKkKlansman', 'A Few Good Men', 'Before Sunset', 'Boogie Nights', 'The Little Mermaid', 'Fantastic Four: Rise of the Silver Surfer', 'Annie Hall', 'Warcraft', 'Scary Movie', 'Non-Stop', 'The Blair Witch Project', 'Nobody', 'The Sting', 'Enemy at the Gates', 'How the Grinch Stole Christmas', 'The Village', 'True Lies', 'Murder on the Orient Express', 'The Lobster', 'Cinema Paradiso', 'Blow', 'RoboCop', 'Unknown', 'Lincoln', 'Lethal Weapon', 'Seven Psychopaths', 'War for the Planet of the Apes', 'Me Before You', 'Hotel Transylvania', 'Final Destination', 'The A-Team', 'Dog Day Afternoon', 'El Camino: A Breaking Bad Movie', 'The Adjustment Bureau', 'GoldenEye', 'For a Few Dollars More', 'American Pie 2', 'Dawn of the Dead', 'Hook', 'Sinister', 'Vicky Cristina Barcelona', 'First Blood', 'Wind River', 'Jumanji: The Next Level', 'Changeling', 'Noah', 'Total Recall', 'Toy Story 4', 'Saw II', 'Batman & Robin', 'Grown Ups', 'The Intern', 'Maze Runner: The Scorch Trials', 'Paul', 'Batman Forever', 'Chappie', 'RocknRolla', '21', 'The Matrix Resurrections', 'Bad Boys II', 'The Grey', 'Focus', 'Perfume: The Story of a Murderer', 'Dodgeball: A True Underdog Story', 'Walk the Line', 'Chronicle', 'Sunshine', 'End of Watch', 'Identity', 'Crank', 'Das Boot', 'Mamma Mia!', 'The Twilight Saga: Breaking Dawn - Part 2', 'Alien: Resurrection', 'Ice Age: Dawn of the Dinosaurs', 'Battleship', 'The Lion King', 'Glass', 'Just Go with It', 'The Twilight Saga: Eclipse', 'Star Trek Beyond', 'The Reader', 'The Bucket List', 'It Follows', "Bridget Jones's Diary", 'Enemy of the State', 'Valkyrie', 'Meet Joe Black', 'Spy', 'Eastern Promises', 'How to Lose a Guy in 10 Days', 'A Separation', 'The Great Escape', 'Escape Plan', 'The Tourist', 'Philadelphia', "Singin' in the Rain", 'Modern Times', 'Airplane!', 'A Nightmare on Elm Street', 'Birds of Prey', 'Lawless', 'Sucker Punch', 'Austin Powers: International Man of Mystery', 'The Elephant Man', 'Black Panther: Wakanda Forever', 'Paranormal Activity', "Ender's Game", 'The Twilight Saga: Breaking Dawn - Part 1', 'The Descendants', 'Minions', 'Pitch Black', 'Southpaw', 'The Beach', 'Amores Perros', 'The Artist', 'The Road', 'San Andreas', 'National Treasure: Book of Secrets', 'Ghost Rider', 'The Divergent Series: Insurgent', 'A History of Violence', 'Ad Astra', 'Ben-Hur', 'The Lincoln Lawyer', 'The Fountain', 'Don Jon', 'The Boondock Saints', "What's Eating Gilbert Grape", 'Me, Myself & Irene', 'The Sound of Music', 'Lion', 'Cruella', 'I Am Number Four', 'Game Night', 'A Quiet Place Part II', 'Cloudy with a Chance of Meatballs', '21 Grams', 'Fantastic Mr. Fox', 'Natural Born Killers', 'Dirty Dancing', 'Disturbia', 'Coraline', 'Austin Powers: The Spy Who Shagged Me', 'Knowing', 'The Lone Ranger', 'Hercules', 'The Platform', 'Hidden Figures', 'Mr. Nobody', 'The Fate of the Furious', 'Life', 'Hell or High Water', 'Orphan', 'Cube', 'Rambo', "The Hitman's Bodyguard", 'Old School', 'Ghostbusters', 'Predators', 'Gandhi', 'The Adventures of Tintin', 'No Strings Attached', 'Warm Bodies', 'The Passion of the Christ', 'Silent Hill', 'Role Models', 'The Invisible Man', 'Chicago', 'Romeo + Juliet', 'Rio', 'Black Adam', 'Madagascar: Escape 2 Africa', 'The Chronicles of Riddick', 'Mother!', 'Mars Attacks!', 'Venom: Let There Be Carnage', 'Happy Gilmore', 'Tarzan', 'Transcendence', 'RoboCop', 'Gremlins', 'Body of Lies', 'Jason Bourne', 'Encanto', 'Stranger Than Fiction', 'True Romance', 'The Babadook', 'The Descent', 'The Karate Kid', 'Munich', 'Kiss Kiss Bang Bang', 'Train to Busan', 'The Impossible', 'The Purge', 'The Girl Next Door', 'Sleepers', 'Shakespeare in Love', 'Primal Fear', 'War Dogs', 'Big', 'The Great Dictator', 'White House Down', 'Ip Man', 'When Harry Met Sally...', 'Safe House', 'Clueless', 'Master and Commander: The Far Side of the World', 'Clerks', 'Legally Blonde', 'The Boy in the Striped Pajamas', 'The Lighthouse', "Ocean's Eight", 'Rush Hour 2', 'Napoleon Dynamite', 'The Ides of March', 'Closer', 'Sunset Blvd.', 'Cowboys & Aliens', 'I, Tonya', 'Thank You for Smoking', 'The Bridge on the River Kwai', 'Blade II', 'Captain Fantastic', 'Big Daddy', 'Dracula', 'Daredevil', 'Ghost', 'The Ugly Truth', 'Ace Ventura: When Nature Calls', 'Planet of the Apes', 'Die Another Day', "Carlito's Way", 'Everest', 'Rocky Balboa', 'The Northman', 'King Arthur: Legend of the Sword', 'Uncharted', "Rosemary's Baby", 'A Fistful of Dollars', 'Dogma', 'Get Smart', 'Match Point', 'Pain & Gain', 'Chef', 'The Polar Express', 'Let the Right One In', 'Remember the Titans', 'The Croods', 'Anger Management', 'Butch Cassidy and the Sundance Kid', 'Ghost in the Shell', "You've Got Mail", 'Garden State', 'The Girl with the Dragon Tattoo', 'Fast & Furious Presents: Hobbs & Shaw', 'Misery', 'Tomb Raider', 'Gangster Squad', 'Rocky II']

POPULAR_MOVIES_100 = ['The Shawshank Redemption', 'The Dark Knight', 'Inception', 'Fight Club', 'Forrest Gump', 'Pulp Fiction', 'The Matrix', 'The Lord of the Rings: The Fellowship of the Ring', 'The Godfather', 'Interstellar', 'The Lord of the Rings: The Return of the King', 'The Dark Knight Rises', 'The Lord of the Rings: The Two Towers', 'Se7en', 'Django Unchained', 'Gladiator', 'Batman Begins', 'Inglourious Basterds', 'The Silence of the Lambs', 'The Wolf of Wall Street', 'Saving Private Ryan', 'The Avengers', 'Star Wars: Episode IV - A New Hope', "Schindler's List", 'The Prestige', 'The Departed', 'Shutter Island', 'Avatar', 'Joker', 'The Green Mile', 'Star Wars: Episode V - The Empire Strikes Back', 'The Godfather Part II', 'Memento', 'Back to the Future', 'Titanic', 'Guardians of the Galaxy', 'Goodfellas', 'Léon: The Professional', 'American Beauty', 'Avengers: Endgame', 'Pirates of the Caribbean: The Curse of the Black Pearl', 'American History X', 'V for Vendetta', 'WALL·E', 'Kill Bill: Vol. 1', 'Terminator 2: Judgment Day', 'Avengers: Infinity War', 'The Truman Show', 'The Usual Suspects', 'The Lion King', 'Iron Man', 'Star Wars: Episode VI - Return of the Jedi', 'Up', 'Finding Nemo', 'Deadpool', 'Braveheart', 'The Shining', 'Reservoir Dogs', 'Eternal Sunshine of the Spotless Mind', "One Flew Over the Cuckoo's Nest", 'Mad Max: Fury Road', 'Toy Story', 'Catch Me If You Can', 'Jurassic Park', 'The Sixth Sense', 'Gone Girl', 'Good Will Hunting', 'No Country for Old Men', 'Raiders of the Lost Ark', 'A Beautiful Mind', 'Star Wars: Episode VII - The Force Awakens', 'The Hunger Games', 'Monsters, Inc.', 'Die Hard', 'Alien', 'Harry Potter and the Deathly Hallows: Part 2', 'Whiplash', 'The Terminator', 'Avengers: Age of Ultron', 'The Intouchables', 'The Martian', 'Snatch', 'Iron Man 3', 'Thor', 'Captain America: The Winter Soldier', 'Captain America: The First Avenger', 'Scarface', 'Slumdog Millionaire', 'Requiem for a Dream', 'Taxi Driver', 'Toy Story 3', 'The Pianist', 'A Clockwork Orange', 'The Hobbit: An Unexpected Journey', 'Gravity', 'Parasite', '300', 'Spider-Man', 'Iron Man 2', 'The Grand Budapest Hotel']