"""
Flask backend for PDF RAG system
"""
import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

from graph import create_graph, get_llm, load_vectorstore

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

vectorstore = None
graph = None
current_settings = None

def reset_graph_cache():
    """Reset the graph cache to force recreation."""
    global graph, current_settings
    graph = None
    current_settings = None


def init_vectorstore():
    """Initialize the vectorstore."""
    global vectorstore
    if vectorstore is None:
        index_dir = "index"
        if not Path(index_dir).exists():
            raise ValueError(f"Index directory '{index_dir}' not found. Please run ingest.py first.")
        
        vectorstore = load_vectorstore(index_dir)
    return vectorstore


def get_or_create_graph(provider="openai", model=None, k=6):
    """Get or create graph with given settings."""
    global graph, current_settings, vectorstore
    
    if vectorstore is None:
        vectorstore = init_vectorstore()
    
    settings = (provider, model, k)
    
    # Always recreate graph if settings changed
    if graph is None or current_settings != settings:
        llm = get_llm(provider=provider, model=model)
        graph = create_graph(vectorstore, llm, k=k)
        current_settings = settings
    
    return graph


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Server is running"})


@app.route("/api/index/status", methods=["GET"])
def index_status():
    """Check if index is loaded."""
    try:
        if vectorstore is None:
            init_vectorstore()
        return jsonify({
            "status": "loaded",
            "message": "Index is loaded and ready"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/index/load", methods=["POST"])
def load_index():
    """Load the index."""
    global vectorstore, graph, current_settings
    try:
        vectorstore = init_vectorstore()
        graph = None
        current_settings = None
        return jsonify({
            "status": "success",
            "message": "Index loaded successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/ask", methods=["POST"])
def ask_question():
    """Ask a question and get answer with citations."""
    try:
        data = request.get_json()
        
        if not data or "question" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'question' in request body"
            }), 400
        
        question = data["question"]
        provider = data.get("provider", "openai")
        model = data.get("model", None)
        
        if model:
            model = model.strip()
        if not model:
            # Set default based on provider
            if provider.lower() == "huggingface":
                model = "mistralai/Mistral-7B-Instruct-v0.2"
            elif provider.lower() == "chatgpt" or provider.lower() == "chatgpt-web" or provider.lower() == "chatgpt_app":
                model = "default"
            else:
                model = "gpt-4o-mini"
        
        k = data.get("k", 6)
        
        # Reset graph cache if provider changed to ensure we use the right LLM
        if current_settings and current_settings[0] != provider.lower():
            reset_graph_cache()
        
        try:
            graph = get_or_create_graph(provider=provider, model=model, k=k)
        except Exception as e:
            error_msg = str(e)
            if "index" in error_msg.lower() or "not found" in error_msg.lower():
                return jsonify({
                    "status": "error",
                    "message": "Index not found. Please run 'python ingest.py' to create the index."
                }), 400
            elif "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                return jsonify({
                    "status": "error",
                    "message": f"OpenAI API quota exceeded. Make sure you're using the ChatGPT App provider, not OpenAI API. Error: {error_msg}"
                }), 400
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to initialize: {error_msg}"
                }), 500
        
        initial_state = {
            "question": question,
            "context": [],
            "answer": ""
        }
        
        try:
            result = graph.invoke(initial_state)
        except Exception as e:
            raise
        
        seen_papers = {}
        sources_list = []
        
        for item in result.get("context", []):
            paper_name = item["meta"].get("paper", "Unknown")
            if paper_name not in seen_papers:
                seen_papers[paper_name] = True
                sources_list.append({
                    "index": item["index"],
                    "paper": paper_name,
                    "source": item["meta"].get("source", "N/A"),
                    "text": item["text"][:500] + "..." if len(item["text"]) > 500 else item["text"],
                    "chunk_count": item.get("chunk_count", 1)
                })
        
        return jsonify({
            "status": "success",
            "question": question,
            "answer": result["answer"],
            "sources": sources_list
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/providers", methods=["GET"])
def get_providers():
    """Get available LLM providers and models."""
    return jsonify({
        "providers": {
            "openai": {
                "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                "default": "gpt-4o-mini"
            },
            "huggingface": {
                "models": [
                    "mistralai/Mistral-7B-Instruct-v0.2",
                    "google/flan-t5-large",
                    "google/flan-t5-base",
                    "microsoft/DialoGPT-medium"
                ],
                "default": "mistralai/Mistral-7B-Instruct-v0.2"
            },
            "chatgpt": {
                "models": ["default"],
                "default": "default",
                "note": "Uses ChatGPT web app (requires manual login)"
            }
        }
    })


@app.route("/", methods=["GET"])
def serve_index():
    """Serve the frontend index.html."""
    return send_file('frontend/index.html')

@app.route("/<path:path>")
def serve_frontend(path):
    """Serve frontend static files (CSS, JS, etc.)."""
    # Skip API routes
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    
    try:
        file_path = Path('frontend') / path
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path))
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 404


if __name__ == "__main__":
    try:
        vectorstore = init_vectorstore()
        print("✓ Index loaded successfully")
    except Exception as e:
        print(f"⚠ Index not loaded: {e}")
        print("  Run 'python ingest.py' first")
    
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
