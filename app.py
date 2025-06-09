from flask import Flask, request, render_template, redirect, url_for, session, flash
import cv2
import numpy as np
from keras_facenet import FaceNet
from PIL import Image
import os
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up database
DATABASE_URL = "sqlite:///attendance.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session_db = Session()

# Initialize FaceNet
embedder = FaceNet()

# Database Models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class ImageEmbedding(Base):
    __tablename__ = 'embeddings'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    embedding = Column(LargeBinary)  # Stores face embedding for comparison

Base.metadata.create_all(engine)

# Routes...
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = User(username=username, password=password, role=role)
        session_db.add(new_user)
        session_db.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))  
    return render_template('register.html')

from flask import Flask, request, render_template, redirect, url_for, session, flash
from sqlalchemy.orm import sessionmaker
 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Assuming you have a `User` model that stores user credentials
        user = session_db.query(User).filter_by(username=username, password=password).first()
        
        if user:
            # User found, log them in by saving their ID in the session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role  # Optionally, you can use role to manage permissions

            if user.role == 'teacher':
                # Redirect to teacher dashboard if the role is 'teacher'
                return redirect(url_for('teacher_dashboard'))
            elif user.role == 'student':
                # Redirect to student dashboard if the role is 'student'
                return redirect(url_for('student_dashboard'))
            else:
                flash("Unknown role. Access denied.")
                return redirect(url_for('login'))
        else:
            # User not found or incorrect password
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))




@app.route('/enroll', methods=['GET', 'POST'])
def enroll_student():
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['photo']

        # Convert uploaded photo to embedding
        image = Image.open(file.stream).convert('RGB')
        image = np.array(image)
        face_embeddings = extract_embeddings(image)

        if face_embeddings:
            embedding = face_embeddings[0]  # Assumes one face per photo
            new_student = ImageEmbedding(name=name, embedding=np.array(embedding).tobytes())
            session_db.add(new_student)
            session_db.commit()
            flash("Student enrolled successfully.")
        else:
            flash("No face detected. Please try again with a clearer photo.")
        
        return redirect(url_for('enroll_student'))
    return render_template('enroll.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')   


@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') == 'student':
        return render_template('student_dashboard.html')
    else:
        flash("Access denied.")
        return redirect(url_for('login'))

@app.route('/upload_group_photo', methods=['GET', 'POST'])
def upload_group_photo():
    if request.method == 'POST':
        file = request.files['group_photo']
        image = Image.open(file.stream).convert('RGB')
        image = np.array(image)

        # Detect faces and extract embeddings for each face in the group photo
        face_embeddings = extract_embeddings(image)
        if face_embeddings:
            attendance_list = []
            for face_embedding in face_embeddings:
                name = compare_embeddings(face_embedding)
                if name:
                    attendance_list.append(name)

            # Update attendance and save to Excel
            mark_attendance(attendance_list)
            flash("Attendance marked successfully.")
            return render_template('attendance_result.html', attendance_list=attendance_list)
        else:
            flash("No faces detected. Please upload a clearer photo.")
            return redirect(url_for('upload_group_photo'))
    return render_template('upload_group_photo.html')

# Function to Compare Embeddings
def compare_embeddings(face_embedding):
    all_students = session_db.query(ImageEmbedding).all()
    for student in all_students:
        stored_embedding = np.frombuffer(student.embedding, dtype=np.float32)
        distance = np.linalg.norm(face_embedding - stored_embedding)
        if distance < 0.5:  # Threshold for FaceNet
            return student.name
    return None

# Function to Mark Attendance in Excel
def mark_attendance(attendance_list):
    filename = "attendance.xlsx"
    date_today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M:%S")

    # Load or create Excel file
    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])

    # Create new entries for the attendance list
    new_entries = pd.DataFrame([{"Name": name, "Date": date_today, "Time": time_now} for name in attendance_list])
    
    # Concatenate new entries to the existing DataFrame
    df = pd.concat([df, new_entries], ignore_index=True)

    # Save the updated DataFrame back to Excel
    df.to_excel(filename, index=False)

# Route for Viewing Attendance
import pandas as pd
from flask import render_template

@app.route('/view_attendance')
def view_attendance():
    # Load the attendance data from the Excel file
    filename = "attendance.xlsx"
    
    # Check if the file exists
    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])  # Empty DataFrame if no file exists

    # Convert the DataFrame into a list of dictionaries (for easier access in Jinja2)
    attendance_records = df.to_dict(orient='records')

    # Pass the attendance records to the template
    return render_template('view_attendance.html', attendance_records=attendance_records)


@app.route('/view_students')
def view_students():
    # Query the database for all students
    students = session_db.query(User).filter_by(role="student").all()  # Assuming 'User' model has a 'role' field
    return render_template('view_students.html', students=students)  

@app.route('/enroll_photos', methods=['GET', 'POST'])
def enroll_photos():
    if request.method == 'POST':
        name = request.form['name']
        files = request.files.getlist('photos')
        for file in files:
            image = Image.open(file.stream).convert('RGB')
            image = np.array(image)
            face_embeddings = extract_embeddings(image)
            if len(face_embeddings) > 0:  # Corrected check
                embedding = face_embeddings[0]
                new_embedding = ImageEmbedding(name=name, embedding=np.array(embedding).tobytes())
                session_db.add(new_embedding)
        session_db.commit()
        flash("Enrollment successful with multiple photos.")
        return redirect(url_for('student_dashboard'))
    return render_template('enroll_photos.html')


@app.route('/generate_report')
def generate_report():
   
    return render_template('generate_report.html')


# Route for Enrolled Students
@app.route('/enrolled_students')  
def enrolled_students():
    # Query the database for all enrolled students
    students = session_db.query(ImageEmbedding).all()
    student_names = [student.name for student in students]
    
    # Return the list of students to be displayed on the page
    return render_template('enrolled_students.html', student_names=student_names)

# Extract Embeddings from Face
def extract_embeddings(image):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    embeddings = []
    for (x, y, w, h) in faces:
        face = image[y:y+h, x:x+w]
        face = cv2.resize(face, (160, 160))
        face_embedding = embedder.embeddings([face])[0]
        embeddings.append(face_embedding)

    return embeddings

if __name__ == '__main__':
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f'{rule.endpoint} -> {rule}')
    app.run(debug=True)


