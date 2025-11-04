# PDF Research Assistant

A RAG (Retrieval-Augmented Generation) system for querying research papers stored as PDFs. Built with LangGraph, FAISS, OpenAI, Flask, and React.

## Features

- 📄 Ingest multiple PDFs from a folder
- 🔍 Semantic search with FAISS vector store
- 🤖 OpenAI LLM support
- 📝 Answers with numbered citations [1], [2], etc.
- 🎨 Clean React UI with Flask backend

## Architecture

- **Backend**: Flask REST API (`server.py`)
- **Frontend**: Simple React UI (no build tools needed)
- **RAG Pipeline**: LangGraph workflow (retrieve → generate)
- **Vector Store**: FAISS

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
PORT=5000  # Optional, defaults to 5000
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
- Create embeddings using OpenAI
- Save FAISS index to `index/`

### 5. Start Backend Server

```bash
python server.py
```

The server will start on `http://localhost:5001` (or the port specified in `.env`)

### 6. Open Frontend

Simply open `frontend/index.html` in your browser, or serve it with a simple HTTP server:

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

1. Open the frontend in your browser
2. Select your preferred OpenAI model in the sidebar
3. The index is automatically loaded when the page opens
4. Ask questions about your papers
5. Get answers with citations!

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/index/status` - Check if index is loaded
- `POST /api/index/load` - Load the index
- `POST /api/ask` - Ask a question
  ```json
  {
    "question": "What are the main findings?",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "k": 6
  }
  ```
- `GET /api/providers` - Get available providers and models

## LLM Provider

### OpenAI
- Models: gpt-4o-mini, gpt-4o, gpt-3.5-turbo
- Requires: `OPENAI_API_KEY` in `.env`
- Used for both embeddings and LLM generation

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
├── ingest.py            # PDF ingestion pipeline
├── graph.py             # LangGraph workflow
├── server.py             # Flask backend
├── requirements.txt     # Dependencies
└── .env                 # Environment variables
```

## Requirements

- Python 3.10+
- OpenAI API key (for embeddings and LLM generation)
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
