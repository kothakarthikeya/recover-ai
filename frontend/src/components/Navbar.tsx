import React from 'react';
import { ShieldCheck, Sparkles, Building2 } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-6 backdrop-blur-md">
      <div className="flex items-center space-x-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 font-bold text-white shadow-lg shadow-brand-500/20">
          <ShieldCheck className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight text-white">RecoverAI</h1>
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-500/10 px-2 py-0.5 text-xs font-semibold text-brand-400 ring-1 ring-inset ring-brand-500/20">
              <Sparkles className="h-3 w-3" /> AI Revenue Agent
            </span>
          </div>
          <p className="text-xs text-slate-400">Detect. Decide. Recover.</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden items-center space-x-2 rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 sm:flex">
          <Building2 className="h-4 w-4 text-slate-400" />
          <div className="text-xs">
            <p className="font-medium text-slate-200">Acme Retail & SaaS</p>
            <p className="text-slate-400">Merchant ID: mch_demo_acme</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400 ring-1 ring-inset ring-amber-500/20">
          <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
          <span>Demo Mode — Synthetic Data</span>
        </div>
      </div>
    </header>
  );
};
