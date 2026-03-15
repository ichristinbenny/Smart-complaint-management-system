import os
import joblib
from django.shortcuts import render, redirect
from .models import Complaint

from nltk.corpus import stopwords

# Load ML model safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "complaint_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "ml", "tfidf_vectorizer.pkl")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

stop_words = set(stopwords.words('english'))

def preprocess(text):
    text = str(text).lower()
    words = text.split()
    words = [word for word in words if word.isalpha() and word not in stop_words]
    return " ".join(words)

def add_complaint(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")

        clean_text = preprocess(description)
        vector = vectorizer.transform([clean_text])
        predicted_department = model.predict(vector)[0]

        Complaint.objects.create(
            title=title,
            description=description,
            department=predicted_department
        )

        return redirect("success")

    return render(request, "add_complaint.html")


def success(request):
    return render(request, "success.html")
