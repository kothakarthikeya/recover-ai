import { fetchApi } from './client';
import type { RecoveryExecuteResponse, BatchRecoveryResponse, OpportunityDetail } from '../types';

export const recoveryApi = {
  getOpportunities: (merchantId?: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (merchantId) params.append('merchant_id', merchantId);
    params.append('limit', limit.toString());
    return fetchApi<OpportunityDetail[]>(`/api/v1/recovery/opportunities?${params.toString()}`);
  },

  getStatus: (eventId: string) => {
    return fetchApi<RecoveryExecuteResponse>(`/api/v1/recovery/${eventId}`);
  },

  executeSingle: (eventId: string) => {
    return fetchApi<RecoveryExecuteResponse>(`/api/v1/recovery/${eventId}/execute`, {
      method: 'POST',
    });
  },

  approveSingle: (eventId: string) => {
    return fetchApi<RecoveryExecuteResponse>(`/api/v1/recovery/${eventId}/approve`, {
      method: 'POST',
    });
  },

  stopSingle: (eventId: string) => {
    return fetchApi<RecoveryExecuteResponse>(`/api/v1/recovery/${eventId}/stop`, {
      method: 'POST',
    });
  },

  executeBatch: (merchantId?: string, limit: number = 50) => {
    return fetchApi<BatchRecoveryResponse>(`/api/v1/recovery/execute-batch`, {
      method: 'POST',
      body: JSON.stringify({ merchant_id: merchantId, limit }),
    });
  },
};
