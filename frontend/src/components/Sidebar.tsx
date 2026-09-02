import React from 'react';
import { 
  LayoutDashboard, 
  Target, 
  BarChart3, 
  History, 
  Settings,
  ShieldCheck,
  Activity
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'opportunities', label: 'Recovery Opportunities', icon: Target },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'audit', label: 'Audit Trail', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900 flex flex-col justify-between p-4 shrink-0 hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Navigation</p>
          <nav className="mt-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-brand-600/15 text-brand-400 border border-brand-500/20' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-brand-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
          <div className="flex items-center space-x-2 text-xs font-medium text-emerald-400">
            <Activity className="h-4 w-4" />
            <span>Policy Guardrail Active</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Deterministic rules authority enabled. Server-side rule evaluation strictly enforced.
          </p>
        </div>
      </div>

      <div className="border-t border-slate-800 pt-4 px-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-5 w-5 text-brand-400" />
          <div>
            <p className="text-xs font-bold text-slate-200">RecoverAI v0.1.0</p>
            <p className="text-[10px] text-slate-400">Razorpay Buildathon Edition</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
