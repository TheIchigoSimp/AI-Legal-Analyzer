import { useState, useEffect } from "react";
import client from "../api/client";
import Navbar from "../components/Navbar";
import DocumentCard from "../components/DocumentCard";
import UploadModal from "../components/UploadModal";

export default function DashboardPage() {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showUpload, setShowUpload] = useState(false);

    const fetchDocs = async () => {
        setLoading(true);
        try {
            const res = await client.get("/documents/");
            setDocs(res.data);
        } catch (err) {
            console.error("Failed to load documents", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchDocs(); }, []);

    return (
        <>
            <Navbar />
            <div className="page-container">
                <div className="page-header">
                    <h1>My Documents</h1>
                    <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
                        + Upload PDF
                    </button>
                </div>

                {loading ? (
                    <div className="loading-center"><div className="spinner" /></div>
                ) : docs.length === 0 ? (
                    <div className="empty-state glass-card">
                        <span>📂</span>
                        <h3>No documents yet</h3>
                        <p>Upload your first legal document to get started</p>
                        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>Upload PDF</button>
                    </div>
                ) : (
                    <div className="doc-grid">
                        {docs.map((doc) => (
                            <DocumentCard key={doc.id} doc={doc} onDeleted={fetchDocs} />

                        ))}
                    </div>
                )}

                {showUpload && (
                    <UploadModal onClose={() => setShowUpload(false)} onUploaded={fetchDocs} />
                )}
            </div>
        </>
    );
}
