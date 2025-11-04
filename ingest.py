"""
PDF Ingestion Pipeline
Reads PDFs from data/papers/, splits them, embeds, and stores in FAISS.
"""
import os
from pathlib import Path
from typing import List
import pickle

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_core.text_splitter import RecursiveCharacterTextSplitter

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import sys

# Try to import Hugging Face embeddings
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        HuggingFaceEmbeddings = None

load_dotenv()


def load_pdfs(papers_dir: str) -> List:
    """Load all PDFs from the papers directory."""
    papers_path = Path(papers_dir)
    if not papers_path.exists():
        papers_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {papers_dir}")
        return []
    
    documents = []
    pdf_files = list(papers_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {papers_dir}")
        return []
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for pdf_file in pdf_files:
        try:
            print(f"Loading: {pdf_file.name}")
            loader = PyPDFLoader(str(pdf_file))
            pages = loader.load()
            
            for page in pages:
                page.metadata["paper"] = pdf_file.stem
                page.metadata["source"] = str(pdf_file)
            
            documents.extend(pages)
            print(f"  Loaded {len(pages)} pages")
        except Exception as e:
            print(f"  Error loading {pdf_file.name}: {e}")
    
    return documents


def split_documents(documents: List, chunk_size: int = 1200, chunk_overlap: int = 200) -> List:
    """Split documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def create_faiss_index(chunks: List, index_dir: str = "index/"):
    """Create FAISS vector store and save it."""
    if not chunks:
        print("No chunks to index")
        return
    
    print("Creating embeddings...")
    
    # Check if we should use Hugging Face embeddings
    use_hf_embeddings = os.getenv("USE_HUGGINGFACE_EMBEDDINGS", "false").lower() == "true"
    
    if use_hf_embeddings and HuggingFaceEmbeddings is not None:
        try:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            print(f"Using Hugging Face embeddings: {model_name}")
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}
            )
            print("✓ Hugging Face embeddings initialized")
        except Exception as e:
            print(f"⚠ Error initializing Hugging Face embeddings: {e}")
            print("Falling back to OpenAI embeddings...")
            use_hf_embeddings = False
    
    if not use_hf_embeddings:
        try:
            embeddings = OpenAIEmbeddings()
            print("Using OpenAI embeddings")
        except Exception as e:
            print(f"❌ Error initializing OpenAI embeddings: {e}")
            print("Please check your .env file and ensure OPENAI_API_KEY is set correctly.")
            sys.exit(1)
    
    print("Building FAISS index...")
    print(f"  This may take a few minutes for {len(chunks)} chunks...")
    try:
        vectorstore = FAISS.from_documents(chunks, embeddings)
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower() or "429" in error_msg:
            print("\n" + "=" * 50)
            print("❌ OpenAI API Quota Exceeded")
            print("=" * 50)
            print("Your OpenAI API quota has been exceeded.")
            print("\nTo fix this:")
            print("1. Check your billing at: https://platform.openai.com/account/billing")
            print("2. Add credits or upgrade your plan")
            print("3. Once you have quota, run this script again")
            print("=" * 50)
        else:
            print(f"\n❌ Error creating embeddings: {e}")
            print("Please check your OpenAI API key and try again.")
        sys.exit(1)
    
    index_path = Path(index_dir)
    index_path.mkdir(parents=True, exist_ok=True)
    
    try:
        vectorstore.save_local(str(index_path))
        print(f"✓ Saved FAISS index to {index_dir}")
        
        metadata_file = index_path / "metadata.pkl"
        metadata = [{"text": chunk.page_content, "meta": chunk.metadata} for chunk in chunks]
        with open(metadata_file, "wb") as f:
            pickle.dump(metadata, f)
        print(f"✓ Saved metadata to {metadata_file}")
    except Exception as e:
        print(f"❌ Error saving index: {e}")
        sys.exit(1)


def main():
    """Main ingestion pipeline."""
    papers_dir = "data/papers"
    index_dir = "index"
    
    print("=" * 50)
    print("PDF Ingestion Pipeline")
    print("=" * 50)
    
    documents = load_pdfs(papers_dir)
    
    if not documents:
        print("No documents to process. Please add PDF files to data/papers/")
        return
    
    chunks = split_documents(documents, chunk_size=1200, chunk_overlap=200)
    create_faiss_index(chunks, index_dir=index_dir)
    
    print("=" * 50)
    print("✓ Ingestion complete!")
    print("=" * 50)
    print("\nYou can now start the server and ask questions!")
    print("Run: python server.py")


if __name__ == "__main__":
    main()
