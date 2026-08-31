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

## Pricing model: built from real market data

The pricing logic is based on a real machine learning model trained on actual market data.

According to the project implementation, the textile pricing model is a real Random Forest model trained on 1,783 real Flipkart India listings in INR. This is the basis for market-grounded pricing rather than purely synthetic or hand-written rules.

The backend explicitly states:

- textile pricing uses a real Random Forest model trained on 1,783 real Flipkart India listings
- pottery, jewelry, woodcraft, painting, and basketry are handled using documented Indian market benchmark estimates, because no public per-item Indian dataset exists for these categories yet
- other pricing factors are layered on top of the base estimate using material, size, intricacy, labor, region, and artisan experience

This is important: the price is not simply a fixed number. It is derived from the user-provided inputs and the model's learned market behavior.

### Important clarification on pricing

The pricing is completely based on the model and the actual inputs given by the user.

That means the final estimate depends on the artisan's actual product information, such as:

- category of the product
- raw material cost
- labor hours
- artisan experience
- product size
- material type
- complexity and finish
- region and market context

The model is therefore not a generic fixed price. It is a calculation based on real market data and the artisan's own input values.

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
