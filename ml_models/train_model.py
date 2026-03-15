import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'dataset.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'model.joblib')

def train():
    print("Loading data...")
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print("Dataset not found!")
        return

    X = df['text']
    y = df['label']

    print("Training model...")
    # Pipeline: TF-IDF -> LogisticRegression for probabilities
    model = make_pipeline(TfidfVectorizer(), LogisticRegression())
    model.fit(X, y)

    print(f"Saving model to {MODEL_PATH}...")
    joblib.dump(model, MODEL_PATH)
    print("Done!")

if __name__ == "__main__":
    train()
