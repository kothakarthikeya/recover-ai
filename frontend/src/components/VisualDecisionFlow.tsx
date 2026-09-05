import React from 'react';
import { Search, Brain, ShieldCheck, Play } from 'lucide-react';
import type { OpportunityDetail } from '../types';
import { formatDate, formatStrategy } from '../utils/formatters';
import { StatusBadge } from './StatusBadge';

interface VisualDecisionFlowProps {
  opportunity: OpportunityDetail;
}

export const VisualDecisionFlow: React.FC<VisualDecisionFlowProps> = ({ opportunity }) => {
  const steps = [
    {
      title: 'Revenue Event Detected',
      icon: Search,
      badge: <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">Detected</span>,
      time: formatDate(opportunity.event_time),
      desc: `${opportunity.event_type.replace(/_/g, ' ')} detected for customer ${opportunity.customer_name}.`,
      color: 'border-slate-700 bg-slate-850',
    },
    {
      title: 'Risk Engine Analysis',
      icon: Search,
      badge: <StatusBadge type="risk" value={opportunity.risk_level} size="sm" />,
      time: 'Calculated by ML Model',
      desc: `ML Recovery Probability: ${opportunity.recovery_probability_formatted}. Expected Recovery: ${opportunity.expected_recovery_formatted}.`,
      color: 'border-slate-700 bg-slate-850',
    },
    {
      title: 'AI Agent Diagnosis',
      icon: Brain,
      badge: <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">{formatStrategy(opportunity.recommended_strategy)}</span>,
      time: 'Reasoning Engine',
      desc: opportunity.diagnosis,
      color: 'border-indigo-800/40 bg-indigo-950/20',
    },
    {
      title: 'Policy Engine Decision',
      icon: ShieldCheck,
      badge: <StatusBadge type="policy" value={opportunity.policy_decision} size="sm" />,
      time: 'Deterministic Rules',
      desc: opportunity.policy_reason,
      color: 'border-sky-800/40 bg-sky-950/20',
    },
    {
      title: 'Bounded Execution',
      icon: Play,
      badge: <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">Simulation Active</span>,
      time: 'Provider Abstraction',
      desc: opportunity.recommended_next_action,
      color: 'border-emerald-800/40 bg-emerald-950/20',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm">
      <h2 className="text-base font-bold text-slate-100 mb-4">Visual Decision Flow Timeline</h2>
      <div className="relative space-y-6 before:absolute before:left-5 before:top-3 before:h-[calc(100%-1.5rem)] before:w-0.5 before:bg-slate-800">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={index} className="relative flex items-start space-x-4 pl-2">
              <div className="relative z-10 flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 text-slate-300 ring-4 ring-slate-900">
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className={`flex-1 rounded-xl border p-4 ${step.color}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-bold text-white">{step.title}</span>
                  <div className="flex items-center space-x-2">
                    {step.badge}
                    <span className="text-[11px] text-slate-400">{step.time}</span>
                  </div>
                </div>
                <p className="mt-2 text-xs text-slate-300 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
