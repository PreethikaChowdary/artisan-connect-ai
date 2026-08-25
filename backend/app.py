"""
app.py

Flask backend serving the 3 mandatory features of SIH26090:

1. POST /api/enhance-image    -> AI background removal + auto-enhance (rembg)
2. POST /api/transcribe        -> voice note transcription (Whisper)
3. POST /api/predict-price     -> HYBRID pricing:
       Stage 1: real-data-trained model gives a market-grounded base price
       Stage 2: transparent artisan-specific multipliers on top
                (material, size, intricacy, labor hours, region, experience)

Run with:
    python app.py
"""

import io
import os
import joblib
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance
from rembg import remove

app = Flask(__name__)
CORS(app)

# ---------- Load the Stage 1 real-data market price model ----------
MARKET_MODEL_PATH = "model/market_price_model.pkl"
market_model = None
if os.path.exists(MARKET_MODEL_PATH):
    market_model = joblib.load(MARKET_MODEL_PATH)

# Maps our handicraft categories to the closest matching category in the
# real Kaggle retail dataset (see train_pricing_model.py for full context)
CATEGORY_MAP = {
    "textile":   {"Category": "Clothing & Apparel", "Sub_Category": "Women's Wear"},
    "pottery":   {"Category": "Home & Furniture",    "Sub_Category": "Home Decor"},
    "jewelry":   {"Category": "Accessories",         "Sub_Category": "Wearable Accessories"},
    "woodcraft": {"Category": "Home & Furniture",    "Sub_Category": "Furniture"},
    "painting":  {"Category": "Home & Furniture",    "Sub_Category": "Home Decor"},
    "basketry":  {"Category": "Accessories",         "Sub_Category": "Bags"},
}

# Stage 2: transparent, explainable adjustment factors -- these capture
# what NO retail dataset tracks: material tier, intricacy of handwork,
# artisan labor, target market tier, and artisan experience.
MATERIAL_MULT = {"standard": 1.0, "premium": 1.4}
SIZE_MULT = {"small": 1.0, "medium": 1.25, "large": 1.6}
INTRICACY_MULT = {"simple": 1.0, "moderate": 1.2, "highly_detailed": 1.5}
REGION_MULT = {"rural": 1.0, "semi_urban": 1.1, "metro": 1.25}
LABOR_RATE = 60  # notional fair wage per hour, INR


# ============================================================
# FEATURE 1: AI Image Enhancer & Studio
# ============================================================
@app.route("/api/enhance-image", methods=["POST"])
def enhance_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    input_image = Image.open(file.stream).convert("RGBA")

    no_bg = remove(input_image)
    clean_bg = Image.new("RGBA", no_bg.size, (255, 255, 255, 255))
    clean_bg.paste(no_bg, (0, 0), no_bg)
    result = clean_bg.convert("RGB")

    result = ImageEnhance.Brightness(result).enhance(1.08)
    result = ImageEnhance.Contrast(result).enhance(1.12)
    result = ImageEnhance.Color(result).enhance(1.08)

    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return send_file(buf, mimetype="image/jpeg")


# ============================================================
# FEATURE 2: Multilingual Auto-Cataloger (transcription)
# ============================================================
import whisper
whisper_model = whisper.load_model("base")

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    file = request.files["audio"]
    temp_path = "temp_audio.wav"
    file.save(temp_path)
    result = whisper_model.transcribe(temp_path)
    os.remove(temp_path)

    return jsonify({"transcript": result["text"], "detected_language": result["language"]})


# ============================================================
# FEATURE 3: Dynamic Pricing Assistant (HYBRID)
# ============================================================
@app.route("/api/predict-price", methods=["POST"])
def predict_price():
    if market_model is None:
        return jsonify({"error": "Market model not trained yet. Run train_pricing_model.py first."}), 500

    data = request.get_json()
    required = ["category", "material", "size", "labor_hours"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing fields, need: {required}"}), 400

    category = data["category"]
    if category not in CATEGORY_MAP:
        return jsonify({"error": f"Unknown category. Choose from {list(CATEGORY_MAP.keys())}"}), 400

    material = data["material"]
    size = data["size"]
    intricacy = data.get("intricacy", "moderate")
    region = data.get("region", "semi_urban")
    labor_hours = float(data["labor_hours"])
    experience_years = float(data.get("artisan_experience_years", 2))

    # ---- STAGE 1: real-data-trained market-grounded base price ----
    mapping = CATEGORY_MAP[category]
    market_row = pd.DataFrame([{
        "Category": mapping["Category"],
        "Sub_Category": mapping["Sub_Category"],
        "Quantity": 1
    }])
    market_base_price = float(market_model.predict(market_row)[0])

    # ---- STAGE 2: transparent artisan-specific adjustments ----
    price = market_base_price
    price *= MATERIAL_MULT.get(material, 1.0)
    price *= SIZE_MULT.get(size, 1.0)
    price *= INTRICACY_MULT.get(intricacy, 1.0)
    price *= REGION_MULT.get(region, 1.0)
    price += labor_hours * LABOR_RATE
    price *= (1 + min(experience_years, 20) * 0.004)

    low = round(price * 0.9, -1)
    high = round(price * 1.15, -1)

    return jsonify({
        "market_base_price": round(market_base_price, 2),
        "predicted_price": round(price, -1),
        "price_range_low": low,
        "price_range_high": high,
        "explanation": {
            "market_base": f"Rs. {market_base_price:.0f} (learned from real retail data, mapped from '{category}' to '{mapping['Sub_Category']}')",
            "material_factor": f"x{MATERIAL_MULT.get(material,1.0)}",
            "size_factor": f"x{SIZE_MULT.get(size,1.0)}",
            "intricacy_factor": f"x{INTRICACY_MULT.get(intricacy,1.0)}",
            "region_factor": f"x{REGION_MULT.get(region,1.0)}",
            "labor_value": f"+Rs. {labor_hours*LABOR_RATE:.0f} ({labor_hours} hrs x Rs.{LABOR_RATE}/hr)",
            "experience_factor": f"x{(1 + min(experience_years,20)*0.004):.3f}"
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
