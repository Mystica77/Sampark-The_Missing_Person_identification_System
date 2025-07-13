# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from database import init_db, add_person, get_all_people, delete_person, store_match_record
from facenet_model.face_model import match_face
from email_utils import send_alert_email
from image_utils import match_face
import os
import cv2
from werkzeug.utils import secure_filename
from mtcnn.mtcnn import MTCNN
from PIL import Image
import numpy as np
from datetime import datetime


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}

app = Flask(__name__) 

app.secret_key = 'my_super_secret_key_12345'
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'facedata', 'val')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Form data
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        height = request.form.get('height')
        weight = request.form.get('weight')
        complexion = request.form.get('complexion')
        hair_color = request.form.get('hair_color')
        eye_color = request.form.get('eye_color')
        clothing = request.form.get('clothing')
        marks = request.form.get('marks')
        last_seen = request.form['last_seen']
        date_missing = request.form['date_missing']
        image = request.files['image']

        reporter_name = request.form['reporter_name']
        relation = request.form['relation']
        mobile = request.form['mobile']
        aadhaar = request.form['aadhaar']
        email = request.form.get('email')
        address = request.form['address']

        # Save image
        if image:
            filename = secure_filename(f"{aadhaar}")
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            #print(image_path)
            image.save(image_path)
        else:
            image_path = ""

        # Store data
        add_person(name, gender, age, height, weight, complexion, hair_color, eye_color,
                   clothing, marks, last_seen, date_missing, image_path,
                   reporter_name, relation, mobile, aadhaar, email, address)

        flash('Missing person report submitted successfully.', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/surveillance', methods=['POST'])
def surveillance():
    uploaded_file = request.files['surveillance_file']
    filename = secure_filename(uploaded_file.filename)
    file_ext = filename.rsplit('.', 1)[-1].lower()
    save_path = os.path.join('static/uploads/facedata/val', filename)
    uploaded_file.save(save_path)

    mtcnn = MTCNN()

    if file_ext in ALLOWED_IMAGE_EXTENSIONS:
        image = Image.open(save_path)
        face = mtcnn.detect_faces(np.array(image))
        if not face:
            flash('No face detected in image.')
            return redirect('/')
        matched_person = match_face(save_path)
        if matched_person:
            send_alert_email(matched_person['email'], matched_person['name'])
            return jsonify({'status': 'success', 'message': f'Match found: {matched_person["name"]}'})
        else:
            return jsonify({'status': 'fail', 'message': 'No match found.'})
            # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # location = "Surveillance Camera"  # You can make this dynamic
            # store_match_record(
            #     matched_person['name'],
            #     matched_person['aadhaar'],
            #     save_path,
            #     location,
            #     timestamp
            # )    
        #     flash(f'Match found: {matched_person["name"]}')
        # else:
        #     flash('No match found.')
    elif file_ext in ALLOWED_VIDEO_EXTENSIONS:
        cap = cv2.VideoCapture(save_path)
        frame_count = 0
        found = False
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % 90 == 0:
                img_path = 'static/temp_frame.jpg'
                cv2.imwrite(img_path, frame)
                matched_person = match_face(img_path)
                if matched_person:
                    send_alert_email(matched_person['email'], matched_person['name'])
                    # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # location = "Surveillance Video"
                    # store_match_record(
                    #     matched_person['name'],
                    #     matched_person['aadhaar'],
                    #     img_path,
                    #     location,
                    #     timestamp
                    # )
                    flash(f'Match found in video: {matched_person["name"]}')
                    found = True
                    break
            frame_count += 1
        cap.release()
        if not found:
            flash('No match found in video.')
    else:
        flash('Unsupported file type.')

    return redirect('/')


# def send_alert_email(person_info):
#     msg = EmailMessage()
#     msg['Subject'] = 'Match Found in Surveillance!'
#     msg['From'] = 'wondersapientia@example.com'
#     msg['To'] = person_info['email']
#     msg.set_content(f"Dear {person_info['name']},\n\n"
#                     "A potential match was found based on the uploaded surveillance.\n"
#                     "Please visit the admin panel for details.\n\n"
#                     "Best regards,\nMissing Person System")

#     with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
#         smtp.starttls()
#         smtp.login('youremail@example.com', 'your_app_password')
#         smtp.send_message(msg)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials. <a href='/admin_login'>Try again</a>"
    return render_template('admin_login.html', admin_page=True)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    people = get_all_people()
    return render_template('dashboard.html', people=people)

@app.route('/remove/<aadhaar>')
def remove(aadhaar):
    delete_person(aadhaar)
    flash('Entry removed successfully.')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
