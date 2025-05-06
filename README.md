# 🧠 Virtual Teaching Assistant – Server (Flask Backend)

This is the **Flask-based backend** for the **Virtual Teaching Assistant** platform, a smart educational system that uses AI to transcribe lectures, generate summaries, create quizzes, and parse learning materials.

---

## 🚀 Features

- 🎤 **Audio Upload & Transcription** – Accept `.wav` files and transcribe using OpenAI Whisper
- 🧾 **AI-Powered Summarization** – Summarize transcripts using LLMs (LLaMA 3 via Groq API)
- 🧪 **Quiz Generation** – Extract questions from lecture content with retry logic
- 📂 **PDF Parsing** – Extract text from uploaded PDFs using `pdfplumber`
- 🔗 **RESTful API** – Clean endpoints for frontend interaction
- 🌐 **Cross-Origin Support** – Enabled via `Flask-CORS`
- 🔐 **Environment-based Config** – Secure API keys via `.env`

---

## 🛠️ Tech Stack

| Category            | Tech/Library                         |
|---------------------|---------------------------------------|
| 🖥️ Server Framework | `Flask`, `waitress` (production WSGI) |
| 🎶 Audio Processing  | `ffmpeg`, `whisper`, `pydub`, `noisereduce`, `soundfile`, `scipy` |
| 💬 LLM Integration   | `langchain`, `langchain_groq`, `langchain_experimental`, `llama3` |
| 📝 NLP Utilities     | Custom prompt chaining via `langchain` |
| 📄 File Parsing      | `pdfplumber` for PDF content extraction |
| 🔐 Environment Mgmt  | `python-dotenv`                      |
| 🌍 CORS Handling     | `Flask-CORS`                         |

---

## 🔧 Setup Instructions

### ✅ Prerequisites

* Python 3.9+
* FFmpeg installed (for audio preprocessing)
* `.env` file with your Groq API key

### 🧪 Installation

```bash
# Clone and enter project
cd server-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 📄 .env Example

```
GROQ_API_KEY=your_groq_api_key_here
```

---

## ▶️ Running the Server

```bash
python app.py
```

Runs at: [http://localhost:5000](http://localhost:5000)

---

## 🌐 API Endpoints

| Method  | Endpoint         | Description                                    |
| ------- | ---------------- | ---------------------------------------------- |
| 📤 POST | `/getTranscript` | Upload `.wav` file and generate summary + quiz |
| 📝 POST | `/summary`       | Generate summary JSON from transcript          |
| 🧪 POST | `/quiz`          | Generate quiz JSON from transcript             |
| 📄 POST | `/pdf`           | Extract raw text from uploaded PDF file        |


---

## 🧪 Testing & Debugging

* Use Swagger alternatives like [Postman](https://www.postman.com/) to test endpoints.
* Debug statements included in logs for API calls to internal services.

---

## 🛡️ Production Deployment

You can deploy using:

* `waitress` (already integrated)
* Docker (optional Dockerfile)
* Render, Heroku, or any Linux server with Python 3.9+

Example production run:

```bash
waitress-serve --host 0.0.0.0 --port 5000 app:app
```

---

## 🤝 Contributing

We welcome all contributors! You can:

* 🔍 File bugs
* 🌱 Suggest improvements
* 📦 Submit pull requests

---

### 👩‍🏫 Let's build better classrooms with AI — one lecture at a time! 🚀
