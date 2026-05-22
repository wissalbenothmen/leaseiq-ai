import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import {
  LayoutDashboard,
  FileText,
  BookOpen,
  CheckSquare,
  BarChart3,
} from "lucide-react";

export function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { user, clearAuth } = useAuthStore();

  const handleLogout = () => {
    clearAuth();
    localStorage.removeItem("leaseiq_token");
    localStorage.removeItem("leaseiq_user");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl font-bold text-indigo-600">LeaseIQ AI</h1>
            <div className="flex gap-1">
              {[
                { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard size={15} /> },
                { label: "Leases", href: "/leases", icon: <FileText size={15} /> },
                { label: "Obligations", href: "/obligations", icon: <CheckSquare size={15} /> },
                { label: "Clauses", href: "/clauses", icon: <BookOpen size={15} /> },
                { label: "Analytics", href: "/analytics", icon: <BarChart3 size={15} /> },
                { label: "API Docs", href: "/docs", icon: null },
              ].map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600 hover:bg-gray-50 rounded transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
                >
                  {link.icon}
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.full_name}</span>
            <button
              onClick={handleLogout}
              aria-label="Logout"
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-transparent border border-gray-300 hover:bg-gray-100 rounded transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto">{children}</main>
    </div>
  );
}
