import React from 'react';
import { CheckCircle2, Clock, MapPin, Milestone, Route } from 'lucide-react';
import { RouteOption } from '../types/route';

interface RouteComparisonProps {
  routes: RouteOption[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  colors: Record<string, string>;
}

export const RouteComparison: React.FC<RouteComparisonProps> = ({
  routes,
  selectedRouteId,
  onSelectRoute,
  colors,
}) => {
  if (!routes || routes.length === 0) {
    return null;
  }

  // Format hours and minutes from total hours
  const formatDuration = (hours: number): string => {
    const totalMinutes = Math.round(hours * 60);
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    return `${h}h ${m.toString().padStart(2, '0')}m`;
  };

  // Fastest route duration for diff comparison
  const fastestDuration = Math.min(...routes.map((r) => r.duration_hours));

  return (
    <div className="p-4 border-t border-dark-border space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Route className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300 tracking-wide">
            ROUTE ALTERNATIVES
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {routes.length} {routes.length === 1 ? 'Corridor' : 'Corridors'} Found
        </span>
      </div>

      <div className="space-y-2">
        {routes.map((route, idx) => {
          const isSelected = route.route_id === selectedRouteId;
          const routeColor = colors[route.route_id] || '#F59E0B';
          const durationDiffHours = route.duration_hours - fastestDuration;
          const diffMinutes = Math.round(durationDiffHours * 60);

          return (
            <div
              key={route.route_id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectRoute(route.route_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectRoute(route.route_id);
                }
              }}
              className={`p-3 rounded border text-left cursor-pointer transition-all select-none ${
                isSelected
                  ? 'bg-dark-elevated border-amber-accent/80 shadow-sm ring-1 ring-amber-accent/30'
                  : 'bg-dark-panel border-dark-border hover:border-slate-600 hover:bg-dark-elevated/60'
              }`}
            >
              {/* Header row: Color bar, name, and selection icon */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full ring-2 ring-dark-bg shrink-0"
                    style={{ backgroundColor: routeColor }}
                  />
                  <h4 className="text-xs font-medium text-slate-200 truncate max-w-[200px]">
                    {route.name}
                  </h4>
                </div>

                <div className="flex items-center space-x-1.5">
                  {idx === 0 && (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                      FASTEST
                    </span>
                  )}
                  {isSelected ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-accent" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-dark-borderLight inline-block" />
                  )}
                </div>
              </div>

              {/* Numerical details in IBM Plex Mono */}
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-dark-border/60">
                {/* Distance */}
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                    Distance
                  </span>
                  <div className="flex items-baseline space-x-1">
                    <Milestone className="w-3 h-3 text-slate-400 inline" />
                    <span className="text-xs font-mono font-medium text-slate-100">
                      {route.distance_miles.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">mi</span>
                  </div>
                </div>

                {/* Duration */}
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                    Est. Time
                  </span>
                  <div className="flex items-baseline space-x-1">
                    <Clock className="w-3 h-3 text-slate-400 inline" />
                    <span className="text-xs font-mono font-medium text-slate-100">
                      {formatDuration(route.duration_hours)}
                    </span>
                  </div>
                </div>

                {/* Checkpoints or Diff */}
                <div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                    {diffMinutes > 0 ? 'Variance' : 'Checkpoints'}
                  </span>
                  <div className="flex items-baseline space-x-1">
                    {diffMinutes > 0 ? (
                      <span className="text-xs font-mono text-amber-400">
                        +{diffMinutes}m
                      </span>
                    ) : (
                      <>
                        <MapPin className="w-3 h-3 text-slate-400 inline" />
                        <span className="text-xs font-mono text-slate-300">
                          {route.checkpoint_count} pts
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
