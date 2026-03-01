import { useState, useEffect } from "react";

export default function ThemeToggle() {
    const [dark, setDark] = useState(() => {
        return localStorage.getItem("theme") !== "light";
    });

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
        localStorage.setItem("theme", dark ? "dark" : "light");
    }, [dark]);

    return (
        <button className="theme-toggle" onClick={() => setDark(!dark)} title={dark ? "Light mode" : "Dark mode"}>
            {dark ? "☀️" : "🌙"}
        </button>
    );
}
