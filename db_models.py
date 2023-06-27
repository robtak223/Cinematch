
from sqlalchemy.orm import mapped_column
from sqlalchemy import GenerativeSelect, Integer, String
from database import db

"""
Main class for users. This is used for login and signup
"""

class Users(db.Model):
    #Corresponding table name in the database
    #__table__ = db.Model.metadata.tables['Users']
    __tablename__ = 'Users'
    UserID = mapped_column(Integer, primary_key=True)
    Username = mapped_column(String)
    Pass = mapped_column(String)
    FullName = mapped_column(String)
    Email = mapped_column(String)

    # Used for return data to the frontend
    def serialize(self):
        return {
            'username' : self.Username,
            'ID' : self.UserID,
            'name' : self.FullName,
            'email' : self.Email
        }
    
    # Used to create a user and initialize their info for storage in database
    def setup(self, user, passw, name, email):
        self.Username = user
        self.Pass = passw
        self.FullName = name
        self.Email = email


"""
Class for logging left and right swipes into the database
"""
class Swipes(db.Model):
    #__table__ = db.Model.metadata.tables['Swipes']
    __tablename__ = 'Swipes'
    ID = mapped_column(Integer, primary_key=True)
    Username = mapped_column(String)
    Title = mapped_column(String)
    Rating = mapped_column(Integer)

    def serialize(self):
        return {
            'username' : self.Username,
            'title' : self.Title,
            'rating' : self.Rating
        }
    def setup(self, user, title, rating):
        self.Username = user
        self.Title = title
        self.Rating = rating

"""
Class for creating groups.
"""
class Groups(db.Model):
    #__table__ = db.Model.metadata.tables['Groups']
    __tablename__ = 'Groups'
    ID = mapped_column(Integer, primary_key=True)
    Username = mapped_column(String)
    GroupID = mapped_column(Integer)
    Leader = mapped_column(String)
    Name = mapped_column(String)

    def serialize(self):
        return {
            'username' : self.Username,
            'ID' : self.ID,
            'groupID' : self.GroupID,
            'Name' : self.Name,
            'Leader' : self.Leader
        }
    def setup(self, user, group, leader, name):
        self.Username = user
        self.GroupID = group
        self.Leader = leader
        self.Name = name


"""
Class for logging up swipes into the database and recording them as movies the user has already seen.
"""
class Up(db.Model):
    #__table__ = db.Model.metadata.tables['Viewed']
    __tablename__ = 'Viewed'
    ID = mapped_column(Integer, primary_key=True)
    Username = mapped_column(String)
    Title = mapped_column(String)
    Rating = mapped_column(Integer)

    def serialize(self):
        return {
            'username' : self.Username,
            'title' : self.Title,
            'rating' : self.Rating
        }
    def setup(self, user, title, rating):
        self.Username = user
        self.Title = title
        self.Rating = rating

"""
Main class for creating friends. Username1 is the source and Username2 is the destination; however, which user
is the source user and which user is the destination user will not impact anything else.
"""
class Friends(db.Model):
    #__table__ = db.Model.metadata.tables['Friends']
    __tablename__ = 'Friends'
    ID = mapped_column(Integer, primary_key=True)
    Username1 = mapped_column(String)
    Username2 = mapped_column(String)

    def serialize(self):
        return {
            'username1' : self.Username1,
            'username2' : self.Username2
        }
    def setup(self, user1, user2):
        self.Username1 = user1
        self.Username2 = user2

"""
Main class for creating a friend request. Username1 is the source and Username2 is the destination. In this case,
username2 should see a pending friend request when the login.
"""
class Requests(db.Model):
    #__table__ = db.Model.metadata.tables['Requests']
    __tablename__ = 'Requests'
    ID = mapped_column(Integer, primary_key=True)
    Source = mapped_column(String)
    Destination = mapped_column(String)

    def serialize(self):
        return {
            'username1' : self.Source,
            'username2' : self.Destination
        }
    def setup(self, src, dest):
        self.Source = src
        self.Destination = dest


"""
Main class for movies.
"""
class Movies(db.Model):
    #__table__ = db.Model.metadata.tables['Requests']
    __tablename__ = 'Movies'
    ID = mapped_column(Integer, primary_key=True)
    Genres = mapped_column(String)
    Title = mapped_column(String)
    Year = mapped_column(Integer)
    Runtime = mapped_column(Integer)

    def serialize(self):
        return {
            'Title' : self.Title
        }


"""
Class for movies by popularity.
"""
class Movie2(db.Model):
    #__table__ = db.Model.metadata.tables['Requests']
    __tablename__ = 'Movie2'
    ID = mapped_column(Integer, primary_key=True)
    Title = mapped_column(String)
    Popularity = mapped_column(Integer)

    def serialize(self):
        return {
            'Title' : self.Title
        }