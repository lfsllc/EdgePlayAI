import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier
import joblib

# === 1. Load dataset with BTTS ===
print("✅ Loading dataset with BTTS...")
df = pd.read_csv("data/historical_matches_fully_enhanced.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()

# === 2. Validate required columns ===
required_cols = [
    "elo_diff", "form_diff", "goal_diff", "rank_diff",
    "momentum_diff", "home_away_split_diff", "h2h_home_wins_last3",
    "h2h_away_wins_last3", "h2h_goal_diff_last3", "draw_rate_last5",
    "avg_goal_diff_last5", "days_since_last_match", "fixture_density_flag",
    "odds_diff", "implied_prob_home", "result", "btts"
]
df = df.dropna(subset=required_cols)

# === 3. 1X2 Prediction Model ===
X_main = df[[col for col in required_cols if col not in ["result", "btts"]]]
y_main = df["result"].map({-1: 0, 0: 1, 1: 2})

X_train_main, X_test_main, y_train_main, y_test_main = train_test_split(
    X_main, y_main, test_size=0.2, random_state=42, stratify=y_main
)

model_main = XGBClassifier(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.03,
    subsample=0.85,
    colsample_bytree=0.85,
    gamma=0.1,
    min_child_weight=2,
    eval_metric='mlogloss',
    random_state=42
)
model_main.fit(X_train_main, y_train_main)

# Save model
joblib.dump(model_main, "model.pkl")
print("✅ 1X2 Model saved as model.pkl")

# === 4. BTTS Prediction Model ===
X_btts = X_main.copy()
y_btts = df["btts"]

X_train_btts, X_test_btts, y_train_btts, y_test_btts = train_test_split(
    X_btts, y_btts, test_size=0.2, random_state=42, stratify=y_btts
)

model_btts = XGBClassifier(
    n_estimators=250,
    max_depth=4,
    learning_rate=0.04,
    subsample=0.85,
    colsample_bytree=0.85,
    gamma=0.15,
    min_child_weight=2,
    eval_metric='logloss',
    random_state=42
)
model_btts.fit(X_train_btts, y_train_btts)

joblib.dump(model_btts, "model_btts.pkl")
print("✅ BTTS Model saved as model_btts.pkl")
