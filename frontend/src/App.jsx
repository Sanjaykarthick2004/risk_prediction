import { Navigate, Route, BrowserRouter, Routes } from "react-router-dom";
import Layout from "./components/common/Layout";
import ProtectedRoute from "./components/common/ProtectedRoute";
import { ToastProvider } from "./components/ui";
import { AuthProvider } from "./context/AuthContext";
import AthleteDetails from "./pages/AthleteDetails";
import Athletes from "./pages/Athletes";
import Dashboard from "./pages/Dashboard";
import Dataset from "./pages/Dataset";
import Evaluation from "./pages/Evaluation";
import Explainability from "./pages/Explainability";
import Login from "./pages/Login";
import ModelTraining from "./pages/ModelTraining";
import Prediction from "./pages/Prediction";
import PredictionHistory from "./pages/PredictionHistory";
import Reports from "./pages/Reports";
import ResetPassword from "./pages/ResetPassword";
import "./styles/global.css";

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
            <Route path="/athletes" element={<Protected><Athletes /></Protected>} />
            <Route path="/athletes/:athleteId" element={<Protected><AthleteDetails /></Protected>} />
            <Route path="/dataset" element={<Protected><Dataset /></Protected>} />
            <Route path="/training" element={<Protected><ModelTraining /></Protected>} />
            <Route path="/evaluation" element={<Protected><Evaluation /></Protected>} />
            <Route path="/prediction" element={<Protected><Prediction /></Protected>} />
            <Route path="/history" element={<Protected><PredictionHistory /></Protected>} />
            <Route path="/explainability" element={<Protected><Explainability /></Protected>} />
            <Route path="/reports" element={<Protected><Reports /></Protected>} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
