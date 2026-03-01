import Navbar from "../components/Navbar";
import ChatInterface from "../components/ChatInterface";

export default function GlobalChatPage() {
    return (
        <>
            <Navbar />
            <div className="page-container">
                <div className="page-header">
                    <h1>Global Chat</h1>
                    <p className="page-subtitle">Ask questions across all your analyzed documents</p>
                </div>
                <ChatInterface />
            </div>
        </>
    );
}
