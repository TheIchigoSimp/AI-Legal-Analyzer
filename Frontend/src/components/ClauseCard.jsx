import RiskBadge from "./RiskBadge";

export default function ClauseCard({ clause }) {
    return (
        <div className="glass-card clause-card fade-in">
            <div className="clause-header">
                <h4 className="clause-title">{clause.section_title}</h4>
                <div className="clause-badges">
                    {clause.clause_type && (
                        <span className="badge badge-analyzed">{clause.clause_type}</span>
                    )}
                    <RiskBadge level={clause.risk_level} />
                    {clause.importance && (
                        <span className={`badge badge-${clause.importance.toLowerCase()}`}>
                            {clause.importance}
                        </span>
                    )}
                </div>
            </div>
            <p className="clause-text">{clause.text}</p>
            <div className="clause-footer">
                <span className="clause-meta">Page {clause.page}</span>
                {clause.risk_reason && (
                    <p className="clause-reason">💡 {clause.risk_reason}</p>
                )}
            </div>
        </div>
    );
}
