import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        if (password !== confirm) {
            setError("Passwords do not match");
            return;
        }
        if (password.length < 6) {
            setError("Password must be at least 6 characters");
            return;
        }

        setLoading(true);
        try {
            await register(username, password);
            navigate("/login");
        } catch (err) {
            setError(err.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <form className="auth-form glass-card fade-in" onSubmit={handleSubmit}>
                <div className="auth-header">
                    <h1>RedLine</h1>
                    <p>Create your account</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <div className="form-group">
                    <label>Username</label>
                    <input
                        className="input"
                        type="text"
                        placeholder="Choose a username"
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
                        placeholder="Choose a password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Confirm Password</label>
                    <input
                        className="input"
                        type="password"
                        placeholder="Confirm your password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        required
                    />
                </div>

                <button className="btn btn-primary auth-btn" type="submit" disabled={loading}>
                    {loading ? <span className="spinner" /> : null}
                    {loading ? "Creating account..." : "Create Account"}
                </button>

                <p className="auth-footer">
                    Already have an account? <Link to="/login">Sign in</Link>
                </p>
            </form>
        </div>
    );
}
