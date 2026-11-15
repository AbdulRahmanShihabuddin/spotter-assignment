import React from 'react';
import { Truck } from 'lucide-react';

interface HeaderProps {
  providerName?: string;
  isMock?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ providerName = 'osrm', isMock = false }) => {
  return (
    <header className="h-14 bg-dark-surface border-b border-dark-border px-4 flex items-center justify-between shrink-0 select-none">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded bg-dark-panel border border-dark-border flex items-center justify-center text-amber-accent">
          <Truck className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-sm font-semibold tracking-tight text-slate-100">
              WEATHER-AWARE TRUCK ROUTING
            </h1>
            <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-dark-panel border border-dark-border text-slate-400">
              COMMERCIAL
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Commercial vehicle corridor planning & multi-route analysis
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs">
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-dark-panel border border-dark-border">
          <span className={`w-2 h-2 rounded-full ${isMock ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
          <span className="text-[11px] font-mono text-slate-300">
            {isMock ? 'ENGINE: MOCK (DEV)' : `ENGINE: ${providerName.toUpperCase()}`}
          </span>
        </div>
      </div>
    </header>
  );
};
