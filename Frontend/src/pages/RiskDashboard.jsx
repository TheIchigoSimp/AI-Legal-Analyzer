import { useState, useEffect } from "react";
import client from "../api/client";
import Navbar from "../components/Navbar";

export default function RiskDashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        client.get("/documents/stats")
            .then((res) => setStats(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <><Navbar /><div className="page-container loading-center"><div className="spinner" /></div></>;

    const risk = stats.risk_distribution;
    const total = risk.High + risk.Medium + risk.Low || 1;

    return (
        <>
            <Navbar />
            <div className="page-container">
                <div className="page-header"><h1>Risk Dashboard</h1></div>

                <div className="stats-grid">
                    <div className="glass-card stat-card fade-in">
                        <div className="stat-value">{stats.total_documents}</div>
                        <div className="stat-label">Total Documents</div>
                    </div>
                    <div className="glass-card stat-card fade-in">
                        <div className="stat-value">{stats.analyzed_documents}</div>
                        <div className="stat-label">Analyzed</div>
                    </div>
                    <div className="glass-card stat-card fade-in">
                        <div className="stat-value">{stats.total_clauses}</div>
                        <div className="stat-label">Total Clauses</div>
                    </div>
                    <div className="glass-card stat-card fade-in">
                        <div className="stat-value">{stats.analyzed_clauses}</div>
                        <div className="stat-label">Classified</div>
                    </div>
                </div>

                <div className="dashboard-grid">
                    <div className="glass-card fade-in">
                        <h3>Risk Distribution</h3>
                        <div className="risk-bars">
                            <div className="risk-bar-row">
                                <span className="badge badge-high">High</span>
                                <div className="risk-bar-track">
                                    <div className="risk-bar-fill high" style={{ width: `${(risk.High / total) * 100}%` }} />
                                </div>
                                <span className="risk-bar-count">{risk.High}</span>
                            </div>
                            <div className="risk-bar-row">
                                <span className="badge badge-medium">Medium</span>
                                <div className="risk-bar-track">
                                    <div className="risk-bar-fill medium" style={{ width: `${(risk.Medium / total) * 100}%` }} />
                                </div>
                                <span className="risk-bar-count">{risk.Medium}</span>
                            </div>
                            <div className="risk-bar-row">
                                <span className="badge badge-low">Low</span>
                                <div className="risk-bar-track">
                                    <div className="risk-bar-fill low" style={{ width: `${(risk.Low / total) * 100}%` }} />
                                </div>
                                <span className="risk-bar-count">{risk.Low}</span>
                            </div>
                        </div>
                    </div>

                    <div className="glass-card fade-in">
                        <h3>Top Risky Clauses</h3>
                        {stats.top_risky_clauses.length === 0 ? (
                            <p className="empty-text">No high-risk clauses found</p>
                        ) : (
                            <div className="risky-list">
                                {stats.top_risky_clauses.map((c, i) => (
                                    <div key={i} className="risky-item">
                                        <div className="risky-title">{c.section_title}</div>
                                        <div className="risky-meta">
                                            <span className="badge badge-high">{c.clause_type}</span>
                                            <span className="risky-doc">📄 {c.doc_filename}</span>
                                        </div>
                                        {c.risk_reason && <p className="risky-reason">{c.risk_reason}</p>}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
}
