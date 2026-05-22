import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { useAuthStore } from "./store/authStore";
import { Layout } from "./components/Layout";
import { ErrorBoundary } from "./components/ErrorBoundary";

const LoginPage       = lazy(() => import("./pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const DashboardPage   = lazy(() => import("./pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const LeasesPage      = lazy(() => import("./pages/LeasesPage").then((m) => ({ default: m.LeasesPage })));
const LeaseDetailPage = lazy(() => import("./pages/LeaseDetailPage").then((m) => ({ default: m.LeaseDetailPage })));
const ObligationsPage = lazy(() => import("./pages/ObligationsPage").then((m) => ({ default: m.ObligationsPage })));
const ClausesPage     = lazy(() => import("./pages/ClausesPage").then((m) => ({ default: m.ClausesPage })));
const AnalyticsPage   = lazy(() => import("./pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage })));
const ApiDocsPage     = lazy(() => import("./pages/ApiDocsPage").then((m) => ({ default: m.ApiDocsPage })));

function RouteFallback() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  if (!token) return <Navigate to="/login" replace />;
  return (
    <Layout>
      <ErrorBoundary>
        <Suspense fallback={<RouteFallback />}>{children}</Suspense>
      </ErrorBoundary>
    </Layout>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Toaster position="bottom-right" toastOptions={{ duration: 3000 }} />
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/leases" element={<ProtectedRoute><LeasesPage /></ProtectedRoute>} />
          <Route path="/leases/:leaseId" element={<ProtectedRoute><LeaseDetailPage /></ProtectedRoute>} />
          <Route path="/obligations" element={<ProtectedRoute><ObligationsPage /></ProtectedRoute>} />
          <Route path="/clauses" element={<ProtectedRoute><ClausesPage /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
          <Route path="/docs" element={<ProtectedRoute><ApiDocsPage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
