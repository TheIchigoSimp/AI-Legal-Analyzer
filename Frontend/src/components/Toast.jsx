import { useState, useEffect } from "react";

let toastCallback = null;

export function showToast(message, type = "success") {
    if (toastCallback) toastCallback({ message, type, id: Date.now() });
}

export default function ToastContainer() {
    const [toasts, setToasts] = useState([]);

    useEffect(() => {
        toastCallback = (toast) => {
            setToasts((prev) => [...prev, toast]);
            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== toast.id));
            }, 3500);
        };
        return () => { toastCallback = null; };
    }, []);

    return (
        <div className="toast-container">
            {toasts.map((t) => (
                <div key={t.id} className={`toast toast-${t.type} fade-in`}>
                    <span>{t.type === "success" ? "✓" : t.type === "error" ? "✕" : "ℹ"}</span>
                    {t.message}
                </div>
            ))}
        </div>
    );
}
