import React, { useEffect, useState } from 'react';
import { Target, Search, ArrowUpDown, ShieldCheck, Play, Eye } from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';
import { recoveryApi } from '../api/recoveryApi';
import type { OpportunityDetail, RecoveryExecuteResponse } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatCurrency, formatEventType, formatStrategy } from '../utils/formatters';
import { ConfirmationModal } from '../components/ConfirmationModal';
import { ResultModal } from '../components/ResultModal';

interface OpportunitiesPageProps {
  onSelectOpportunity: (eventId: string) => void;
}

export const OpportunitiesPage: React.FC<OpportunitiesPageProps> = ({ onSelectOpportunity }) => {
  const [opportunities, setOpportunities] = useState<OpportunityDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [selectedOpp, setSelectedOpp] = useState<OpportunityDetail | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<RecoveryExecuteResponse | null>(null);

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const data = await analyticsApi.getOpportunities(undefined, 50);
      setOpportunities(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, []);

  const handleOpenConfirm = (opp: OpportunityDetail) => {
    setSelectedOpp(opp);
    setIsConfirmOpen(true);
  };

  const handleExecuteConfirm = async () => {
    if (!selectedOpp) return;
    setIsExecuting(true);
    try {
      const res = await recoveryApi.executeSingle(selectedOpp.revenue_event_id);
      setExecutionResult(res);
      setIsConfirmOpen(false);
      await loadOpportunities();
    } catch (err: any) {
      alert(`Execution Error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const filteredOpps = opportunities.filter((opp) => 
    opp.customer_name.toLowerCase().includes(search.toLowerCase()) ||
    opp.event_type.toLowerCase().includes(search.toLowerCase()) ||
    opp.revenue_event_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Target className="h-6 w-6 text-brand-400" />
            <h1 className="text-xl font-bold text-white">Recovery Opportunities</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized by expected recovery amount, recovery probability, and event age.
          </p>
        </div>

        <div className="relative w-full max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search customer, event type..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2 pl-9 pr-4 text-xs text-slate-200 placeholder-slate-500 focus:border-brand-500 focus:outline-none"
          />
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : filteredOpps.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center">
          <Target className="mx-auto h-8 w-8 text-slate-600" />
          <h3 className="mt-2 text-sm font-bold text-white">No Opportunities Found</h3>
          <p className="mt-1 text-xs text-slate-400">
            You're all caught up! No recoverable revenue opportunities currently require action.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3">Customer</th>
                  <th className="px-4 py-3">Problem</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Probability</th>
                  <th className="px-4 py-3">Expected Recovery</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3">AI Recommendation</th>
                  <th className="px-4 py-3">Policy Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredOpps.map((opp) => (
                  <tr key={opp.revenue_event_id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-white">
                      {opp.customer_name}
                      <span className="block text-[10px] text-slate-500 font-mono">{opp.revenue_event_id.slice(0, 12)}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{formatEventType(opp.event_type)}</td>
                    <td className="px-4 py-3 font-bold text-white">{formatCurrency(opp.amount_paise)}</td>
                    <td className="px-4 py-3 font-semibold text-sky-400">{opp.recovery_probability_formatted}</td>
                    <td className="px-4 py-3 font-bold text-emerald-400">{formatCurrency(opp.expected_recovery_paise)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge type="risk" value={opp.risk_level} size="sm" />
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-200">
                      {formatStrategy(opp.recommended_strategy)}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge type="policy" value={opp.policy_decision} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => onSelectOpportunity(opp.revenue_event_id)}
                          className="flex items-center space-x-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700"
                        >
                          <Eye className="h-3 w-3" />
                          <span>Review</span>
                        </button>

                        {opp.policy_decision === 'ALLOW' && (
                          <button
                            onClick={() => handleOpenConfirm(opp)}
                            className="flex items-center space-x-1 rounded-lg bg-brand-600 px-2.5 py-1 text-[11px] font-bold text-white hover:bg-brand-500"
                          >
                            <Play className="h-3 w-3" />
                            <span>Execute</span>
                          </button>
                        )}
                        {opp.policy_decision === 'ESCALATE' && (
                          <button
                            onClick={() => onSelectOpportunity(opp.revenue_event_id)}
                            className="rounded-lg bg-amber-500/20 px-2.5 py-1 text-[11px] font-bold text-amber-300 border border-amber-500/30 hover:bg-amber-500/30"
                          >
                            Approve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirmation & Result Modals */}
      <ConfirmationModal
        isOpen={isConfirmOpen}
        opportunity={selectedOpp}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={handleExecuteConfirm}
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
