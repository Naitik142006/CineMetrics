import axios from 'axios';
import {
  UpcomingDashboardResponse,
  UpcomingMovieItem,
  MovieDetail,
  ActivePredictionResponse,
  SHAPWaterfallResponse,
  WhatIfSimulationResponse,
  TalentDossierResponse,
  MarketTrendResponse,
  SimilarMovie,
} from '../types';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health & Model Governance
  async getHealth() {
    const res = await apiClient.get('/health');
    return res.data;
  },

  async getModelPerformance() {
    const res = await apiClient.get('/model/performance');
    return res.data;
  },

  // Upcoming & Intelligence Dashboard
  async getUpcomingDashboard(): Promise<UpcomingDashboardResponse> {
    const res = await apiClient.get<UpcomingDashboardResponse>('/upcoming/dashboard');
    return res.data;
  },

  async getUpcomingMovies(params?: {
    market_segment?: string;
    min_readiness?: number;
    sort_by?: string;
    limit?: number;
  }): Promise<UpcomingMovieItem[]> {
    const res = await apiClient.get<UpcomingMovieItem[]>('/upcoming', { params });
    return res.data;
  },

  // Search & Catalog
  async searchMovies(params: {
    q?: string;
    market_segment?: string;
    release_year?: number;
    status?: string;
    limit?: number;
  }) {
    const res = await apiClient.get('/movies/search', { params });
    return res.data;
  },

  async getMovieDetail(movieId: string): Promise<MovieDetail> {
    const res = await apiClient.get<MovieDetail>(`/movies/${movieId}`);
    return res.data;
  },

  async getSimilarMovies(movieId: string, limit = 6): Promise<SimilarMovie[]> {
    const res = await apiClient.get<SimilarMovie[]>(`/movies/${movieId}/similar`, {
      params: { limit },
    });
    return res.data;
  },

  // Prediction & SHAP Explainability
  async getMoviePrediction(movieId: string): Promise<ActivePredictionResponse> {
    const res = await apiClient.get<ActivePredictionResponse>(`/movies/${movieId}/prediction`);
    return res.data;
  },

  async getMovieExplanation(movieId: string): Promise<SHAPWaterfallResponse> {
    const res = await apiClient.get<SHAPWaterfallResponse>(`/movies/${movieId}/explanation`);
    return res.data;
  },

  async getPredictionHistory(movieId: string) {
    const res = await apiClient.get(`/movies/${movieId}/prediction/history`);
    return res.data;
  },

  // What-If Simulation
  async simulateWhatIf(payload: {
    base_movie_id: string;
    budget_usd_override?: number;
    director_override?: string;
    lead_actor_override?: string;
    simulated_trailer_views?: number;
    simulated_sentiment_polarity?: number;
  }): Promise<WhatIfSimulationResponse> {
    const res = await apiClient.post<WhatIfSimulationResponse>('/simulate/what-if', payload);
    return res.data;
  },

  // Talent Dossiers & Analytics
  async getActorDossier(actorName: string): Promise<TalentDossierResponse> {
    const res = await apiClient.get<TalentDossierResponse>(`/analytics/actor/${encodeURIComponent(actorName)}`);
    return res.data;
  },

  async getDirectorDossier(directorName: string): Promise<TalentDossierResponse> {
    const res = await apiClient.get<TalentDossierResponse>(`/analytics/director/${encodeURIComponent(directorName)}`);
    return res.data;
  },

  async getMarketTrends(): Promise<MarketTrendResponse> {
    const res = await apiClient.get<MarketTrendResponse>('/analytics/market');
    return res.data;
  },

  // Weekly Sync & Data Pipeline
  async getSyncStatus() {
    const res = await apiClient.get('/sync/status');
    return res.data;
  },

  async triggerSync(force = true, maxTitles = 30) {
    const res = await apiClient.post(`/sync/trigger?force=${force}&max_titles=${maxTitles}`);
    return res.data;
  },

  // Stage 4 Advance Booking Bayesian Recalibration
  async syncStage4Telemetry(movieId: string, persist = true) {
    const res = await apiClient.post(`/movies/${movieId}/sync-stage4`, null, {
      params: { persist },
    });
    return res.data;
  },

  async updateAdvanceBooking(movieId: string, payload: {
    advance_tickets_sold: number;
    average_ticket_price_usd?: number;
    hours_to_release?: number;
    screen_count?: number;
    early_critic_score_pct?: number;
    early_rotten_tomatoes_pct?: number;
    persist_update?: boolean;
  }) {
    const res = await apiClient.post(`/movies/${movieId}/advance-booking-update`, payload);
    return res.data;
  },

  // Authentication
  async login(email: string, password: string) {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },

  async register(name: string, email: string, password: string) {
    const res = await apiClient.post('/auth/register', { name, email, password });
    return res.data;
  },

  async getCurrentUser(token: string) {
    const res = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  },
};

