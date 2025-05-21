import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier

# === 1. Load and normalize dataset ===
print("✅ Loading fully enhanced dataset...")
df = pd.read_csv("data/historical_matches_fully_enhanced.csv", low_memory=False)
df.columns = df.columns.str.strip().str.lower()
# Rename columns to match expected schema
df = df.rename(columns={
    "hometeam": "home_team",
    "awayteam": "away_team"
})
print(f"✅ Loaded data: {df.shape}")
print(f"📄 Data columns: {df.columns.tolist()}")

# === 2. Load and normalize Elo ratings ===
print("📁 Loading Elo ratings...")
elo_df = pd.read_csv("data/clubelo_ratings.csv")
elo_df.columns = elo_df.columns.str.strip().str.lower()
elo_df = elo_df[["club", "elo", "rank"]]

# === 3. Merge Elo ratings ===
elo_home = elo_df.rename(columns={"club": "home_team", "elo": "home_elo", "rank": "home_rank"})
elo_away = elo_df.rename(columns={"club": "away_team", "elo": "away_elo", "rank": "away_rank"})

# Show columns for debugging if error happens again
print(f"📄 Match data columns: {df.columns.tolist()}")

# Merge
df = df.merge(elo_home, on="home_team", how="left")
df = df.merge(elo_away, on="away_team", how="left")
print("✅ Merged Elo ratings")

# === 4. Compute Elo differences ===
df["elo_diff"] = df["home_elo"] - df["away_elo"]
df["rank_diff"] = df["away_rank"] - df["home_rank"]

# === 5. Filter required columns ===
required_cols = [
    "form_diff", "goal_diff", "elo_diff", "rank_diff",
    "momentum_diff", "home_away_split_diff", "result",
    "h2h_home_wins_last3", "h2h_away_wins_last3", "h2h_goal_diff_last3",
    "draw_rate_last5", "avg_goal_diff_last5",
    "days_since_last_match", "fixture_density_flag"
]
df = df.dropna(subset=required_cols)

# === 6. Feature Set ===
features = [
    "elo_diff", "form_diff", "goal_diff", "rank_diff",
    "momentum_diff", "home_away_split_diff",
    "h2h_home_wins_last3", "h2h_away_wins_last3", "h2h_goal_diff_last3",
    "draw_rate_last5", "avg_goal_diff_last5",
    "days_since_last_match", "fixture_density_flag"
]
target = df["result"].map({-1: 0, 0: 1, 1: 2})  # Remap for XGBoost

X = df[features]
y = target

# === 7. Train/Test Split ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# === 8. Train XGBoost with tuned params ===
print("⚙️ Training tuned XGBoost classifier...")
model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0.2,
    min_child_weight=3,
    eval_metric='mlogloss',
    random_state=42
)
model.fit(X_train, y_train)

# === 9. Evaluation ===
y_pred = model.predict(X_test)

# Remap to original classes
label_map = {0: -1, 1: 0, 2: 1}
y_pred_mapped = pd.Series(y_pred).map(label_map)
y_test_mapped = y_test.map(label_map)

accuracy = accuracy_score(y_test_mapped, y_pred_mapped)
print(f"\n✅ Model Accuracy: {accuracy:.2%}")
print("\n📊 Classification Report:")
print(classification_report(y_test_mapped, y_pred_mapped))
print("\n🧮 Confusion Matrix:")
print(confusion_matrix(y_test_mapped, y_pred_mapped))

import joblib

# === Save the trained model ===
joblib.dump(model, "model.pkl")
print("✅ Model saved as model.pkl")
