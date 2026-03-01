import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import Navbar from "../components/Navbar";
import ClauseCard from "../components/ClauseCard";
import ChatInterface from "../components/ChatInterface";

export default function DocumentPage() {
    const { docId } = useParams();
    const [doc, setDoc] = useState(null);
    const [clauses, setClauses] = useState([]);
    const [activeTab, setActiveTab] = useState("analysis");
    const [analyzing, setAnalyzing] = useState(false);
    const [loading, setLoading] = useState(true);

    const fetchDoc = async () => {
        try {
            const res = await client.get(`/documents/${docId}`);
            setDoc(res.data);
        } catch (err) {
            console.error("Failed to load document", err);
        }
    };

    const fetchClauses = async () => {
        try {
            const res = await client.get(`/documents/${docId}/clauses`);
            setClauses(res.data);
        } catch (err) {
            console.error("Failed to load clauses", err);
        } finally {
            setLoading(false);
        }
    };

    const runAnalysis = async () => {
        setAnalyzing(true);
        try {
            const res = await client.post(`/documents/${docId}/analyze`);
            setClauses(res.data);
            setDoc((prev) => ({ ...prev, is_analyzed: true }));
        } catch (err) {
            console.error("Analysis failed", err);
        } finally {
            setAnalyzing(false);
        }
    };

    useEffect(() => {
        fetchDoc();
        fetchClauses();
    }, [docId]);

    if (!doc) return <><Navbar /><div className="page-container loading-center"><div className="spinner" /></div></>;

    return (
        <>
            <Navbar />
            <div className="page-container">
                <div className="page-header">
                    <button className="btn btn-outline btn-sm" onClick={() => navigate("/")} style={{ marginBottom: "0.5rem" }}>
                        ← Back to Dashboard
                    </button>

                    <div>
                        <h1>{doc.filename}</h1>
                        <p className="doc-page-meta">
                            {doc.page_count} pages •
                            {doc.is_analyzed ? (
                                <span className="badge badge-analyzed" style={{ marginLeft: "0.5rem" }}>✓ Analyzed</span>
                            ) : (
                                <span className="badge badge-pending" style={{ marginLeft: "0.5rem" }}>Not analyzed</span>
                            )}
                        </p>
                    </div>
                    {!doc.is_analyzed && (
                        <button className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>
                            {analyzing ? <><span className="spinner" /> Analyzing...</> : "🔍 Analyze Document"}
                        </button>
                    )}
                </div>

                {/* Tabs */}
                <div className="tabs">
                    <button
                        className={`tab ${activeTab === "analysis" ? "active" : ""}`}
                        onClick={() => setActiveTab("analysis")}
                    >
                        Analysis
                    </button>
                    <button
                        className={`tab ${activeTab === "chat" ? "active" : ""}`}
                        onClick={() => doc.is_analyzed && setActiveTab("chat")}
                        disabled={!doc.is_analyzed}
                    >
                        💬 Chat {!doc.is_analyzed && "(analyze first)"}
                    </button>
                </div>

                {/* Tab Content */}
                {activeTab === "analysis" && (
                    <div className="clause-list">
                        {loading ? (
                            <div className="loading-center"><div className="spinner" /></div>
                        ) : clauses.length === 0 ? (
                            <div className="empty-state glass-card">
                                <span>📋</span>
                                <h3>No clauses extracted yet</h3>
                                <p>Click "Analyze Document" to classify and score all clauses</p>
                            </div>
                        ) : (
                            clauses.map((clause, i) => <ClauseCard key={i} clause={clause} />)
                        )}
                    </div>
                )}

                {activeTab === "chat" && doc.is_analyzed && (
                    <ChatInterface docId={docId} />
                )}
            </div>
        </>
    );
}
