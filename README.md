# Group Photo Based Attendance System

This project uses face recognition to take attendance from a group photo.  
It detects student faces and marks attendance automatically.

## 🔧 Technologies Used

- Python
- OpenCV
- HaarCascade
- FaceNet
- Flask
- HTML/CSS

## 🚀 Features

- Upload group photo
- Detect and recognize faces
- Mark attendance and save in Excel
- Login/Register for teacher and student

## 🛠 How to Run

1. Clone the repo:  https://github.com/Laxman2171/Group-Photo-Based-Attendance-System.git

2. Create virtual environment and activate it:
   
3. Install dependencies:

4. Run the app:

   
##  How It Works

1. **Face Detection**:  
   - The system uses HaarCascade to detect all faces in the group photo.

2. **Face Recognition**:  
   - Detected faces are passed through FaceNet to get unique face embeddings.
   - These embeddings are compared with the student database.

3. **Attendance Marking**:  
   - If a face matches a student, their name is marked present.
   - The attendance is saved in an Excel sheet with the current date.

4. **Login System**:  
   - Teachers and students can log in or register through the web interface.
   - Only teachers can upload group photos and check attendance records.

5. **Frontend and Backend**:  
   - Flask is used for the backend (server, login, upload).
   - HTML and CSS create a simple, clean web interface.




