import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import Navbar from "../components/Navbar";
import ClauseCard from "../components/ClauseCard";
import ChatInterface from "../components/ChatInterface";
import FilterBar from "../components/FilterBar";
import PdfViewer from "../components/PdfViewer";
import { showToast } from "../components/Toast";

export default function DocumentPage() {
    const { docId } = useParams();
    const navigate = useNavigate();
    const [doc, setDoc] = useState(null);
    const [clauses, setClauses] = useState([]);
    const [activeTab, setActiveTab] = useState("analysis");
    const [analyzing, setAnalyzing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ type: "All", risk: "All", search: "" });
    const [analysisProgress, setAnalysisProgress] = useState("");


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
        setAnalysisProgress("Extracting clauses...");
        try {
            // Simulate progress stages
            const progressStages = [
                { msg: "Classifying clause types...", delay: 2000 },
                { msg: "Scoring risk levels...", delay: 4000 },
                { msg: "Generating embeddings...", delay: 6000 },
                { msg: "Storing in vector database...", delay: 8000 },
            ];
            progressStages.forEach(({ msg, delay }) => {
                setTimeout(() => setAnalysisProgress(msg), delay);
            });
            const res = await client.post(`/documents/${docId}/analyze`);
            setClauses(res.data);
            setDoc((prev) => ({ ...prev, is_analyzed: true }));
            setAnalysisProgress("");
            showToast(`Analysis complete — ${res.data.length} clauses classified`, "success");
        } catch (err) {
            console.error("Analysis failed", err);
            showToast("Analysis failed. Please try again.", "error");
            setAnalysisProgress("");
        } finally {
            setAnalyzing(false);
        }
    };

    const exportReport = async () => {
        try {
            const res = await client.get(`/documents/${docId}/export`);
            const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${doc.filename.replace(".pdf", "")}_report.json`;
            a.click();
            URL.revokeObjectURL(url);
            showToast("Report exported!", "success");
        } catch (err) {
            console.error("Export failed", err);
            showToast("Export failed", "error");
        }
    };

    useEffect(() => {
        fetchDoc();
        fetchClauses();
    }, [docId]);

    if (!doc) return <><Navbar /><div className="page-container loading-center"><div className="spinner" /></div></>;

    const filteredClauses = clauses.filter((c) => {
        if (filters.type !== "All" && c.clause_type !== filters.type) return false;
        if (filters.risk !== "All" && c.risk_level !== filters.risk) return false;
        if (filters.search && !c.text.toLowerCase().includes(filters.search.toLowerCase()) &&
            !c.section_title.toLowerCase().includes(filters.search.toLowerCase())) return false;
        return true;
    });


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
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        {!doc.is_analyzed && (
                            <button className="btn btn-primary" onClick={runAnalysis} disabled={analyzing}>
                                {analyzing ? <><span className="spinner" /> Analyzing...</> : "🔍 Analyze Document"}
                            </button>
                        )}
                        {doc.is_analyzed && (
                            <button className="btn btn-outline" onClick={exportReport}>
                                📥 Export Report
                            </button>
                        )}
                    </div>

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
                    <button
                        className={`tab ${activeTab === "pdf" ? "active" : ""}`}
                        onClick={() => setActiveTab("pdf")}
                    >
                        📑 PDF
                    </button>

                </div>

                {/* Tab Content */}
                {activeTab === "analysis" && (
                    <div className="clause-list">
                        {clauses.length > 0 && <FilterBar filters={filters} onChange={setFilters} />}
                        {loading ? (
                            <div className="loading-center"><div className="spinner" /></div>
                        ) : filteredClauses.length === 0 ? (
                            <div className="empty-state glass-card">
                                <span>📋</span>
                                <h3>{clauses.length === 0 ? "No clauses extracted yet" : "No clauses match your filters"}</h3>
                                <p>{clauses.length === 0 ? 'Click "Analyze Document" to classify and score all clauses' : "Try adjusting your filters"}</p>
                            </div>
                        ) : (
                            filteredClauses.map((clause, i) => <ClauseCard key={i} clause={clause} />)
                        )}
                    </div>
                )}


                {activeTab === "chat" && doc.is_analyzed && (
                    <ChatInterface docId={docId} />
                )}

                {activeTab === "pdf" && (
                    <PdfViewer docId={docId} />
                )}

            </div>
        </>
    );
}
