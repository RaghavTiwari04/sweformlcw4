import joblib
import pandas as pd
import numpy as np
import os


class AKIDetector:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "../model/aki_model.pkl")
        self.model = joblib.load(model_path)

    def predict(self, lab_entry):
        features = {
            "sex": lab_entry["sex"],
            "creatinine_mean": lab_entry["mean"],
            "creatinine_min": lab_entry["min"],
            "creatinine_max": lab_entry["max"],
            "creatinine_median": lab_entry["median"],
            "creatinine_std": lab_entry["std"],
            "creatinine_count": len(lab_entry["results"]),
        }

        df = pd.DataFrame([features])
        prediction = self.model.predict(df)

        return bool(prediction)
