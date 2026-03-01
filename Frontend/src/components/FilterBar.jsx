export default function FilterBar({ filters, onChange }) {
    const types = ["All", "Termination", "Liability", "Indemnity", "Confidentiality", "Payment", "Governing Law", "General"];
    const risks = ["All", "High", "Medium", "Low"];

    return (
        <div className="filter-bar">
            <div className="filter-group">
                <label>Clause Type</label>
                <select className="input filter-select" value={filters.type} onChange={(e) => onChange({ ...filters, type: e.target.value })}>
                    {types.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
            </div>
            <div className="filter-group">
                <label>Risk Level</label>
                <select className="input filter-select" value={filters.risk} onChange={(e) => onChange({ ...filters, risk: e.target.value })}>
                    {risks.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
            </div>
            <div className="filter-group">
                <label>Search</label>
                <input
                    className="input"
                    placeholder="Search clauses..."
                    value={filters.search}
                    onChange={(e) => onChange({ ...filters, search: e.target.value })}
                />
            </div>
        </div>
    );
}
