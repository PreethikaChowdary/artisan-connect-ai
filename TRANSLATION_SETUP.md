# 🌐 Bilingual Translation Setup Guide

## Quick Start

The artisan-connect-ai platform now supports **automatic translation of product descriptions** from any language into **English** and **हिंदी (Hindi)** for buyers.

### ✅ What's Implemented

✓ Artisans can describe products in **any language**  
✓ Automatic translation to **English** and **Hindi**  
✓ Bilingual display on buyer dashboard  
✓ Loading indicators while translating  
✓ Client-side caching of translations  
✓ Graceful fallback if translation fails  
✓ Complete error handling  

---

## Setup Instructions

### Step 1: Get Google Translate API Key

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Cloud Translation API**:
   - Click "APIs & Services" → "Library"
   - Search for "Cloud Translation API"
   - Click it and press "Enable"
4. Create credentials (API Key):
   - Click "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated key

### Step 2: Configure Backend

```bash
# Open backend/.env file and add your API key:
GOOGLE_TRANSLATE_API_KEY=YOUR_ACTUAL_KEY_HERE
```

**Example:**
```
GOOGLE_TRANSLATE_API_KEY=AIzaSyD-x2Z3K4L5M6N7O8P9Q0R1S2T3U4V5W6X
```

### Step 3: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key packages needed:
- `flask` - Web framework
- `flask-cors` - Cross-origin support
- `requests` - HTTP library for Google Translate API
- `python-dotenv` - Load environment variables

### Step 4: Start the Backend Server

```bash
cd backend
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
* Press CTRL+C to quit
```

### Step 5: Open Frontend

Open `frontend/index.html` in your browser:
```
file:///C:/Users/preet/artisan-connect-ai/frontend/index.html
```

---

## Testing the Translation System

### Test 1: Register as Artisan

1. Click **"English"** language button
2. Click **"Register"** tab
3. Select **"Artisan"** role
4. Fill in details:
   - **Name:** Test Artisan
   - **Mobile:** 9876543210
   - **Aadhaar:** 123456789012
   - **OTP:** 123456
   - **Experience:** 5
   - Click **"Create account"**

### Test 2: Create a Test Listing with Non-English Description

1. You're now in the Artisan Dashboard
2. Upload a photo (any product image)
3. In **"Voice Cataloger"** section:
   - Select language: **"Hindi (हिंदी)"** or **"Tamil (தமிழ்)"**
   - Click the speaker button to enable recording
   - Speak a description in that language (or just type in the fallback field)
   - Example (in Hindi): "यह एक सुंदर लाल रंग की कढ़ाई वाली साड़ी है जो हाथ से बनी है"
   - Click speaker button to stop recording
4. In **"Pricing Assistant"**:
   - Choose category: "Textile"
   - Set material, size, intricacy (use defaults)
   - Enter labor hours: 6
5. Click **"Generate & Publish Listing"**

### Test 3: View as Buyer and See Translations

1. **Logout** from artisan account
2. Click **"Login"** tab
3. Select **"Buyer"** role
4. Login as a buyer (any test email/password)
5. You'll see the **"Buyer Dashboard"** with your listing
6. **Notice:**
   - The listing shows **"English"** and **"हिंदी"** descriptions
   - While loading, you'll see "translating..." text
   - After a few seconds, both translations appear
   - The original Hindi description is translated to English
   - The original Hindi description is preserved in Hindi

---

## How the Translation Works

### For Sellers (Artisans)

```
┌─────────────────────────┐
│ Artisan speaks/types    │
│ description in any      │
│ language (e.g., Tamil)  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Description saved to    │
│ listing in original     │
│ language                │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Listing published to    │
│ marketplace             │
└─────────────────────────┘
```

### For Buyers

```
┌─────────────────────────┐
│ Buyer opens marketplace │
│ and sees listings       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Frontend detects new    │
│ listings needing        │
│ translation             │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ For each listing,       │
│ fetch translation API   │
│ (English + Hindi)       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Show "translating..."   │
│ loading indicators      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Google Translate API    │
│ translates description  │
│ to EN and HI            │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Update DOM with         │
│ translations            │
│ Remove loading state    │
└─────────────────────────┘
```

---

## API Endpoint Reference

### Translate Buyer Bilingual

**Endpoint:** `POST /api/translate-buyer-bilingual`

**Request:**
```json
{
  "text": "यह एक सुंदर कढ़ाई वाली साड़ी है"
}
```

**Success Response (200):**
```json
{
  "english": "This is a beautiful embroidered saree",
  "hindi": "यह एक सुंदर कढ़ाई वाली साड़ी है",
  "source_length": 32
}
```

**Error Response (503 - API Not Configured):**
```json
{
  "error": "Translation service is not configured. Please check back later.",
  "english": "यह एक सुंदर कढ़ाई वाली साड़ी है",
  "hindi": "यह एक सुंदर कढ़ाई वाली साड़ी है"
}
```

---

## Troubleshooting

### Backend won't start
- **Ensure Python 3.7+** is installed: `python --version`
- **Install requirements:** `pip install -r requirements.txt`
- **Check Flask is running:** Look for "Running on http://127.0.0.1:5000"

### Translations not showing
1. **Check backend is running** on port 5000
2. **Verify API key is set** in `backend/.env`
3. **Check browser console** (F12 → Console) for errors
4. **Check backend logs** for translation errors

### API quota exceeded
- Google Translate API has free tier limits
- Check [Google Cloud Console](https://console.cloud.google.com/) billing/quotas
- Consider implementing translation caching

### Empty translations
- Ensure description text is not empty
- Check that the text is under 2000 characters
- Verify API key has permissions for Cloud Translation API

### Getting 503 error
- API key is not configured or invalid
- Set `GOOGLE_TRANSLATE_API_KEY` in `backend/.env`
- Restart backend server after changing `.env`

---

## Features Implemented

### Backend Features (`backend/app.py`)
✓ POST `/api/translate-buyer-bilingual` endpoint  
✓ Automatic language detection  
✓ Translation to English and Hindi  
✓ Error handling with fallback to original text  
✓ Request validation (empty text, length limit)  
✓ Timeout protection (15 seconds)  
✓ Detailed logging for debugging  

### Frontend Features (`frontend/index.html`)
✓ Loading indicators ("translating..." and "अनुवाद हो रहा है")  
✓ Translation API calls  
✓ Client-side caching of translations  
✓ Graceful degradation if backend unavailable  
✓ Error handling with fallback display  
✓ Bilingual description display on buyer dashboard  
✓ Helpful tip for sellers about auto-translation  

### UI/UX Improvements
✓ Loading animation while translating  
✓ Clean bilingual layout with English and Hindi blocks  
✓ Error messages in appropriate language  
✓ Language note at top of buyer dashboard  
✓ Tip in artisan voice cataloger section  

---

## Future Enhancements

1. **Support More Languages**
   - Extend beyond English/Hindi
   - Add Tamil, Telugu, Marathi, Bengali support for buyers

2. **Offline Translation**
   - Use browser-based translation models
   - Reduce dependency on external API

3. **Audio Translations**
   - Generate audio versions of translations
   - Text-to-speech in multiple languages

4. **Translation Quality Rating**
   - Allow buyers to rate translation quality
   - Feedback for improving translations

5. **Custom Terminology**
   - Support craft-specific vocabulary
   - Region-specific dialect support

6. **Bulk Translation**
   - Pre-translate all descriptions when artisan publishes
   - Store translations with listing

---

## Security Notes

⚠️ **API Key Security:**
- Never commit `backend/.env` to version control
- Keep `.env` file private
- Consider using Google Cloud IAM for production
- Rotate keys periodically

⚠️ **API Rate Limiting:**
- Implement rate limiting on production backend
- Monitor API usage in Google Cloud Console
- Set up billing alerts to avoid surprise charges

---

## Support & Questions

For issues or questions about the translation system:

1. Check the troubleshooting section above
2. Review backend logs for API errors
3. Check browser console (F12) for frontend errors
4. Verify `.env` configuration matches your API key

---

**Last Updated:** 2026-08-30  
**Platform:** artisan-connect-ai  
**Status:** ✅ Fully Implemented
