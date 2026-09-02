import React from 'react';
import { CheckCircle2, XCircle, X, ShieldCheck } from 'lucide-react';
import type { RecoveryExecuteResponse } from '../types';
import { formatCurrency, formatStrategy } from '../utils/formatters';

interface ResultModalProps {
  isOpen: boolean;
  result: RecoveryExecuteResponse | null;
  onClose: () => void;
}

export const ResultModal: React.FC<ResultModalProps> = ({ isOpen, result, onClose }) => {
  if (!isOpen || !result) return null;

  const isSuccess = result.attempt_status === 'SUCCESS';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2">
            {isSuccess ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : (
              <XCircle className="h-6 w-6 text-red-400" />
            )}
            <h3 className="text-lg font-bold text-white">
              {isSuccess ? 'Recovery Successful' : 'Recovery Execution Result'}
            </h3>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div className={`rounded-xl border p-4 text-center ${isSuccess ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {isSuccess ? 'Amount Successfully Recovered' : 'Attempt Result'}
            </p>
            <p className={`mt-1 text-3xl font-extrabold ${isSuccess ? 'text-emerald-400' : 'text-red-400'}`}>
              {isSuccess ? formatCurrency(result.amount_recovered_paise) : '₹0.00'}
            </p>
            <p className="mt-2 text-xs text-slate-300">{result.message}</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">Strategy</span>
              <span className="font-semibold text-white">{formatStrategy(result.strategy)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">Attempt Status</span>
              <span className={`font-semibold ${isSuccess ? 'text-emerald-400' : 'text-red-400'}`}>{result.attempt_status}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-400">Provider</span>
              <span className="font-semibold text-white">Simulation Engine</span>
            </div>
            {result.provider_reference && (
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-400">Provider Reference</span>
                <span className="font-mono text-slate-300">{result.provider_reference}</span>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="flex items-center space-x-2 rounded-lg bg-brand-600 px-5 py-2 text-sm font-bold text-white hover:bg-brand-500"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>Done</span>
          </button>
        </div>
      </div>
    </div>
  );
};
