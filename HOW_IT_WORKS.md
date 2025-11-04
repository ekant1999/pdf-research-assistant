››# How This Project Works

## Overview

This is a **RAG (Retrieval-Augmented Generation)** system that lets you ask questions about research papers stored as PDFs. It combines semantic search with LLM generation to provide answers with citations.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PDFs      │ --> │  Ingestion  │ --> │   FAISS     │
│ data/papers │     │  ingest.py  │     │   Index     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │ <-> │ Flask API   │ <-> │  LangGraph  │
│  frontend/  │     │  server.py  │     │  graph.py   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │     LLM      │
                                        │   (OpenAI)   │
                                        └─────────────┘
```

## Workflow

### 1. Ingestion Phase (`ingest.py`)

**What happens:**
1. Reads all PDFs from `data/papers/`
2. Extracts text from each page
3. Splits text into chunks (1200 chars, 200 overlap)
4. Creates embeddings for each chunk using OpenAI
5. Stores embeddings in FAISS vector database
6. Saves metadata (paper name, source path) for each chunk

**Result:** A searchable vector index of all document chunks

### 2. Query Phase (LangGraph Workflow)

**When you ask a question:**

#### Step 1: Retrieve (`retrieve_node`)
- Takes your question
- Embeds it using the same embedding model
- Searches FAISS for the k most similar chunks (default: k=6)
- Returns chunks with their metadata

#### Step 2: Generate (`generate_node`)
- Takes retrieved chunks and your question
- Formats them with numbered citations [1], [2], etc.
- Sends to OpenAI LLM
- LLM generates answer based ONLY on the provided context
- Includes citations in the answer

### 3. Frontend Flow

1. User types question in React UI
2. React sends POST to `/api/ask` with:
   - Question
   - OpenAI model name
   - k (number of chunks to retrieve)
3. Flask backend:
   - Initializes LangGraph workflow
   - Runs retrieve → generate
   - Returns answer + sources
4. React displays answer with citations

## Why All Sources Might Be the Same

If you see the same paper cited multiple times, it's because:

1. **Multiple chunks from same paper are relevant** - The retrieval found k=6 chunks that are all from the same document because that document is highly relevant to your question

2. **This is normal behavior** - Different chunks from the same paper can contain different information, so citing them separately is useful

3. **To get more diverse sources:**
   - Increase k (number of chunks) in the UI slider
   - The system will retrieve more chunks, potentially from different papers

## Key Components

### `ingest.py`
- PDF loading and parsing
- Text chunking
- Embedding creation
- FAISS index creation

### `graph.py`
- LangGraph workflow definition
- State management (question → context → answer)
- Retrieve and generate nodes
- LLM provider abstraction

### `server.py`
- Flask REST API
- Endpoints for health, index status, asking questions
- Graph initialization and execution
- Error handling

### `frontend/app.jsx`
- React UI components
- State management (provider, model, history)
- API calls to backend
- Chat interface with message bubbles

## Data Flow Example

**Question:** "What is LLM?"

1. **Retrieve:** 
   - Searches FAISS for chunks similar to "What is LLM?"
   - Finds 6 chunks (e.g., all from "Make Your LLM Fully Utilize the Context.pdf")
   - Returns chunks with metadata

2. **Generate:**
   - Formats chunks as:
     ```
     [1] Chunk 1 text from the paper...
     [2] Chunk 2 text from the paper...
     ...
     [6] Chunk 6 text from the paper...
     ```
   - Sends to LLM: "Answer: What is LLM? Based on context..."
   - LLM generates answer with citations [1], [2], etc.

3. **Display:**
   - Frontend shows answer with numbered citations
   - Shows sources list below

## Why This Architecture?

- **RAG (Retrieval-Augmented Generation):** Better than pure LLM because:
  - LLM doesn't need to remember all your papers
  - Can work with large document sets
  - Provides traceable citations
  - More accurate (LLM answers only from provided context)

- **LangGraph:** 
  - Clean separation of retrieve and generate steps
  - Easy to extend (add reranking, filtering, etc.)
  - State management built-in

- **FAISS:**
  - Fast similarity search
  - Handles large vector databases
  - Efficient nearest neighbor search

## Configuration

- **Embeddings:** OpenAI (text-embedding-3-small)
- **LLM:** OpenAI (gpt-4o-mini, gpt-4o, or gpt-3.5-turbo)
- **Chunking:** 1200 chars with 200 overlap (configurable in `ingest.py`)
- **Retrieval:** k=6 chunks (configurable in UI)

