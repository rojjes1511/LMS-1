from flask import Flask, render_template, redirect, request, flash, url_for,jsonify, make_response
from flask_login import LoginManager, login_user, login_required,current_user
from werkzeug.utils import secure_filename    
from datetime import datetime, timedelta
from flask_restful import Resource, Api, fields, marshal_with, reqparse
import os
from model import *
from werkzeug.exceptions import HTTPException
import json
from flask_cors import CORS

app = Flask(__name__, template_folder='template')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mad1.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SCHEDULER_API_ENABLED'] = True
app.secret_key = 'some_secret_key'
app.config['UPLOAD_FOLDER_IMAGE'] = "static/image"
app.config['UPLOAD_FOLDER_PDF'] = "static/pdf"




login_manager = LoginManager(app)
db.init_app(app)
app.app_context().push()
api=Api(app)
CORS(app)



# ----------- Exception Handling ------------------------------------------------------------#
class NotFoundError(HTTPException):
    def __init__(self, status_code, message=''):
        self.response = make_response(message, status_code)

class NotGivenError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)

#----------------------------------------------------------------------------------------#

############################################# API Field's ##########################################################
user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'password': fields.String,
    'username': fields.String,
}

# Serialization fields for Librarian model
librarian_fields = {
    'l_id': fields.Integer,
    'l_name': fields.String,
    'l_password': fields.String,
    'l_username': fields.String
}

# Serialization fields for EBook model
ebook_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'author_name': fields.String,
    'release_date': fields.DateTime(dt_format='iso8601'),
    'image': fields.String,
    'pdf': fields.String,
    'return_date_expected': fields.DateTime(dt_format='iso8601'),
    'total_pages': fields.Integer,
    'return_date': fields.DateTime(dt_format='iso8601'),
    'content': fields.String,
    'price': fields.Float,
    'section_id': fields.Integer,
    'section_name': fields.String,
}

# Serialization fields for Review model
review_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'rating': fields.Integer,
    'user_review': fields.String,
    'ebook_id': fields.Integer
}

# Serialization fields for Section model
section_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601')
}

# Serialization fields for BookRequest model
book_request_fields = {
    'id': fields.Integer,
    'request_id': fields.String,
    'request_time': fields.DateTime(dt_format='iso8601'),
    'return_time': fields.DateTime(dt_format='iso8601'),
    'status': fields.String,
    'user_id': fields.Integer,
    'ebook_id': fields.Integer,
    'section_id': fields.Integer,
    'is_requested': fields.Boolean,
    'is_returned': fields.Boolean,
    'is_revoked': fields.Boolean,
    'is_issued': fields.Boolean
}

####################################### Parser's for API's ###########################################################
user_parser = reqparse.RequestParser()
user_parser.add_argument('name')
user_parser.add_argument('password')
user_parser.add_argument('username')

# Parser for EBook model
ebook_parser = reqparse.RequestParser()
ebook_parser.add_argument('name')
ebook_parser.add_argument('image')
ebook_parser.add_argument('pdf')
ebook_parser.add_argument('release_date')
ebook_parser.add_argument('author_name')
ebook_parser.add_argument('total_pages')
ebook_parser.add_argument('return_date')
ebook_parser.add_argument('content')
ebook_parser.add_argument('section_id')
ebook_parser.add_argument('section_name')
ebook_parser.add_argument('price')

# Parser for Review model
review_parser = reqparse.RequestParser()
review_parser.add_argument('user_id')
review_parser.add_argument('rating')
review_parser.add_argument('user_review')
review_parser.add_argument('ebook_id')


# Parser for Section model
section_parser = reqparse.RequestParser()
section_parser.add_argument('name')
section_parser.add_argument('description')
section_parser.add_argument('date_created')

book_request_parser = reqparse.RequestParser()
book_request_parser.add_argument('request_id')
book_request_parser.add_argument('request_time')
book_request_parser.add_argument('return_time')
book_request_parser.add_argument('status')
book_request_parser.add_argument('user_id')
book_request_parser.add_argument('section_id')
book_request_parser.add_argument('ebook_id')
book_request_parser.add_argument('is_requested')
book_request_parser.add_argument('is_returned')
book_request_parser.add_argument('is_revoked')
book_request_parser.add_argument('is_issued')


#############################################################################################

############################################# API's ##########################################################

############################################# User API ##########################################################

class UserAPI(Resource):
    @marshal_with(user_fields)
    def get(self, id):
        user = User.query.filter_by(id=id).first()
        if user is None:
            raise NotFoundError(404, 'User not found')
        return user

    @marshal_with(user_fields)
    def put(self, id):
        args = user_parser.parse_args()
        u_name=args.get('name')
        u_password=args.get('password')
        u_username=args.get('username')
        
        us=User.query.filter_by(id=id).first()
        if us:
            us.name=u_name
            us.password=u_password
            us.username=u_username
            db.session.commit()
            return us


        user = User.query.filter_by(User.id==id,User.password==u_password,User.name==u_name,User.username==u_username).first()
        
        if user is None:
            raise NotFoundError(404, 'User not found')
        if u_name is None:
            raise NotGivenError(400, 1001, 'Name not given')
        if u_password is None:
            raise NotGivenError(400, 1002, 'Password not given')
        if u_username is None:
            raise NotGivenError(400, 1003, 'Username not given')

        else:
            raise NotGivenError(400, 1004, 'Invalid User')  

    @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()
        u_name = args.get('name')
        u_password = args.get('password')
        u_username = args.get('username')

        user = User.query.filter_by(password=u_password, name=u_name, username=u_username).first()

        if user is not None:
            raise NotFoundError(404, 'User already exists')

        if u_name is None or u_password is None or u_username is None:
            raise NotGivenError(400, 1001, 'Name, password, or username not given')

        new_user = User(name=u_name, password=u_password, username=u_username)
        db.session.add(new_user)
        db.session.commit()

        # Return the newly created user including the 'id'
        return new_user
    
    @marshal_with(user_fields)
    def delete(self, id):
        user = User.query.filter_by(id=id).first()

        if user is None:
            raise NotFoundError(404, 'User not found')

        # Check and delete associated records in BookRequest
        book_request = BookRequest.query.filter_by(user_id=user.id).first()
        if book_request:
            db.session.delete(book_request)

        # Check and delete associated records in Review
        review = Review.query.filter_by(user_id=user.id).first()
        if review:
            db.session.delete(review)

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        return user
        
################################### Librarian Api  ###########################################################################

class LibrarianAPI(Resource):
    @marshal_with(librarian_fields)
    def get(self, l_id):
        librarian = Librarian.query.filter_by(l_id=l_id).first()
        if librarian is None:
            raise NotFoundError(404, 'Librarian not found')
        return librarian
    
    @marshal_with(librarian_fields)
    def put(self, l_id):
        args = user_parser.parse_args()
        l_name = args.get('name')
        l_password = args.get('password')
        l_username = args.get('username')

        librarian = Librarian.query.get(l_id)
        if librarian is None:
            raise NotFoundError(404, 'Librarian not found')

        if l_name is None or l_password is None or l_username is None:
            raise NotGivenError(400, 1001, 'Name, password, or username not given')

        librarian.l_name = l_name
        librarian.l_password = l_password
        librarian.l_username = l_username

        db.session.commit()
        return librarian




##########################################   EBook API    #####################################################################################



class EBookAPI(Resource):
    @marshal_with(ebook_fields)
    def get(self, id):
        ebook = EBook.query.filter_by(id=id).first()
        if ebook is None:
            raise NotFoundError(404, 'EBook not found')
        return ebook

    @marshal_with(ebook_fields)
    def put(self, id):
        args = ebook_parser.parse_args()
        e_name = args.get('name')
        e_image = args.get('image')
        e_pdf = args.get('pdf')
        e_release_date_str = args.get('release_date')
        e_release_date = datetime.strptime(e_release_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        e_author_name = args.get('author_name')
        e_total_pages = args.get('total_pages')
        e_return_date_str = args.get('return_date')
        e_return_date = datetime.strptime(e_return_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        e_content = args.get('content')
        e_section_id = args.get('section_id')
        e_section_name = args.get('section_name')
        e_price = args.get('price')

        ebook = EBook.query.filter_by(id=id).first()

        if ebook is None:
            raise NotFoundError(404, 'EBook not found')

        # Update fields only if they are provided in the request
        if e_name is not None:
            ebook.name = e_name
        if e_image is not None:
            ebook.image = e_image
        if e_pdf is not None:
            ebook.pdf = e_pdf
        if e_release_date is not None:
            ebook.release_date = e_release_date
        if e_author_name is not None:
            ebook.author_name = e_author_name
        if e_total_pages is not None:
            ebook.total_pages = e_total_pages
        if e_return_date is not None:
            ebook.return_date = e_return_date
        if e_content is not None:
            ebook.content = e_content
        if e_section_id is not None:
            ebook.section_id = e_section_id
        if e_section_name is not None:
            ebook.section_name = e_section_name
        if e_price is not None:
            ebook.price = e_price

        db.session.commit()
        return ebook

        
    @marshal_with(ebook_fields)
    def delete(self, id):
        ebook = EBook.query.filter_by(id=id).first()

        if ebook is None:
            raise NotFoundError(404, 'EBook not found')

        section = Section.query.filter_by(id=ebook.section_id).first()
        book_request = BookRequest.query.filter_by(ebook_id=ebook.id).first()
        review = Review.query.filter_by(ebook_id=ebook.id).first()

        db.session.delete(ebook)

        if section:
            db.session.delete(section)
        if book_request:
            db.session.delete(book_request)
        if review:
            db.session.delete(review)

        db.session.commit()

        return ebook
    
    @marshal_with(ebook_fields)
    def post(self):
        args = ebook_parser.parse_args()
        e_name = args.get('name')
        e_image = args.get('image')
        e_pdf = args.get('pdf')
        e_release_date_str = args.get('release_date')
        e_release_date = datetime.strptime(e_release_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        e_author_name = args.get('author_name')
        e_total_pages = args.get('total_pages')
        e_return_date_str = args.get('return_date')
        e_return_date = datetime.strptime(e_return_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        e_content = args.get('content')
        e_section_id = args.get('section_id')
        e_section_name = args.get('section_name')
        e_price = args.get('price')

        # Validate required fields
        if e_name is None:
            raise NotGivenError(400, 1001, 'Name not given')
        if e_image is None:
            raise NotGivenError(400, 1002, 'Image not given')
        if e_pdf is None:
            raise NotGivenError(400, 1003, 'Pdf not given')
        if e_release_date is None:
            raise NotGivenError(400, 1004, 'Release_date not given')
        if e_author_name is None:
            raise NotGivenError(400, 1005, 'Author_name not given')
        if e_total_pages is None:
            raise NotGivenError(400, 1006, 'Total_pages not given')
        if e_return_date is None:
            raise NotGivenError(400, 1007, 'Return_date not given')
        if e_content is None:
            raise NotGivenError(400, 1008, 'Content not given')
        if e_section_id is None:
            raise NotGivenError(400, 1009, 'Section_id not given')
        if e_section_name is None:
            raise NotGivenError(400, 1010, 'Section_name not given')
        if e_price is None:
            raise NotGivenError(400, 1011, 'Price not given')

        # Create a new ebook instance
        new_ebook = EBook(name=e_name, image=e_image, pdf=e_pdf, release_date=e_release_date, author_name=e_author_name,
                          total_pages=e_total_pages, return_date=e_return_date, content=e_content, section_id=e_section_id,
                          section_name=e_section_name, price=e_price)
        
        # Add and commit the new ebook to the database
        db.session.add(new_ebook)
        db.session.commit()

        return new_ebook, 201
    
    
############################################## Review API #########################################################################################

class ReviewAPI(Resource):
    @marshal_with(review_fields)
    def get(self, id):
        review = Review.query.filter_by(id=id).first()
        if review is None:
            raise NotFoundError(404, 'Review not found')
        return review

    @marshal_with(review_fields)
    def put(self, id):
        args = review_parser.parse_args()
        r_user_id=args.get('user_id')
        r_rating=args.get('rating')
        r_user_review=args.get('user_review')
        r_ebook_id=args.get('ebook_id')
        
        review = Review.query.filter_by(id=id).first()
        if review is None:
            raise NotFoundError(404, 'Review not found')
        if r_user_id is None:
            raise NotGivenError(400, 1001, 'User_id not given')
        if r_rating is None:
            raise NotGivenError(400, 1002, 'Rating not given')
        if r_user_review is None:
            raise NotGivenError(400, 1003, 'User_review not given')
        if r_ebook_id is None:
            raise NotGivenError(400, 1004, 'Ebook_id not given')

        else:
            review.user_id=r_user_id
            review.rating=r_rating
            review.user_review=r_user_review
            review.ebook_id=r_ebook_id
            db.session.commit()
            return review
        
    @marshal_with(review_fields)
    def post(self):
        args = review_parser.parse_args()
        r_user_id = args.get('user_id')
        r_rating = args.get('rating')
        r_user_review = args.get('user_review')
        r_ebook_id = args.get('ebook_id')

        # Validate required fields
        if r_user_id is None:
            raise NotGivenError(400, 1001, 'User_id not given')
        if r_rating is None:
            raise NotGivenError(400, 1002, 'Rating not given')
        if r_user_review is None:
            raise NotGivenError(400, 1003, 'User_review not given')
        if r_ebook_id is None:
            raise NotGivenError(400, 1004, 'Ebook_id not given')

        # Create a new review instance
        new_review = Review(user_id=r_user_id, rating=r_rating, user_review=r_user_review, ebook_id=r_ebook_id)

        # Add and commit the new review to the database
        db.session.add(new_review)
        db.session.commit()

        return new_review, 201
        
    @marshal_with(review_fields)
    def delete(self, id):
        review = Review.query.filter_by(id=id).first()
        if review is None:
            raise NotFoundError(404, 'Review not found')
        db.session.delete(review)
        db.session.commit()
        return review
    
############################################## Section API #########################################################################################    
    
class SectionAPI(Resource):
    @marshal_with(section_fields)
    def get(self, id):
        section = Section.query.filter_by(id=id).first()
        if section is None:
            raise NotFoundError(404, 'Section not found')
        return section

    @marshal_with(section_fields)
    def put(self, id):
        args = section_parser.parse_args()
        s_name = args.get('name')
        s_description = args.get('description')
        s_date_created = args.get('date_created')

        if s_name is None:
            raise NotGivenError(400, 1001, 'Name not given')
        if s_description is None:
            raise NotGivenError(400, 1002, 'Description not given')
        if s_date_created is None:
            raise NotGivenError(400, 1003, 'Date_created not given')

        section = Section.query.filter_by(id=id).first()
        if section:
            section.name = s_name
            section.description = s_description
            section.date_created = datetime.strptime(s_date_created, "%Y-%m-%dT%H:%M:%SZ")
            db.session.commit()
            return section
        else:
            sec = Section.query.filter(
                Section.name == s_name,
                Section.description == s_description,
                Section.date_created == datetime.strptime(s_date_created, "%Y-%m-%dT%H:%M:%SZ")
            ).first()
            if sec is None:
                raise NotFoundError(404, 'Section not found')
            else:
                raise NotGivenError(400, 1004, 'Invalid Section')    
    
    @marshal_with(section_fields)
    def post(self):
        args = section_parser.parse_args()
        s_name = args.get('name')
        s_description = args.get('description')
        s_date_created_str = args.get('date_created')  # Get the date as a string

       
        if s_name is None:
            raise NotGivenError(400, 1001, 'Name not given')
        if s_description is None:
            raise NotGivenError(400, 1002, 'Description not given')
        if s_date_created_str is None:
            raise NotGivenError(400, 1003, 'Date_created not given')

       
        s_date_created = datetime.strptime(s_date_created_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        new_section = Section(name=s_name, description=s_description, date_created=s_date_created)
        db.session.add(new_section)
        db.session.commit()

        return new_section, 201

        
    @marshal_with(section_fields)
    def delete(self, id):
        section = Section.query.get(id)

        if section is None:
            raise NotFoundError(404, 'Section not found')

        book_requests = BookRequest.query.filter_by(section_id=section.id).all()
        for book_request in book_requests:
            db.session.delete(book_request)

        db.session.delete(section)
        db.session.commit()

        return section

    
############################################## BookRequest API #########################################################################################    
    
class BookRequestAPI(Resource):
    @marshal_with(book_request_fields)
    def get(self, id):
        book_request = BookRequest.query.filter_by(id=id).first()
        if book_request is None:
            raise NotFoundError(404, 'BookRequest not found')
        return book_request


#####################################################   API Add Resources    ###############################################   

api.add_resource(UserAPI,"/api/user/<int:id>","/api/user")
api.add_resource(LibrarianAPI,"/api/librarian/<int:l_id>","/api/librarian")
api.add_resource(EBookAPI,"/api/ebook/<int:id>","/api/ebook")
api.add_resource(ReviewAPI,"/api/review/<int:id>","/api/review")
api.add_resource(SectionAPI,"/api/section/<int:id>","/api/section")
api.add_resource(BookRequestAPI,"/api/book_request/<int:id>")


#################################################    Debug & Port    ###############################################


if __name__ == '__main__':
    
    app.run(debug=True,port=8080)


###################################################   -: API Ended :-       #################################################################