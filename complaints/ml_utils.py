import joblib
import os
from django.conf import settings
from .models import Department
from .keywords import match_department_by_keywords


def _get_department_by_keyword(base_name: str):
    """
    Try to find a department by a flexible name match so that
    'Water', 'Water Supply', 'Water Dept' etc. all work.
    """
    return (
        Department.objects.filter(name__iexact=base_name).first()
        or Department.objects.filter(name__icontains=base_name.lower()).first()
    )


def predict_department(description):
    model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'model.joblib')

    if not os.path.exists(model_path):
        # Fallback: use keywords extracted from complaint dataset.csv
        dept_name = match_department_by_keywords(description)
        dept = _get_department_by_keyword(dept_name) if dept_name else None
        return [dept] if dept else []

    try:
        model = joblib.load(model_path)
        # Using predict_proba to get probabilities for all classes
        probs = model.predict_proba([description])[0]
        classes = model.classes_
        threshold = 0.20 # Minimum probability to consider a class
        
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
        
        depts = []
        for pred in predicted_classes:
            d = Department.objects.filter(name__iexact=pred).first() or Department.objects.filter(name__icontains=str(pred).lower()).first()
            if d:
                depts.append(d)
                
        return depts
    except Exception as e:
        print(f"Prediction error: {e}")
        # Fallback to keywords from dataset
        dept_name = match_department_by_keywords(description)
        dept = _get_department_by_keyword(dept_name) if dept_name else None
        return [dept] if dept else []
