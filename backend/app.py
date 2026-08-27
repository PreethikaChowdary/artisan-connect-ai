"""
app.py

Flask backend serving the 3 mandatory features of SIH26090.

Pricing approach (v4, corrected to use genuine Indian data):
  - textile: real Random Forest model trained on 1,783 real Flipkart
    India listings (INR prices)
  - pottery/jewelry/woodcraft/painting/basketry: documented Indian
    market-benchmark estimates (no public per-item Indian dataset
    exists yet for these categories -- this is stated honestly rather
    than disguised as ML output)
  - On top of either base: transparent multipliers for material,
    size, intricacy, labor hours, region, and artisan experience

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

TEXTILE_MODEL_PATH = "model/textile_price_model.pkl"
textile_model = None
if os.path.exists(TEXTILE_MODEL_PATH):
    textile_model = joblib.load(TEXTILE_MODEL_PATH)

# Documented Indian market-benchmark base prices (INR) -- research
# estimates, used only where no public per-item Indian dataset exists.
INDIAN_BENCHMARK_PRICES = {
    "pottery":   450,
    "jewelry":   700,
    "woodcraft": 600,
    "painting":  1200,
    "basketry":  350,
}

MATERIAL_MULT = {"standard": 1.0, "premium": 1.4}
SIZE_MULT = {"small": 1.0, "medium": 1.25, "large": 1.6}
INTRICACY_MULT = {"simple": 1.0, "moderate": 1.2, "highly_detailed": 1.5}
REGION_MULT = {"rural": 1.0, "semi_urban": 1.1, "metro": 1.25}
LABOR_RATE = 60


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
try:
    import whisper
    whisper_model = whisper.load_model("base")
except Exception as e:
    print(f"Whisper not available, /api/transcribe will be disabled: {e}")
    whisper_model = None

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    if whisper_model is None:
        return jsonify({"error": "Whisper isn't installed on this server."}), 501
    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400
    file = request.files["audio"]
    temp_path = "temp_audio.wav"
    file.save(temp_path)
    result = whisper_model.transcribe(temp_path)
    os.remove(temp_path)
    return jsonify({"transcript": result["text"], "detected_language": result["language"]})


# ============================================================
# FEATURE 3: Dynamic Pricing Assistant (Indian data only)
# ============================================================
@app.route("/api/predict-price", methods=["POST"])
def predict_price():
    data = request.get_json()
    required = ["category", "material", "size", "labor_hours"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing fields, need: {required}"}), 400

    category = data["category"]
    material = data["material"]
    size = data["size"]
    intricacy = data.get("intricacy", "moderate")
    region = data.get("region", "semi_urban")
    labor_hours = float(data["labor_hours"])
    experience_years = float(data.get("artisan_experience_years", 2))

    # ---- base price: real ML for textile, documented estimate otherwise ----
    base_source = ""
    if category == "textile" and textile_model is not None:
        row = pd.DataFrame([{
            "sub_category": "Kurtas, Ethnic Sets and Bottoms",
            "average_rating": 4.0,
            "discount_pct": 30,
        }])
        base_price = float(textile_model.predict(row)[0])
        base_source = "real ML model trained on 1,783 Flipkart India listings"
    elif category in INDIAN_BENCHMARK_PRICES:
        base_price = float(INDIAN_BENCHMARK_PRICES[category])
        base_source = "documented Indian market-benchmark estimate"
    else:
        return jsonify({"error": f"Unknown category: {category}"}), 400

    price = base_price
    price *= MATERIAL_MULT.get(material, 1.0)
    price *= SIZE_MULT.get(size, 1.0)
    price *= INTRICACY_MULT.get(intricacy, 1.0)
    price *= REGION_MULT.get(region, 1.0)
    price += labor_hours * LABOR_RATE
    price *= (1 + min(experience_years, 20) * 0.004)

    low = round(price * 0.9, -1)
    high = round(price * 1.15, -1)

    return jsonify({
        "base_price": round(base_price, 2),
        "base_source": base_source,
        "predicted_price": round(price, -1),
        "price_range_low": low,
        "price_range_high": high,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)