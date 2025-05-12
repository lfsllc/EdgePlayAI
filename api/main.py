from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import os
import traceback

# ✅ Initialize FastAPI app
app = FastAPI()

# ✅ Load the trained model
model_path = "models/match_outcome_model.pkl"
model = joblib.load(model_path) if os.path.exists(model_path) else None

# ✅ Define the input schema
class OddsInput(BaseModel):
    odds_home: float
    odds_draw: float
    odds_away: float

# ✅ Define the prediction route
@app.post("/predict")
def predict_odds(data: OddsInput):
    try:
        if model is None:
            print("❌ Model not loaded")
            return {"error": "Model not loaded"}

        print("📥 Received odds:", data.dict())
        X = np.array([[data.odds_home, data.odds_draw, data.odds_away]])
        print("✅ Input array:", X)

        prediction = model.predict_proba(X)[0]
        print("✅ Prediction result:", prediction)

        return {
            "Home Win Probability": round(float(prediction[0]) * 100, 2),
            "Draw Probability": round(float(prediction[1]) * 100, 2),
            "Away Win Probability": round(float(prediction[2]) * 100, 2)
        }

    except Exception as e:
        print("❌ Internal Server Error:")
        traceback.print_exc()
        return {"error": "Internal server error", "details": str(e)}
