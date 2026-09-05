import React, { useEffect, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';
import type { StrategyPerformanceItem, ScenarioPerformanceItem, AuditSummary } from '../types';
import { formatCurrency, formatEventType, formatStrategy } from '../utils/formatters';

export const AnalyticsPage: React.FC = () => {
  const [strategies, setStrategies] = useState<StrategyPerformanceItem[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioPerformanceItem[]>([]);
  const [auditSummary, setAuditSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true);
      try {
        const [stratData, scenData, auditData] = await Promise.all([
          analyticsApi.getStrategies(),
          analyticsApi.getScenarios(),
          analyticsApi.getAuditSummary(),
        ]);
        setStrategies(stratData.strategies);
        setScenarios(scenData.scenarios);
        setAuditSummary(auditData);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded-lg bg-slate-850" />
        <div className="h-64 rounded-xl bg-slate-900 border border-slate-800" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-brand-400" />
          <h1 className="text-xl font-bold text-white">Analytics & Performance Intelligence</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Detailed strategy efficacy, revenue loss scenario breakdown, and policy enforcement metrics.
        </p>
      </div>

      {/* Strategy Performance Section */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-slate-100">Recovery Strategy Efficacy</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strat) => (
            <div key={strat.strategy} className="rounded-xl border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-sm text-white">{formatStrategy(strat.strategy)}</span>
                <span className="text-xs font-bold text-emerald-400">{strat.success_rate_percent.toFixed(1)}% Success</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400">Attempts</span>
                  <p className="font-semibold text-slate-200">{strat.attempts_count}</p>
                </div>
                <div>
                  <span className="text-slate-400">Successes</span>
                  <p className="font-semibold text-emerald-400">{strat.successes_count}</p>
                </div>
                <div>
                  <span className="text-slate-400">Attempted Amount</span>
                  <p className="font-semibold text-slate-200">{strat.amount_attempted_formatted}</p>
                </div>
                <div>
                  <span className="text-slate-400">Recovered Amount</span>
                  <p className="font-bold text-emerald-400">{strat.amount_recovered_formatted}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Revenue Loss Scenario Breakdown Section */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-slate-100">Revenue Loss Scenario Breakdown</h2>
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3">Scenario</th>
                  <th className="px-4 py-3">Event Count</th>
                  <th className="px-4 py-3">Revenue at Risk</th>
                  <th className="px-4 py-3">Expected Recovery</th>
                  <th className="px-4 py-3">Actual Recovered</th>
                  <th className="px-4 py-3 text-right">Recovery Rate %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {scenarios.map((scen) => (
                  <tr key={scen.event_type} className="hover:bg-slate-850/50">
                    <td className="px-4 py-3 font-semibold text-white">{formatEventType(scen.event_type)}</td>
                    <td className="px-4 py-3 text-slate-300">{scen.event_count.toLocaleString()}</td>
                    <td className="px-4 py-3 font-bold text-red-400">{scen.amount_at_risk_formatted}</td>
                    <td className="px-4 py-3 font-semibold text-sky-400">{formatCurrency(scen.expected_recovery_paise)}</td>
                    <td className="px-4 py-3 font-bold text-emerald-400">{scen.amount_recovered_formatted}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">{scen.recovery_rate_percent.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Policy & Enforcement Metrics */}
      {auditSummary && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-100">Deterministic Policy & Enforcement Audit Metrics</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6 text-center text-xs">
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Recommendations</span>
              <p className="mt-1 text-xl font-bold text-indigo-400">{auditSummary.total_recommendations}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Policy Checks</span>
              <p className="mt-1 text-xl font-bold text-sky-400">{auditSummary.total_policy_evaluations}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Executions</span>
              <p className="mt-1 text-xl font-bold text-slate-100">{auditSummary.total_executions}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Successes</span>
              <p className="mt-1 text-xl font-bold text-emerald-400">{auditSummary.total_successes}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Policy Blocks</span>
              <p className="mt-1 text-xl font-bold text-red-400">{auditSummary.total_blocks}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
              <span className="text-slate-400">Escalations</span>
              <p className="mt-1 text-xl font-bold text-amber-400">{auditSummary.total_escalations}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
