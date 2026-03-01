import { useState, useRef, useEffect } from "react";
import client from "../api/client";

export default function ChatInterface({ docId = null }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef();

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

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
            };
            if (docId) payload.doc_id = docId;

            const res = await client.post("/query/", payload);
            const data = res.data;

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
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Sorry, something went wrong. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
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
    );
}
