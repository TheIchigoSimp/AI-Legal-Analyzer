import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { showToast } from "../components/Toast";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await login(username, password);
            showToast("Welcome back!", "success");
            navigate("/");
        } catch (err) {
            showToast("Login failed", "error");
            setError(err.response?.data?.detail || "Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <form className="auth-form glass-card fade-in" onSubmit={handleSubmit}>
                <div className="auth-header">
                    <h1>RedLine</h1>
                    <p>AI Legal Analyzer</p>
                </div>
                {error && <div className="auth-error">{error}</div>}
                <div className="form-group">
                    <label>Username</label>
                    <input
                        className="input"
                        type="text"
                        placeholder="Enter username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Password</label>
                    <input
                        className="input"
                        type="password"
                        placeholder="Enter password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button className="btn btn-primary auth-btn" type="submit" disabled={loading}>
                    {loading ? <span className="spinner" /> : null}
                    {loading ? "Signing in..." : "Sign In"}
                </button>
                <p className="auth-footer">
                    Don't have an account? <Link to="/register">Register</Link>
                </p>
            </form>
        </div>
    );
}