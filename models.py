from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin

#Initiates the database
db = SQLAlchemy()
#Initiates the admin side
admin = Admin()

Base = declarative_base()
metadata = Base.metadata



class Clubusers(db.Model,UserMixin,Base):
    __tablename__="clubusers"
    memberID = db.Column(db.Integer,db.ForeignKey("users.id"),primary_key=True)
    clubID = db.Column(db.Integer,db.ForeignKey("clubs.clubID"),primary_key=True)
    
    
admin.add_view(ModelView(Clubusers,db.session))





class Rating (db.Model,UserMixin,Base):
    __tablename__ = "reviews"

    ratingID = db.Column(db.Integer,primary_key=True)
    clubID = db.Column(db.Integer,db.ForeignKey('clubs.clubID'))
    memberID = db.Column(db.Integer,db.ForeignKey('users.id'))
    rating = db.Column(db.Float,nullable=False)
    comment = db.Column(db.Text,nullable=False)

    def get_club_rating(self):
        ratings = Rating.query.filter_by(clubID = self.clubID).all()
        clubRating=[]
        for rating in ratings:
            user = User.query.get(rating.memberID)
            data= {
                'ratingID': rating.ratingID,
                'member': user.username,
                "memberID":user.memberID,
                'rating' : rating.rating,
                'comment':rating.comment,
                'clubID':rating.clubID
            }
            
            clubRating.append(data)
        return clubRating
    
    #Route for adding
    @staticmethod
    def insert_new_review(userID,clubID,rating,comment):
        newReview = Rating(memberID= userID , clubID= clubID , rating= rating , comment= comment )
        db.session.add(newReview)
        db.session.commit()

admin.add_view(ModelView(Rating,db.session))



class Followers(db.Model,UserMixin,Base):
    __tablename__ = "followers"
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
      

    def followers(self):
        followers = (
            db.session.query(Followers, User.name)
            .join(User, Followers.follower_id == User.id)
            .filter(Followers.user_id == self.user_id)
            .all()
        )

        followerData = []
        for follower, name in followers:
            data = {
                'user_id': follower.follower_id,
                'name': name,
            }
            followerData.append(data)

        return followerData

admin.add_view(ModelView(Followers,db.session))



class Summaries(db.Model, UserMixin,Base):
    __tablename__ = 'summaries'

    summaryID = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String, nullable=False)
    bookID = db.Column(db.Integer, db.ForeignKey('books.bookID'), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    

    def booksummaries(self):
        summaries=Summaries.query.filter_by(bookID = self.bookID).all()
        booksummaries = []
        for summary in summaries:
            user = User.query.get(summary.userID)
            data = {
                'summaryID': summary.summaryID,
                'summary': summary.summary,
                'bookID': summary.bookID,
                "userID":summary.userID,
                'user': user.username
            }
            booksummaries.append(data)
        return booksummaries
    
    def usersummaries(self):
        summaries=Summaries.query.filter_by(userID = self.userID).all()
        booksummaries = []
        for summary in summaries:
            book = Books.query.get(summary.bookID)
            data = {
                'summaryID': summary.summaryID,
                'summary': summary.summary,
                "book":book.title,
                'bookID': summary.bookID,
                'userID': summary.userID
            }
            booksummaries.append(data)
        return booksummaries
    


admin.add_view(ModelView(Summaries,db.session))



class Books(db.Model, UserMixin,Base):
    __tablename__ = "books"

    bookID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    synopsis= db.Column(db.String,nullable= False)
    chapters =db.Column(db.Integer,nullable=False)
    imageURL = db.Column(db.String, nullable=False)
    clubID = db.Column(db.Integer, db.ForeignKey('clubs.clubID'))

    # Define the 'summaries' relationship
    summaries = db.relationship("Summaries", backref='books')
    
    def getbooks(self):
      # Assuming that each club object has an attribute 'clubID'
      books = Books.query.filter_by(clubID=self.clubID).all()
      books_data = []
      for book in books:
          data = {
              'bookID': book.bookID,
              'bookTitle': book.title,
              'bookAuthor': book.author,
              'bookImageURL': book.imageURL,
              "bookSynopsis":book.synopsis,
              "bookchapters":book.chapters,
              'clubID': book.clubID,
          }
          books_data.append(data)
      return books_data



admin.add_view(ModelView(Books,db.session))




class Clubs(db.Model,UserMixin,Base):
    __tablename__ = "clubs"

    clubID = db.Column(db.Integer,primary_key=True)
    nameOfClub = db.Column(db.String,nullable=False)
    description = db.Column(db.Text,nullable=False)
    imageURL = db.Column(db.String,nullable=False)
    location = db.Column(db.String,nullable=False)
    dateFounded = db.Column(db.DateTime(),nullable=False)

    members = db.relationship(Clubusers, backref='clubs')
    books = db.relationship(Books, backref='clubs')
    ratings = db.relationship(Rating, backref='clubs')



admin.add_view(ModelView(Clubs,db.session))



class User(db.Model,UserMixin,Base):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(8),nullable=False)


    followers = db.relationship('User',secondary=Followers.__table__,primaryjoin=(Followers.follower_id == id),secondaryjoin=(Followers.user_id == id),backref=db.backref('followed_by', lazy='dynamic'),lazy='dynamic')
    clubs = db.relationship('Clubusers',backref="users")
    ratings = db.relationship("Rating", backref='users')
    summaries = db.relationship("Summaries", backref='users')
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return True
    

admin.add_view(ModelView(User,db.session)) #Enables the table to be viewed on the admin side or table



