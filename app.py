from models import *
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask,  render_template, request, jsonify,flash
from sqlalchemy import or_
import datetime,os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required,get_jwt_identity
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

app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this to a secure key
# Initialize the JWTManager
jwt = JWTManager(app)

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
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(hours=24))
        return jsonify({'access_token': access_token,
                        "userid":current_user.id}), 200
    else:
        return jsonify({'message': 'Invalid username,email or password'}), 401



# Route for profile
@app.route('/userprofile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()  
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    fullname = user.first_name + user.last_name

    user_clubs = Clubusers.query.filter_by(memberID=user_id).all()

    club_ids = [club.clubID for club in user_clubs]

    clubs = Clubs.query.filter(Clubs.clubID.in_(club_ids)).all()

    club_data = []
    for club in clubs:
        club_data.append({
            "clubID": club.clubID,
            "clubName": club.nameOfClub,
            "description": club.description,
            "imageLink": club.imageURL,
        })
    followers_data = [{'user_id': follower.id, 'name': follower.username} for follower in user.followers]

    return jsonify({
        "name": fullname,
        "username": user.username,
        "email": user.email,
        "clubs": club_data,
        'follower':followers_data,
        "summaries":[summary.usersummaries() for summary in user.summaries]
    })


# Route for other profile
@app.route('/profile/<int:id>', methods=['GET'])
def userprofile(id): 
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    fullname = user.first_name + user.last_name

    user_clubs = Clubusers.query.filter_by(memberID=id).all()

    club_ids = [club.clubID for club in user_clubs]

    clubs = Clubs.query.filter(Clubs.clubID.in_(club_ids)).all()

    club_data = []
    for club in clubs:
        club_data.append({
            "clubID": club.clubID,
            "clubName": club.nameOfClub,
            "description": club.description,
            "imageLink": club.imageURL,
        })
    
    followers_data = [{'user_id': follower.id, 'name': follower.username} for follower in user.followers]

    return jsonify({
        "name": fullname,
        "username": user.username,
        "email": user.email,
        "clubs": club_data,
        'follower':followers_data,
        "summaries":[summary.usersummaries() for summary in user.summaries]
    })

#Route for following users
@app.route('/follow', methods=['POST'])
@jwt_required()
def follow_user():
    current_user_id = get_jwt_identity() 
    data = request.get_json()
    user_id_to_follow = data.get('user_id')

    if not user_id_to_follow:
        return jsonify({"message": "user_id is required"}), 400

    user_to_follow = User.query.get(user_id_to_follow)

    if not user_to_follow:
        return jsonify({"message": "User to follow not found"}), 404

    existing_follow = Followers.query.filter_by(
        user_id=current_user_id, follower_id=user_id_to_follow
    ).first()

    if existing_follow:
        return jsonify({"message": "You are already following this user"}), 400

    new_follow = Followers(user_id=current_user_id, follower_id=user_id_to_follow)
    db.session.add(new_follow)
    db.session.commit()

    return jsonify({"message": "You are now following the user"}), 201


# Route for logout
@app.route('/userlogout', methods=['GET'])
@jwt_required()
def logout():
    logout_user()
    return 'Logged out successfully'

@app.route('/deleteaccount', methods=['GET'])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity() 

    if user_id:
        # Query the database to find the user
        user = User.query.get(user_id)

        if user:
            try:
                # Delete the user from the database
                db.session.delete(user)
                db.session.commit()

                return 'Your account has been deleted.'
            except Exception as e:
                db.session.rollback()  
                return jsonify({'error': 'An error occurred while deleting the user.'}), 500
        else:
            return 'User not found.'
    else:
        return 'Invalid or expired token.'


#Route for getting the all clubs
@app.route("/clubs", methods=['GET'])
@jwt_required()
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
@app.route('/club/<int:id>/rating')
@jwt_required()
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
         'ratingsData':[rating.get_club_rating() for rating in club.ratings]
         }
     return jsonify(data)
   

#Route for creating a rating
@app.route('/rating', methods=['POST'])
@jwt_required()
def create_rating():
    # Get the data from the request
    data = request.get_json()
    
    if not data:
      return jsonify({'error': 'Invalid JSON data'}), 400
    
    comment = data.get('comment')
    rating = data.get('rating')
    clubId = data.get('clubID')
    userid = data.get('userID')


    newRating = Rating(comment=comment, rating=rating, memberID=userid, clubID=clubId)
    db.session.add(newRating)
    db.session.commit()

    return jsonify({'message':'New rating created successfully!'})



#Route for getting each club and books in the club
@app.route("/clubs/<int:id>")
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def get_all_books():
    booksList = Books.query.all()
    booksData = []
    for book in booksList:
        data = {
            'bookID': book.bookID,
            'bookTitle': book.title,
            'bookauthor': book.author,
            'bookImageURL': book.imageURL,
            "bookSynopsis":book.synopsis,
            'bookChapters':book.chapters,
            'clubID': book.clubID,
        }
        booksData.append(data)
        return jsonify (booksData)
   
@app.route('/joinclub', methods=['POST'])
@jwt_required()
def join_club():
    # Get the authenticated user's ID from the JWT token
    memberID = get_jwt_identity()
    
    # Extract the club ID from the request data
    data = request.get_json()
    clubID = data.get('clubID')

    if not clubID:
        return jsonify({"error": "clubID is required"}), 400

    newMembership = Clubusers(memberID=memberID, clubID=clubID)

    try:
        db.session.add(newMembership)
        db.session.commit()
        return jsonify({"Success": "You have joined the club!"}), 201
    except Exception as e:
        print(str(e))
        return jsonify({"Error": str(e)}), 500
    

# Route for creating a new book
@app.route("/createbook", methods=["POST"])
@jwt_required()
def add_a_book():
    data = request.get_json()
    if not data:
      return jsonify({'error': 'Invalid JSON data'}), 400
    
    
    title = data.get("title")
    author = data.get("author")
    imageURL = data.get("imageURL")
    book_summary =data.get("synopsis")
    bookChapters = data.get("chapters")
    clubID = data.get("clubID")

    # Check if any required field is missing
    if not title or not author or not imageURL or not clubID or not book_summary or not bookChapters:
       return jsonify({"message": "All fields are required"}), 400
    
    newBook = Books(title=title,author=author,imageURL=imageURL,synopsis=book_summary,chapters=bookChapters,clubID=clubID)
    db.session.add(newBook)
    db.session.commit()

    return jsonify({"success": "New book created successfully!"})


#Rotes for writing asummary
@app.route("/summaries", methods=["POST"])
def create_summary():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    # Extract data from the JSON request
    summary_text = data.get('summary')
    book_id = data.get('bookID')
    user_id = data.get("userID")


    # Check if required data is present
    if not summary_text or not book_id :
        return jsonify({"message": "Summary, bookID, and userID are required"}), 400

    try:
        # Create a new summary
        new_summary = Summaries(summary=summary_text, bookID=book_id, userID=user_id)

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
@jwt_required()
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
      'bookChapters':book.chapters,
      'bookSynopsis':book.synopsis,
      'clubID': book.clubID,
      'reviews':[book.booksummaries() for book in book.summaries]
      }
    booksData.append(data)
    return jsonify (booksData)



if __name__ == '__main__':
    app.run(debug=True, port=5003)

#For admin the route is /admin/
#So if someone logs in as an admin we show them the button for admin if not we don't show them the admin button