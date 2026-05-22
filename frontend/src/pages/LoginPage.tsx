import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { FileText, AlertCircle } from "lucide-react";
import { apiClient } from "../api/client";
import { useAuthStore } from "../store/authStore";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const setUser = useAuthStore((state) => state.setUser);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.login(email, password);
      const { access_token, user } = response.data;
      apiClient.setToken(access_token);
      setUser(user, access_token);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0c0f2e 100%)' }}
    >
      <div className="absolute top-16 left-16 w-80 h-80 bg-indigo-600/20 rounded-full blur-3xl animate-pulse pointer-events-none" />
      <div
        className="absolute bottom-16 right-16 w-96 h-96 bg-violet-600/15 rounded-full blur-3xl animate-pulse pointer-events-none"
        style={{ animationDelay: '1.5s' }}
      />
      <div
        className="absolute top-1/2 left-1/3 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl animate-pulse pointer-events-none"
        style={{ animationDelay: '3s' }}
      />
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 shadow-2xl">
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/30 border border-indigo-400/40 flex items-center justify-center mb-4">
              <FileText size={28} className="text-indigo-300" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">LeaseIQ AI</h1>
            <p className="text-sm text-white/60 mt-1">Lease Intelligence Platform</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/70 mb-1.5 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/70 mb-1.5 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
              />
            </div>
            {error && (
              <div role="alert" aria-live="polite" className="flex items-center gap-2 text-red-300 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                <AlertCircle size={14} aria-hidden="true" />
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-indigo-500/25 focus:outline-none focus:ring-2 focus:ring-indigo-400 mt-2"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
          <p className="mt-6 text-center text-white/50 text-sm">
            Don't have an account?{" "}
            <Link to="/register" className="text-indigo-300 hover:text-indigo-200 font-medium transition-colors">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
