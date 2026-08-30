# artisan-connect-ai
AI-powered platform empowering artisans with intelligent digital tools, language support, and market connectivity.

## 🌐 Bilingual Description Translation (English & Hindi)

### How It Works

**For Sellers (Artisans):**
- Artisans can describe their products in **any language** they're comfortable with (Hindi, Tamil, Telugu, Marathi, Bengali, English, etc.)
- Descriptions are captured through voice recording or manual text input
- The artisan's language preference is flexible — they can speak in whatever language is most natural to them

**For Buyers:**
- Every product description is automatically translated into **English** and **हिंदी (Hindi)**
- Buyers see both language versions side-by-side on the buyer dashboard
- Translations happen automatically when listings are loaded
- If the backend translation service is unavailable, the original description is shown as fallback

### Technical Architecture

#### Backend (`backend/app.py`)
- **Endpoint:** `POST /api/translate-buyer-bilingual`
- **Input:** Product description in any language
- **Output:** JSON with `english` and `hindi` translations
- **Service:** Uses Google Translate API for automatic language detection and translation
- **Features:**
  - Automatic source language detection
  - Character limit validation (max 2000 chars)
  - Timeout protection (15 seconds per request)
  - Graceful error handling with fallback to original text
  - Detailed logging for debugging

**Example Request:**
```json
{
  "text": "यह एक हाथ से बनी कढ़ाई वाली साड़ी है"
}
```

**Example Response:**
```json
{
  "english": "This is a handmade embroidered saree",
  "hindi": "यह एक हाथ से बनी कढ़ाई वाली साड़ी है",
  "source_length": 38
}
```

#### Frontend (`frontend/index.html`)
- **Translation Trigger:** Automatically triggered when buyer loads listings
- **Caching:** Translations are cached client-side to avoid duplicate requests
- **Loading States:** 
  - Shows "translating..." and "अनुवाद हो रहा है" indicators while fetching
  - Indicators are removed once translations are applied
- **Error Handling:**
  - Graceful degradation if API is unavailable
  - Falls back to original description text
  - Console logs for debugging

### Environment Setup

1. **Get Google Translate API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create or select a project
   - Enable the "Cloud Translation API"
   - Create an API key (or use a service account)

2. **Configure Backend:**
   ```bash
   # In backend/.env
   GOOGLE_TRANSLATE_API_KEY=your_api_key_here
   ```

3. **Start Backend:**
   ```bash
   cd backend
   python app.py
   ```

### Usage Examples

#### Seller Workflow
1. Seller logs in as Artisan
2. Selects a language for the description (e.g., Tamil/తెలుగు)
3. Speaks or types the product description
4. System captures the description in the selected language
5. When listing is published, backend automatically translates to English & Hindi
6. Buyer sees both versions on the dashboard

#### Buyer Workflow
1. Buyer logs in and views the marketplace
2. Each product listing displays:
   - **English version** of the description
   - **हिंदी version** of the description
3. Buyer can read in their preferred language
4. All descriptions are automatically translated when the page loads

### Supported Languages for Input

Sellers can speak or type descriptions in any language. The Google Translate API will automatically detect and translate from:
- Hindi (हिंदी)
- English
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Marathi (मराठी)
- Bengali (বাংলা)
- Or any other language Google Translate supports

### API Response Codes

| Status | Meaning |
|--------|---------|
| 200 | Successful translation |
| 400 | No description provided or too long |
| 502 | Translation API error (returns fallback) |
| 503 | Translation service not configured |
| 500 | Unexpected error |

### Caching Strategy

Frontend caches translations using the pattern: `{listingId}:en-hi`
- Cache key uniquely identifies each listing's translations
- Prevents duplicate API calls for the same listing
- Persists in browser session memory

### Error Handling & Fallbacks

1. **Backend Unavailable:** Returns original text with 503 status
2. **API Quota Exceeded:** Logs error, shows "(Translation unavailable - check back later)"
3. **Network Error:** Graceful fallback to original description
4. **Empty Translations:** Shows placeholder text in both languages

### Performance Considerations

- Translations are fetched in parallel for all visible listings
- Loading indicators show progress
- Completed translations are cached to avoid re-translation
- Timeout set to 15 seconds per translation request
- Graceful degradation if any translation times out

### Future Enhancements

1. **Offline Translation:** Support for offline translation models
2. **Custom Dictionary:** Support for regional/craft-specific terminology
3. **Translation Quality Rating:** Allow buyers to rate translation quality
4. **More Languages:** Expand beyond English/Hindi to other Indian languages
5. **Audio Translation:** Provide audio versions in multiple languages

