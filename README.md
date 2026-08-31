# Kaarigar

Kaarigar is a browser-based artisan marketplace prototype built to help rural and semi-urban craftspeople list products, price them transparently, and reach buyers with multilingual product descriptions.

The project combines:
- artisan listing generation
- multilingual translation for buyer-facing descriptions
- AI-assisted pricing using a trained price model with transparent fallback logic
- local image cleanup for product photos
- lightweight admin, artisan, and buyer views in one frontend app

This project is designed as a working prototype/demo system rather than a production-grade database-backed marketplace.

## Project Overview

The application supports three main user journeys:

1. Artisan workflow
   - Upload or capture a product photo
   - Speak or type the product description in their own language
   - Choose product category and craft details
   - Generate a listing with a price estimate
   - Publish the listing to the local marketplace

2. Buyer workflow
   - Browse a public marketplace
   - View product descriptions in English and Hindi
   - Review a transparent price explanation
   - Contact the artisan or request a purchase

3. Admin workflow
   - View registered artisans, buyers, and listings
   - Monitor listing activity by category
   - Manage marketplace visibility in the local prototype

## Architecture

### Frontend
Location: `frontend/index.html`

The frontend is a single-page app with browser-local state using `localStorage`. It contains:
- login/register flows
- artisan dashboard
- buyer marketplace
- admin dashboard
- listing generation UI
- pricing assistant form
- multilingual description rendering
- image preview and cleanup step

### Backend
Location: `backend/app.py`

The backend is a Flask service that provides:
- bilingual translation endpoint
- pricing prediction endpoint
- image enhancement endpoint
- market benchmark pricing fallback logic

The app uses Flask + Flask-CORS, and it loads environment variables from `.env` if present.

## ML + Pricing Model

### Pricing approach
The pricing engine is designed to be honest about what is genuinely data-driven and what is benchmark-based.

- Textile pricing uses a real Random Forest model trained on Indian marketplace pricing data.
- Pottery, jewelry, woodcraft, painting, and basketry are handled with documented Indian market benchmark estimates and transparent multiplier logic where public per-item Indian datasets are not available.
- The system combines:
  - raw material cost
  - category base benchmark
  - size multiplier
  - material multiplier
  - intricacy multiplier
  - labor hours
  - artisan experience
  - region multiplier (rural / semi-urban / metro)

### Model loading behavior
The backend checks for a trained model at:
- `backend/model/market_price_model.pkl`
- `backend/model/textile_price_model.pkl`

If no compatible model is found, the backend gracefully falls back to benchmark-based pricing rather than crashing.

### Key pricing logic in the backend
These values are configured in `backend/app.py`:

- `INDIAN_BENCHMARK_PRICES`
- `CATEGORY_SIZE_CAPS`
- `MARKET_FLOOR`
- `MATERIAL_MULT`
- `SIZE_MULT`
- `INTRICACY_MULT`
- `REGION_MULT`

For pottery, the app also has tighter rural-vs-urban controls so small rural pottery stays in a realistic lower range while metro pricing remains meaningfully higher.

### Frontend parity
The browser UI mirrors the same formula structure so the live prototype behaves consistently between the frontend and backend pricing estimate flow.

## Translation System

### Buyer description translation
The backend supports a bilingual translation route:

- `POST /api/translate-buyer-bilingual`

This accepts a description in any seller language and returns:
- `english`
- `hindi`
- `source_length`

### Translation behavior
The system chooses the following order:
1. If a Google Translate API key is present, use the Google Cloud Translation API.
2. If not, fall back to a local NLLB multilingual model path when the required libraries are installed.
3. If neither is available, return the original description text as a safe fallback instead of failing the request.

### Offline / API-free fallback
The project includes logic for:
- source language detection
- romanized Indic input normalization
- local NLLB translation fallback
- graceful error-to-original fallback behavior

This is particularly important for demo use in local/offline environments without paid API credentials.

## Image Processing

The backend includes an image enhancement endpoint:

- `POST /api/enhance-image`

Behavior:
- accepts uploaded product image
- removes background using `rembg`
- creates a clean white background
- enhances brightness, contrast, and color
- saves the output as JPEG for presentation

This helps artisan listings look cleaner and more presentable.

## Local Storage Prototype Notes

This app currently stores data in the browser using `localStorage` rather than a centralized server database.

Implications:
- the app works as a standalone prototype
- admin can see all listings in the same browser context
- buyer/artisan views depend on the same current browser session and data store
- shared multi-user data requires a real backend database and authentication layer

## Repository Structure

```text
artisan-connect-ai/
├── backend/
│   ├── app.py
│   ├── generate_synthetic_fallback.py
│   ├── model/
│   ├── requirements.txt
│   └── ...
├── frontend/
│   └── index.html
├── .gitignore
├── README.md
└── ...
```

## Setup Instructions

### 1. Python environment
From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Optional translation API key
If you want to use Google Translate instead of the local fallback:

```bash
# backend/.env
GOOGLE_TRANSLATE_API_KEY=your_key_here
```

### 3. Start the backend
```bash
cd backend
python app.py
```

### 4. Open the web app
Open:

```text
frontend/index.html
```

in a browser, or serve it through any simple local static server if needed.

## API Endpoint Summary

### Translation
```http
POST /api/translate-buyer-bilingual
```
Request:
```json
{
  "text": "यह मिट्टी का बर्तन हाथ से बना है"
}
```
Response:
```json
{
  "english": "This clay pot is handmade.",
  "hindi": "यह मिट्टी का बर्तन हाथ से बना है",
  "source_length": 32
}
```

### Pricing
```http
POST /api/predict-price
```
Request accepts fields like:
- category
- material
- size
- intricacy
- region
- labor_hours
- artisan_experience_years
- raw_material_cost
- other_craft_type

### Image cleanup
```http
POST /api/enhance-image
```
Accepts a product image upload and returns an enhanced JPEG result.

## Notes on Data and Model Reliability

This project was built as a prototype and intentionally keeps its pricing and translation logic transparent:
- model-driven for textile when data is present
- benchmark-based for categories that lack public item-level Indian datasets
- fallback behavior designed to avoid crashes when APIs or models are missing

This makes it useful for demo, research, and concept validation, while remaining honest about the limits of a prototype system.

## Current Status

The app is functional as a local prototype that demonstrates:
- multilingual product listing flow
- local/offline translation fallback
- explainable pricing
- browser-local marketplace behavior
- artisan, buyer, and admin experience in a single UI

## Future Improvements

- move from `localStorage` to a real backend database
- add secure authentication and role-based authorization
- integrate a production-grade translation service
- train more category-specific pricing models with richer datasets
- add exportable dashboards and analytics
- expand multilingual support beyond the current Indian-language set

## License

This project is provided as a prototype for demonstration and learning use.
