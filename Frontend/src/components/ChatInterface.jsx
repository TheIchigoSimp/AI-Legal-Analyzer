import { useState, useRef, useEffect } from "react";
import client from "../api/client";
import { showToast } from "./Toast";

export default function ChatInterface({ docId = null }) {
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef();

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Load sessions
    useEffect(() => {
        const params = docId ? { doc_id: docId } : {};
        client.get("/chat/sessions", { params })
            .then((res) => setSessions(res.data))
            .catch(console.error);
    }, [docId]);

    // Load session messages
    const loadSession = async (sid) => {
        setSessionId(sid);
        try {
            const res = await client.get(`/chat/sessions/${sid}/messages`);
            setMessages(res.data.map((m) => ({
                role: m.role,
                content: m.content,
                meta: m.meta,
            })));
        } catch (err) {
            console.error("Failed to load session", err);
        }
    };

    const startNewChat = () => {
        setSessionId(null);
        setMessages([]);
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const payload = {
                question: input,
                top_k: 5,
                session_id: sessionId || undefined,
            };
            if (docId) payload.doc_id = docId;

            const res = await client.post("/chat/send", payload);
            const data = res.data;

            if (!sessionId) {
                setSessionId(data.session_id);
                // Refresh sessions list
                const params = docId ? { doc_id: docId } : {};
                const sessRes = await client.get("/chat/sessions", { params });
                setSessions(sessRes.data);
            }

            const botMsg = {
                role: "assistant",
                content: data.answer,
                meta: {
                    referenced_clauses: data.referenced_clauses,
                    overall_risk: data.overall_risk,
                    confidence: data.confidence,
                },
            };
            setMessages((prev) => [...prev, botMsg]);
        } catch (err) {
            showToast("Failed to get response", "error");
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Sorry, something went wrong. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-layout">
            {/* Session sidebar */}
            <div className="chat-sidebar glass-card">
                <button className="btn btn-primary btn-sm chat-new-btn" onClick={startNewChat}>
                    + New Chat
                </button>
                <div className="chat-session-list">
                    {sessions.map((s) => (
                        <div
                            key={s.id}
                            className={`chat-session-item ${sessionId === s.id ? "active" : ""}`}
                            onClick={() => loadSession(s.id)}
                        >
                            <span className="session-title">{s.title}</span>
                            <span className="session-date">{new Date(s.created_at).toLocaleDateString()}</span>
                        </div>
                    ))}
                    {sessions.length === 0 && <p className="empty-text">No chat history</p>}
                </div>
            </div>

            {/* Chat area */}
            <div className="chat-container">
                <div className="chat-messages">
                    {messages.length === 0 && (
                        <div className="chat-empty">
                            <span>💬</span>
                            <p>{docId ? "Ask questions about this document" : "Ask questions across all your documents"}</p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`chat-bubble ${msg.role}`}>
                            <div className="bubble-content">{msg.content}</div>
                            {msg.meta && (
                                <div className="bubble-meta">
                                    <span className={`badge badge-${msg.meta.overall_risk?.toLowerCase()}`}>
                                        {msg.meta.overall_risk} Risk
                                    </span>
                                    <span className="meta-confidence">
                                        Confidence: {(msg.meta.confidence * 100).toFixed(0)}%
                                    </span>
                                    {msg.meta.referenced_clauses?.length > 0 && (
                                        <span className="meta-refs">
                                            📎 {msg.meta.referenced_clauses.length} clauses referenced
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div className="chat-bubble assistant">
                            <div className="bubble-content typing">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                <form className="chat-input-bar" onSubmit={sendMessage}>
                    <input
                        className="input chat-input"
                        placeholder={docId ? "Ask about this document..." : "Ask about your legal documents..."}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button className="btn btn-primary" type="submit" disabled={!input.trim() || loading}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
