import pandas as pd
import nltk
import joblib
import os

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

nltk.download('stopwords')
nltk.download('wordnet')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "complaints.csv")

data = pd.read_csv(csv_path)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess(text):
    text = str(text).lower()
    words = text.split()
    words = [
        lemmatizer.lemmatize(word)
        for word in words
        if word.isalpha() and word not in stop_words
    ]
    return " ".join(words)

data["clean_text"] = data["complaint_text"].apply(preprocess)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(data["clean_text"])
y = data["department"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearSVC()
model.fit(X_train, y_train)

joblib.dump(model, os.path.join(BASE_DIR, "complaint_model.pkl"))
joblib.dump(vectorizer, os.path.join(BASE_DIR, "tfidf_vectorizer.pkl"))

print("✅ Model trained and saved successfully")
