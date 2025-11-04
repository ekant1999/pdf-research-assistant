const { useState, useEffect, useRef } = React;

const API_BASE = 'http://localhost:5001/api';

function App() {
    const chatHistoryRef = useRef(null);
    const [provider, setProvider] = useState('huggingface');
    const [model, setModel] = useState('mistralai/Mistral-7B-Instruct-v0.2');
    const [k, setK] = useState(6);
    const [indexStatus, setIndexStatus] = useState('loading');
    const [question, setQuestion] = useState('');
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Provider-specific models
    const providerModels = {
        openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
        huggingface: ['mistralai/Mistral-7B-Instruct-v0.2', 'google/flan-t5-large', 'google/flan-t5-base', 'microsoft/DialoGPT-medium']
    };

    // Update model when provider changes
    useEffect(() => {
        const defaultModel = provider === 'openai' ? 'gpt-4o-mini' : 'mistralai/Mistral-7B-Instruct-v0.2';
        setModel(defaultModel);
    }, [provider]);

    // Auto-load index on mount
    useEffect(() => {
        loadIndex();
    }, []);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [history, loading]);


    const checkIndexStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/index/status`);
            const data = await response.json();
            setIndexStatus(data.status === 'loaded' ? 'loaded' : 'error');
            setError(data.status === 'error' ? data.message : null);
        } catch (err) {
            setIndexStatus('error');
            setError('Failed to connect to server');
        }
    };

    const loadIndex = async () => {
        setIndexStatus('loading');
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/index/load`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.status === 'success') {
                setIndexStatus('loaded');
            } else {
                setIndexStatus('error');
                // Don't show error if index doesn't exist yet - that's expected
                if (!data.message.includes('not found')) {
                    setError(data.message);
                }
            }
        } catch (err) {
            setIndexStatus('error');
            // Silently fail - index will be loaded when needed
        }
    };

    const askQuestion = async () => {
        if (!question.trim() || loading) return;

        setLoading(true);
        setError(null);
        const currentQuestion = question;
        setQuestion('');

        try {
            const response = await fetch(`${API_BASE}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: currentQuestion,
                    provider: provider,
                    model,
                    k
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                setHistory([...history, {
                    question: currentQuestion,
                    answer: data.answer,
                    sources: data.sources
                }]);
            } else {
                setError(data.message || 'Failed to get answer');
                // Still add to history with error message
                setHistory([...history, {
                    question: currentQuestion,
                    answer: `Error: ${data.message || 'Failed to get answer'}`,
                    sources: []
                }]);
            }
        } catch (err) {
            const errorMsg = 'Failed to connect to server. Make sure the backend is running on http://localhost:5001';
            setError(errorMsg);
            setHistory([...history, {
                question: currentQuestion,
                answer: `Error: ${errorMsg}`,
                sources: []
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        // Handle key press (legacy support)
        if (e.key === 'Enter' && !e.shiftKey && !loading && question.trim()) {
            e.preventDefault();
            askQuestion();
        }
    };

    return (
        <div className="container">
            <div className="header">
                <h1>📚 PDF Research Assistant</h1>
                <p>Ask questions about your research papers and get answers with citations</p>
            </div>
            
            <div className="content">
                <div className="sidebar">
                    <h2>⚙️ Configuration</h2>
                    
                    <div className="config-section">
                        <label>Provider</label>
                        <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                            <option value="huggingface">Hugging Face (Free)</option>
                            <option value="openai">OpenAI</option>
                        </select>
                    </div>

                    <div className="config-section">
                        <label>Model</label>
                        <select value={model} onChange={(e) => setModel(e.target.value)}>
                            {providerModels[provider]?.map(m => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                    </div>

                    <div className="config-section">
                        <label>Number of Chunks (k): {k}</label>
                        <div className="slider-container">
                            <input
                                type="range"
                                min="3"
                                max="15"
                                value={k}
                                onChange={(e) => setK(parseInt(e.target.value))}
                            />
                            <div className="slider-value">{k}</div>
                        </div>
                    </div>


                    <div className="config-section">
                        <h3 style={{fontSize: '0.9em', marginTop: '20px', marginBottom: '10px'}}>📖 Instructions</h3>
                        <p style={{fontSize: '0.85em', color: '#666', lineHeight: '1.6'}}>
                            1. Add PDFs to <code>data/papers/</code><br/>
                            2. Run <code>python ingest.py</code><br/>
                            3. Ask questions!
                        </p>
                    </div>
                </div>

                <div className="main-content">
                    <div className="chat-container">
                        <div className="chat-history" ref={chatHistoryRef}>
                            {history.length === 0 && !loading && (
                                <div className="empty-state">
                                    <h3>👋 Welcome!</h3>
                                    <p>Start by asking a question about your research papers.</p>
                                </div>
                            )}
                            
                            {history.map((item, idx) => (
                                <div key={idx}>
                                    <div className="message">
                                        <div className="question">
                                            {item.question}
                                        </div>
                                    </div>
                                    <div className="message">
                                        <div className="answer">
                                            <div dangerouslySetInnerHTML={{__html: item.answer.replace(/\n/g, '<br/>')}} />
                                            {item.sources && item.sources.length > 0 && (
                                                <div className="sources" style={{marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e9ecef'}}>
                                                    <div className="sources-title" style={{fontSize: '0.85em', fontWeight: 600, marginBottom: '8px', color: '#6c757d'}}>📄 Sources:</div>
                                                    {item.sources.map((source, sidx) => (
                                                        <div key={sidx} className="source-item" style={{background: '#f8f9fa', padding: '8px 12px', borderRadius: '8px', marginBottom: '6px', fontSize: '0.85em'}}>
                                                            <strong style={{color: '#2563eb'}}>[{source.index}]</strong> {source.paper}
                                                            {source.chunk_count > 1 && (
                                                                <span style={{color: '#6c757d', fontSize: '0.8em', marginLeft: '8px'}}>
                                                                    ({source.chunk_count} chunks)
                                                                </span>
                                                            )}
                                                            <small style={{display: 'block', color: '#6c757d', marginTop: '4px', fontSize: '0.85em'}}>{source.source.split('/').pop()}</small>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            
                            {loading && (
                                <div className="message">
                                    <div className="loading">Thinking...</div>
                                </div>
                            )}
                        </div>

                        {error && (
                            <div className="message">
                                <div className="answer" style={{background: '#fee', borderColor: '#fcc', color: '#c33'}}>
                                    ⚠️ {error}
                                </div>
                            </div>
                        )}

                        <div className="input-container">
                            <input
                                type="text"
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                onKeyPress={handleKeyPress}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey && !loading && question.trim()) {
                                        e.preventDefault();
                                        askQuestion();
                                    }
                                }}
                                placeholder="Ask a question about your papers..."
                                disabled={loading}
                                autoFocus
                            />
                            <button
                                className="btn btn-primary"
                                onClick={askQuestion}
                                disabled={loading || !question.trim()}
                                type="button"
                            >
                                {loading ? '⏳ Asking...' : '🚀 Ask'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));

