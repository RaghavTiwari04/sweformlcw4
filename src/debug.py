import pandas as pd
import joblib
import numpy as np

lab_entry = {
    "sex": 1,
    "min": 183.61,
    "mean": 216.38973074076898,
    "max": 392.62838444461397,
    "median": 201.035,
    "std": 54.2220279567911,
    "sum": 2596.676768889228,
    "results": [
        183.61,
        199.17,
        188.48,
        211.05,
        197.72,
        198.61,
        202.9,
        220.87,
        209.01,
        183.7734023282627,
        208.8549821163513,
        392.62838444461397,
    ],
}


def predict(lab_entry):
    model = joblib.load("model/aki_model.pkl")
    features = {
        "sex": 1,
        "creatinine_mean": np.mean(lab_entry["results"]),
        "creatinine_min": min(lab_entry["results"]),
        "creatinine_max": max(lab_entry["results"]),
        "creatinine_median": np.median(lab_entry["results"]),
        "creatinine_std": np.std(lab_entry["results"]),
        "creatinine_count": np.sum(lab_entry["results"]),
    }
    df = pd.DataFrame([features])
    df = df.fillna(0)  # Handle any potential NaN values
    prediction = model.predict(df)
    if prediction == 1:
        print("=================================PREDICTION: ", prediction)
    return prediction


print(predict(lab_entry))
