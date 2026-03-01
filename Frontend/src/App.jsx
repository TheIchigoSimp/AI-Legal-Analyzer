import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import DocumentPage from "./pages/DocumentPage";
import GlobalChatPage from "./pages/GlobalChatPage";
import RiskDashboard from "./pages/RiskDashboard";
import ToastContainer from "./components/Toast";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><RiskDashboard /></ProtectedRoute>} />
        <Route path="/documents/:docId" element={<ProtectedRoute><DocumentPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><GlobalChatPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <ToastContainer />
    </>
  );
}

export default App;
