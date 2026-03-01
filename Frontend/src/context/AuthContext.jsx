import { createContext, useContext, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [username, setUsername] = useState(localStorage.getItem("username"));

    const login = async (usernameInput, password) => {
        const formData = new URLSearchParams();
        formData.append("username", usernameInput);
        formData.append("password", password);

        const res = await client.post("/auth/login", formData, {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });

        const accessToken = res.data.access_token;
        localStorage.setItem("token", accessToken);
        localStorage.setItem("username", usernameInput);
        setToken(accessToken);
        setUsername(usernameInput);
    };

    const register = async (usernameInput, password) => {
        await client.post("/auth/register", {
            username: usernameInput,
            password: password,
        });
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        setToken(null);
        setUsername(null);
    };

    const isAuthenticated = !!token;

    return (
        <AuthContext.Provider value={{ token, username, login, register, logout, isAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
