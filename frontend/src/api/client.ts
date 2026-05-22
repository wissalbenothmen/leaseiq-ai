import axios, { AxiosInstance } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8022/api/v1";

const TOKEN_KEY = "leaseiq_token";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: { "Content-Type": "application/json" },
    });

    // Read token from localStorage on every request — single source of truth.
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Only force navigation if we're already past login — avoids loops.
          if (!window.location.pathname.startsWith("/login")) {
            window.location.assign("/login");
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  // Auth endpoints
  async register(email: string, password: string, full_name: string) {
    return this.client.post("/auth/register", { email, password, full_name });
  }

  async login(username: string, password: string) {
    return this.client.post("/auth/login", { username, password });
  }

  async getMe() {
    return this.client.get("/auth/me");
  }

  // Lease endpoints
  async createLease(leaseData: any) {
    return this.client.post("/leases", leaseData);
  }

  async listLeases(params?: any) {
    return this.client.get("/leases", { params });
  }

  async getLease(leaseId: string) {
    return this.client.get(`/leases/${leaseId}`);
  }

  async updateLease(leaseId: string, data: any) {
    return this.client.patch(`/leases/${leaseId}`, data);
  }

  async deleteLease(leaseId: string) {
    return this.client.delete(`/leases/${leaseId}`);
  }

  // Clause endpoints
  async listClausesByLease(leaseId: string, params?: any) {
    return this.client.get(`/clauses/lease/${leaseId}`, { params });
  }

  async getClause(clauseId: string) {
    return this.client.get(`/clauses/${clauseId}`);
  }

  async updateClause(clauseId: string, data: any) {
    return this.client.patch(`/clauses/${clauseId}`, data);
  }

  // Obligation endpoints
  async createObligation(obligationData: any) {
    return this.client.post("/obligations", obligationData);
  }

  async listObligationsByLease(leaseId: string, params?: any) {
    return this.client.get(`/obligations/lease/${leaseId}`, { params });
  }

  async getOverdueObligations() {
    return this.client.get("/obligations/overdue");
  }

  async getUpcomingObligations(days: number = 30) {
    return this.client.get("/obligations/upcoming", { params: { days } });
  }

  async updateObligation(obligationId: string, data: any) {
    return this.client.patch(`/obligations/${obligationId}`, data);
  }

  async completeObligation(obligationId: string) {
    return this.client.post(`/obligations/${obligationId}/complete`);
  }

  // Critical date endpoints
  async listDatesByLease(leaseId: string, params?: any) {
    return this.client.get(`/critical-dates/lease/${leaseId}`, { params });
  }

  async getUpcomingDates(days: number = 90) {
    return this.client.get("/critical-dates/upcoming/portfolio", { params: { days } });
  }

  // Analytics endpoints
  async getPortfolioRiskSummary() {
    return this.client.get("/analytics/portfolio/risk-summary");
  }

  async getExpiringLeases(days: number = 365) {
    return this.client.get("/analytics/portfolio/expiring-leases", { params: { days } });
  }

  async getObligationCompliance() {
    return this.client.get("/analytics/portfolio/obligation-compliance");
  }

  async getLeaseRiskBreakdown(leaseId: string) {
    return this.client.get(`/analytics/lease/${leaseId}/risk-breakdown`);
  }

  async getLeaseStatusDistribution() {
    return this.client.get("/analytics/portfolio/lease-status-distribution");
  }

  // Lease detail (full with clauses, obligations, critical dates)
  async getLeaseDetail(leaseId: string) {
    return this.client.get(`/leases/${leaseId}/detail`);
  }

  // AI analysis
  async analyzeClause(clauseId: string) {
    return this.client.post(`/clauses/${clauseId}/analyze`);
  }

  async analyzeAllClauses(leaseId: string) {
    return this.client.post(`/clauses/lease/${leaseId}/analyze-all`);
  }

  // Create clause
  async createClause(data: any) {
    return this.client.post("/clauses", data);
  }

  // Create critical date
  async createCriticalDate(data: any) {
    return this.client.post("/critical-dates", data);
  }

  // Critical date by ID
  async getCriticalDate(dateId: string) {
    return this.client.get(`/critical-dates/${dateId}`);
  }

  // Phase D — voice ↔ lease cross-validation
  async voiceCrossValidateLease(leaseId: string) {
    return this.client.post(`/leases/${leaseId}/cross-validate-voice`);
  }

  async downloadTenantBriefingPdf(leaseId: string) {
    return this.client.get(`/leases/${leaseId}/tenant-briefing.pdf`, { responseType: "blob" });
  }
}

export const apiClient = new ApiClient();
