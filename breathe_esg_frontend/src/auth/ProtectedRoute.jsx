import { Navigate, useLocation } from "react-router-dom";
import Spinner from "../components/Spinner";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ children, minRole = null }) {
  const location = useLocation();
  const { loading, authenticated, hasRoleAtLeast } = useAuth();

  if (loading) {
    return <Spinner label="Loading session..." />;
  }
  if (!authenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (minRole && !hasRoleAtLeast(minRole)) {
    return <Navigate to="/analytics" replace />;
  }
  return children;
}

