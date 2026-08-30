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
import re
import joblib
import pandas as pd
import torch
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance
from rembg import remove
from dotenv import load_dotenv
import requests

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except Exception:
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None

load_dotenv()

app = Flask(__name__)
CORS(app)


# ============================================================
# BUYER FEATURE: Bilingual listing descriptions (English + Hindi)
# ============================================================
GOOGLE_TRANSLATE_API_KEY = (os.getenv("GOOGLE_TRANSLATE_API_KEY") or "").strip()
PLACEHOLDER_API_KEYS = {"YOUR_GOOGLE_API_KEY", "changeme", "placeholder", ""}
if GOOGLE_TRANSLATE_API_KEY in PLACEHOLDER_API_KEYS:
    GOOGLE_TRANSLATE_API_KEY = ""

NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"
TELUGU_ROMANIZED_MAP = {
    "naaku": "నాకు",
    "naku": "నాకు",
    "ishtam": "ఇష్టము",
    "ishta": "ఇష్టము",
    "bagundi": "బాగుంది",
    "baga": "బాగా",
    "chala": "చాలా",
    "manchi": "మంచి",
    "pattu": "పట్టు",
    "rangu": "రంగు",
    "nenu": "నేను",
    "meeru": "మీరు",
    "mari": "మరి",
    "sare": "సరే",
    "ledu": "లేదు",
    "gundam": "గుండం",
    "sari": "సరి",
    "sweekars": "శ్రీకారం",
}
HINDI_ROMANIZED_MAP = {
    "main": "मैं",
    "mai": "मैं",
    "bahut": "बहुत",
    "acha": "अच्छा",
    "accha": "अच्छा",
    "sahi": "सही",
    "kapda": "कपड़ा",
    "saree": "साड़ी",
    "samay": "समय",
    "din": "दिन",
    "nahi": "नहीं",
    "hai": "है",
    "dikh raha": "दिख रहा",
    "kamaal": "कमाल",
}
nllb_tokenizer = None
nllb_model = None


def detect_nllb_source_lang(text):
    """Return the NLLB source-language code most likely used by the seller."""
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "tel_Telu"
    if re.search(r'[\u0900-\u097F]', text):
        return "hin_Deva"
    if re.search(r'[\u0A00-\u0A7F]', text):
        return "mar_Deva"
    if re.search(r'[\u0980-\u09FF]', text):
        return "ben_Beng"
    if re.search(r'[A-Za-z]', text):
        return "eng_Latn"
    return "tel_Telu"


def romanized_indic_to_native_script(text):
    """Convert common romanized Indian-language phrases into native script before translation."""
    if not text:
        return ""

    if re.search(r'[\u0C00-\u0C7F\u0900-\u097F]', text):
        return text

    lowered = text.lower()
    lang_hint = None
    if any(pattern in lowered for pattern in ["naaku", "naku", "ishtam", "bagundi", "chala", "manchi", "pattu", "nenu", "meeru"]):
        lang_hint = "telugu"
    elif any(pattern in lowered for pattern in ["main", "bahut", "acha", "accha", "sahi", "kapda", "saree", "samay", "nahi", "hai"]):
        lang_hint = "hindi"

    if lang_hint is None:
        return text

    map_to_use = TELUGU_ROMANIZED_MAP if lang_hint == "telugu" else HINDI_ROMANIZED_MAP
    tokens = re.findall(r"[A-Za-z]+", text)
    if not tokens:
        return text

    for token in tokens:
        key = token.lower()
        if key in map_to_use:
            text = re.sub(rf"\b{re.escape(token)}\b", map_to_use[key], text, flags=re.IGNORECASE)
    return text


def normalize_translation_input(text):
    """Clean noisy speech-to-text output before translating."""
    if not text:
        return ""
    cleaned = romanized_indic_to_native_script(str(text))
    cleaned = re.sub(r'\s+', ' ', str(cleaned).strip())
    cleaned = re.sub(r'\b(?:um|uh|like|basically|actually|you know|well)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b([A-Za-z0-9\u0C00-\u0C7F\u0900-\u097F]+)(?:\s+\1)+\b', r'\1', cleaned, flags=re.IGNORECASE)

    sentences = []
    for sentence in re.split(r'(?<=[.!?])\s+', cleaned):
        normalized_sentence = sentence.strip()
        if not normalized_sentence:
            continue
        if sentences and normalized_sentence.lower() == sentences[-1].lower():
            continue
        sentences.append(normalized_sentence)

    cleaned = ' '.join(sentences).strip()
    if len(cleaned) > 2000:
        cleaned = cleaned[:2000].rsplit(' ', 1)[0]
    return cleaned


def load_local_nllb_model():
    global nllb_model, nllb_tokenizer
    if nllb_model is not None and nllb_tokenizer is not None:
        return nllb_tokenizer, nllb_model
    if AutoTokenizer is None or AutoModelForSeq2SeqLM is None:
        raise RuntimeError("transformers package is not installed")
    nllb_tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME)
    nllb_model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
    return nllb_tokenizer, nllb_model


def translate_with_local_nllb(text, target_lang):
    """Translate text using the local NLLB multilingual model without any API key."""
    if not text or not text.strip():
        return ""
    tokenizer, model = load_local_nllb_model()
    source_lang = detect_nllb_source_lang(text)
    tokenizer.set_src_lang_special_tokens(source_lang)
    tokenizer.set_tgt_lang_special_tokens(target_lang)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    model.eval()
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang),
            max_length=512,
            do_sample=False,
        )
    return tokenizer.decode(generated[0], skip_special_tokens=True).strip()


@app.route("/api/translate-buyer-bilingual", methods=["POST"])
def translate_buyer_bilingual():
    """
    Translates product descriptions to both English and Hindi.
    Accepts descriptions in any language and automatically detects
    the source language before translating. Falls back to a local NLLB model
    when no Google Translate API key is configured.
    """
    try:
        data = request.get_json(silent=True) or {}
        text = normalize_translation_input(data.get("text", ""))

        if not text:
            return jsonify({"error": "No description provided"}), 400

        if len(text) > 2000:
            return jsonify({"error": "Description too long (max 2000 characters)"}), 400

        def translate_google(target_lang):
            """Translate text to target language (en or hi) using Google Translate."""
            try:
                response = requests.post(
                    "https://translation.googleapis.com/language/translate/v2",
                    params={"key": GOOGLE_TRANSLATE_API_KEY},
                    json={
                        "q": text,
                        "target": target_lang,
                        "format": "text"
                    },
                    timeout=15
                )
                response.raise_for_status()
                result = response.json()

                if "data" not in result or "translations" not in result["data"]:
                    raise ValueError("Invalid response structure from translation API")

                translated_text = result["data"]["translations"][0].get("translatedText", "")
                if not translated_text:
                    raise ValueError(f"No translation returned for target language: {target_lang}")

                return translated_text
            except requests.Timeout:
                raise Exception(f"Translation API timeout for language {target_lang}")
            except requests.RequestException as e:
                raise Exception(f"Translation API error for {target_lang}: {str(e)}")

        try:
            if GOOGLE_TRANSLATE_API_KEY:
                english = translate_google("en")
                hindi = translate_google("hi")
                print(f"Successfully translated via Google: {len(text)} chars -> EN: {len(english)} chars, HI: {len(hindi)} chars")
            else:
                print("WARNING: GOOGLE_TRANSLATE_API_KEY not configured; using local NLLB fallback")
                english = translate_with_local_nllb(text, "eng_Latn")
                hindi = translate_with_local_nllb(text, "hin_Deva")
                print(f"Successfully translated via local NLLB: {len(text)} chars -> EN: {len(english)} chars, HI: {len(hindi)} chars")

            return jsonify({
                "english": english,
                "hindi": hindi,
                "source_length": len(text)
            })
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            print(error_msg)
            return jsonify({
                "error": error_msg,
                "english": text,
                "hindi": text
            }), 502

    except Exception as error:
        error_msg = f"Bilingual buyer translation error: {str(error)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500

MODEL_CANDIDATE_PATHS = [
    "model/market_price_model.pkl",
    "model/textile_price_model.pkl",
]
pricing_model = None


def load_pricing_model():
    """Load the preferred pricing model, with safe fallback if a pickle is incompatible."""
    global pricing_model
    if pricing_model is not None:
        return pricing_model

    for model_path in MODEL_CANDIDATE_PATHS:
        if not os.path.exists(model_path):
            continue
        try:
            pricing_model = joblib.load(model_path)
            print(f"Loaded pricing model from: {model_path}")
            return pricing_model
        except Exception as exc:
            print(f"Warning: could not load pricing model from {model_path}: {exc}")

    print("Warning: no compatible pricing model found; using benchmark fallback pricing.")
    return None


def build_model_feature_row(data):
    """Convert raw pricing fields into a model-friendly row while accepting multiple input names."""
    material_cost = data.get("raw_material_cost")
    if material_cost is None:
        material_cost = data.get("material_cost")
    if material_cost is None:
        material_cost = data.get("materialCost")
    if material_cost is None:
        material_cost = data.get("raw_material_cost_inr")

    labor_hours = data.get("labor_hours", data.get("work_hours", 0))
    experience_years = data.get("artisan_experience_years", data.get("experience_years", 0))
    category = data.get("category", "textile")
    material = data.get("material", "standard")
    size = data.get("size", "medium")
    intricacy = data.get("intricacy", "moderate")
    region = data.get("region", "semi_urban")

    row = {
        "raw_material_cost": float(material_cost or 0),
        "material_cost": float(material_cost or 0),
        "labor_hours": float(labor_hours or 0),
        "experience_years": float(experience_years or 0),
        "artisan_experience_years": float(experience_years or 0),
        "category": category,
        "material": material,
        "size": size,
        "intricacy": intricacy,
        "region": region,
        "sub_category": data.get("sub_category", category),
        "average_rating": data.get("average_rating", 4.0),
        "discount_pct": data.get("discount_pct", 25),
        "other_craft_type": data.get("other_craft_type", "")
    }
    return row


def predict_with_loaded_model(model, data):
    """Use the loaded model with the actual raw feature values from the request."""
    if model is None:
        return None
    try:
        row = pd.DataFrame([build_model_feature_row(data)])

        if hasattr(model, "feature_names_in_"):
            expected = list(model.feature_names_in_)
            aligned = {}
            for name in expected:
                if name in row.columns:
                    aligned[name] = row.iloc[0][name]
                else:
                    aligned[name] = 0
            row = pd.DataFrame([aligned])

        prediction = model.predict(row)
        if len(prediction) == 0:
            return None
        return float(prediction[0])
    except Exception as exc:
        print(f"Warning: pricing model prediction failed with raw features: {exc}")
        return None


pricing_model = load_pricing_model()

# Documented Indian market-benchmark base prices (INR) -- research
# estimates, used only where no public per-item Indian dataset exists.
INDIAN_BENCHMARK_PRICES = {
    "pottery":   450,
    "jewelry":   700,
    "woodcraft": 600,
    "painting":  1200,
    "basketry":  350,
}

CATEGORY_SIZE_CAPS = {
    "textile": {"small": 1200, "medium": 2200, "large": 3500},
    "pottery": {"small": 900, "medium": 1700, "large": 2600},
    "jewelry": {"small": 1800, "medium": 3600, "large": 6000},
    "woodcraft": {"small": 1400, "medium": 3000, "large": 4500},
    "painting": {"small": 2200, "medium": 4500, "large": 7000},
    "basketry": {"small": 1000, "medium": 1800, "large": 3000},
    "other": {"small": 1200, "medium": 2200, "large": 3500},
}

MARKET_FLOOR = {
    "textile": {"small": 250, "medium": 500, "large": 900},
    "pottery": {"small": 300, "medium": 650, "large": 1100},
    "jewelry": {"small": 400, "medium": 900, "large": 1600},
    "woodcraft": {"small": 350, "medium": 800, "large": 1400},
    "painting": {"small": 500, "medium": 1200, "large": 2000},
    "basketry": {"small": 250, "medium": 600, "large": 1000},
    "other": {"small": 250, "medium": 600, "large": 1000},
}

MATERIAL_MULT = {"standard": 1.0, "premium": 1.2}
SIZE_MULT = {"small": 1.0, "medium": 1.35, "large": 1.8}
INTRICACY_MULT = {"simple": 0.9, "moderate": 1.0, "highly_detailed": 1.25}
REGION_MULT = {"rural": 0.9, "semi_urban": 1.0, "metro": 1.18}
LABOR_RATE = 40


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
    other_craft_type = data.get("other_craft_type", "")
    material = data["material"]
    size = data["size"]
    intricacy = data.get("intricacy", "moderate")
    region = data.get("region", "semi_urban")
    labor_hours = float(data["labor_hours"])
    experience_years = float(data.get("artisan_experience_years", 2))
    raw_material_cost = float(
        data.get("raw_material_cost", data.get("material_cost", 0)) or 0
    )

    # ---- base price: prefer the saved AI model using the actual raw feature values,
    # then fall back to documented Indian market estimates if the model is unavailable.
    base_source = ""
    model = load_pricing_model()
    if model is not None:
        raw_prediction = predict_with_loaded_model(model, data)
        if raw_prediction is not None:
            base_price = max(float(raw_prediction), 0.0)
            base_source = "AI pricing model using raw feature values"
        else:
            base_price = float(INDIAN_BENCHMARK_PRICES.get(category, 500))
            base_source = "benchmark fallback after model prediction failure"
    elif category in INDIAN_BENCHMARK_PRICES:
        base_price = float(INDIAN_BENCHMARK_PRICES[category])
        base_source = "documented Indian market-benchmark estimate"
    else:
        # "Other" or any unrecognized category: use a safe generic fallback
        # instead of rejecting the request outright
        base_price = 500.0
        base_source = f"generic fallback estimate (category '{category}' not in our specialized list)"

    price = base_price
    price *= MATERIAL_MULT.get(material, 1.0)
    price *= SIZE_MULT.get(size, 1.0)
    price *= INTRICACY_MULT.get(intricacy, 1.0)
    price *= REGION_MULT.get(region, 1.0)
    price += labor_hours * LABOR_RATE
    price *= (1 + min(experience_years, 20) * 0.0035)

    # Raw material is a hard cost: the suggested selling price must recover it
    # and leave room for labor and artisan skill.
    if raw_material_cost > 0:
        minimum_price = raw_material_cost * 1.05 + labor_hours * 35 + experience_years * 15
        maximum_cost_based_price = raw_material_cost * 1.30 + labor_hours * 50 + experience_years * 25
        feature_multiplier = (
            MATERIAL_MULT.get(material, 1.0)
            * SIZE_MULT.get(size, 1.0)
            * INTRICACY_MULT.get(intricacy, 1.0)
            * REGION_MULT.get(region, 1.0)
        )
        cost_based_price = raw_material_cost + raw_material_cost * 0.05 * feature_multiplier
        cost_based_price += labor_hours * 35 + experience_years * 15
        price = max(min(cost_based_price, maximum_cost_based_price), minimum_price)

    category_cap = max(
        CATEGORY_SIZE_CAPS.get(category, CATEGORY_SIZE_CAPS["other"]).get(size, 2000),
        raw_material_cost * 1.3 if raw_material_cost > 0 else 0,
    )
    category_floor = max(
        MARKET_FLOOR.get(category, MARKET_FLOOR["other"]).get(size, 250),
        raw_material_cost * 1.05 if raw_material_cost > 0 else 0,
    )
    exact_price = max(float(category_floor), min(float(price), float(category_cap)))
    exact_price = round(exact_price, -1)

    return jsonify({
        "base_price": round(base_price, 2),
        "base_source": base_source,
        "predicted_price": exact_price,
        "exact_price": exact_price,
        "price_range_low": exact_price,
        "price_range_high": exact_price,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)