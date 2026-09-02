import { fetchApi } from './client';
import type {
  OverviewAnalytics,
  PipelineAnalyticsResponse,
  StrategyAnalyticsResponse,
  ScenarioAnalyticsResponse,
  TimeSeriesAnalyticsResponse,
  OpportunityDetail,
  AuditSummary,
} from '../types';

export const analyticsApi = {
  getOverview: (merchantId?: string) => {
    const params = merchantId ? `?merchant_id=${merchantId}` : '';
    return fetchApi<OverviewAnalytics>(`/api/v1/analytics/overview${params}`);
  },

  getPipeline: (merchantId?: string) => {
    const params = merchantId ? `?merchant_id=${merchantId}` : '';
    return fetchApi<PipelineAnalyticsResponse>(`/api/v1/analytics/pipeline${params}`);
  },

  getStrategies: (merchantId?: string) => {
    const params = merchantId ? `?merchant_id=${merchantId}` : '';
    return fetchApi<StrategyAnalyticsResponse>(`/api/v1/analytics/strategies${params}`);
  },

  getScenarios: (merchantId?: string) => {
    const params = merchantId ? `?merchant_id=${merchantId}` : '';
    return fetchApi<ScenarioAnalyticsResponse>(`/api/v1/analytics/scenarios${params}`);
  },

  getTimeSeries: (merchantId?: string) => {
    const params = merchantId ? `?merchant_id=${merchantId}` : '';
    return fetchApi<TimeSeriesAnalyticsResponse>(`/api/v1/analytics/timeseries${params}`);
  },

  getOpportunities: (merchantId?: string, limit: number = 20) => {
    const params = new URLSearchParams();
    if (merchantId) params.append('merchant_id', merchantId);
    params.append('limit', limit.toString());
    return fetchApi<OpportunityDetail[]>(`/api/v1/analytics/opportunities?${params.toString()}`);
  },

  getAuditSummary: (merchantId?: string, limit: number = 25) => {
    const params = new URLSearchParams();
    if (merchantId) params.append('merchant_id', merchantId);
    params.append('limit', limit.toString());
    return fetchApi<AuditSummary>(`/api/v1/analytics/audit-summary?${params.toString()}`);
  },
};
