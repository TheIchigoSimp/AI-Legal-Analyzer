import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PdfViewer({ docId }) {
    const [numPages, setNumPages] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);

    const token = localStorage.getItem("token");
    const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const pdfUrl = `${apiBase}/documents/${docId}/pdf`;

    return (
        <div className="pdf-viewer">
            <div className="pdf-controls">
                <button
                    className="btn btn-outline btn-sm"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => p - 1)}
                >
                    ← Prev
                </button>
                <span className="pdf-page-info">
                    Page {currentPage} of {numPages || "..."}
                </span>
                <button
                    className="btn btn-outline btn-sm"
                    disabled={currentPage >= numPages}
                    onClick={() => setCurrentPage((p) => p + 1)}
                >
                    Next →
                </button>
            </div>

            <div className="pdf-canvas">
                <Document
                    file={{
                        url: pdfUrl,
                        httpHeaders: { Authorization: `Bearer ${token}` },
                    }}
                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                    loading={<div className="loading-center"><div className="spinner" /></div>}
                    error={<div className="pdf-error">Failed to load PDF</div>}
                >
                    <Page
                        pageNumber={currentPage}
                        width={700}
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                    />
                </Document>
            </div>
        </div>
    );
}
