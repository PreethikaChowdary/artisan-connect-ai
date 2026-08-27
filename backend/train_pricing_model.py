"""
train_pricing_model.py  (v4 -- corrected to use genuine INDIAN data only)

IMPORTANT CONTEXT -- read this before your judge Q&A:
Our earlier version trained on a US retail dataset and used its prices
directly as INR, without currency conversion. That was a real mistake:
a $50 US item is not a Rs.50 item. This version fixes that by using
ONLY genuinely Indian-priced data, and being explicit about what is and
isn't ML-derived.

STAGE 1 -- REAL ML, REAL INDIAN DATA:
  Trained on 1,783 real Flipkart India listings (ethnic wear / fabrics),
  scraped in INR. This gives a genuinely real-data-trained base price
  for our "textile" category -- the one category where usable Indian
  per-item pricing data is publicly available.

STAGE 2 -- DOCUMENTED INDIAN MARKET BENCHMARKS (not ML):
  For pottery, jewelry, woodcraft, painting, and basketry, no clean
  public Indian dataset with per-item prices currently exists. Rather
  than force-fit a mismatched foreign or generic dataset, we use
  researched Indian market-benchmark base prices for these categories.
  These are clearly labelled as estimates, not model output -- this is
  more honest than dressing up a bad proxy as "AI".

STAGE 3 -- TRANSPARENT ARTISAN-SPECIFIC ADJUSTMENTS (same as before):
  material tier, size, intricacy, labor hours, target market region,
  and artisan experience are layered on top of the Stage 1/2 base price.

Run:
    python train_pricing_model.py
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# Stage 2: documented Indian market-benchmark base prices (INR), used
# for categories where no public per-item Indian pricing dataset exists.
# These are estimates based on general market research, not ML output.
INDIAN_BENCHMARK_PRICES = {
    "pottery":   450,
    "jewelry":   700,
    "woodcraft": 600,
    "painting":  1200,
    "basketry":  350,
}

def main():
    # ---- STAGE 1: real ML on real Indian textile data ----
    df = pd.read_csv("data/textile_training_data.csv")
    print(f"Training on {len(df)} real Flipkart India (ethnic wear / fabrics) listings.")

    features = ["sub_category", "average_rating", "discount_pct"]
    X = df[features]
    y = df["selling_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), ["sub_category"])],
        remainder="passthrough",
    )
    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)),
    ])

    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\nTextile model (REAL Indian data):")
    print(f"  Mean Absolute Error: Rs. {mae:.2f}")
    print(f"  R^2 score: {r2:.3f}")

    joblib.dump(model, "model/textile_price_model.pkl")
    print("  Saved -> model/textile_price_model.pkl")

    # a representative base price using median rating/discount, for reference
    sample = pd.DataFrame([{
        "sub_category": "Kurtas, Ethnic Sets and Bottoms",
        "average_rating": df["average_rating"].median(),
        "discount_pct": df["discount_pct"].median(),
    }])
    textile_base = model.predict(sample)[0]
    print(f"  Representative textile base price: Rs. {textile_base:.2f}")

    print("\nOther categories use documented Indian market-benchmark estimates")
    print("(not ML output -- no public per-item Indian dataset exists for these yet):")
    for cat, price in INDIAN_BENCHMARK_PRICES.items():
        print(f"  {cat:12s} -> Rs. {price} (research estimate)")

if __name__ == "__main__":
    main()