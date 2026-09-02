import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'info';
  trend?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  trend,
}) => {
  const variantStyles = {
    default: 'bg-slate-900 border-slate-800 text-slate-100',
    danger: 'bg-red-950/20 border-red-900/30 text-red-100',
    warning: 'bg-amber-950/20 border-amber-900/30 text-amber-100',
    success: 'bg-emerald-950/20 border-emerald-900/30 text-emerald-100',
    info: 'bg-sky-950/20 border-sky-900/30 text-sky-100',
  };

  const iconStyles = {
    default: 'bg-slate-800 text-slate-300',
    danger: 'bg-red-500/10 text-red-400',
    warning: 'bg-amber-500/10 text-amber-400',
    success: 'bg-emerald-500/10 text-emerald-400',
    info: 'bg-sky-500/10 text-sky-400',
  };

  return (
    <div className={`rounded-xl border p-5 transition-all hover:border-slate-700 shadow-sm ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg ${iconStyles[variant]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight">{value}</div>
        {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        {trend && (
          <div className="mt-2 flex items-center text-xs font-medium text-emerald-400">
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  );
};
