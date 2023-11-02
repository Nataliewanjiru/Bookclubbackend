from models import *
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask,  render_template, request, jsonify,flash
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
@app.route('/userprofile', methods=['GET'])
def profile():
    fullname = current_user.first_name + current_user.last_name
    return jsonify({
        "name": fullname,
        "username": current_user.username,
        "email": current_user.email
    })

# Route for logout
@app.route('/userlogout', methods=['GET'])
def logout():
    logout_user()
    return 'Logged out successfully'


# Get users route
@app.route('/user', methods=['GET'])
@login_required
def get_all_users():
    user = User.query.filter_by(id=current_user.id).first()
    user_data = {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'email': user.email,
    }
   

    return jsonify(user_data)



#Route for getting the all clubs
@app.route("/clubs", methods=['GET'])
def get_all_clubs():
    clubsList = Clubs.query.all()
    clubsData = []
    for club in clubsList:
        data = {
            'clubID': club.clubID,
            'clubName': club.nameOfClub,
            'description': club.description,
            'imageLink': club.imageURL,
            'location': club.location,
            'dateFounded': club.dateFounded
        }
        clubsData.append(data)
    
    return jsonify (clubsData)


#Route for getting ratings for a club
@app.route('/club/<int:id>/rating', methods=['GET'])
def get_ratings_for_a_club(id):
     club = Clubs.query.filter_by(clubID=id).first()
     if not club:
      return jsonify({"message":"Club not found"})
     data = {
         'clubID': club.clubID,
         'clubName': club.nameOfClub,
         'description': club.description,
         'imageLink': club.imageURL,
         'location': club.location,
         'dateFounded': club.dateFounded,
         'ratingsData':[rating.get_club_rating() for rating in club.rating]
         }
     return jsonify(data)
   

#Route for creating a rating
@app.route('/rating', methods=['POST'])
@login_required
def create_rating():
    # Get the data from the request
    data = request.get_json()
    
    if not data:
      return jsonify({'error': 'Invalid JSON data'}), 400
    
    comment = data.get('comment')
    rating = data.get('rating')
    clubId = data.get('clubID')


    newRating = Rating(comment=comment, rating=rating, memberID=current_user.id, clubID=clubId)
    db.session.add(newRating)
    db.session.commit()

    return jsonify({'message':'New rating created successfully!'})



#Route for getting each club and books in the club
@app.route("/clubs/<int:id>")
def get_single_club(id):
    club = Clubs.query.filter_by(clubID=id).first()
    if not club:
        return jsonify({"message":"Club not found"})
    data = {
        'clubID': club.clubID,
        'clubName': club.nameOfClub,
        'description': club.description,
        'imageLink': club.imageURL,
        'location': club.location,
        'dateFounded': club.dateFounded,
        'booksData':[book.getbooks() for book in club.books]
        }
    return jsonify(data)




# Route for creating a new club
@app.route("/createClub", methods=["POST"])
@login_required
def create_new_club():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400



    nameOfClub = data.get('nameOfClub')
    description = data.get('description')
    imageURL = data.get('imageURL')
    location = data.get('location')
    dateFounded = data.get('dateFounded')

    # Check if any required field is missing
    if not nameOfClub or not description or not imageURL or not location or not dateFounded:
        return jsonify({"message": "All fields are required"}), 400

    try:
        newClub = Clubs(nameOfClub=nameOfClub, description=description, imageURL=imageURL, location=location, dateFounded=dateFounded)
        db.session.add(newClub)
        db.session.commit()
        return jsonify({"success": "New club created successfully!"})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500



#Route for getting all books
@app.route("/getbooks")
def get_all_books():
    booksList = Books.query.all()
    booksData = []
    for book in booksList:
        data = {
            'bookID': book.bookID,
            'bookTitle': book.title,
            'bookauthor': book.author,
            'bookImageURL': book.imageURL,
            'clubID': book.clubID,
        }
        booksData.append(data)
        return jsonify (booksData)
   
   

# Route for creating a new book
@app.route("/createbook", methods=["POST"])
@login_required
def add_a_book():
    data = request.get_json()
    if not data:
      return jsonify({'error': 'Invalid JSON data'}), 400
    
    
    title = data.get("title")
    author = data.get("author")
    imageURL = data.get("imageURL")
    clubID = data.get("clubID")

    # Check if any required field is missing
    if not title or not author or not imageURL or not clubID:
       return jsonify({"message": "All fields are required"}), 400
    
    newBook = Books(title=title,author=author,imageURL=imageURL,clubID=clubID)
    db.session.add(newBook)
    db.session.commit()

    return jsonify({"success": "New book created successfully!"})


#Rotes for writing asummary
@app.route("/summaries", methods=["POST"])
@login_required 
def create_summary():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    # Extract data from the JSON request
    summary_text = data.get('summary')
    book_id = data.get('bookID')


    # Check if required data is present
    if not summary_text or not book_id :
        return jsonify({"message": "Summary, bookID, and userID are required"}), 400

    try:
        # Create a new summary
        new_summary = Summaries(summary=summary_text, bookID=book_id, userID=current_user.id)

        # Add the summary to the database
        db.session.add(new_summary)
        db.session.commit()

        # Return a success message
        return jsonify({"message": "Summary created successfully"}), 201

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

   
       
#Route for book summary
@app.route("/book/<int:id>", methods=['GET'])
@login_required
def book_summary(id):
    book = Books.query.filter_by(bookID=id).first()
    if not book:
     return jsonify({"message":"Book not found"})
    
    booksData=[]
    data = {
      'bookID': book.bookID,
      'bookTitle': book.title,
      'bookauthor': book.author,
      'bookImageURL': book.imageURL,
      'clubID': book.clubID,
      'reviews':[book.booksummaries() for book in book.summaries]
      }
    booksData.append(data)
    return jsonify (booksData)



if __name__ == '__main__':
    app.run(debug=True, port=5006)

#For admin the route is /admin/
#So if someone logs in as an admin we show them the button for admin if not we don't show them the admin button