import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import Navbar from "./components/Navbar";
import { ToastProvider } from "./components/Toast";
import JobsPage from "./pages/JobsPage";
import ReviewPage from "./pages/ReviewPage";
import UploadPage from "./pages/UploadPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AdminUsersPage from "./pages/AdminUsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-emerald-50/40">
            <Navbar />
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Navigate to="/analytics" replace />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute>
                      <AnalyticsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/upload"
                  element={
                    <ProtectedRoute minRole="ANALYST">
                      <UploadPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/records"
                  element={
                    <ProtectedRoute minRole="ANALYST">
                      <ReviewPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/jobs"
                  element={
                    <ProtectedRoute minRole="ANALYST">
                      <JobsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute minRole="ADMIN">
                      <AdminUsersPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </main>
          </div>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
