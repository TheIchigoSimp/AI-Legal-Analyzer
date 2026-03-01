import { useState, useRef } from "react";
import client from "../api/client";

export default function UploadModal({ onClose, onUploaded }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [dragOver, setDragOver] = useState(false);
    const fileRef = useRef();

    const handleUpload = async () => {
        if (!file) return;
        setError("");
        setLoading(true);

        const formData = new FormData();
        formData.append("file", file);

        try {
            await client.post("/documents/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            onUploaded();
            onClose();
        } catch (err) {
            setError(err.response?.data?.detail || "Upload failed");
        } finally {
            setLoading(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped?.type === "application/pdf") {
            setFile(dropped);
            setError("");
        } else {
            setError("Only PDF files are accepted");
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal glass-card fade-in" onClick={(e) => e.stopPropagation()}>
                <h2>Upload Document</h2>

                <div
                    className={`drop-zone ${dragOver ? "drag-over" : ""} ${file ? "has-file" : ""}`}
                    onClick={() => fileRef.current.click()}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                >
                    {file ? (
                        <div className="drop-file-info">
                            <span>📄</span>
                            <p>{file.name}</p>
                            <small>{(file.size / 1024).toFixed(1)} KB</small>
                        </div>
                    ) : (
                        <div className="drop-placeholder">
                            <span>📁</span>
                            <p>Drag & drop a PDF here</p>
                            <small>or click to browse</small>
                        </div>
                    )}
                </div>

                <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    style={{ display: "none" }}
                    onChange={(e) => {
                        setFile(e.target.files[0]);
                        setError("");
                    }}
                />

                {error && <div className="auth-error">{error}</div>}

                <div className="modal-actions">
                    <button className="btn btn-outline" onClick={onClose}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleUpload} disabled={!file || loading}>
                        {loading ? <span className="spinner" /> : null}
                        {loading ? "Uploading..." : "Upload"}
                    </button>
                </div>
            </div>
        </div>
    );
}
