"""
LangGraph workflow for RAG: retrieve → generate
"""
from typing import List, Dict, TypedDict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import os

# Try to use new langchain-huggingface package, fallback to old imports
try:
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
except ImportError:
    try:
        from langchain_community.chat_models import ChatHuggingFace
        from langchain_community.llms import HuggingFaceEndpoint
    except ImportError:
        ChatHuggingFace = None
        HuggingFaceEndpoint = None


class GraphState(TypedDict):
    """State for the RAG graph."""
    question: str
    context: List[Dict]
    answer: str


def retrieve_node(state: GraphState, vectorstore: FAISS, k: int = 6) -> Dict:
    """Retrieve relevant chunks from vectorstore."""
    question = state["question"]
    docs = vectorstore.similarity_search(question, k=k)
    
    paper_to_chunks = {}
    seen_texts = set()
    
    for doc in docs:
        text_key = doc.page_content[:100]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        
        paper_name = doc.metadata.get("paper", "Unknown")
        if paper_name not in paper_to_chunks:
            paper_to_chunks[paper_name] = []
        
        paper_to_chunks[paper_name].append({
            "text": doc.page_content,
            "meta": doc.metadata
        })
    
    context = []
    index = 1
    for paper_name, chunks in paper_to_chunks.items():
        combined_text = "\n\n".join([chunk["text"] for chunk in chunks])
        context.append({
            "text": combined_text,
            "meta": chunks[0]["meta"],
            "index": index,
            "chunk_count": len(chunks)
        })
        index += 1
    
    return {"context": context}


def generate_node(state: GraphState, llm) -> Dict:
    """Generate answer from context with citations."""
    question = state["question"]
    context = state["context"]
    
    context_text = "\n\n".join([
        f"[{item['index']}] {item['text']}"
        for item in context
    ])
    
    system_prompt = """You are a helpful research assistant. Answer the question based ONLY on the provided context. 
Always include numbered citations [1], [2], etc. that correspond to the source numbers in the context.
If information is not in the context, say so explicitly.
Format your answer clearly with proper citations."""
    
    user_prompt = f"""Context:
{context_text}

Question: {question}

Answer:"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        
        # Handle different response types
        if hasattr(response, 'content'):
            answer = response.content
        elif isinstance(response, str):
            answer = response
        elif hasattr(response, 'text'):
            answer = response.text
        else:
            answer = str(response)
        
        # Clean up the answer
        if not answer or answer.strip() == "":
            raise ValueError("Empty response from LLM")
            
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        import traceback
        traceback.print_exc()
        # If there's an error, try to get a simpler response
        try:
            # For Hugging Face models, use a simpler prompt format
            # FLAN-T5 models work better with question-answer format
            # Truncate context to avoid token limits
            context_snippet = context_text[:1500] if len(context_text) > 1500 else context_text
            
            combined_prompt = f"""Answer the following question based on the context provided.

Context: {context_snippet}

Question: {question}

Answer:"""
            
            # Try with just a single HumanMessage (no SystemMessage)
            simple_response = llm.invoke([HumanMessage(content=combined_prompt)])
            if hasattr(simple_response, 'content'):
                answer = simple_response.content
            elif isinstance(simple_response, str):
                answer = simple_response
            else:
                answer = str(simple_response)
            
            if not answer or answer.strip() == "":
                raise ValueError("Empty response from simplified prompt")
                
        except StopIteration as stop_err:
            # Handle StopIteration specifically - this happens with Hugging Face Inference API
            # Try to extract what we can from the sources
            answer = f"Based on the retrieved sources from your PDFs:\n\n"
            for idx, item in enumerate(context[:3], 1):
                answer += f"[{item['index']}] From {item['meta'].get('paper', 'Unknown')}: {item['text'][:300]}...\n\n"
            answer += "\nNote: The Hugging Face model had trouble generating a complete answer. Please review the sources above, or try switching to OpenAI provider for better results."
        except Exception as e2:
            error_msg2 = str(e2) if str(e2) else repr(e2)
            # Determine which provider is being used based on LLM type
            llm_type = type(llm).__name__
            if 'ChatGPTWebLLM' in llm_type or 'chatgpt' in str(type(llm)).lower():
                provider_name = "ChatGPT web app"
                suggestions = [
                    "1. Make sure you're logged into ChatGPT in the browser window that opened",
                    "2. Try refreshing the browser window and logging in again",
                    "3. The ChatGPT web interface may have changed - the selectors may need updating",
                    "4. Switch to OpenAI API provider (if you have quota) or Hugging Face provider"
                ]
            elif 'HuggingFace' in llm_type or 'huggingface' in str(type(llm)).lower():
                provider_name = "Hugging Face model"
                suggestions = [
                    "1. Switching to OpenAI provider (if you have quota)",
                    "2. Trying a different Hugging Face model (e.g., mistralai/Mistral-7B-Instruct-v0.2)",
                    "3. Switch to ChatGPT App provider"
                ]
            else:
                provider_name = "the language model"
                suggestions = [
                    "1. Try a different provider",
                    "2. Check your API keys and configuration",
                    "3. The retrieved sources are shown below - you can read them directly"
                ]
            
            # Provide a helpful error message with context
            answer = f"I apologize, but I encountered an error while generating an answer using {provider_name}. The system successfully retrieved relevant sources from your PDFs, but the language model had trouble generating a response.\n\nError details: {error_msg2 if error_msg2 else error_msg}\n\nYou can try:\n" + "\n".join(suggestions) + "\n\n4. The retrieved sources are shown below - you can read them directly."
    
    return {"answer": answer}


def create_graph(vectorstore: FAISS, llm, k: int = 6) -> StateGraph:
    """Create the LangGraph workflow."""
    workflow = StateGraph(GraphState)
    
    def retrieve_wrapper(state: GraphState):
        return retrieve_node(state, vectorstore, k=k)
    
    def generate_wrapper(state: GraphState):
        return generate_node(state, llm)
    
    workflow.add_node("retrieve", retrieve_wrapper)
    workflow.add_node("generate", generate_wrapper)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


def get_llm(provider: str = "openai", model: str = None, **kwargs):
    """Get LLM instance based on provider."""
    if provider.lower() == "openai":
        model = model.strip() if model else "gpt-4o-mini"
        
        allowed_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        if model not in allowed_models:
            raise ValueError(f"Invalid model: {model}. Allowed models: {', '.join(allowed_models)}")
        
        return ChatOpenAI(model=model, temperature=0, **kwargs)
    
    elif provider.lower() == "chatgpt" or provider.lower() == "chatgpt-web" or provider.lower() == "chatgpt_app":
        try:
            from chatgpt_web import ChatGPTWebLLM
        except ImportError as e:
            error_msg = str(e)
            if "playwright" in error_msg.lower():
                raise ValueError(
                    "ChatGPT Web integration requires playwright. "
                    "Install it with: pip install playwright && playwright install chromium"
                )
            else:
                raise ValueError(
                    f"Failed to import ChatGPT Web integration: {error_msg}. "
                    "Make sure playwright is installed: pip install playwright && playwright install chromium"
                )
        except Exception as e:
            raise ValueError(
                f"Failed to initialize ChatGPT Web integration: {str(e)}. "
                "Make sure playwright is installed: pip install playwright && playwright install chromium"
            )
        
        # Default to headless=False so users can see browser and login
        headless = kwargs.get("headless", os.getenv("CHATGPT_HEADLESS", "false").lower() == "true")
        timeout = kwargs.get("timeout", 60000)
        
        try:
            return ChatGPTWebLLM(headless=headless, timeout=timeout)
        except Exception as e:
            raise ValueError(
                f"Failed to create ChatGPT Web LLM instance: {str(e)}. "
                "Make sure playwright is installed: pip install playwright && playwright install chromium"
            )
    
    elif provider.lower() == "huggingface":
        if ChatHuggingFace is None or HuggingFaceEndpoint is None:
            raise ValueError("Hugging Face support not available. Please install langchain-huggingface: pip install langchain-huggingface")
        
        # Hugging Face free models via Inference API
        model = model.strip() if model else "mistralai/Mistral-7B-Instruct-v0.2"
        
        # Free models that work well for text generation via Inference API
        allowed_models = [
            "google/flan-t5-base",
            "google/flan-t5-large",
            "microsoft/DialoGPT-medium",
            "mistralai/Mistral-7B-Instruct-v0.2"
        ]
        
        hf_token = os.getenv("HUGGINGFACE_API_KEY")
        if not hf_token:
            raise ValueError("HUGGINGFACE_API_KEY not found in environment. Please set it in .env file. Get a free token at: https://huggingface.co/settings/tokens")
        
        try:
            # Use HuggingFaceEndpoint with Inference API (works with both old and new packages)
            # Adjust parameters based on model type
            if "flan-t5" in model.lower():
                # FLAN-T5 models work better with different parameters
                llm_endpoint = HuggingFaceEndpoint(
                    repo_id=model,
                    huggingfacehub_api_token=hf_token,
                    temperature=0.3,
                    max_new_tokens=150,
                    model_kwargs={"max_length": 256},
                    **kwargs
                )
            else:
                # Other models
                llm_endpoint = HuggingFaceEndpoint(
                    repo_id=model,
                    huggingfacehub_api_token=hf_token,
                    temperature=0.1,
                    model_kwargs={"max_length": 512},
                    **kwargs
                )
            # Wrap in ChatHuggingFace for compatibility
            return ChatHuggingFace(llm=llm_endpoint)
        except Exception as e:
            if model not in allowed_models:
                raise ValueError(f"Invalid Hugging Face model: {model}. Allowed models: {', '.join(allowed_models)}. Error: {e}")
            raise ValueError(f"Failed to initialize Hugging Face model {model}: {e}")
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: openai, huggingface, chatgpt")


def load_vectorstore(index_dir: str = "index/"):
    """Load FAISS vectorstore."""
    # Try to use the same embeddings as used during ingestion
    use_hf_embeddings = os.getenv("USE_HUGGINGFACE_EMBEDDINGS", "false").lower() == "true"
    
    # Try to import Hugging Face embeddings
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            HuggingFaceEmbeddings = None
    
    if use_hf_embeddings and HuggingFaceEmbeddings is not None:
        try:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            print(f"Warning: Failed to use Hugging Face embeddings: {e}")
            # Try OpenAI embeddings, but handle missing API key gracefully
            try:
                embeddings = OpenAIEmbeddings()
            except Exception as e2:
                raise ValueError(
                    f"Failed to initialize embeddings. Hugging Face failed: {e}. "
                    f"OpenAI also failed: {e2}. "
                    "Please set USE_HUGGINGFACE_EMBEDDINGS=true and ensure Hugging Face models are available, "
                    "or set OPENAI_API_KEY if you want to use OpenAI embeddings."
                )
    else:
        # Try OpenAI embeddings, but handle missing API key gracefully
        try:
            embeddings = OpenAIEmbeddings()
        except Exception as e:
            # If OpenAI fails, try to use Hugging Face as fallback
            print(f"Warning: OpenAI embeddings failed: {e}. Trying Hugging Face fallback...")
            if HuggingFaceEmbeddings is not None:
                try:
                    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                    embeddings = HuggingFaceEmbeddings(
                        model_name=model_name,
                        model_kwargs={'device': 'cpu'}
                    )
                    print("✓ Using Hugging Face embeddings as fallback")
                except Exception as e2:
                    raise ValueError(
                        f"Failed to initialize embeddings. OpenAI failed: {e}. "
                        f"Hugging Face fallback also failed: {e2}. "
                        "Please set USE_HUGGINGFACE_EMBEDDINGS=true or set OPENAI_API_KEY."
                    )
            else:
                raise ValueError(
                    f"Failed to initialize OpenAI embeddings: {e}. "
                    "Please set OPENAI_API_KEY or install langchain-huggingface for free embeddings."
                )
    
    vectorstore = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    return vectorstore
