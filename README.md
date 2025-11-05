# PDF Research Assistant

A RAG (Retrieval-Augmented Generation) system for querying research papers stored as PDFs. Built with LangGraph, FAISS, ChatGPT Web App, Flask, and React.

## Features

- 📄 Ingest multiple PDFs from a folder
- 🔍 Semantic search with FAISS vector store
- 🤖 ChatGPT Web App integration (no API key required!)
- 📝 Answers with numbered citations [1], [2], etc.
- 🎨 Clean React UI with Flask backend
- 💾 Persistent ChatGPT session (login once, use forever)

## Architecture

- **Backend**: Flask REST API (`server.py`)
- **Frontend**: Simple React UI (no build tools needed)
- **RAG Pipeline**: LangGraph workflow (retrieve → generate)
- **Vector Store**: FAISS
- **LLM**: ChatGPT Web App via Playwright automation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

**For ChatGPT Web App (Recommended - No API Key Required):**

Edit `.env` and configure embeddings:

```bash
# Use Hugging Face embeddings (free, no API key needed)
USE_HUGGINGFACE_EMBEDDINGS=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: ChatGPT web app settings
CHATGPT_HEADLESS=false  # Set to true to run browser in background
```

**For OpenAI API (Alternative):**

If you prefer using OpenAI API for embeddings:

```bash
OPENAI_API_KEY=your_api_key_here
USE_HUGGINGFACE_EMBEDDINGS=false
```

### 3. Add PDFs

Place your PDF files in `data/papers/`:

```bash
mkdir -p data/papers
# Copy your PDFs here
```

### 4. Ingest PDFs

Run the ingestion script to process PDFs and create the vector index:

```bash
python ingest.py
```

This will:
- Read all PDFs from `data/papers/`
- Split them into chunks (1200 chars, 200 overlap)
- Create embeddings using Hugging Face (or OpenAI if configured)
- Save FAISS index to `index/`

### 5. Start Backend Server

```bash
python server.py
```

The server will start on `http://localhost:5001`

### 6. First-Time ChatGPT Login

When you first use the ChatGPT App provider:

1. A browser window will open automatically
2. You'll see ChatGPT's login page
3. **Log in to your ChatGPT account** in the browser window
4. The system will wait for you to complete login (up to 5 minutes)
5. Your session will be saved in `~/.chatgpt-browser` for future use
6. You only need to log in once!

### 7. Open Frontend

The Flask server also serves the frontend. Simply open:

```
http://localhost:5001
```

Or serve it manually:

```bash
# Option 1: Python
cd frontend
python -m http.server 8000

# Option 2: Node.js
cd frontend
npx http-server -p 8000

# Then open http://localhost:8000
```

## Usage

1. Open the frontend in your browser (`http://localhost:5001`)
2. Select **"ChatGPT App"** from the Provider dropdown
3. The index is automatically loaded when the page opens
4. Ask questions about your papers
5. Get answers with citations!

**Note**: The first time you use ChatGPT App, you'll need to log in. After that, your session is saved and you won't need to log in again.

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/index/status` - Check if index is loaded
- `POST /api/index/load` - Load the index
- `POST /api/ask` - Ask a question
  ```json
  {
    "question": "What are the main findings?",
    "provider": "chatgpt",
    "model": "default",
    "k": 6
  }
  ```
- `GET /api/providers` - Get available providers and models

## LLM Provider

### ChatGPT Web App (Recommended)

- **Requires**: ChatGPT account (free)
- **Setup**: Playwright + one-time login
- **Cost**: Free (with your ChatGPT account)
- **API Key**: Not required
- **Session**: Persistent (login once, use forever)

**Advantages:**
- ✅ No API key needed
- ✅ Free to use (with ChatGPT account)
- ✅ No usage limits (subject to ChatGPT's terms)
- ✅ Full access to ChatGPT's capabilities

**Note**: The browser runs in non-headless mode by default so you can see and interact with it. Set `CHATGPT_HEADLESS=true` in `.env` to run in background.

### Alternative Providers

The system also supports:
- **OpenAI API**: Requires `OPENAI_API_KEY`, pay-per-use
- **Hugging Face**: Free models via Inference API, requires `HUGGINGFACE_API_KEY`

## Project Structure

```
.
├── data/
│   └── papers/          # Place PDFs here
├── frontend/             # React frontend
│   ├── index.html
│   ├── app.jsx
│   └── styles.css
├── index/               # FAISS index (created after ingestion)
├── chatgpt_web.py       # ChatGPT web app integration
├── ingest.py            # PDF ingestion pipeline
├── graph.py             # LangGraph workflow
├── server.py             # Flask backend
├── requirements.txt     # Dependencies
├── CHATGPT_WEB_SETUP.md # Detailed ChatGPT setup guide
└── .env                 # Environment variables
```

## Requirements

- Python 3.10+
- Playwright + Chromium (for ChatGPT web app)
- ChatGPT account (free)
- Modern web browser (for React frontend)

## Development

### Backend Development
```bash
python server.py
```

### Frontend Development
The frontend uses React via CDN (no build step needed). Just edit `frontend/app.jsx` and refresh the browser.

For production, you might want to:
1. Build React with a bundler (Vite, Webpack, etc.)
2. Serve static files from Flask
3. Use a reverse proxy (nginx)

## License

MIT
