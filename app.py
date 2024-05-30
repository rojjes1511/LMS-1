from flask import Flask, render_template, redirect, request, flash, url_for,jsonify
from flask_login import LoginManager, login_user, login_required,current_user
from werkzeug.utils import secure_filename    
from datetime import datetime, timedelta
from matplotlib.backends.backend_agg import FigureCanvasAgg
from collections import defaultdict
import os
import plotly
from model import *
from appii import *
from flask import render_template
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from sqlalchemy import text
from sqlalchemy.orm import joinedload



app = Flask(__name__, template_folder='template')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mad1.sqlite3'
app.secret_key = 'some_secret_key'
app.config['UPLOAD_FOLDER_IMAGE'] = "static/image"
app.config['UPLOAD_FOLDER_PDF'] = "static/pdf"

api.init_app(app)
login_manager = LoginManager(app)
db.init_app(app)
app.app_context().push()

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id)) or db.session.query(Librarian).get(int(user_id))

##################################################    APP Routs    ################################################

#------------------------------------------      Home Page      -------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template("home.html")

#------------------------------------------      User Login      -------------------------------------------------------------------------# 


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == "GET":
        return render_template("user_login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if (
            len(username) >= 6 and
            any(char.islower() for char in username) and
            any(char.isupper() for char in username) and
            '@' in username
        ):
            if len(password) >= 5:
                user = User.query.filter(User.username == username, User.password == password).first()

                if user:
                    login_user(user)
                    return redirect(url_for('user', user_id=user.id))
                else:
                    flash('Invalid username or password', 'danger')
                    return render_template("user_login.html")
            else:
                flash('Password must be at least 5 characters long', 'danger')
                return render_template("user_login.html")
        else:
            flash('Invalid username format', 'danger')
            return render_template("user_login.html")


#------------------------------------------      User      -------------------------------------------------------------------------#    
        
# User profile page
@app.route('/user/<int:user_id>')
@login_required
def user(user_id):
    user = User.query.get(user_id)
    books = EBook.query.all()
    sections = Section.query.all()

    user_book_status = BookRequest.query.filter_by(user_id=current_user.id, is_requested=True).all()
    for i in user_book_status:
        if (
            i.return_time < datetime.now() and
            i.is_requested and
            not i.is_revoked and
            not i.is_returned and
            i.is_issued and
            i.status == 'issued'
        ):

            i.is_requested = False
            i.is_revoked = True
            i.is_returned = False
            i.is_issued = True
            i.status = 'revoked'
            db.session.commit()
            flash('Book request revoked due to delay in reading!', 'danger')

    top_rated_books = EBook.query.order_by(EBook.average_rating.desc()).limit(5).all()

    # Fetch top 5 requested books
    top_requested_books = (
        db.session.query(EBook, func.count(BookRequest.id).label('request_count'))
        .join(BookRequest, EBook.id == BookRequest.ebook_id)
        .group_by(EBook.id)
        .order_by(func.count(BookRequest.id).desc())
        .limit(5)
        .all()
    )
    # Fetch 5 random books
    random_books = EBook.query.order_by(func.random()).limit(5).all()

    # Fetch latest 5 books
    latest_books = EBook.query.order_by(EBook.release_date.desc()).limit(5).all()

    # Fetch all sections
    sections = Section.query.all()


    return render_template(
        'user.html',
        user=user,
        books=books,
        sections=sections,
        latest_books=latest_books,
        top_rated_books=top_rated_books,
        top_requested_books=top_requested_books,
        random_books=random_books
    )


#################################################    Librarian Routs      ##################################################################################


#------------------------------------------      Librarian Login      -------------------------------------------------------------------------#

@app.route('/librarian_login', methods=['GET', 'POST'])
def librarian_login():
    if request.method == "GET":
        return render_template("librarian_login.html")

    if request.method == "POST":
        username = request.form.get('l_username')
        password = request.form.get('l_password')

        librarian = Librarian.query.filter(Librarian.l_username == username, Librarian.l_password == password).first()

        if librarian:
            login_user(librarian)
            return redirect(url_for('librarian', librarian_id=librarian.l_id))
        else:
            flash('Invalid username or password', 'danger')
            return render_template("librarian_login.html")



#------------------------------------------      Librarian      -------------------------------------------------------------------------#


# Librarian profile page
@app.route('/librarian/<int:librarian_id>')
def librarian(librarian_id):
    librarian = db.session.get(Librarian, librarian_id)


    if librarian:
        books = EBook.query.all()  # Fetch all books or modify the query as needed
        sections = Section.query.all()  # Fetch all sections or modify the query as needed

        return render_template('librarian.html', librarian=librarian, books=books, sections=sections)
    else:
        flash('Librarian not found.', 'error')
        return redirect(url_for('librarian_login'))


#################################################    Login Routs      ##################################################################################


#------------------------------------------      User Login      -------------------------------------------------------------------------#

@app.route('/user_login/user_registration', methods=['GET', 'POST'])
def user_registration():
    if request.method == "GET":
        return render_template("user_registration.html")

    if request.method == "POST":
        username = str(request.form.get('username'))
        password = str(request.form.get('password'))
        name = str(request.form.get('name'))

        # Check if the username meets the criteria
        if (
            len(username) >= 6 and
            any(char.islower() for char in username) and
            any(char.isupper() for char in username) and
            '@' in username
        ):
            if len(password) >= 5:
                if name.strip():
                    existing_user = User.query.filter((User.username == username) | (User.name == name)).first()

                    if existing_user:
                        flash('Username or email already exists', 'danger')
                        return redirect(url_for("user_registration"))

                    new_user = User(username=username, name=name, password=password)
                    db.session.add(new_user)
                    db.session.commit()

                    flash('User registered successfully!', 'success')
                    return redirect(url_for("user_login"))
                else:
                    flash('Name cannot be empty', 'danger')
            else:
                flash('Password must be at least 5 characters long', 'danger')

        else:
            flash('Invalid username format', 'danger')

        return redirect(url_for("user_registration"))
    

#------------------------------------------      Librarian Login      -------------------------------------------------------------------------#

@app.route('/librarian_login/librarian_registration', methods=['GET', 'POST'])
def librarian_registration():
    if request.method == "GET":
        return render_template("librarian_registration.html")

    if request.method == "POST":
        username = str(request.form.get('l_username'))
        password = str(request.form.get('l_password'))
        name = str(request.form.get('l_name'))

        existing_user = Librarian.query.filter((Librarian.l_username == username) | (Librarian.l_name == name)).first()

        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for("librarian_registration"))

        new_user = Librarian(l_username=username, l_name=name, l_password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully!', 'success')
        return redirect(url_for("librarian_login"))



#################################################    User Functions Routs      ##################################################################################
from flask import send_from_directory
@app.route('/read_book/<int:book_id>', methods=['GET'])
@login_required
def read_book(book_id):
    book = EBook.query.get(book_id)

    if not book:
        # Handle the case where the book is not found
        return redirect(url_for('error_page'))

    pdf_filename = secure_filename(os.path.basename(book.pdf))

    return send_from_directory(app.static_folder, f'pdf/{pdf_filename}', as_attachment=False, mimetype='application/pdf')


###############################################  Downlode Book   #########################################################################
def get_section_id(book_id):
    book= EBook.query.get(book_id)
    return book.section_id



@app.route('/pdf/<int:book_id>', methods=['GET', 'POST'])
@login_required
def pdf(book_id):
    book = EBook.query.get(book_id)
    download = Downlode.query.filter_by(user_id=current_user.id, ebook_id=book_id).first()

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'pay':
            if not download:
                # Create a new record if it doesn't exist
                download = Downlode(user_id=current_user.id, section_id=get_section_id(book_id), ebook_id=book_id, status='Not Payed', is_payed=False, is_downloded=False)

                db.session.add(download)
            else:
                download.is_payed = True
                download.is_downloded = False
                download.user_id = current_user.id
                download.ebook_id = book_id
                download.section_id = get_section_id(book_id)
                download.status = 'payed'

            db.session.commit()
            flash('Payment successful!', 'success')

        elif action == 'download' and download and download.is_payed and not download.is_downloded:
            download.is_downloded = True
            download.user_id = current_user.id
            download.ebook_id = book_id
            download.section_id = get_section_id(book_id)
            download.status = 'downloaded'
            db.session.commit()
            flash('Download successful!', 'success')

    return render_template("pdf.html", user=current_user, book=book, is_downloaded=download.is_downloded if download else False)

       
@app.route('/download/<int:book_id>')
@login_required
def download(book_id):
    book= EBook.query.get(book_id)
    if not book:
        # Handle the case where the book is not found
        return redirect(url_for('error_page'))
    
    pdf_filename = secure_filename(os.path.basename(book.pdf))
    return send_from_directory(app.static_folder, f'pdf/{pdf_filename}', as_attachment=True, mimetype='application/pdf')

#------------------------------------------      User book     -------------------------------------------------------------------------#

@app.route('/user_login/user/u_ebook', methods=['GET', 'POST'])
@login_required
def u_ebook():
    if request.method == "GET":
        return render_template("u_ebook.html",user=current_user,books=EBook.query.all())

    if request.method == "POST":
        return redirect(url_for("u_ebook"))


#------------------------------------------      User section     -------------------------------------------------------------------------#


@app.route('/user_login/user/u_section', methods=['GET', 'POST'])
@login_required
def u_section():
    if request.method == "GET":
        return render_template("u_section.html", user=current_user,books=EBook.query.all(), sections=Section.query.all())

    if request.method == "POST":

        return redirect(url_for("u_section"))


#------------------------------------------      User book detail of Section    -------------------------------------------------------------------------#


@app.route('/section_books/<int:id>', methods=['GET', 'POST'])
@login_required
def section_books(id):
    if request.method == "GET":
        # Use print statement to debug and check the queried books for the given section
        books = EBook.query.filter_by(section_id=id).all()

        print("Queried Books:", books)

        return render_template("section_books.html", user=current_user, books=books, section_id=id, sections=Section.query.all())

    if request.method == "POST":
        return redirect(url_for("section_books"))


#------------------------------------------      User  detail of Returned books    -------------------------------------------------------------------------#

@app.route('/user_login/user/u_returned', methods=['GET', 'POST'])
@login_required
def u_returned():
    if request.method == "GET":
        # Query user-returned books
        user_returned_books = BookRequest.query.filter_by(user_id=current_user.id, is_returned=True).all()

        return render_template("u_returned.html", user=current_user, user_returned_books=user_returned_books)

    if request.method == "POST":
        return redirect(url_for("u_returned"))


#------------------------------------------      User  detail of Revoked books    -------------------------------------------------------------------------#


@app.route('/user_login/user/u_revoked', methods=['GET', 'POST'])
@login_required
def u_revoked():
    if request.method == "GET":

        user_revoked_books = BookRequest.query.filter_by(user_id=current_user.id, is_revoked=True).all()

        return render_template("u_revoked.html",user=current_user,books=EBook.query.all(),user_revoked_books=user_revoked_books)

    if request.method == "POST":
        return redirect(url_for("u_revoked"))


########################################################   Librarian functionality    ############################################################# 


#---------------------------------------------------------   Librarian All Books    -----------------------------------------------------------------------------#

@app.route('/librarian_login/librarian/l_ebook', methods=['GET', 'POST'])
@login_required
def l_ebook():
    if request.method == "GET":
        return render_template("l_ebook.html",librarian=Librarian.query.all(),books=EBook.query.all())
    
    if request.method == "POST":
        return redirect(url_for("l_ebook"))


#---------------------------------------------------------   Librarian All Sections    -----------------------------------------------------------------------------#


@app.route('/librarian_login/librarian/l_section', methods=['GET', 'POST'])
@login_required
def l_section():
    if request.method == "GET":
        return render_template("l_section.html",librarian=Librarian.query.all(),sections=Section.query.all())
    
    if request.method == "POST":
        return redirect(url_for("l_section"))


#---------------------------------------------------------   Librarian All Users Returned Books    -----------------------------------------------------------------------------#


@app.route('/librarian_login/librarian/l_returned', methods=['GET', 'POST'])
@login_required
def l_returned():
    if request.method == "GET":
        # Query relevant information about returned books
        book_status = BookRequest.query.join(EBook).filter(
            BookRequest.is_returned == True,
            BookRequest.is_requested == False,
            BookRequest.is_revoked == False
        ).all()

        book_status = [
            {
                'id': i.ebook_id,
                'request_id': i.request_id,
                'user_id': i.user_id,
                'bookname': EBook.query.get(i.ebook_id).name,
                'returned_by': User.query.get(i.user_id).name,
                'return_date_expected': i.return_time,
                'is_requested': "✔" if i.is_requested else  "❌",
                'is_issued': "✔" if i.is_issued else  "❌",
                'is_returned': "✔" if i.is_returned else  "❌",
                'is_revoked': "✔" if i.is_revoked else  "❌",
            } for i in book_status
        ]

        for s in book_status:
            ebook = EBook.query.get(s['id'])
            ebook.calculate_average_rating()
            s['average_rating'] = ebook.average_rating
            # Include the book image URL
            s['image_url'] = ebook.image

        return render_template("l_returned.html", librarian=current_user, book_status=book_status)

    if request.method == "POST":
        return redirect(url_for("l_returned"))


#---------------------------------------------------------   Librarian All Users Revoked Books    -----------------------------------------------------------------------------#

@app.route('/librarian_login/librarian/l_revoked', methods=['GET', 'POST'])
@login_required
def l_revoked():
    if request.method == "GET":
        
        # Query relevant information about returned books
        book_status = BookRequest.query.join(EBook).filter(
            BookRequest.is_returned == False,
            BookRequest.is_requested == False,
            BookRequest.is_revoked == True
        ).all()

        book_status = [
            {
                'id': i.ebook_id,
                'request_id': i.request_id,
                'user_id': i.user_id,
                'bookname': EBook.query.get(i.ebook_id).name,
                'returned_by': User.query.get(i.user_id).name,
                'return_date_expected': i.return_time,
                'is_requested': "✔" if i.is_requested else  "❌",
                'is_issued': "✔" if i.is_issued else  "❌",
                'is_returned': "✔" if i.is_returned else  "❌",
                'is_revoked': "✔" if i.is_revoked else  "❌",
            } for i in book_status
        ]

        for s in book_status:
            ebook = EBook.query.get(s['id'])
            ebook.calculate_average_rating()
            s['average_rating'] = ebook.average_rating
            # Include the book image URL
            s['image_url'] = ebook.image

        return render_template("l_revoked.html",librarian=Librarian.query.all(),books=EBook.query.all(),book_status=book_status)
    
    if request.method == "POST":
        return redirect(url_for("l_revoked"))
    


#################################### Add section and book ##################################################################
    

#------------------------------------------      Add section     -------------------------------------------------------------------------#


@app.route('/librarian_login/librarian/add_section', methods=['GET', 'POST'])
@login_required
def add_section():
    if request.method == "GET":
        return render_template("add_section.html",librarian=Librarian.query.all())
    
    if request.method == "POST":
        name = str(request.form.get('name'))
        description = str(request.form.get('description'))
        date_created = datetime.now()
        new_section = Section(name=name, description=description, date_created=date_created)
        db.session.add(new_section)
        db.session.commit()

        flash('Section added successfully!', 'success')
        return redirect(url_for("add_section"))
    

#------------------------------------------      Add book     -------------------------------------------------------------------------#


@app.route('/librarian_login/librarian/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == "GET":
        # Your logic for handling GET requests
        return render_template("add_book.html", librarian=librarian, sections=Section.query.all())

    if request.method == "POST":
        # Logic for handling POST requests
        release_date_str = request.form.get('release_date')
        return_date_str = request.form.get('return_date')

        # Validate date formats
        try:
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return render_template("add_book.html", sections=Section.query.all())

        # Validate file uploads
        if 'image' not in request.files or 'pdf' not in request.files:
            flash('Both image and PDF files are required.', 'error')
            return render_template("add_book.html", sections=Section.query.all())

        image_file = request.files['image']
        pdf_file = request.files['pdf']

        if image_file.filename == '' or pdf_file.filename == '':
            flash('Both image and PDF files are required.', 'error')
            return render_template("add_book.html", sections=Section.query.all())

        # Add more specific validation for image and PDF file types if needed

        # Validate other form fields
        if not all([request.form.get('name'), request.form.get('author_name'),
                    request.form.get('total_pages'), request.form.get('content'),
                    request.form.get('section'), request.form.get('price')]):
            flash('All fields must be filled out.', 'error')
            return render_template("add_book.html", sections=Section.query.all())


        # Save uploaded files to the server
        image_filename = secure_filename(image_file.filename)
        pdf_filename = secure_filename(pdf_file.filename)

        # Ensure the directories exist
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], 'image'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER_PDF'], 'pdf'), exist_ok=True)

        image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], 'image', image_filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER_PDF'], 'pdf', pdf_filename)

        image_url = url_for('static', filename=f'image/{image_filename}')
        pdf_url = url_for('static', filename=f'pdf/{pdf_filename}')

        image_file.save(image_path)
        pdf_file.save(pdf_path)

        name = request.form.get('name')
        author_name = request.form.get('author_name')
        total_pages = request.form.get('total_pages')
        content = request.form.get('content')
        section_id = request.form.get('section')
        section = Section.query.get(section_id)
        section_name = section.name if section else None

        price = request.form.get('price')

        # Create a new EBook object using the file paths
        new_book = EBook(
            name=name,
            image=image_url,
            pdf=pdf_url,
            release_date=release_date,
            author_name=author_name,
            total_pages=total_pages,
            return_date=return_date,
            content=content,
            section_id=section_id,
            section_name=section_name,
            price=price
        )

        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for("add_book"))

    # Render the form for GET requests
    return render_template("add_book.html", sections=Section.query.all())


########################### Edit section and book #########################################

#---------------------------------------    Edit Book        -----------------------------------------------------------------------------#


@app.route('/librarian_login/librarian/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = EBook.query.get(book_id)
    sections = Section.query.all()

    if request.method == 'POST':
        book.name = request.form['name']

        # Process image update
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                # Handle image upload and update
                image_filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], 'image', image_filename)
                image_url = url_for('static', filename=f'image/{image_filename}')
                image_file.save(image_path)
                book.image = image_url

        # Process document update
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename != '':
                # Handle document upload and update
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER_PDF'], 'pdf', pdf_filename)
                pdf_url = url_for('static', filename=f'pdf/{pdf_filename}')
                pdf_file.save(pdf_path)
                book.pdf = pdf_url

        book.author_name = request.form['author_name']
        book.total_pages = request.form['total_pages']
        book.content = request.form['content']
        release_date_str = request.form['release_date']
        return_date_str = request.form['return_date']

        book.release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
        book.return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        # Process section update
        section_id = request.form['section']
        book.section = Section.query.get(section_id)
        book.section_name = book.section.name


        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('edit_book', book_id=book.id))

    return render_template('edit_book.html', book=book, sections=sections)





@app.route('/librarian_login/librarian/edit_section/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    section = Section.query.get(section_id)

    if request.method == 'POST':
        # Update section details based on the form submission
        section.name = request.form['name']
        section.description = request.form['description']
        # Update other fields as needed

        db.session.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('edit_section', section_id=section.id))

    return render_template('edit_section.html', section=section)

@app.route('/librarian_login/librarian/edit_selection', methods=['GET', 'POST'])
def edit_selection():
    if request.method == 'POST':
        selected_item_id = request.form.get('selected_item_id')
        selected_item_type = request.form.get('selected_item_type')

        if selected_item_type == 'book':
            return redirect(url_for('edit_book', book_id=selected_item_id))
        elif selected_item_type == 'section':
            return redirect(url_for('edit_section', section_id=selected_item_id))

    # Fetch the list of books and sections
    books = EBook.query.all()
    sections = Section.query.all()
    
    return render_template('edit_selection.html', books=books, sections=sections)


########################### Delete section and book #########################################


@app.route('/librarian_login/librarian/delet_book', methods=['GET', 'POST'])
def delet_book():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        book = EBook.query.get(book_id)
        if book:
            db.session.delete(book)
            db.session.commit()
            flash('Book deleted successfully!', 'success')
        else:
            flash('Book not found!', 'error')
    books = EBook.query.all()
    return render_template('delet_book.html', books=books)

# In your app.py file
@app.route('/librarian_login/librarian/delet_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = db.session.get(EBook, book_id)


    if book:
        # Delete associated book requests
        bookr=BookRequest.query.filter_by(ebook_id=book_id).all()
        for i in bookr:
            db.session.delete(i)
            db.session.commit()
        
        # Delete associated reviews
        review=Review.query.filter_by(ebook_id=book_id).all()
        for i in review:
            db.session.delete(i)
            db.session.commit()
        # Delete the rating
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    else:
        flash('Book not found!', 'error')

    return redirect(url_for('delet_book'))


@app.route('/librarian_login/librarian/delet_section', methods=['GET', 'POST'])
def delet_section():
    if request.method == 'POST':
        # Handle the deletion logic here (replace this with your actual logic)
        # Get the section_id from the form data
        section_id = request.form.get('section_id')

        if section_id:
            # Delete the section with the given section_id
            section = Section.query.get(section_id)
            if section:
                db.session.delete(section)
                db.session.commit()
                flash('Section deleted successfully!', 'success')
            else:
                flash('Section not found!', 'error')
        else:
            flash('Invalid section ID!', 'error')

        # After deletion, you might want to redirect to a different page
        return redirect(url_for('delet_section'))

    # Fetch the list of sections from the database
    sections = Section.query.all()

    return render_template('delet_section.html', sections=sections)


@app.route('/librarian_login/librarian/delete_section/<int:section_id>', methods=['GET', 'POST'])
@login_required
def delete_section(section_id):
    if request.method == 'POST':
        try:
            # Get the section from the database
            section = Section.query.get(section_id)

            if section:
                # Delete associated books
                EBook.query.filter_by(section_id=section_id).delete()

                # Delete the section
                db.session.delete(section)
                db.session.commit()
                flash('Section and associated books deleted successfully!', 'success')
            else:
                flash('Section not found!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting section and books: {str(e)}', 'error')

        return redirect(url_for('delete_section', section_id=section_id))  # Redirect to the same section after deletion

    # Rest of your code for handling GET requests
    sections = Section.query.all()
    return render_template('delet_section.html', sections=sections, selected_section_id=section_id)  # Use a different name to avoid conflict


########################### View section and book #########################################


@app.route('/user_login/user/book_detail/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book_detail(book_id):
    user = current_user
    ebook = EBook.query.get(book_id)

    if not ebook:
        flash('Book not found.', 'danger')
        return redirect(url_for('home'))

    user_book_status = BookRequest.query.filter_by(ebook_id=ebook.id, user_id=user.id).all()
    if user_book_status:
        user_book_status = user_book_status[-1]
    else:
        user_book_status = None

    if request.method == 'POST':
        # Handle the review submission
        user_rating = int(request.form.get('userRating'))
        user_review = request.form.get('userReview')
        

        new_review = Review(user_id=user.id, ebook_id=ebook.id, rating=user_rating, user_review=user_review)
        db.session.add(new_review)
        db.session.commit()

        # Recalculate average rating and update the ebook instance
        ebook.recalculate_average_rating()

        flash('Review submitted successfully!', 'success')

    # Check user book status after processing the review
    if user_book_status:
        is_requested = user_book_status.is_requested
        is_revoked = user_book_status.is_revoked
        is_returned = user_book_status.is_returned
        is_issued= user_book_status.is_issued
    else:
        is_requested = False
        is_revoked = False
        is_returned =False
        is_issued=False

    return render_template('book_detail.html', user=user, book=ebook, is_requested=is_requested, is_revoked=is_revoked,
                           is_returned=is_returned,is_issued=is_issued, average_rating=ebook.average_rating, section=Section.query.all())
    

@app.route('/bookrequest/<id>', methods=['GET', 'POST'])
@login_required
def bookrequest(id):
    ebook = EBook.query.get(id)

    if request.method == 'GET':
        user_book_status_count = BookRequest.query.filter_by(user_id=current_user.id, is_returned=False,is_revoked=False).count()
        if user_book_status_count >= 5:
            flash('You cannot request more than 5 books at a time!', 'danger')
            return render_template('bookrequestconfirm.html', book=ebook, book_id=id, disabled=True)
        else:
            return render_template('bookrequestconfirm.html', book=ebook, book_id=id)

    if request.method == 'POST':
        request_id = BookRequest.generate_request_id(current_user.id, id)
        return_time_str = request.form.get('return_time')
        return_time = datetime.strptime(return_time_str, '%Y-%m-%dT%H:%M') if return_time_str else datetime.now()

        # Check if the request already exists
        user_b_status = BookRequest.query.filter_by(request_id=request_id,user_id=current_user.id, ebook_id=id).first()

        if user_b_status:
            flash('Book request already exists!', 'warning')
        else:
            # Create a new request
            user_b_status = BookRequest(
                request_id=request_id,
                user_id=current_user.id,
                ebook_id=id,
                section_id=ebook.section_id,
                return_time=return_time,
                request_time=datetime.now(),
                is_requested=True,
                is_revoked=False,
                is_returned=False,
                is_issued=False,
                status='requested'
            )

            db.session.add(user_b_status)
            db.session.commit()
            flash('Book requested successfully!', 'success')

        return redirect(url_for('book_detail', book_id=id))

    return redirect(url_for('book_detail', book_id=id))


@app.route('/user/requested_book', methods=['GET', 'POST'])
@login_required
def requested_book():
    if request.method == "GET":
        user_book_statuss=BookRequest.query.filter_by(user_id=current_user.id).all()
        status=[]
        for i in user_book_statuss:
            s={}
            s['id']=i.ebook_id
            ebook = EBook.query.get(i.ebook_id)
            if ebook:
                s['bookname'] = ebook.name
            else:
                s['bookname'] = "Unknown Book"
            s['return_date_expected']=i.return_time
            s['is_requested']= "✔" if i.is_requested else "❌"
            s['is_issued'] = "✔" if i.is_issued else "❌"
            s['is_returned'] = "✔" if i.is_returned else "❌"
            s['is_revoked'] = "✔" if i.is_revoked else "❌"
            status.append(s)
        return render_template("requested_book.html",user=current_user,user_book_statuss=status)

@app.route('/current_status', methods=['GET', 'POST'])
@login_required
def current_status():
    if request.method == 'GET':
        user = current_user
        user_book_status = BookRequest.query.filter_by(user_id=user.id).all()
        status = []
        for i in user_book_status:
            s = {}
            s['id'] = i.ebook_id
            s['section_id'] = i.section_id
            ebook = EBook.query.get(i.ebook_id)
            if ebook:
                s['bookname'] = ebook.name
            else:
                s['bookname'] = "Unknown Book"
            s['return_date_expected'] = i.return_time
            s['is_requested'] = "✔" if i.status == "requested" else "❌"
            s['is_issued'] = "✔" if i.status == "issued" else "❌"
            s['is_returned'] = "✔" if i.is_returned else "❌"
            s['is_revoked'] = "✔" if i.status == "revoked" else"❌"
            status.append(s)
        return render_template('current_status.html', user_book_status=status)

    if request.method == 'POST':
        return redirect(url_for('current_status'))



@app.route('/current_status_librarian', methods=['GET', 'POST'])
@login_required
def current_status_librarian():
    if request.method == 'GET':
        user = Librarian.query.get(current_user.id)

        # Retrieve book status with details
        book_requests = BookRequest.query.all()
        book_status = []

        for i in book_requests:
            s = {}
            s['id'] = i.ebook_id
            s['request_id'] = i.request_id
            s['user_id'] = i.user_id
            ebook = EBook.query.get(i.ebook_id)

            # Check if ebook exists before accessing its properties
            if ebook:
                s['bookname'] = ebook.name
                # Calculate the average rating using the model method
                ebook.calculate_average_rating()
                s['average_rating'] = ebook.average_rating
                # Include the book image URL
                s['image_url'] = ebook.image
            else:
                s['bookname'] = "Unknown Book"
                s['average_rating'] = None
                s['image_url'] = None

            s['issued_to'] = User.query.get(i.user_id).name
            s['return_date_expected'] = i.return_time
            s['is_requested'] = "✔" if i.status == 'requested' else "❌"
            s['is_returned'] = "✔" if i.status == 'returned' else "❌"
            s['is_revoked'] = "✔" if i.status == 'revoked' else "❌"
            s['is_issued'] = "✔" if i.status == 'issued' else "❌"

            book_status.append(s)

        # Retrieve the most requested book
        most_requested_book = (
            db.session.query(EBook)
            .join(BookRequest, EBook.id == BookRequest.ebook_id)
            .group_by(EBook.id)
            .order_by(func.count(BookRequest.ebook_id).desc())
            .first()
        )
        num_requests = BookRequest.query.filter_by(ebook_id=most_requested_book.id).count()
        most_requested_book.num_requests = num_requests
        # Retrieve the book with the highest average rating
        highest_rated_book = (
            db.session.query(EBook)
            .order_by(func.coalesce(EBook.average_rating, 0).desc())
            .first()
        )

        return render_template(
            'current_status_librarian.html',
            librarian=user,
            book_status=book_status,
            most_requested_book=most_requested_book,
            highest_rated_book=highest_rated_book
        )

    if request.method == 'POST':
        return redirect(url_for('current_status_librarian'))



@app.route('/user_login/user/request_read/<int:book_id>', methods=['POST'])
@login_required
def request_read(book_id):
    user = current_user
    ebook = EBook.query.get(book_id)

    if not ebook:
        flash('Book not found.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            return_time = datetime.utcnow() + timedelta(days=30)

            # Generate a unique request ID
            request_id = BookRequest.generate_request_id(user.id, ebook.id)

            # Create a book request
            book_request = BookRequest(
                request_id=request_id,
                user_id=user.id,
                ebook_id=ebook.id,
                section_id=ebook.section_id,
                return_time=return_time,
                request_time=datetime.utcnow(),
                status='requested',
                is_requested=True,
                is_revoked=False,
                is_returned=False,
                is_issued=False
            )

            db.session.add(book_request)
            db.session.commit()

            flash('Request submitted successfully! Book will be available for read after approval.', 'success')

        except ValueError:
            flash('Error submitting request. Please check your input.', 'danger')

    return redirect(url_for('book_detail', book_id=ebook.id))

@app.route('/issuedbooks')
@login_required
def issuedbooks():
    book_requests = BookRequest.query.all()

    book_status = []

    for i in book_requests:
        s = {}
        s['id'] = i.ebook_id
        s['request_id'] = i.request_id
        s['user_id'] = i.user_id
        ebook = EBook.query.get(i.ebook_id)
        if ebook:
            s['bookname'] = ebook.name
        else:
            s['bookname'] = "Unknown Book"
        s['issued_to'] = User.query.get(i.user_id).name
        s['return_date_expected'] = i.return_time
        s['is_returned'] = "✔" if i.status == 'returned' else "❌"
        s['is_revoked'] = "✔" if i.status == 'revoked' else "❌"
        s['is_requested'] = "✔" if i.status == 'requested' else "❌"
        s['is_issued'] = "✔" if i.is_issued else "❌"

        book_status.append(s)

    return render_template('issue_book.html', book_status=book_status)


@app.route('/librarian/issue/<string:request_id>')
def issue(request_id):
    user_book_status = BookRequest.query.filter_by(request_id=request_id).first()

    if not user_book_status:
        flash('Book request not found.', 'danger')
        return redirect(url_for('current_status_librarian'))

    # Calculate the duration (request_time - return_time) and update return_time accordingly
    duration =user_book_status.return_time - user_book_status.request_time
    return_time_expected = datetime.now() + duration

    user_book_status.is_requested = True
    user_book_status.is_revoked = False
    user_book_status.is_returned = False
    user_book_status.is_issued = True
    user_book_status.status = 'issued'
    user_book_status.return_time = return_time_expected  # Update return_time

    db.session.commit()

    flash('Book issued successfully!', 'success')
    return redirect(url_for('current_status_librarian'))

@app.route('/user_login/user/return_book/<int:book_id>')
@login_required
def return_book(book_id):
    user = current_user
    ebook = EBook.query.get(book_id)

    if not ebook:
        flash('Book not found.', 'danger')
        return redirect(url_for('home'))

    user_book_status = BookRequest.query.filter_by(ebook_id=ebook.id, user_id=user.id).all()
    if user_book_status!=[]:
        user_book_status = user_book_status[-1]
    if not user_book_status:
        flash('Book not found in your account.', 'danger')
        return redirect(url_for('current_status'))
    user_book_status.is_requested =False
    user_book_status.is_returned = True
    user_book_status.is_revoked=False
    user_book_status.is_issued=True

    db.session.commit()
    book_request = BookRequest.query.filter_by(ebook_id=ebook.id, user_id=user.id).all()
    if book_request!=[]:
        book_request = book_request[-1]
    if book_request:
        book_request.status = 'returned'
        db.session.commit()
    
    flash('Book returned successfully!', 'success')
    return redirect(url_for('current_status'))

@app.route('/librarian/revoke/<string:request_id>')
def revoke(request_id):
    
    user_book_status = BookRequest.query.filter_by(request_id=request_id).first()

    if not user_book_status:
        flash('Book not found in user account.', 'danger')
        return redirect(url_for('current_status_librarian'))
    
    user_book_status.is_requested = False
    user_book_status.is_revoked =True
    user_book_status.is_issued = True
    user_book_status.is_returned = False
    user_book_status.status = 'revoked'
    
    db.session.commit()
   
    flash('Book revoked successfully!', 'success')
    return redirect(url_for('current_status_librarian'))

@app.route('/u_search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query', default='', type=str)
    sections = Section.query.filter(Section.name.ilike(f"%{query}%")).all()
    books = EBook.query.filter(
        (EBook.name.ilike(f"%{query}%")) |
        (EBook.author_name.ilike(f"%{query}%")) 
    ).all()

    return render_template('u_search.html',user=current_user, query=query, sections=sections, books=books)

@app.route('/l_search', methods=['GET', 'POST'])
def l_search():
    query = request.args.get('query', default='', type=str)
    sections = Section.query.filter(Section.name.ilike(f"%{query}%")).all()
    books = EBook.query.filter(
        (EBook.name.ilike(f"%{query}%")) |
        (EBook.author_name.ilike(f"%{query}%")) 
    ).all()

    return render_template('l_search.html', query=query, sections=sections, books=books)


@app.route('/u_stat', methods=['GET', 'POST'])
@login_required
def u_stat():
    if request.method == 'GET':
        user = current_user
        user_book_status = BookRequest.query.filter_by(user_id=user.id).all()
        total_requests = BookRequest.query.filter_by(user_id=user.id).count()
        total_returned = BookRequest.query.filter_by(user_id=user.id, is_returned=True).count()
        total_revoked = BookRequest.query.filter_by(user_id=user.id, is_revoked=True).count()
        # Create a dictionary to store the count of requests for each eBook
        ebook_counts = defaultdict(int)

        # Create a dictionary to store the count of requests for each section
        section_counts = defaultdict(int)

        for book_request in user_book_status:
            if book_request.ebook:
                ebook_counts[book_request.ebook.name] += 1
            if book_request.section:
                section_counts[book_request.section.name] += 1

        # Prepare data for plotting eBook usage
        ebook_names = list(ebook_counts.keys())
        ebook_request_counts = list(ebook_counts.values())

        # Generate and save the eBook usage bar chart
        fig_ebook, ax_ebook = plt.subplots()
        ax_ebook.bar(ebook_names, ebook_request_counts)
        ax_ebook.set_xlabel('EBook Names')
        ax_ebook.set_ylabel('Number of Requests')
        ax_ebook.set_title('Number of Requests per EBook')
        ax_ebook.tick_params(axis='x', rotation=45)

        # Save the eBook usage plot to a BytesIO object
        img_buf_ebook = BytesIO()
        FigureCanvasAgg(fig_ebook).print_png(img_buf_ebook)
        img_buf_ebook.seek(0)

        # Embed the eBook usage plot in the HTML template
        plot_url_ebook = base64.b64encode(img_buf_ebook.getvalue()).decode('utf-8')

        # Prepare data for plotting section usage
        section_names = list(section_counts.keys())
        section_request_counts = list(section_counts.values())

        # Generate and save the section usage pie chart
        fig_section, ax_section = plt.subplots()
        ax_section.pie(section_request_counts, labels=section_names, autopct='%1.1f%%', startangle=90)
        ax_section.set_title('User Requests by Section')

        # Save the section usage plot to a BytesIO object
        img_buf_section = BytesIO()
        FigureCanvasAgg(fig_section).print_png(img_buf_section)
        img_buf_section.seek(0)

        # Embed the section usage plot in the HTML template
        plot_url_section = base64.b64encode(img_buf_section.getvalue()).decode('utf-8')

        return render_template('u_stat.html',
                               total_requests=total_requests,
                                 total_returned=total_returned,
                                    total_revoked=total_revoked,
                                user=current_user, plot_url_ebook=plot_url_ebook, plot_url_section=plot_url_section)






@app.route('/l_stat', methods=['GET', 'POST'])
@login_required
def l_stat():
    if request.method == 'GET':
        book_requests = BookRequest.query.all()
        sections = Section.query.all()
        total_users = User.query.count()
        total_books = EBook.query.count()
        total_sections = Section.query.count()
        total_book_requests = BookRequest.query.count()

        # Retrieve all book requests
        all_book_requests = BookRequest.query.options(joinedload(BookRequest.ebook), joinedload(BookRequest.section)).all()

        # Create a dictionary to store the count of requests for each eBook
        ebook_counts = defaultdict(int)
        for book_request in all_book_requests:
            if book_request.ebook:
                ebook_counts[book_request.ebook.name] += 1

        # Prepare data for plotting eBook requests
        all_books = EBook.query.all()

        # Create a dictionary to store the count of requests for each book
        book_request_counts = defaultdict(int)
        for book_request in all_book_requests:
            if book_request.ebook:
                book_name = book_request.ebook.name if book_request.ebook else "Unknown Book"
                book_request_counts[book_name] += 1

        # Prepare data for plotting book request counts
        book_names = [book.name for book in all_books]
        book_request_values = [book_request_counts[book.name] for book in all_books]

        # Generate the book request counts bar chart using Plotly
        book_request_fig = go.Figure(go.Bar(x=book_names, y=book_request_values))
        book_request_fig.update_layout(title='Number of Requests per Book', xaxis_title='Book Names', yaxis_title='Number of Requests')

        # Create a dictionary to store the average ratings for each eBook
        ebook_avg_ratings = defaultdict(float)

        for ebook in EBook.query.all():
            ebook_avg_ratings[ebook.name] = ebook.average_rating

        # Prepare data for plotting average ratings
        avg_rating_names = list(ebook_avg_ratings.keys())
        avg_rating_values = list(ebook_avg_ratings.values())

        # Generate the average ratings bar chart using Plotly
        avg_rating_fig = go.Figure(go.Bar(x=avg_rating_names, y=avg_rating_values))
        avg_rating_fig.update_layout(title='Average Rating per EBook', xaxis_title='EBook Names', yaxis_title='Average Rating')

        # Create a subplot with two charts side by side
        subplot_fig = make_subplots(rows=1, cols=2, subplot_titles=['Number of Requests per EBook', 'Average Rating per EBook'])
        subplot_fig.add_trace(book_request_fig['data'][0], row=1, col=1)
        subplot_fig.add_trace(avg_rating_fig['data'][0], row=1, col=2)

        # Create a line chart for user duration
        user_durations = []

        for book_request in all_book_requests:
            if book_request.return_time:
                duration = book_request.return_time - book_request.request_time
                user_durations.append(duration.total_seconds() / 3600)  # Convert to hours

        # Calculate total duration in hours for each user
        # Calculate total duration in hours for each user
        user_durations = db.session.query(User.username, func.sum((func.strftime('%s', BookRequest.return_time) - func.strftime('%s', BookRequest.request_time)) / 3600.0)) \
                                    .join(BookRequest, User.id == BookRequest.user_id) \
                                    .group_by(User.username) \
                                    .all()

        # Create a bar chart for user duration
        user_duration_fig = go.Figure(go.Bar(x=[username for username, _ in user_durations],
                                            y=[total_duration for _, total_duration in user_durations],
                                            name='User Duration'))

        user_duration_fig.update_layout(title='Overall User Duration',
                                        xaxis_title='Users',
                                        yaxis_title='Total Duration (Hours)')

        sections = Section.query.all()  # Assuming you want to display data for all sections
        section_counts = defaultdict(int)

        for book_request in all_book_requests:
            if book_request.section:
                section_counts[book_request.section.name] += 1

        section_doughnut_fig = go.Figure(go.Pie(labels=[section.name for section in sections],
                                               values=[section_counts[section.name] for section in sections]))
        section_doughnut_fig.update_layout(title='Sections')
           # Create an area chart for the number of users
        user_counts_over_time = (
                db.session.query(func.date(BookRequest.request_time).label('date'), func.count(User.id).label('user_count'))
                .join(User, User.id == BookRequest.user_id)
                .group_by(func.date(BookRequest.request_time))
                .all()
            )

        user_over_time_fig = go.Figure(go.Scatter(x=[str(date) for date, _ in user_counts_over_time],
                                                  y=[count for _, count in user_counts_over_time],
                                                  mode='lines+markers',
                                                  name='Number of Users'))

        user_over_time_fig.update_layout(title='Number of Users Over Time', xaxis_title='Date', yaxis_title='Number of User Requests')
        most_requested_book = (
            db.session.query(EBook)
            .join(BookRequest, EBook.id == BookRequest.ebook_id)
            .group_by(EBook.id)
            .order_by(func.count(BookRequest.ebook_id).desc())
            .first()
        )
        num_requests = BookRequest.query.filter_by(ebook_id=most_requested_book.id).count()
        most_requested_book.num_requests = num_requests
        # Retrieve the book with the highest average rating
        highest_rated_book = (
            db.session.query(EBook)
            .order_by(func.coalesce(EBook.average_rating, 0).desc())
            .first()
        )
        # Create a scatter chart for the number of books and sections
        book_counts = EBook.query.count()
        section_counts = Section.query.count()
        scatter_fig = go.Figure()
        scatter_fig.add_trace(go.Scatter(x=['Books'], y=[book_counts], mode='markers', name='Number of Books'))
        scatter_fig.add_trace(go.Scatter(x=['Sections'], y=[section_counts], mode='markers', name='Number of Sections'))
        scatter_fig.update_layout(title='Books and Sections', xaxis_title='Categories', yaxis_title='Counts')

        # Display the top requested books with images
        top_requested_books = db.session.query(EBook, func.count(BookRequest.ebook_id).label('total_requests')) \
            .outerjoin(BookRequest, EBook.id == BookRequest.ebook_id) \
            .group_by(EBook.id) \
            .order_by(func.count(BookRequest.ebook_id).desc()) \
            .limit(5) \
            .all()

        # Display the top rated books with images
        top_rated_books = EBook.query.order_by(EBook.average_rating.desc()).limit(5).all()
        plotly_deps = plotly.offline.get_plotlyjs()
        return render_template('l_stat.html',
                               total_users=total_users,
                                total_books=total_books,
                                total_sections=total_sections,
                                total_book_requests=total_book_requests,
                                plotly_deps=plotly_deps,
                               user_duration_html=plotly.io.to_html(user_duration_fig),
                               section_doughnut_html=plotly.io.to_html(section_doughnut_fig),
                               user_area_html=plotly.io.to_html(user_over_time_fig),
                               scatter_html=plotly.io.to_html(scatter_fig),
                               top_requested_books=top_requested_books, top_rated_books=top_rated_books,
                               most_requested_book=most_requested_book,
                               
            highest_rated_book=highest_rated_book,
            book_request_html=plotly.io.to_html(book_request_fig))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) or db.session.get(Librarian, int(user_id))


@app.context_processor
def inject_librarian():
    librarian=Librarian.query.all() 
    return dict(librarian=librarian)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)