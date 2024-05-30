from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    reviews = db.relationship('Review', back_populates='reviewer', lazy=True)
    book_requests = db.relationship('BookRequest', backref='user_book_requests', lazy=True, overlaps="book_requests,user_book_requests")



class Librarian(db.Model, UserMixin):
    __tablename__ = 'librarians'
    l_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    l_username = db.Column(db.String, unique=True, nullable=False)
    l_name = db.Column(db.String, nullable=False)
    l_password = db.Column(db.String, nullable=False)

    def get_id(self):
        return str(self.l_id)



class EBook(db.Model):
    __tablename__ = 'ebook'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    image = Column(String(255), nullable=True)
    pdf = Column(String(255), nullable=False)
    release_date = Column(DateTime, nullable=False)
    author_name = Column(String(100), nullable=False)
    total_pages = Column(Integer, nullable=False)
    return_date = Column(DateTime, nullable=True)
    return_date_expected = Column(DateTime)
    content = Column(Text, nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    section = db.relationship('Section', back_populates='books', lazy=True)
    section_name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
   
    # Relationships
    reviews_relation = relationship('Review', back_populates='book_relation', lazy=True)
    book_requests = relationship('BookRequest', backref='ebook_book_requests', lazy=True, overlaps="book_requests,ebook_book_requests")
    return_time = Column(DateTime, nullable=True)
    average_rating = Column(Float, default=0)

    def calculate_average_rating(self):
        # Calculate the average rating using SQL's AVG function
        result = db.session.query(func.avg(Review.rating)).filter_by(ebook_id=self.id).scalar()

        # Update the average_rating attribute
        self.average_rating = result or 0  # If there are no reviews, set average_rating to 0
        db.session.commit()

    def recalculate_average_rating(self):
        reviews = db.session.query(Review).filter_by(ebook_id=self.id).all()
        total_rating = sum(review.rating for review in reviews)
        num_reviews = len(reviews)

        if num_reviews > 0:
            self.average_rating = total_rating / num_reviews
        else:
            self.average_rating = 0.0

        db.session.commit()

    def num_requests(self):
        return BookRequest.query.filter_by(ebook_id=self.id).count()

class Review(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', name='fk_review_user_id'), nullable=False)
    rating = Column(Integer, nullable=False)
    user_review = Column(Text, nullable=False)
    ebook_id = Column(Integer, ForeignKey('ebook.id', name='fk_review_book_id'), nullable=False)
    reviewer = relationship('User', back_populates='reviews')
    book_relation = relationship('EBook', back_populates='reviews_relation')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'ebook_id', name='unique_user_ebook_review'),
    )


class Section(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    date_created = Column(DateTime, nullable=True)


    # Relationships
    book_requests = relationship('BookRequest', backref='section_book_requests', lazy=True, overlaps="book_requests,section_book_requests")
    books = db.relationship('EBook', back_populates='section', lazy=True)
class BookRequest(db.Model):
    id = Column(Integer,autoincrement=True, primary_key=True)
    request_id= Column(String(100),unique=True, nullable=False)
    request_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    return_time = Column(DateTime, nullable=True)
    status = Column(String(20), default='requested')  
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    ebook_id = Column(Integer, ForeignKey('ebook.id'), nullable=True)
    section_id = Column(Integer, ForeignKey('section.id'), nullable=True)
    is_requested = db.Column(db.Boolean, default=False)
    is_returned = db.Column(db.Boolean, default=False)
    is_revoked= db.Column(db.Boolean, default=False)
    is_issued= db.Column(db.Boolean, default=False) 

    # Define relationships with unique backref names
    user = relationship('User', backref='user_book_requests', lazy=True, overlaps="book_requests,user_book_requests")
    ebook = relationship('EBook', backref='ebook_book_requests', lazy=True, overlaps="book_requests,ebook_book_requests")
    section = relationship('Section', backref='section_book_requests', lazy=True, overlaps="book_requests,section_book_requests")

    def __init__(self, request_id, user_id, ebook_id, section_id, return_time, request_time, status, is_requested, is_returned, is_revoked, is_issued):
        self.request_id = request_id
        self.user_id = user_id
        self.ebook_id = ebook_id
        self.section_id = section_id
        self.return_time = return_time
        self.request_time = request_time
        self.status = status
        self.is_requested = is_requested
        self.is_returned = is_returned
        self.is_revoked = is_revoked
        self.is_issued = is_issued

    @staticmethod
    def generate_request_id(user_id, book_id):
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4().hex)[:8]
        return f"{user_id}_{book_id}_{timestamp}_{unique_id}"

class Downlode(db.Model):
    id = db.Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    ebook_id = Column(Integer, ForeignKey('ebook.id'), nullable=True)
    section_id = Column(Integer, ForeignKey('section.id'), nullable=True)
    status = Column(String(20), default='Not Payed')
    is_payed = db.Column(db.Boolean, default=False)
    is_downloded = db.Column(db.Boolean, default=False)

    # Define relationships with unique backref names
    user = relationship('User', backref='user_downloads', lazy=True, overlaps="user_downloads,downlode_user")
    ebook = relationship('EBook', backref='ebook_downloads', lazy=True, overlaps="ebook_downloads,downlode_ebook")
    section = relationship('Section', backref='section_downloads', lazy=True, overlaps="section_downloads,downlode_section")

    def __init__(self, user_id, ebook_id, section_id, status, is_payed, is_downloded):
        self.user_id = user_id
        self.ebook_id = ebook_id
        self.section_id = section_id
        self.status = status
        self.is_payed = is_payed
        self.is_downloded = is_downloded

    