# Kaarigar

## Project Summary

Kaarigar is an AI-driven market linkage and smart cataloging system for marginalized artisans. The goal is to remove the biggest barriers artisans face while going digital: poor product photos, no time to write listings, language barriers, unclear pricing, and limited market reach.

The platform is designed to help artisans create professional listings from their own voice, understand fair pricing through an AI-assisted pricing model, and reach buyers more easily without requiring them to be digitally advanced users.

## Why this solution exists

Artisans often face five real-world problems when trying to sell online:

- poor-quality or missing product photos
- no time or skill to write detailed listings
- inability to describe products in English or other non-native languages
- uncertainty about fair pricing for handmade products
- limited access to digital tools and marketplaces

Kaarigar addresses these in a single flow: AI Image Studio, multilingual auto-cataloging, and a dynamic pricing assistant.

## Why Aadhaar authentication was chosen

The system is built around Aadhaar-based registration because many artisans do not have Gmail accounts or other standard digital identities.

In a real-world deployment, many artisans may not have:

- a personal email account
- consistent internet access for long digital onboarding flows
- comfort with traditional web-based registration systems

Because of that, the app uses mobile number + Aadhaar-based registration instead of email-first onboarding. This makes the entry barrier much lower for artisans who are active in the real economy but are not digitally fluent.

The prototype includes an Aadhaar + OTP-style flow for demonstration. This is simulated for the project prototype. In production, a real UIDAI Aadhaar e-KYC integration would require the proper licensing and government-approved setup.

The important point is that the design decision is intentional: the system is built to work for artisans who are not typical app users, not only for people with mainstream digital access.

## Core features

### 1. AI Image Studio

Artisans can upload a product photo and improve it before publishing.

The backend applies image cleanup to remove backgrounds and make product images cleaner and more presentation-ready.

### 2. Multilingual Auto-Cataloger

Artisans can record a product description in their own language instead of writing a polished English listing.

The app supports a multilingual flow where the description is processed and translated for buyers. This helps with language barriers and reduces the effort needed to create a listing.

### 3. Dynamic Pricing Assistant

The pricing module is designed to give artisans a practical and transparent estimate based on real input variables.

This is not a random guess. The pricing is driven by:

- category
- material
- size
- labor hours
- raw material cost
- artisan experience
- region
- intricacy
- other relevant listing inputs provided by the artisan

The model is designed to make pricing more explainable and fair, rather than simply showing a random number.

## Pricing model: built from real market data and actual user inputs

The pricing logic is integrated directly into the backend in `backend/app.py`.

### How the model is used

The app follows this sequence:

1. It receives product inputs from the artisan in the `/api/predict-price` request.
2. It converts those values into a model-friendly feature row.
3. It tries to run the saved model if a compatible pickle file is available.
4. If the model is missing or fails, it falls back to documented Indian benchmark pricing instead of crashing.
5. It then adjusts the value using handcrafted market multipliers and cost constraints.
6. It returns the final price in INR.

This means the final price is not a fixed number. It is computed from the actual artisan inputs and the model output.

### Input features passed into the model

The backend constructs a row with the following fields before prediction:

- `raw_material_cost` / `material_cost`
- `labor_hours`
- `artisan_experience_years` / `experience_years`
- `category`
- `material`
- `size`
- `intricacy`
- `region`
- `sub_category`
- `average_rating`
- `discount_pct`
- `other_craft_type`

These are the actual features used to build the model input row in `build_model_feature_row()` and then passed into `model.predict()`.

### What the model outputs

If the pricing model loads successfully, the backend calls:

- `predict_with_loaded_model(model, data)`
- then `model.predict(row)`

The predicted value is treated as the model's base price. The route then does:

- `base_price = max(float(raw_prediction), 0.0)`
- multiplies by material, size, intricacy, and region multipliers
- adds labor cost (`labor_hours * LABOR_RATE`)
- applies artisan experience adjustment
- checks raw material cost floor/ceiling constraints
- clamps the price between the category floor and category cap

The return JSON includes:

- `base_price`
- `base_source`
- `predicted_price`
- `exact_price`
- `price_range_low`
- `price_range_high`

So the output is the final printed price estimate in INR for that item, based on the model and the user's product details.

### Real data used by the model

The project explicitly states that the textile pricing model is a real Random Forest model trained on 1,783 real Flipkart India listings in INR.

For categories like pottery, jewelry, woodcraft, painting, and basketry, the project uses benchmark estimates because there is no public per-item Indian dataset for those categories in the current implementation. Those values are not invented as a fake model output; they are used as documented fallback pricing logic.

### Actual formula logic

The backend does the following in sequence:

1. `base_price` comes from the model if available, otherwise from a benchmark.
2. `price *= MATERIAL_MULT[material]`
3. `price *= SIZE_MULT[size]`
4. `price *= INTRICACY_MULT[intricacy]`
5. `price *= REGION_MULT[region]`
6. `price += labor_hours * 38`
7. `price *= (1 + min(experience_years, 20) * 0.0035)`
8. It enforces a minimum cost floor based on raw material cost, labor, and experience.
9. It caps the final price by category-size limits and region-specific pottery rules.

This is the actual integration between the ML model and the input features: the model predicts a base value, and the system then adjusts it with real business logic grounded in material cost, labor, region, and craftsmanship characteristics.

## Why this matters

This is especially relevant for handmade and craft-based products, where pricing is often unfair or inconsistent because artisans do not have standardized market guidance.

The app tries to make pricing more transparent by giving the artisan a calculation that is grounded in real market patterns and explained in terms of actual inputs.

## Solution flow

The product is designed around a simple user flow:

1. Artisan registers with mobile number and Aadhaar-based onboarding
2. Artisan uploads or captures a product photo
3. Artisan records a product description in their own language
4. The system processes the listing and prepares product metadata
5. The pricing assistant calculates an estimate from the actual user inputs and market model
6. Artisan reviews the listing before publishing
7. Buyer sees the listing, translated and explained in understandable language
8. Admin monitors and verifies listings

## Technical approach

The project has been built as a prototype with a fast, demonstrable pipeline rather than a fully production-scale platform.

### Frontend

The frontend is a browser-based app designed as a responsive web experience. It includes:

- artisan dashboard
- buyer marketplace
- admin dashboard
- listing generation UI
- pricing explanation flow
- language and translation display
- image preview workflow

### Backend

The backend is a Flask service that handles:

- pricing prediction
- multilingual translation
- image enhancement and cleanup
- market benchmark fallback logic

### Storage and prototype status

This is a prototype and not a full production-scale multi-user database system. The app currently uses browser storage for demonstration purposes. This means the prototype is useful for validation and workflow testing, but a real deployment would require a production database and proper authentication layer.

## Realism and honesty about scope

The project is intentionally transparent about what is simulated and what is actual.

Examples:

- Aadhaar verification is simulated in the prototype
- real UIDAI e-KYC requires proper licensing and production approval
- local browser storage is used for demo speed and simplicity
- the ML pricing flow is based on real data for textile products, while some categories rely on benchmark-based estimates where public Indian item-level data is not available

This honesty is important because it keeps the prototype credible and technically feasible.

## Demo-ready vision

The project is designed to show that a digital marketplace can be built around the actual needs of artisans rather than a typical e-commerce user model.

It is not just a listing platform. It is an AI-assisted business support tool for artisans.

## Project positioning

Kaarigar aims to fill a real gap in the market.

Unlike mass-market e-commerce tools that simply offer a generic listing slot, this system is designed to help artisans with the hard parts of going digital:

- image quality
- product description generation
- language support
- pricing transparency
- direct market visibility

## Future production path

The prototype lays the foundation for a larger system. The next steps in a real deployment would include:

- proper UIDAI-compliant Aadhaar verification with the required licensing
- a production-grade database instead of browser storage
- stronger role-based access for artisans, buyers, and admins
- mobile app or PWA deployment
- deeper market analytics and broader dataset support

## Final note

Kaarigar is built around a simple principle: artisans should not need to be fluent in English, comfortable with complex e-commerce tools, or reliant on a Gmail account just to start earning through digital commerce.

The project uses Aadhaar-based onboarding because it is a practical identity path for the target user group, and the pricing is grounded in the real market data and the inputs supplied by the artisan, rather than arbitrary or fixed pricing.

This makes the solution more usable, more relevant, and more aligned with the real problems faced by marginalized artisans in India.
