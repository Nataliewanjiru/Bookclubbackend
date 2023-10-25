from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

#Initiates the database
db = SQLAlchemy()
#Initiates the admin side
admin = Admin()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String(128), nullable=False)

admin.add_view(ModelView(User,db.session)) #Enables the table to be viewed on the admin side or table
