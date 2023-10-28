from models import *
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask,  render_template, request, jsonify
from sqlalchemy import or_
import jwt,datetime,os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash



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



#deals with the login routes
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


#main page route
@app.route('/')
def index():
    return "Welcome to our API"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#Route for register
@app.route('/usersignup', methods=['POST'])
def register_user():
  try:
       data = request.get_json() 
       if not data:
           return jsonify({'error': 'Invalid JSON data'}), 400
       
       username = data.get('username')
       first_name = data.get('first_name')
       last_name = data.get('last_name')
       email = data.get('email')
       password = data.get('password')
   
       # Check if the username is already taken
       existing_user = User.query.filter_by(username=username).first()
       if existing_user:
           response = {'message': 'Username is already taken. Please choose another one.'}
           return jsonify(response), 400
       # Create a new user
       hashed_password = generate_password_hash(password, method='sha256')
       new_user = User(first_name=first_name,last_name=last_name,username=username,email=email, password=hashed_password, role="User")
   
       # Add the new user to the database
       db.session.add(new_user)
       db.session.commit()
   
       response = {'message': 'Registration successful!'}
       return jsonify(response)
  except Exception as e:
    print(e)
    response = {"status": False,"msg": str(e)}
    return jsonify(response), 500
  


#Routes for login
@app.route('/userlogin', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not ((username or email) and password):
      return jsonify({'error': 'Invalid JSON data'}), 400  

    user = User.query.filter(or_(User.username == username, User.email == email)).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        token = jwt.encode({'username': username, 'exp': expiration}, app.config['SECRET_KEY'], algorithm='HS256')
        token_str = token.decode("utf-8")
        return jsonify({'token': token_str})
    else:
        return jsonify({'message': 'Invalid username,email or password'}), 401



# Route for profile
@app.route('/userprofile')
@login_required
def profile():
    fullname = current_user.first_name + current_user.last_name
    return jsonify({
        "name": fullname,
        "username": current_user.username,
        "email": current_user.email
    })

# Route for logout
@app.route('/userlogout')
@login_required
def logout():
    logout_user()
    return 'Logged out successfully'


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
            'username': user.username,
            'email': user.email
        }
        user_list.append(user_data)

    return jsonify(user_list)




if __name__ == '__main__':
    app.run(debug=True, port=5002)