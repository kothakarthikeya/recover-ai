import React from 'react';
import { Settings, ShieldCheck, Key, Sliders, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <Settings className="h-6 w-6 text-brand-400" />
          <h1 className="text-xl font-bold text-white">Merchant & Policy Settings</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Configure merchant profile, server-side policy thresholds, and Razorpay Sandbox integration.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Merchant Account Configuration */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Sliders className="h-4 w-4 text-brand-400" /> Merchant Identity
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Merchant Legal Name</label>
              <input
                type="text"
                disabled
                value="Acme Retail & SaaS Solutions Private Limited"
                className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Merchant ID</label>
              <input
                type="text"
                disabled
                value="mch_demo_acme"
                className="mt-1 w-full font-mono border border-slate-800 bg-slate-950 px-3 py-2 text-slate-200 rounded-xl"
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Support Email</label>
              <input
                type="text"
                disabled
                value="billing-recovery@acme.example.com"
                className="mt-1 w-full border border-slate-800 bg-slate-950 px-3 py-2 text-slate-200 rounded-xl"
              />
            </div>
          </div>
        </div>

        {/* Policy Engine Configuration */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Policy Guardrail Thresholds (Authoritative)
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-slate-800/80">
              <div>
                <p className="font-semibold text-white">Max Automatic Retry Attempts</p>
                <p className="text-slate-400 text-[11px]">Maximum retry attempts allowed per event</p>
              </div>
              <span className="font-bold text-brand-400 bg-brand-500/10 px-2.5 py-1 rounded-lg border border-brand-500/20">2 attempts</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-800/80">
              <div>
                <p className="font-semibold text-white">High Value Escalation Threshold</p>
                <p className="text-slate-400 text-[11px]">Requires merchant human approval</p>
              </div>
              <span className="font-bold text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20">₹1,00,000</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-800/80">
              <div>
                <p className="font-semibold text-white">Minimum Recovery Probability</p>
                <p className="text-slate-400 text-[11px]">Suppresses action if below threshold</p>
              </div>
              <span className="font-bold text-sky-400 bg-sky-500/10 px-2.5 py-1 rounded-lg border border-sky-500/20">25.0%</span>
            </div>

            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-semibold text-white">Recovery Cutoff Window</p>
                <p className="text-slate-400 text-[11px]">Blocks recovery for older events</p>
              </div>
              <span className="font-bold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg">72 hours</span>
            </div>
          </div>
        </div>

        {/* Razorpay Test Mode Credentials */}
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Key className="h-4 w-4 text-amber-400" /> Razorpay Test Mode Sandbox Integration
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs">
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <span className="text-slate-400">Payment Execution Mode</span>
              <p className="mt-1 font-bold text-amber-400 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Simulation / Test Mode
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <span className="text-slate-400">Razorpay Key ID</span>
              <p className="mt-1 font-mono text-slate-200">rzp_test_placeholder</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <span className="text-slate-400">Webhook Secret</span>
              <p className="mt-1 font-mono text-slate-200">placeholder_webhook_secret</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
