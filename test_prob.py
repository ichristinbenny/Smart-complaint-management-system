import joblib
m = joblib.load('e:\\Projectx\\ml_models\\model.joblib')
p = m.predict_proba(['There is a big pothole in the road near the bus stop and water is leaking from an underground pipe through the pothole.'])[0]
for c, v in zip(m.classes_, p):
    print(f'{c}: {v:.4f}')
