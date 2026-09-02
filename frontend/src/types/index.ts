export type RecoveryStrategy = 
  | 'SMART_RETRY'
  | 'PAYMENT_REMINDER'
  | 'PAYMENT_LINK'
  | 'SUBSCRIPTION_RETRY'
  | 'ESCALATE'
  | 'NO_ACTION';

export type PolicyDecision = 'ALLOW' | 'BLOCK' | 'ESCALATE' | 'NO_ACTION';

export type AttemptStatus = 
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCESS'
  | 'FAILED'
  | 'BLOCKED'
  | 'STOPPED'
  | 'ESCALATED';

export interface OverviewAnalytics {
  total_revenue_paise: number;
  revenue_at_risk_paise: number;
  expected_recovery_paise: number;
  actual_recovered_paise: number;
  unrecovered_paise: number;
  attempted_recovery_paise: number;
  recovery_rate_percent: number;
  total_events_count: number;
  events_analyzed_count: number;
  total_recovery_attempts_count: number;
  successful_recoveries_count: number;
  total_revenue_formatted: string;
  revenue_at_risk_formatted: string;
  expected_recovery_formatted: string;
  actual_recovered_formatted: string;
  recovery_rate_formatted: string;
}

export interface PipelineStageItem {
  stage: string;
  count: number;
  amount_paise: number;
  amount_formatted: string;
}

export interface StrategyPerformanceItem {
  strategy: RecoveryStrategy;
  attempts_count: number;
  successes_count: number;
  failures_count: number;
  amount_attempted_paise: number;
  amount_recovered_paise: number;
  success_rate_percent: number;
  amount_attempted_formatted: string;
  amount_recovered_formatted: string;
}

export interface ScenarioPerformanceItem {
  event_type: string;
  event_count: number;
  amount_at_risk_paise: number;
  expected_recovery_paise: number;
  amount_attempted_paise: number;
  amount_recovered_paise: number;
  recovery_rate_percent: number;
  amount_at_risk_formatted: string;
  amount_recovered_formatted: string;
}

export interface TimeSeriesDataPoint {
  date: string;
  at_risk_paise: number;
  expected_recovery_paise: number;
  attempted_paise: number;
  recovered_paise: number;
  attempts_count: number;
  successes_count: number;
}

export interface OpportunityDetail {
  revenue_event_id: string;
  customer_name: string;
  event_type: string;
  amount_paise: number;
  amount_formatted: string;
  recovery_probability: number;
  recovery_probability_formatted: string;
  expected_recovery_paise: number;
  expected_recovery_formatted: string;
  risk_level: string;
  diagnosis: string;
  recommended_strategy: RecoveryStrategy;
  policy_decision: PolicyDecision;
  policy_reason: string;
  recommended_next_action: string;
  event_time: string;
}

export interface AuditSummaryItem {
  id: string;
  revenue_event_id: string;
  action: string;
  actor: string;
  policy_result: string;
  details?: string;
  amount_recovered_paise: number;
  created_at: string;
}

export interface AuditSummary {
  total_recommendations: number;
  total_policy_evaluations: number;
  total_executions: number;
  total_successes: number;
  total_failures: number;
  total_escalations: number;
  total_blocks: number;
  recent_logs: AuditSummaryItem[];
}

export interface RecoveryExecuteResponse {
  revenue_event_id: string;
  attempt_id: string;
  strategy: RecoveryStrategy;
  policy_decision: PolicyDecision;
  attempt_status: AttemptStatus;
  event_status: string;
  amount_attempted_paise: number;
  amount_recovered_paise: number;
  provider_reference?: string;
  message: string;
  requires_human_approval: boolean;
  executed_at: string;
}

export interface BatchRecoveryResponse {
  total_opportunities: number;
  eligible_count: number;
  executed_count: number;
  successful_count: number;
  failed_count: number;
  blocked_count: number;
  escalated_count: number;
  total_amount_attempted_paise: number;
  total_amount_recovered_paise: number;
  expected_recovery_amount_paise: number;
  recovery_rate_percent: number;
  results: RecoveryExecuteResponse[];
}
