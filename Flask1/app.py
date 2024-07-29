import base64
from flask import Flask, jsonify, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tkinter import Tk, filedialog
import io
import PyPDF2
import fitz  # PyMuPDF
import os
import json
from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from sqlalchemy import func


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app) #allows hashing passwords
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey7'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                #return redirect(url_for('dashboard'))
                return redirect(url_for('index'))
    return render_template('login.html', form=form)


#@app.route('/dashboard', methods=['GET', 'POST'])
#@login_required
#def dashboard():
#    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    extra_images = db.Column(db.JSON, nullable=True)
    content = db.Column(db.String(200), nullable=False)  # Add content field
    extra_images_status = db.Column(db.Boolean, nullable=False, default=False) 
    images = db.Column(db.JSON, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    #date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Add date_created field
    #date_created = 5

    def __repr__(self):
        return '<PDFFile %r>' % self.file_name
    



# Initialize the database schema
with app.app_context():
    db.create_all()

@app.route('/', methods=['POST', 'GET'])
@login_required #have to put it right before function definition otherwise it won't work
def index():
    if request.method == 'POST':
        #if 'pdf_file' in request.files:
        print(request.form)
        if "reset" in request.form:
            print("3")
            pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
            for pdf in pdfs:
                print("a: ", pdf.extra_images_status)
                pdf.extra_images_status = False
                print("b: ", pdf.extra_images_status)
                if pdf.images:
                    pdf.images = json.loads(pdf.images)
                if pdf.extra_images:
                    print("c: ", pdf.extra_images_status)
                    pdf.extra_images_status = True
                    pdf.extra_images = json.loads(pdf.extra_images)
            print("d: ", pdf.extra_images_status)
            #query = PDFFile.query #doesn't order by date like the first line does
            #query = query.filter_by() 
            #pdfs = query.all()
            return render_template('index.html', pdfs=pdfs)
        elif 'search_gender' in request.form or 'search_age' in request.form and 'submit_button' not in request.form:
            print("1")
            #print("yo")
            search_gender = request.form.get('search_gender').lower()
            search_age = request.form.get('search_age').lower()
            #print("yo1: ", search_gender)
            #print("yo2: ", search_age)

            query = PDFFile.query
            
            if search_gender:
                query = query.filter(func.lower(PDFFile.gender)==search_gender)
            if search_age:
                query = query.filter(func.lower(PDFFile.age)==search_age)
                
            pdfs = query.all()
            for pdf in pdfs:
                print("a2: ", pdf.extra_images_status)
                pdf.extra_images_status = False
                print("b2: ", pdf.extra_images_status)
                if pdf.images:
                    pdf.images = json.loads(pdf.images)
                if pdf.extra_images:
                    print("c2: ", pdf.extra_images_status)
                    pdf.extra_images_status = True
                    pdf.extra_images = json.loads(pdf.extra_images)
            print("d2: ", pdf.extra_images_status)
            return render_template('index.html', pdfs=pdfs, search_gender=search_gender, search_age=search_age)
        elif 'submit_button' in request.form:
            print("2")
            print(request.form)
            file = request.files['pdf_file']
            print("test: ", file)
            age = request.form['age']
            gender = request.form['gender']

            if not age or not gender or not file:
                error = "Please fill out all required fields and upload the PDF file."
                #pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
                for pdf in pdfs: #I thought this would be undefined
                    pdf.extra_images_status = False
                    print("interesting")
                    print(pdfs)
                    if pdf.images:
                        pdf.images = json.loads(pdf.images)
                    if pdf.extra_images:
                        pdf.extra_images = json.loads(pdf.extra_images)
                        pdf.extra_images_status = True
                return render_template('index.html', pdfs=pdfs, error=error)

        #print(file)
        #print(age)
        #print(gender)

            #if file.filename == '':
            #    return "No selected file"
            
            #if file and file.filename.endswith('.pdf'):
            file_data = file.read()
            pdf_text = decode_pdf(file_data)
            pdf_image = decode_pdf_images(file_data)
            print("len: ", len(pdf_image))
            images_json = json.dumps(pdf_image)

            extra_pictures = request.files.getlist('pictures')
            extra_images = []
            extra_images_status = False
            for picture in extra_pictures:
                image_bytes = picture.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                extra_images.append(image_base64)
            extra_images_json = json.dumps(extra_images)
            if len(extra_images) != 0:
                extra_images_status = True
            print("d3: ", extra_images_status)
             #   print("true")
              #  new_pdf = PDFFile(age=age, gender=gender, file_name=file.filename, file_data=file_data, content=pdf_text, images=images_json)
            #for i in pdf_image:
            #    print(type(i))
                #print(json.load(i))
            #else:
            new_pdf = PDFFile(age=age, gender=gender, file_name=file.filename, file_data=file_data, content=pdf_text, images=images_json,extra_images = extra_images_json ,extra_images_status=extra_images_status)
                
            try:
                db.session.add(new_pdf)
                db.session.commit()
                return redirect('/')
            except Exception as e:
                return f"We could not add the specific item due to this error: {str(e)}"
        
    pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
    for pdf in pdfs:
        print("a4: ", pdf.extra_images_status)
        pdf.extra_images_status = False
        print("b4: ", pdf.extra_images_status)
        if pdf.images:
            pdf.images = json.loads(pdf.images)
        if len(pdf.extra_images) != 4: #[""] has length of 4 and means no extra images
            print("c44: ", len(pdf.extra_images))
            print("c4: ", pdf.extra_images_status)
            pdf.extra_images_status = True
            pdf.extra_images = json.loads(pdf.extra_images)
        print("d4: ", pdf.extra_images_status)
    return render_template('index.html', pdfs=pdfs)
'''
def extract_images_from_pdf(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        
        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = os.path.join(output_folder, f"image{page_num+1}_{image_index+1}.{image_ext}")
            
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
                
    print("Images extracted and saved to:", output_folder)
    '''

def extract_images_from_pdf(pdf_path): #not used
    pdf_document = fitz.open(pdf_path)
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        
        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_name = f"image{page_num+1}_{image_index+1}.{image_ext}"
            
            # Convert the image bytes to a base64 string
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Store the image data in a dictionary
            images.append({
                'name': image_name,
                'data': image_base64,
                'ext': image_ext
            })
    return images

def decode_pdf(pdf_data):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))  # Change PdfFileReader to PdfReader
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

def decode_pdf_images(pdf_data):
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Convert image bytes to a data URL
            image_data_url = f"data:image/{image_ext};base64," + base64.b64encode(image_bytes).decode('utf-8')
            images.append(image_data_url)
    print(len(images))

    return images


@app.route('/delete_pdf/<int:id>')
@login_required
def delete_pdf(id):
    task_to_delete = PDFFile.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        f"We could not delete the specific item due to this error: {str(e)}"


@app.route('/view_more/<int:id>', methods=['GET'])
@login_required
def view_more(id):
    #pdf = next((p for p in pdfs if p['id'] == pdf_id), None)
    try:
        pdf = PDFFile.query.get(id)
        if not pdf:
            response = jsonify({'error': 'PDF not found'})
            response.status_code = 404
            return response
        return jsonify({'content': pdf.content})
    except Exception as e:
        response = jsonify({'error': 'An internal server error occurred'})
        response.status_code = 500
        print(e)  # Log the exception to the server logs
        return response
    """
    pdf = PDFFile.query.get_or_404(id)
    print('test')
    print(id)
    print(pdf)
    if pdf:
        print('content')
        print(pdf['content'])
        return jsonify({'content': pdf['content']})
    else:
        return jsonify({'error': 'PDF not found'}), 404
    """

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = PDFFile.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        #print(task.content)
        try:
            db.session.commit()
            return redirect("/")
        except:
            return f"We could not update the item due to this error: {str(e)}"
    else:
        return render_template('update.html', task = task)

@app.route('/download_pdf/<int:id>')
@login_required
def download_pdf(id):
    pdf_file = PDFFile.query.get_or_404(id)
    return send_file(io.BytesIO(pdf_file.file_data), download_name=pdf_file.file_name, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)