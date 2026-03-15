import joblib
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.joblib')

def predict(text, threshold=0.20):
    try:
        model = joblib.load(MODEL_PATH)
        
        # Get probabilities
        probs = model.predict_proba([text])[0]
        classes = model.classes_
        
        results = []
        for i, prob in enumerate(probs):
            if prob >= threshold:
                results.append((classes[i], prob))
        
        # Sort by highest probability first
        results.sort(key=lambda x: x[1], reverse=True)
        
        # If no class passes the threshold, just return the highest one
        if not results:
            highest_idx = probs.argmax()
            results = [(classes[highest_idx], probs[highest_idx])]
            
        predicted_classes = [r[0] for r in results]
        print(",".join(predicted_classes))
        return predicted_classes
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        predict(sys.argv[1])
    else:
        print("Please provide text to predict")
