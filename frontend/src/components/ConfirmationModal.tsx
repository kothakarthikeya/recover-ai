import React from 'react';
import { AlertCircle, CheckCircle2, ShieldCheck, Play, X } from 'lucide-react';
import type { OpportunityDetail } from '../types';
import { formatCurrency, formatStrategy } from '../utils/formatters';

interface ConfirmationModalProps {
  isOpen: boolean;
  opportunity: OpportunityDetail | null;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  opportunity,
  onClose,
  onConfirm,
  isLoading,
}) => {
  if (!isOpen || !opportunity) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2">
            <div className="rounded-lg bg-brand-500/10 p-2 text-brand-400">
              <Play className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Confirm Recovery Execution</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs text-slate-400">Target Customer</p>
            <p className="text-sm font-bold text-white">{opportunity.customer_name}</p>

            <div className="mt-3 grid grid-cols-2 gap-3 border-t border-slate-800/80 pt-3 text-xs">
              <div>
                <span className="text-slate-400">Amount at Risk</span>
                <p className="text-sm font-bold text-white">{formatCurrency(opportunity.amount_paise)}</p>
              </div>
              <div>
                <span className="text-slate-400">Expected Recovery</span>
                <p className="text-sm font-bold text-emerald-400">{formatCurrency(opportunity.expected_recovery_paise)}</p>
              </div>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">Strategy</span>
              <span className="font-semibold text-white">{formatStrategy(opportunity.recommended_strategy)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">Policy Authorization</span>
              <span className="flex items-center gap-1 font-semibold text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" /> Approved (ALLOW)
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">ML Probability</span>
              <span className="font-semibold text-white">{opportunity.recovery_probability_formatted}</span>
            </div>
          </div>

          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-300 flex items-start space-x-2">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Simulation Mode Active</p>
              <p className="text-amber-300/80 mt-0.5">
                This execution uses a deterministic simulation engine for buildathon demo purposes. No real-money transaction will be initiated.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className="flex items-center space-x-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-bold text-white hover:bg-brand-500 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Executing...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>Execute Recovery</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
