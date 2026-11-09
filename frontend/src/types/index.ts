export type CurrencyMode = 'USD' | 'INR';

export interface MovieSummary {
  id: string;
  canonical_id: string;
  primary_title: string;
  original_title?: string;
  release_date?: string;
  release_year?: number;
  industry?: string;
  genres: string[];
  director?: string;
  lead_actor?: string;
  budget_usd: number;
  budget_inr_crores: number;
  box_office_gross_usd?: number;
  box_office_gross_inr_crores?: number;
  is_released: boolean;
  youtube_trailer_id?: string;
  poster_path?: string;
  backdrop_path?: string;
}

export interface UpcomingMovieItem {
  id: string;
  canonical_id: string;
  primary_title: string;
  release_date: string;
  release_year: number;
  industry: string;
  genres: string[];
  director: string;
  lead_actor: string;
  budget_usd: number;
  budget_inr_crores: number;
  readiness_score: number;
  lifecycle_stage: string;
  status_badge: string;
  expected_gross_usd: number;
  expected_gross_formatted_usd: string;
  expected_gross_formatted_inr: string;
  pessimistic_bound_80_usd: number;
  optimistic_bound_80_usd: number;
  risk_assessment_tier: string;
  risk_badge: string;
  buzz_score: number;
  trailer_view_count: number;
  youtube_trailer_id?: string;
  poster_path?: string;
  backdrop_path?: string;
  days_to_release?: number;
  is_stage4_active?: boolean;
}

export interface DashboardSection {
  key: string;
  title: string;
  description: string;
  item_count: number;
  items: UpcomingMovieItem[];
}

export interface UpcomingDashboardResponse {
  total_upcoming_tracked: number;
  last_updated: string;
  sections: Record<string, DashboardSection>;
}

export interface ConformalForecast {
  expected_gross_usd: number;
  expected_gross_inr_crores: number;
  expected_usd_formatted: string;
  expected_inr_formatted: string;
  pessimistic_bound_80_usd: number;
  pessimistic_bound_80_inr: number;
  pessimistic_formatted_usd: string;
  pessimistic_formatted_inr: string;
  optimistic_bound_80_usd: number;
  optimistic_bound_80_inr: number;
  optimistic_formatted_usd: string;
  optimistic_formatted_inr: string;
  extreme_downside_95_usd?: number;
  extreme_upside_95_usd?: number;
  conformal_confidence: number;
}

export interface SuccessClassification {
  predicted_category: string;
  probabilities: Record<string, number>;
}

export interface FinancialRiskAudit {
  estimated_budget_usd: number;
  estimated_budget_inr_crores: number;
  recovery_ratio_expected: number;
  break_even_status: string;
  risk_assessment_tier: string;
  risk_badge: string;
  prob_break_even: number;
  prob_commercial_profit: number;
  prob_catastrophic_disaster: number;
}

export interface ActivePredictionResponse {
  movie_id: string;
  canonical_id: string;
  title: string;
  prediction_stage: string;
  readiness_score: number;
  status_badge: string;
  model_version: string;
  last_updated: string;
  currency_display: string;
  forecast: ConformalForecast;
  success_classification: SuccessClassification;
  financial_risk: FinancialRiskAudit;
  top_positive_driver?: string;
  top_negative_driver?: string;
  narrative_summary?: string;
  days_to_release?: number;
  is_stage4_active?: boolean;
  stage4_details?: any;
}

export interface SHAPFactor {
  feature_name: string;
  feature_label: string;
  shap_value_log10: number;
  shap_impact_usd: number;
  shap_impact_inr_crores: number;
  direction: string;
}

export interface SHAPWaterfallResponse {
  movie_id: string;
  movie_title: string;
  base_value_log10: number;
  base_value_usd: number;
  base_value_inr_crores: number;
  final_predicted_log10: number;
  final_predicted_revenue_usd: number;
  final_predicted_revenue_inr_crores: number;
  additivity_axiom_verified: boolean;
  additivity_error: number;
  top_positive_factors: SHAPFactor[];
  top_negative_factors: SHAPFactor[];
  waterfall_breakdown: SHAPFactor[];
  narrative_summary: string;
}

export interface ScenarioMetrics {
  expected_gross_usd: number;
  expected_gross_formatted_usd: string;
  expected_gross_formatted_inr: string;
  pessimistic_bound_80_usd: number;
  optimistic_bound_80_usd: number;
  prob_break_even: number;
  prob_commercial_profit: number;
  risk_assessment_tier: string;
  risk_badge: string;
}

export interface CounterfactualDelta {
  delta_revenue_usd: number;
  delta_revenue_inr_crores: number;
  percentage_change: number;
  roi_impact: string;
  risk_shift: string;
  strategic_verdict: string;
}

export interface WhatIfSimulationResponse {
  simulation_id: string;
  base_movie_id: string;
  base_movie_title: string;
  execution_latency_ms: number;
  applied_perturbations: Record<string, any>;
  baseline_scenario: ScenarioMetrics;
  simulated_scenario: ScenarioMetrics;
  delta_analysis: CounterfactualDelta;
}

export interface FilmCredit {
  title: string;
  year: number;
  gross_usd: number;
  gross_formatted_usd: string;
  roi_multiplier: number;
  success_category: string;
}

export interface TalentDossierResponse {
  person_name: string;
  role: string;
  total_films_tracked: number;
  career_cumulative_gross_usd: number;
  career_cumulative_gross_formatted_usd: string;
  career_average_gross_formatted_usd: string;
  career_average_gross_formatted_inr: string;
  career_median_roi: number;
  commercial_hit_rate: number;
  star_power_tier: string;
  filmography_highlights: FilmCredit[];
}

export interface MarketSegmentMetric {
  segment_name: string;
  film_count: number;
  total_box_office_usd: number;
  total_box_office_formatted: string;
  average_budget_formatted: string;
  hit_rate_pct: number;
  market_share_pct: number;
}

export interface MarketTrendResponse {
  reporting_period: string;
  total_films_analyzed: number;
  segments: MarketSegmentMetric[];
}

export interface SimilarMovie {
  id: string;
  canonical_id: string;
  primary_title: string;
  release_year: number;
  industry: string;
  genres: string[];
  director: string;
  lead_actor: string;
  budget_usd: number;
  gross_usd: number;
  gross_formatted_usd: string;
  gross_formatted_inr: string;
  similarity_score: number;
  poster_path?: string;
}

export interface MovieDetail extends MovieSummary {
  runtime_minutes?: number;
  original_language?: string;
  cast_members: string[];
  overview?: string;
  production_company?: string;
  poster_path?: string;
  backdrop_path?: string;
  active_prediction?: any;
  buzz_metrics?: any;
}

