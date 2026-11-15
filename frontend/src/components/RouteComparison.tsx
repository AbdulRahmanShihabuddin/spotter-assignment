import React from 'react';
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock,
  Milestone,
  Route,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
} from 'lucide-react';
import { RouteOption, RouteRecommendation } from '../types/route';
import { getRiskBadgeClasses } from '../utils/risk';

interface RouteComparisonProps {
  routes: RouteOption[];
  recommendation?: RouteRecommendation | null;
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  colors: Record<string, string>;
}

export const RouteComparison: React.FC<RouteComparisonProps> = ({
  routes,
  recommendation,
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

  const fastestDuration = Math.min(...routes.map((r) => r.duration_hours));

  return (
    <div className="p-4 border-t border-dark-border space-y-3">
      {/* Route Recommendation Banner */}
      {recommendation && (
        <div
          className={`p-3 rounded-lg border text-xs leading-relaxed ${
            recommendation.has_recommendation
              ? 'bg-amber-950/40 border-amber-500/50 text-slate-200'
              : 'bg-rose-950/50 border-rose-600/60 text-rose-200'
          }`}
        >
          <div className="flex items-center space-x-2 font-semibold mb-1">
            {recommendation.has_recommendation ? (
              <>
                <Award className="w-4 h-4 text-amber-accent shrink-0" />
                <span className="text-amber-300 font-mono text-[11px] uppercase tracking-wider">
                  Recommended Corridor
                </span>
              </>
            ) : (
              <>
                <ShieldX className="w-4 h-4 text-rose-400 shrink-0" />
                <span className="text-rose-300 font-mono text-[11px] uppercase tracking-wider">
                  No Safe Recommendation
                </span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-300 font-sans">
            {recommendation.reason}
          </p>
        </div>
      )}

      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Route className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
            Route Alternatives
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {routes.length} {routes.length === 1 ? 'Corridor' : 'Corridors'} Found
        </span>
      </div>

      {/* Alternative Route Cards */}
      <div className="space-y-2.5">
        {routes.map((route, idx) => {
          const isSelected = route.route_id === selectedRouteId;
          const routeColor = colors[route.route_id] || '#F59E0B';
          const durationDiffHours = route.duration_hours - fastestDuration;
          const diffMinutes = Math.round(durationDiffHours * 60);

          const maxRisk = route.max_risk_level || 'Low';
          const riskBadge = getRiskBadgeClasses(maxRisk);
          const summary = route.risk_summary;

          const isRecommended = Boolean(route.is_recommended);
          const isEligible = route.is_eligible !== false;
          const rank = route.rank;

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
                  ? 'bg-dark-elevated border-amber-accent/80 shadow-md ring-1 ring-amber-accent/30'
                  : 'bg-dark-panel border-dark-border hover:border-slate-600 hover:bg-dark-elevated/60'
              }`}
            >
              {/* Header row: Color dot, name, and badges */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center space-x-2 truncate">
                  <span
                    className="w-2.5 h-2.5 rounded-full ring-2 ring-dark-bg shrink-0"
                    style={{ backgroundColor: routeColor }}
                  />
                  <h4 className="text-xs font-medium text-slate-200 truncate max-w-[190px]">
                    {route.name}
                  </h4>
                </div>

                <div className="flex items-center space-x-1.5 shrink-0">
                  {isRecommended ? (
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/60 flex items-center space-x-1">
                      <span>★</span>
                      <span>RECOMMENDED</span>
                    </span>
                  ) : !isEligible ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800/80">
                      NO TRAVEL
                    </span>
                  ) : rank ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      #{rank}
                    </span>
                  ) : idx === 0 ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                      FASTEST
                    </span>
                  ) : null}

                  {isSelected ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-accent" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-dark-borderLight inline-block" />
                  )}
                </div>
              </div>

              {/* Weather Risk Banner for Route */}
              <div className="flex items-center justify-between py-1 px-2 rounded bg-dark-surface/90 border border-dark-border/60 mb-2">
                <div className="flex items-center space-x-1.5">
                  {maxRisk === 'Low' ? (
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  ) : maxRisk === 'Moderate' ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  ) : (
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  )}
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                    Risk Assessment:
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${riskBadge.bg} ${riskBadge.text} ${riskBadge.border}`}
                >
                  {maxRisk.toUpperCase()}
                </span>
              </div>

              {/* Lexicographic Metric Priority Breakdown (Severe, High, Avg, Time) */}
              {summary && (
                <div className="grid grid-cols-4 gap-1.5 py-1.5 px-2 mb-2 rounded bg-dark-bg/60 border border-dark-border/40 text-[10px] font-mono text-center">
                  <div>
                    <span className="text-[9px] text-slate-500 block uppercase">Severe</span>
                    <span
                      className={`font-semibold ${
                        summary.severe_risk_miles > 0 ? 'text-red-400' : 'text-slate-300'
                      }`}
                    >
                      {summary.severe_risk_miles.toFixed(1)} mi
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 block uppercase">High</span>
                    <span
                      className={`font-semibold ${
                        summary.high_risk_miles > 0 ? 'text-orange-400' : 'text-slate-300'
                      }`}
                    >
                      {summary.high_risk_miles.toFixed(1)} mi
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 block uppercase">Avg Risk</span>
                    <span className="text-slate-300 font-semibold">
                      {summary.average_risk.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 block uppercase">Points</span>
                    <span className="text-slate-300">
                      {route.checkpoint_count}
                    </span>
                  </div>
                </div>
              )}

              {/* Distance and Travel Duration */}
              <div className="grid grid-cols-3 gap-2 pt-1 border-t border-dark-border/40">
                {/* Distance */}
                <div>
                  <span className="text-[9px] text-slate-500 uppercase tracking-wider block">
                    Distance
                  </span>
                  <div className="flex items-baseline space-x-1">
                    <Milestone className="w-2.5 h-2.5 text-slate-400 inline" />
                    <span className="text-xs font-mono font-medium text-slate-100">
                      {route.distance_miles.toLocaleString(undefined, {
                        maximumFractionDigits: 1,
                      })}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">mi</span>
                  </div>
                </div>

                {/* Duration */}
                <div>
                  <span className="text-[9px] text-slate-500 uppercase tracking-wider block">
                    Travel Time
                  </span>
                  <div className="flex items-baseline space-x-1">
                    <Clock className="w-2.5 h-2.5 text-slate-400 inline" />
                    <span className="text-xs font-mono font-medium text-slate-100">
                      {formatDuration(route.duration_hours)}
                    </span>
                  </div>
                </div>

                {/* Variance / Checkpoints */}
                <div>
                  <span className="text-[9px] text-slate-500 uppercase tracking-wider block">
                    {diffMinutes > 0 ? 'Variance' : 'Checkpoints'}
                  </span>
                  <div className="flex items-baseline space-x-1">
                    {diffMinutes > 0 ? (
                      <span className="text-xs font-mono text-amber-400">
                        +{diffMinutes}m
                      </span>
                    ) : (
                      <span className="text-xs font-mono text-slate-300">
                        {route.checkpoint_count} pts
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Ineligibility notice if route is unsuitable */}
              {route.ineligibility_reason && (
                <div className="mt-2 text-[10px] font-mono text-rose-300 bg-rose-950/50 px-2 py-1 rounded border border-rose-800/60 flex items-center space-x-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  <span>{route.ineligibility_reason}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
