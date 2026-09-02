import React, { useEffect, useState } from 'react';
import { History, ShieldCheck, Search, Filter } from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';
import type { AuditSummaryItem } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';

export const AuditTrailPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditSummaryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterAction, setFilterAction] = useState<string>('ALL');

  useEffect(() => {
    const loadAudit = async () => {
      setLoading(true);
      try {
        const res = await analyticsApi.getAuditSummary(undefined, 50);
        setLogs(res.recent_logs);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadAudit();
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (filterAction === 'ALL') return true;
    return log.action.includes(filterAction);
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <History className="h-6 w-6 text-brand-400" />
            <h1 className="text-xl font-bold text-white">System Audit Trail</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Immutable chronological ledger of AI diagnoses, policy decisions, and execution outcomes.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-brand-500 focus:outline-none"
          >
            <option value="ALL">All Actions</option>
            <option value="POLICY">Policy Evaluations</option>
            <option value="RECOVERY">Recovery Executions</option>
            <option value="AGENT">AI Recommendations</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center">
          <History className="mx-auto h-8 w-8 text-slate-600" />
          <h3 className="mt-2 text-sm font-bold text-white">No Audit Logs Recorded</h3>
          <p className="mt-1 text-xs text-slate-400">No recovery activity recorded yet.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Event ID</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Result / Decision</th>
                  <th className="px-4 py-3">Details</th>
                  <th className="px-4 py-3 text-right">Amount Recovered</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-850/50">
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-400">{formatDate(log.created_at)}</td>
                    <td className="px-4 py-3 font-mono text-slate-300">{log.revenue_event_id.slice(0, 14)}</td>
                    <td className="px-4 py-3 font-bold text-white">{log.action}</td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">{log.actor}</td>
                    <td className="px-4 py-3 font-semibold text-slate-200">{log.policy_result}</td>
                    <td className="px-4 py-3 text-slate-300 max-w-md truncate">{log.details || '-'}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">
                      {log.amount_recovered_paise > 0 ? formatCurrency(log.amount_recovered_paise) : '₹0.00'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
