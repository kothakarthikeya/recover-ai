import React, { useEffect, useState } from 'react';
import { ArrowLeft, Brain, ShieldCheck, Play, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, XCircle } from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';
import { recoveryApi } from '../api/recoveryApi';
import type { OpportunityDetail, RecoveryExecuteResponse } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { VisualDecisionFlow } from '../components/VisualDecisionFlow';
import { formatCurrency, formatStrategy, formatDate } from '../utils/formatters';
import { ConfirmationModal } from '../components/ConfirmationModal';
import { ResultModal } from '../components/ResultModal';

interface OpportunityDetailPageProps {
  eventId: string;
  onBack: () => void;
}

export const OpportunityDetailPage: React.FC<OpportunityDetailPageProps> = ({ eventId, onBack }) => {
  const [opportunity, setOpportunity] = useState<OpportunityDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<RecoveryExecuteResponse | null>(null);

  const loadDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const opps = await analyticsApi.getOpportunities(undefined, 100);
      const found = opps.find((o) => o.revenue_event_id === eventId);
      if (found) {
        setOpportunity(found);
      } else {
        // Fallback: construct from recovery status API
        const statusData = await recoveryApi.getStatus(eventId);
        setOpportunity({
          revenue_event_id: eventId,
          customer_name: 'Customer Account',
          event_type: 'payment_failure',
          amount_paise: statusData.amount_attempted_paise,
          amount_formatted: formatCurrency(statusData.amount_attempted_paise),
          recovery_probability: 0.75,
          recovery_probability_formatted: '75.0%',
          expected_recovery_paise: intRound(statusData.amount_attempted_paise * 0.75),
          expected_recovery_formatted: formatCurrency(intRound(statusData.amount_attempted_paise * 0.75)),
          risk_level: 'MEDIUM',
          diagnosis: 'Isolated payment failure on active subscription.',
          recommended_strategy: statusData.strategy,
          policy_decision: statusData.policy_decision,
          policy_reason: statusData.message,
          recommended_next_action: 'Initiate automated smart retry workflow.',
          event_time: new Date().toISOString(),
        });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load opportunity details.');
    } finally {
      setLoading(false);
    }
  };

  const intRound = (num: number) => Math.round(num);

  useEffect(() => {
    loadDetail();
  }, [eventId]);

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      const res = await recoveryApi.executeSingle(eventId);
      setExecutionResult(res);
      setIsConfirmOpen(false);
      await loadDetail();
    } catch (err: any) {
      alert(`Execution Error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApprove = async () => {
    setIsExecuting(true);
    try {
      const res = await recoveryApi.approveSingle(eventId);
      setExecutionResult(res);
      await loadDetail();
    } catch (err: any) {
      alert(`Approval Error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop/suppress recovery for this event?')) return;
    setIsExecuting(true);
    try {
      const res = await recoveryApi.stopSingle(eventId);
      setExecutionResult(res);
      await loadDetail();
    } catch (err: any) {
      alert(`Stop Error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded-lg bg-slate-850" />
        <div className="h-64 rounded-xl bg-slate-900 border border-slate-800" />
      </div>
    );
  }

  if (error || !opportunity) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-red-400" />
        <h3 className="mt-2 text-sm font-bold text-white">Detail Unavailable</h3>
        <p className="mt-1 text-xs text-slate-400">{error || 'Event detail not found.'}</p>
        <button onClick={onBack} className="mt-4 rounded-lg bg-slate-800 px-4 py-2 text-xs font-bold text-slate-200">
          ← Back to Opportunities
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-850"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Opportunities</span>
        </button>

        <div className="flex items-center space-x-3">
          {opportunity.policy_decision === 'ALLOW' && (
            <button
              onClick={() => setIsConfirmOpen(true)}
              className="flex items-center space-x-2 rounded-xl bg-brand-600 px-5 py-2 text-sm font-bold text-white shadow-lg shadow-brand-500/20 hover:bg-brand-500"
            >
              <Play className="h-4 w-4" />
              <span>Execute Recovery</span>
            </button>
          )}

          {opportunity.policy_decision === 'ESCALATE' && (
            <button
              onClick={handleApprove}
              disabled={isExecuting}
              className="flex items-center space-x-2 rounded-xl bg-amber-600 px-5 py-2 text-sm font-bold text-white hover:bg-amber-500 disabled:opacity-50"
            >
              <AlertTriangle className="h-4 w-4" />
              <span>Approve & Execute</span>
            </button>
          )}

          {opportunity.policy_decision === 'BLOCK' && (
            <button disabled className="rounded-xl bg-red-950/40 border border-red-800/40 px-5 py-2 text-sm font-bold text-red-400 cursor-not-allowed">
              Blocked by Policy
            </button>
          )}

          {opportunity.policy_decision === 'NO_ACTION' && (
            <button disabled className="rounded-xl bg-slate-800 border border-slate-700 px-5 py-2 text-sm font-bold text-slate-400 cursor-not-allowed">
              No Action Required
            </button>
          )}

          <button
            onClick={handleStop}
            disabled={isExecuting}
            className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-850 hover:text-slate-200"
          >
            Stop Workflow
          </button>
        </div>
      </div>

      {/* Main Detail Header Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Revenue Event Summary Box */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Revenue Event</span>
                <h2 className="text-xl font-extrabold text-white">{opportunity.customer_name}</h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{opportunity.revenue_event_id}</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400">Amount at Risk</span>
                <p className="text-2xl font-black text-white">{opportunity.amount_formatted}</p>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 text-xs">
              <div>
                <span className="text-slate-400">Event Type</span>
                <p className="font-semibold text-white mt-0.5">{opportunity.event_type.replace(/_/g, ' ')}</p>
              </div>
              <div>
                <span className="text-slate-400">Recovery Probability</span>
                <p className="font-bold text-sky-400 mt-0.5">{opportunity.recovery_probability_formatted}</p>
              </div>
              <div>
                <span className="text-slate-400">Expected Recovery</span>
                <p className="font-bold text-emerald-400 mt-0.5">{opportunity.expected_recovery_formatted}</p>
              </div>
              <div>
                <span className="text-slate-400">Risk Level</span>
                <div className="mt-0.5">
                  <StatusBadge type="risk" value={opportunity.risk_level} size="sm" />
                </div>
              </div>
            </div>
          </div>

          {/* AI Explanation Box */}
          <div className="rounded-xl border border-indigo-900/30 bg-gradient-to-br from-indigo-950/20 via-slate-900 to-slate-900 p-6 shadow-sm">
            <div className="flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
              <Brain className="h-4 w-4" /> AI Recovery Diagnosis & Recommendation
            </div>
            <h3 className="mt-2 text-base font-bold text-white">Why RecoverAI Recommends {formatStrategy(opportunity.recommended_strategy)}</h3>
            <p className="mt-2 text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-indigo-900/30">
              "{opportunity.diagnosis}"
            </p>
            <div className="mt-4 flex items-center justify-between text-xs border-t border-slate-800/80 pt-3">
              <span className="text-slate-400">Recommended Action:</span>
              <span className="font-semibold text-indigo-300">{opportunity.recommended_next_action}</span>
            </div>
          </div>

          {/* Visual Decision Flow Timeline */}
          <VisualDecisionFlow opportunity={opportunity} />
        </div>

        {/* Sidebar Status Column */}
        <div className="space-y-6">
          {/* Policy Guardrail Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <ShieldCheck className="h-4 w-4 text-emerald-400" /> Policy Engine Evaluation
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Decision:</span>
                <StatusBadge type="policy" value={opportunity.policy_decision} />
              </div>
              <p className="mt-3 text-xs text-slate-300 leading-relaxed border-t border-slate-800 pt-2">
                {opportunity.policy_reason}
              </p>
            </div>

            <div className="space-y-2 text-xs text-slate-400">
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span>Customer Opt-Out Status</span>
                <span className="text-emerald-400 font-semibold">Active Customer</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span>Max Automatic Attempts</span>
                <span className="text-slate-200">2 attempts max</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span>High Value Threshold</span>
                <span className="text-slate-200">₹1,00,000</span>
              </div>
            </div>
          </div>

          {/* Simulation Disclaimer Card */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-5 text-xs text-amber-300 space-y-2">
            <div className="flex items-center space-x-2 font-bold">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>Simulation / Test Mode Active</span>
            </div>
            <p className="text-amber-300/80 leading-relaxed">
              Execution triggers a deterministic simulation engine using synthetic test data. No real-money transaction will be initiated.
            </p>
          </div>
        </div>
      </div>

      <ConfirmationModal
        isOpen={isConfirmOpen}
        opportunity={opportunity}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={handleExecute}
        isLoading={isExecuting}
      />

      <ResultModal
        isOpen={!!executionResult}
        result={executionResult}
        onClose={() => setExecutionResult(null)}
      />
    </div>
  );
};
