# Drobe — AI-Powered Wardrobe Manager

Drobe is a desktop app that helps you manage your wardrobe and plan outfits using AI. Add your clothes with photos, track how many times you've worn each item before it needs a wash, and describe a vibe or event to get a personalised outfit suggestion powered by Google Gemini — all from your own machine.

---

## Features

- 👕 **Wardrobe Catalog** — Add clothes with photos and descriptions, stored locally
- 🧺 **Laundry Tracker** — Log wears and automatically mark items as unavailable when they need washing
- ✨ **AI Outfit Suggestions** — Describe a vibe ("smart casual coffee date") and Gemini suggests an outfit from your actual available clothes
- 🗑️ **Remove Items** — Clean up your wardrobe as needed

---

## Setup

### 1. Clone the repo
```
git clone https://github.com/mananchothani2006/AI-driven_Wardrobe.git
cd AI-driven_Wardrobe
```

### 2. Install dependencies
```
pip install customtkinter pillow google-genai python-dotenv tkinterweb markdown
```

### 3. Add your Gemini API key
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```
Get a free API key at [aistudio.google.com](https://aistudio.google.com)

### 4. Run the app
```
python app.py
```

---

## Project Structure

```
├── app.py        # Desktop UI (CustomTkinter)
├── main.py       # Backend logic and Gemini integration
├── .env          # Your API key (not committed)
├── clothes.json  # Auto-generated wardrobe data
└── wardrobe/     # Auto-generated folder for clothing images
```

---

## Tech Stack

- Python, CustomTkinter, Pillow
- Google Gemini API (gemini-3.6-flash)
- JSON for local data persistence
