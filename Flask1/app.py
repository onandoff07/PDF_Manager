from flask import Flask, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tkinter import Tk, filedialog
import io
import PyPDF2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    content = db.Column(db.String(200), nullable=False)  # Add content field
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    #date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Add date_created field
    #date_created = 5

    def __repr__(self):
        return '<PDFFile %r>' % self.file_name
    



# Initialize the database schema
with app.app_context():
    db.create_all()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        #if 'pdf_file' in request.files:
        print(request.form)
        if 'search_gender' in request.form or 'search_age' in request.form and 'submit_button' not in request.form:
            print("1")
            #print("yo")
            search_gender = request.form.get('search_gender')
            search_age = request.form.get('search_age')
            #print("yo1: ", search_gender)
            #print("yo2: ", search_age)

            query = PDFFile.query
            
            if search_gender:
                query = query.filter_by(gender=search_gender)
            if search_age:
                query = query.filter_by(age=search_age)
            
            pdfs = query.all()
            return render_template('index.html', pdfs=pdfs, search_gender=search_gender, search_age=search_age)
        elif 'submit_button' in request.form:
            print("2")
            file = request.files['pdf_file']
            #print("test: ", file)
            age = request.form['age']
            gender = request.form['gender']
        #print(file)
        #print(age)
        #print(gender)

            #if file.filename == '':
            #    return "No selected file"
            
            #if file and file.filename.endswith('.pdf'):
            file_data = file.read()
            pdf_text = decode_pdf(file_data)
                
            new_pdf = PDFFile(age=age, gender=gender, file_name=file.filename, file_data=file_data, content=pdf_text)
                
            try:
                db.session.add(new_pdf)
                db.session.commit()
                return redirect('/')
            except Exception as e:
                return f"We could not add the specific item due to this error: {str(e)}"
        elif "reset" in request.form:
            print("3")
            pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
            return render_template('index.html', pdfs=pdfs)
        
    pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
    return render_template('index.html', pdfs=pdfs)


def decode_pdf(pdf_data):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))  # Change PdfFileReader to PdfReader
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

@app.route('/delete_pdf/<int:id>')
def delete_pdf(id):
    task_to_delete = PDFFile.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        f"We could not delete the specific item due to this error: {str(e)}"

@app.route('/update/<int:id>', methods=['GET', 'POST'])
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
def download_pdf(id):
    pdf_file = PDFFile.query.get_or_404(id)
    return send_file(io.BytesIO(pdf_file.file_data), download_name=pdf_file.file_name, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)