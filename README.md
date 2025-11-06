# PDF Research Assistant

A RAG (Retrieval-Augmented Generation) system for querying research papers stored as PDFs. Built with LangGraph, FAISS, ChatGPT Web App, Flask, and React.

## Features

- 📄 Ingest multiple PDFs from a folder
- 🔍 Semantic search with FAISS vector store
- 🤖 ChatGPT Web App integration (no API key required!)
- 📝 Answers with numbered citations [1], [2], etc.
- 🎨 Clean React UI with Flask backend
- 💾 Persistent ChatGPT session (login once, use forever)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file (or copy from `.env.example`):

```bash
# Use Hugging Face embeddings (free, no API key needed)
USE_HUGGINGFACE_EMBEDDINGS=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: ChatGPT web app settings
CHATGPT_HEADLESS=false  # Set to true to run browser in background
```

### 3. Add PDFs and Ingest

```bash
# Place PDFs in data/papers/
mkdir -p data/papers
# Copy your PDFs here

# Process PDFs and create vector index
python ingest.py
```

### 4. Start Server

```bash
python server.py
```

Server runs on `http://localhost:5001`

### 5. First-Time Setup

1. Open `http://localhost:5001` in your browser
2. Select **"ChatGPT App"** from the Provider dropdown
3. A browser window will open for ChatGPT login (one-time only)
4. Log in to your ChatGPT account
5. Your session is saved for future use

## Usage

1. Open `http://localhost:5001` in your browser
2. Ask questions about your papers
3. Get answers with citations!

## Architecture

- **Backend**: Flask REST API (`server.py`)
- **Frontend**: React UI (no build step needed)
- **RAG Pipeline**: LangGraph workflow (retrieve → generate)
- **Vector Store**: FAISS
- **LLM**: ChatGPT Web App via Playwright automation

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/index/status` - Check if index is loaded
- `POST /api/index/load` - Load the index
- `POST /api/ask` - Ask a question
  ```json
  {
    "question": "What are the main findings?",
    "k": 6
  }
  ```

## LLM Provider

### ChatGPT Web App (Recommended)

- ✅ No API key needed
- ✅ Free (with ChatGPT account)
- ✅ Persistent session (login once)
- ⚠️ Requires Playwright + Chromium

**Note**: Browser runs in non-headless mode by default. Set `CHATGPT_HEADLESS=true` in `.env` to run in background.

## Project Structure

```
.
├── data/papers/          # Place PDFs here
├── frontend/             # React frontend
├── index/                # FAISS index (created after ingestion)
├── chatgpt_web.py        # ChatGPT web app integration
├── ingest.py             # PDF ingestion pipeline
├── graph.py              # LangGraph workflow
├── server.py             # Flask backend
└── requirements.txt      # Dependencies
```

## Requirements

- Python 3.10+
- Playwright + Chromium
- ChatGPT account (free)

## Troubleshooting

**"Failed to initialize ChatGPT Web LLM"**
- Make sure Playwright is installed: `pip install playwright && playwright install chromium`

**"Broken pipe" error**
- The system automatically retries on connection errors
- Make sure you're logged into ChatGPT
- Try refreshing the page

**Index not found**
- Run `python ingest.py` to create the index

## License

MIT
