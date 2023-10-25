from models import *
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask, redirect, render_template, request, jsonify
import os

#Creates the flask application
app = Flask(__name__)

#Load environment variables from .env
load_dotenv()

SECRET_KEY = os.environ.get("secretkey")
DATABASE_URL = os.environ.get("dburl")

# Access environment variables using config()
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#initialize and configure the Flask-Admin extension
admin.init_app(app)
#escape the cors error
CORS(app)


db.init_app(app)


@app.route('/')
def index():
    return "Welcome to our API"

# Get users route
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    user_list = []

    for user in users:
        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
        user_list.append(user_data)

    return jsonify(user_list)

if __name__ == '__main__':
    app.run(debug=True, port=5001)