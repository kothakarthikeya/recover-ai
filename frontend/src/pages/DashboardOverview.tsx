import React, { useEffect, useState } from 'react';
import { 
  DollarSign, 
  AlertTriangle, 
  TrendingUp, 
  CheckCircle2, 
  Percent, 
  Play,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';
import { recoveryApi } from '../api/recoveryApi';
import type { OverviewAnalytics, PipelineStageItem, TimeSeriesDataPoint, BatchRecoveryResponse } from '../types';
import { KPICard } from '../components/KPICard';
import { PipelineFunnel } from '../components/PipelineFunnel';
import { formatCurrency } from '../utils/formatters';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';

interface DashboardOverviewProps {
  onSelectOpportunity: (eventId: string) => void;
  onNavigateToOpportunities: () => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  onNavigateToOpportunities,
}) => {
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);
  const [pipeline, setPipeline] = useState<PipelineStageItem[]>([]);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [batchExecuting, setBatchExecuting] = useState<boolean>(false);
  const [batchResult, setBatchResult] = useState<BatchRecoveryResponse | null>(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovData, pipeData, tsData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getPipeline(),
        analyticsApi.getTimeSeries(),
      ]);
      setOverview(ovData);
      setPipeline(pipeData.pipeline);
      setTimeSeries(tsData.timeseries);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRunBatchRecovery = async () => {
    setBatchExecuting(true);
    try {
      const res = await recoveryApi.executeBatch(undefined, 20);
      setBatchResult(res);
      await loadDashboardData();
    } catch (err: any) {
      alert(`Batch execution error: ${err.message}`);
    } finally {
      setBatchExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-64 rounded-lg bg-slate-850" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-slate-900 border border-slate-800" />
          ))}
        </div>
        <div className="h-48 rounded-xl bg-slate-900 border border-slate-800" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-red-400" />
        <h3 className="mt-2 text-base font-bold text-white">RecoverAI Backend Unavailable</h3>
        <p className="mt-1 text-xs text-red-300">{error}</p>
        <button
          onClick={loadDashboardData}
          className="mt-4 inline-flex items-center space-x-2 rounded-lg bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-500"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 10-Second Executive Summary Banner */}
      <div className="rounded-2xl border border-brand-500/30 bg-gradient-to-r from-brand-900/40 via-slate-900 to-slate-900 p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-400">
              <Sparkles className="h-4 w-4" /> 10-Second Executive Summary
            </div>
            <h2 className="mt-1 text-xl font-bold text-white">
              RecoverAI identified <span className="text-amber-400">{overview?.revenue_at_risk_formatted}</span> at risk, expects to recover <span className="text-sky-400">{overview?.expected_recovery_formatted}</span>, and has successfully recovered <span className="text-emerald-400">{overview?.actual_recovered_formatted}</span>.
            </h2>
            <p className="mt-1 text-xs text-slate-300">
              Deterministic Policy Engine enforced • Simulated test mode active • Dynamic paise precision
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunBatchRecovery}
              disabled={batchExecuting}
              className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-brand-500/25 hover:brightness-110 disabled:opacity-50"
            >
              {batchExecuting ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  <span>Processing Batch...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>Execute Allowed Batch</span>
                </>
              )}
            </button>
          </div>
        </div>

        {batchResult && (
          <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-center justify-between">
            <span>
              Batch Executed: {batchResult.executed_count} opportunities. Recovered {formatCurrency(batchResult.total_amount_recovered_paise)} across {batchResult.successful_count} successful attempts.
            </span>
            <button onClick={() => setBatchResult(null)} className="text-slate-400 hover:text-white">Dismiss</button>
          </div>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          title="Total Ingested Revenue"
          value={overview?.total_revenue_formatted || '₹0'}
          subtitle={`${overview?.total_events_count.toLocaleString()} total revenue events tracked`}
          icon={DollarSign}
          variant="default"
        />
        <KPICard
          title="Revenue at Risk"
          value={overview?.revenue_at_risk_formatted || '₹0'}
          subtitle="Unresolved & pending payment failures"
          icon={AlertTriangle}
          variant="danger"
        />
        <KPICard
          title="ML Expected Recovery"
          value={overview?.expected_recovery_formatted || '₹0'}
          subtitle="Sum of probability × risk amount"
          icon={TrendingUp}
          variant="info"
        />
        <KPICard
          title="Actual Recovered Revenue"
          value={overview?.actual_recovered_formatted || '₹0'}
          subtitle={`${overview?.successful_recoveries_count} successful execution workflows`}
          icon={CheckCircle2}
          variant="success"
        />
        <KPICard
          title="Actual Recovery Rate"
          value={overview?.recovery_rate_formatted || '0%'}
          subtitle="Actual Recovered ÷ Attempted Amount"
          icon={Percent}
          variant="warning"
        />
        <KPICard
          title="Recovery Attempts"
          value={(overview?.total_recovery_attempts_count || 0).toString()}
          subtitle="Server-side policy authorized actions"
          icon={Play}
          variant="default"
        />
      </div>

      {/* 7-Stage Recovery Pipeline Funnel */}
      <PipelineFunnel stages={pipeline} />

      {/* Performance Time-Series Chart */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-100">Expected vs. Actual Recovery Performance</h3>
            <p className="text-xs text-slate-400">ML Model Prediction vs. Execution Outcomes (Integer Paise Precision)</p>
          </div>
          <button
            onClick={onNavigateToOpportunities}
            className="text-xs font-semibold text-brand-400 hover:text-brand-300"
          >
            Explore Opportunities →
          </button>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={timeSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorExpected" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} tickFormatter={(val) => `₹${val/100000}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                formatter={(value: any) => [formatCurrency(Number(value)), 'Amount']}
              />
              <Area type="monotone" dataKey="expected_recovery_paise" name="Expected Recovery" stroke="#0284c7" fillOpacity={1} fill="url(#colorExpected)" strokeWidth={2} />
              <Area type="monotone" dataKey="recovered_paise" name="Actual Recovered" stroke="#10b981" fillOpacity={1} fill="url(#colorRecovered)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
