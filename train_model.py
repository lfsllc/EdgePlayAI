import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import joblib
import os

# ✅ Load your merged dataset
df = pd.read_csv("data/historical_matches.csv")

# ✅ Basic cleanup (adjust column names as needed based on your CSV)
# Make sure these column names match your CSV exactly
required_columns = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'B365H', 'B365D', 'B365A']
df = df.dropna(subset=required_columns)

# ✅ Define features and label
X = df[['B365H', 'B365D', 'B365A']]
y = df['FTR']  # FTR = Full Time Result (H, D, A)

# ✅ Map labels to numeric (H=0, D=1, A=2)
label_map = {'H': 0, 'D': 1, 'A': 2}
y = y.map(label_map)

# ✅ Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ✅ Train the model
model = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
model.fit(X_train, y_train)

# ✅ Evaluate performance
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model accuracy: {accuracy:.2%}")

# ✅ Save the model
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/match_outcome_model.pkl")
print("✅ Model saved to models/match_outcome_model.pkl")

