# 🇮🇳 Jan-Sahayak — AI-Powered Public Welfare Assistant

> **Bridging healthcare, mental wellness, and information gaps in rural India through AI.**

Jan-Sahayak is a multilingual, AI-powered platform built for **HACK4IMPACT** that delivers fact-checked information, telemedicine triage, mental health support, and anonymous peer counselling — accessible via **Web** and **Telegram Bot**.

---

## ✨ Features

### 🔎 Fact Checker (RAG-powered)
- Verify claims by typing text, pasting a URL, or uploading an image/screenshot.
- Uses a **Retrieval-Augmented Generation (RAG)** pipeline with **ChromaDB** and **Groq LLMs** for accurate, source-backed answers.
- OCR support via **Tesseract** for image-based fact-checking.
- Covers Indian government schemes, PIB fact-checks, and curated datasets.

### 🩺 Telemedicine & First-Aid Triage
- Describe symptoms in English, Hindi, or Hinglish.
- AI-powered severity assessment (**LOW / MODERATE / HIGH / EMERGENCY**).
- Life-saving first-aid steps for emergencies (snake bites, heart attacks, burns, bleeding, etc.).
- Recommends nearest doctor specialty and emergency transport (Ambulance 108).
- Keyword-based fallback ensures offline reliability.

### 🧠 Mental Health — AI Therapist
- Rogerian (person-centred) AI counsellor powered by **Llama 3.3 70B** via Groq.
- Crisis detection with immediate helpline sharing (iCall, AASRA, Vandrevala Foundation).
- Per-session conversation memory for continuity.
- Responds in Hindi, Hinglish, or English.

### 📔 Anonymous Diary
- Write and save personal journal entries anonymously.
- Mood tracking support.
- Entries stored locally per user.

### 💬 Anonymous Peer Chat
- Real-time anonymous peer-to-peer chat via **Socket.IO**.
- Queue-based matching system.
- Safe space for users to connect and share.

### 🤖 Telegram Bot
- Full access to all features directly from Telegram.
- Interactive keyboard menus for easy navigation.
- Image upload support for fact-checking.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask, Flask-SocketIO |
| **AI / LLM** | Groq API (Llama 3.3 70B, Llama 3.1 8B) |
| **RAG Pipeline** | LangChain, ChromaDB, Sentence-Transformers |
| **OCR** | Tesseract, Pillow |
| **PDF Ingestion** | PyMuPDF (fitz) |
| **Telegram Bot** | python-telegram-bot |
| **Frontend** | HTML, Tailwind CSS, Vanilla JS |

---

## 📁 Project Structure

```
HACK4IMPACT/
├── app.py                # Flask application entry point
├── telegram_bot.py       # Telegram bot (all features)
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not committed)
│
├── routes/               # Flask Blueprints
│   ├── fact_checker.py   # RAG-powered fact verification
│   ├── therapist.py      # AI therapist (Rogerian)
│   ├── telemedicine.py   # Symptom triage & first-aid
│   ├── diary.py          # Anonymous diary entries
│   └── peer_match.py     # Socket.IO peer chat
│
├── rag/                  # RAG pipeline
│   ├── dataprep.py       # PDF/text ingestion → ChromaDB
│   └── llmrag.py         # LLM query + retrieval logic
│
├── data/                 # Knowledge base (PDFs + text files)
│   ├── fact_checks.txt
│   └── govt_schemes.txt
│
├── templates/            # Frontend HTML pages
│   ├── new.html          # Landing page
│   ├── fact.html         # Fact checker UI
│   ├── health.html       # Mental health UI
│   └── med.html          # Telemedicine UI
│
└── static/               # Static assets (CSS, JS, images)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and in PATH

### Installation

```bash
# Clone the repository
git clone https://github.com/DeveloperKush/HACK4IMPACT.git
cd HACK4IMPACT

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

Get your API keys:
- **Groq API Key**: [console.groq.com](https://console.groq.com)
- **Telegram Bot Token**: Talk to [@BotFather](https://t.me/BotFather) on Telegram

### Running the Application

**1. Start the Flask server:**
```bash
python app.py
```
The server will build the RAG index from the `data/` folder and start on `http://localhost:5000`.

**2. Start the Telegram bot** (in a separate terminal):
```bash
python telegram_bot.py
```

---

## 🤖 Telegram Bot Usage

1. Search for your bot on Telegram and send `/start`.
2. Choose a service from the menu:
   - **Fact Checker** — Send text or an image to verify
   - **Telemedicine** — Describe symptoms for triage
   - **Mental Health** → Therapist, Diary, or Peer Chat

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/verify` | Verify a claim (text or image) |
| `POST` | `/fact-check/verify` | Verify a claim (Telegram bot) |
| `POST` | `/telemedicine/chat` | Symptom triage & first-aid |
| `POST` | `/mental-health/chat` | AI therapist conversation |
| `POST` | `/mental-health/reset` | Reset therapist session |
| `POST` | `/diary/save` | Save a diary entry |
| `GET`  | `/diary/<user_uuid>` | Retrieve diary entries |

---

## 👥 Team

Built with ❤️ for **HACK4IMPACT** hackathon at IIITD.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).