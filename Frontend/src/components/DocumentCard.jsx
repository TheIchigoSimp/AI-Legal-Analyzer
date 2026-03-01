import { useNavigate } from "react-router-dom";

export default function DocumentCard({ doc }) {
    const navigate = useNavigate();

    return (
        <div className="glass-card doc-card fade-in" onClick={() => navigate(`/documents/${doc.id}`)}>
            <div className="doc-card-header">
                <div className="doc-icon">📄</div>
                <div className="doc-info">
                    <h3 className="doc-title">{doc.filename}</h3>
                    <p className="doc-meta">
                        {doc.page_count} pages • {doc.clause_count || 0} clauses • {new Date(doc.created_at).toLocaleDateString()}
                    </p>

                </div>
            </div>
            <div className="doc-card-footer">
                {doc.is_analyzed ? (
                    <span className="badge badge-analyzed">✓ Analyzed</span>
                ) : (
                    <span className="badge badge-pending">Pending Analysis</span>
                )}
            </div>
        </div>
    );
}
