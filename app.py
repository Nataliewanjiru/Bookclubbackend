from models import *
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_cors import CORS
from flask import Flask, redirect, render_template, request, jsonify
import os


app = Flask(__name__)

load_dotenv()

SECRET_KEY = os.environ.get("secretkey")
DATABASE_URL = os.environ.get("dburl")
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


admin.init_app(app)
CORS(app)

migrate = Migrate(app, db)

db.init_app(app)

@app.route('/')
def index():
    return "Welcome to our API"


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