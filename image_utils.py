
import numpy as np
from mtcnn.mtcnn import MTCNN
from PIL import Image
import joblib  # changed from pickle to joblib
from facenet_model.face_model import get_embedding
from database import get_person_by_aadhaar
# Load model and encoder using joblib
model_svm, out_encoder = joblib.load('facenet_model/face_recognition_model.pkl')

def extract_face(image_path, required_size=(160, 160)):
    image = Image.open(image_path).convert('RGB')
    pixels = np.asarray(image)
    detector = MTCNN()
    results = detector.detect_faces(pixels)
    if results:
        x1, y1, width, height = results[0]['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        face = pixels[y1:y2, x1:x2]
        image = Image.fromarray(face).resize(required_size)
        return np.asarray(image)
    return None

def match_face(image_path):
    face = extract_face(image_path)
    if face is None:
        return None
    embedding = get_embedding(face)
    probs = model_svm.predict_proba([embedding])[0]
    class_index = np.argmax(probs)
    prediction = out_encoder.inverse_transform([class_index])[0]
    confidence = probs[class_index]
    # if confidence > 0.85:
    #     return {'name': prediction }  # Add email fetch logic if needed
    # return None
    if confidence > 0.85:
        # Get actual name and email from database
        person = get_person_by_aadhaar(prediction)  # e.g., ('John Doe', 'john@example.com')
        if person:
            name, email = person
            print(f"{name},{prediction}")
            return {'name': name, 'email': email, 'aadhaar': prediction}
        else:
            return None
        
        