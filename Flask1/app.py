from flask import Flask, jsonify, render_template, url_for, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tkinter import Tk, filedialog
import io
import PyPDF2
import fitz  # PyMuPDF
import os

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
    #images = db.Column(db.String(200), nullable=False)
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
        if "reset" in request.form:
            print("3")
            pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
            #query = PDFFile.query #doesn't order by date like the first line does
            #query = query.filter_by() 
            #pdfs = query.all()
            return render_template('index.html', pdfs=pdfs)
        elif 'search_gender' in request.form or 'search_age' in request.form and 'submit_button' not in request.form:
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
            print(request.form)
            file = request.files['pdf_file']
            print("test: ", file)
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
        
    pdfs = PDFFile.query.order_by(PDFFile.date_created).all()
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

def extract_images_from_pdf(pdf_path):
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

@app.route('/delete_pdf/<int:id>')
def delete_pdf(id):
    task_to_delete = PDFFile.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        f"We could not delete the specific item due to this error: {str(e)}"

@app.route('/view_more/<int:id>', methods=['GET'])
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