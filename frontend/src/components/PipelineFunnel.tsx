import React from 'react';
import type { PipelineStageItem } from '../types';
import { ChevronRight, Search, Brain, ShieldCheck, CheckCircle, Play, DollarSign } from 'lucide-react';

interface PipelineFunnelProps {
  stages: PipelineStageItem[];
}

export const PipelineFunnel: React.FC<PipelineFunnelProps> = ({ stages }) => {
  const getIconForStage = (stageName: string) => {
    switch (stageName) {
      case 'DETECTED': return Search;
      case 'RISK_ANALYZED': return Search;
      case 'AI_RECOMMENDED': return Brain;
      case 'POLICY_EVALUATED': return ShieldCheck;
      case 'ELIGIBLE': return CheckCircle;
      case 'ATTEMPTED': return Play;
      case 'RECOVERED': return DollarSign;
      default: return Search;
    }
  };

  const getStageColor = (stageName: string) => {
    switch (stageName) {
      case 'DETECTED': return 'from-slate-800 to-slate-850 border-slate-700 text-slate-300';
      case 'RISK_ANALYZED': return 'from-slate-800 to-slate-850 border-slate-700 text-slate-300';
      case 'AI_RECOMMENDED': return 'from-indigo-950/40 to-slate-900 border-indigo-800/40 text-indigo-300';
      case 'POLICY_EVALUATED': return 'from-sky-950/40 to-slate-900 border-sky-800/40 text-sky-300';
      case 'ELIGIBLE': return 'from-emerald-950/40 to-slate-900 border-emerald-800/40 text-emerald-300';
      case 'ATTEMPTED': return 'from-amber-950/40 to-slate-900 border-amber-800/40 text-amber-300';
      case 'RECOVERED': return 'from-emerald-900/60 to-emerald-950 border-emerald-500/50 text-emerald-400 font-bold';
      default: return 'from-slate-800 to-slate-850 border-slate-700 text-slate-300';
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-100">Recovery Pipeline Funnel</h2>
          <p className="text-xs text-slate-400">7-Stage conversion flow from event detection to actual recovered revenue</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7">
        {stages.map((stg, index) => {
          const Icon = getIconForStage(stg.stage);
          const isLast = index === stages.length - 1;
          const colorClass = getStageColor(stg.stage);

          return (
            <div key={stg.stage} className="relative flex flex-col justify-between">
              <div className={`rounded-xl border bg-gradient-to-b p-3.5 ${colorClass} transition-all hover:scale-[1.02]`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold tracking-wider uppercase opacity-80">
                    {stg.stage.replace(/_/g, ' ')}
                  </span>
                  <Icon className="h-4 w-4 opacity-75" />
                </div>
                <div>
                  <div className="text-lg font-bold text-white">{stg.count.toLocaleString()}</div>
                  <div className="text-xs font-semibold opacity-90 mt-0.5">{stg.amount_formatted}</div>
                </div>
              </div>
              {!isLast && (
                <ChevronRight className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10 h-5 w-5 text-slate-600" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
