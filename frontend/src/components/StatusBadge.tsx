import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, MinusCircle, Clock, ShieldAlert } from 'lucide-react';
import type { PolicyDecision, AttemptStatus } from '../types';

interface StatusBadgeProps {
  type: 'policy' | 'attempt' | 'risk';
  value: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  if (type === 'policy') {
    const val = value as PolicyDecision;
    switch (val) {
      case 'ALLOW':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20 ${sizeClasses}`}>
            <CheckCircle2 className="h-3.5 w-3.5" /> Allowed
          </span>
        );
      case 'BLOCK':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20 ${sizeClasses}`}>
            <XCircle className="h-3.5 w-3.5" /> Blocked
          </span>
        );
      case 'ESCALATE':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20 ${sizeClasses}`}>
            <AlertTriangle className="h-3.5 w-3.5" /> Requires Approval
          </span>
        );
      case 'NO_ACTION':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-slate-500/10 text-slate-400 ring-1 ring-inset ring-slate-500/20 ${sizeClasses}`}>
            <MinusCircle className="h-3.5 w-3.5" /> No Action
          </span>
        );
      default:
        return <span className="text-slate-400">{value}</span>;
    }
  }

  if (type === 'attempt') {
    const val = value as AttemptStatus;
    switch (val) {
      case 'SUCCESS':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20 ${sizeClasses}`}>
            <CheckCircle2 className="h-3.5 w-3.5" /> Success
          </span>
        );
      case 'FAILED':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20 ${sizeClasses}`}>
            <XCircle className="h-3.5 w-3.5" /> Failed
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-sky-500/10 text-sky-400 ring-1 ring-inset ring-sky-500/20 ${sizeClasses}`}>
            <Clock className="h-3.5 w-3.5 animate-spin" /> In Progress
          </span>
        );
      case 'ESCALATED':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20 ${sizeClasses}`}>
            <AlertTriangle className="h-3.5 w-3.5" /> Escalated
          </span>
        );
      default:
        return <span className={`inline-flex items-center gap-1 rounded-full bg-slate-500/10 text-slate-400 ring-1 ring-inset ring-slate-500/20 ${sizeClasses}`}>{value}</span>;
    }
  }

  if (type === 'risk') {
    switch (value.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20 ${sizeClasses}`}>
            <ShieldAlert className="h-3.5 w-3.5" /> CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20 ${sizeClasses}`}>
            HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-sky-500/10 text-sky-400 ring-1 ring-inset ring-sky-500/20 ${sizeClasses}`}>
            MEDIUM
          </span>
        );
      case 'LOW':
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20 ${sizeClasses}`}>
            LOW
          </span>
        );
      default:
        return <span className="text-slate-400">{value}</span>;
    }
  }

  return <span className="text-slate-400">{value}</span>;
};
