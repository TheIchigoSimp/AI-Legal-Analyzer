import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
    const { username, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    const isActive = (path) => location.pathname === path;

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <Link to="/">RedLine</Link>
            </div>

            <nav className="sidebar-nav">
                <Link to="/" className={`sidebar-link ${isActive("/") ? "active" : ""}`}>
                    <span className="sidebar-icon">📄</span>
                    Documents
                </Link>
                <Link to="/dashboard" className={`sidebar-link ${isActive("/dashboard") ? "active" : ""}`}>
                    <span className="sidebar-icon">📊</span>
                    Risk Dashboard
                </Link>

                <Link to="/chat" className={`sidebar-link ${isActive("/chat") ? "active" : ""}`}>
                    <span className="sidebar-icon">💬</span>
                    Global Chat
                </Link>
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-user">
                    <div className="user-avatar">{username?.[0]?.toUpperCase()}</div>
                    <span className="user-name">{username}</span>
                </div>
                <button className="btn btn-outline btn-sm" onClick={handleLogout}>Logout</button>
            </div>
        </aside>
    );
}
