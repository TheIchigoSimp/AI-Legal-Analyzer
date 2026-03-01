export default function RiskBadge({ level }) {
    if (!level) return null;
    const cls = level.toLowerCase();
    return <span className={`badge badge-${cls}`}>{level} Risk</span>;
}
