import React from 'react';
import { AlertTriangle, Calendar, CloudRain, CloudSnow, MapPin, Wind, X } from 'lucide-react';
import { Checkpoint, RiskLevelType } from '../types/route';
import { getRiskBadgeClasses } from '../utils/risk';

interface CheckpointInspectorProps {
  checkpoint: Checkpoint | null;
  onClose: () => void;
  truckWeightLbs?: number;
}

export const CheckpointInspector: React.FC<CheckpointInspectorProps> = ({
  checkpoint,
  onClose,
  truckWeightLbs,
}) => {
  if (!checkpoint) return null;

  const weather = checkpoint.weather;
  const overallRisk: RiskLevelType = weather?.risk_level || 'Low';
  const badge = getRiskBadgeClasses(overallRisk);

  const formatDateTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="p-3.5 bg-dark-panel border-t border-dark-border space-y-2.5 text-xs animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-200 font-mono">
            CP #{checkpoint.sequence}
          </span>
          <span className="text-slate-400 font-mono text-[11px]">
            • {checkpoint.distance_miles.toFixed(1)} mi
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${badge.bg} ${badge.text} ${badge.border}`}>
            {overallRisk.toUpperCase()}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-0.5 rounded"
            title="Close inspector"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Timestamp & Coordinates Meta */}
      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 bg-dark-surface p-2 rounded border border-dark-border/60">
        <div className="flex items-center space-x-1.5 truncate">
          <Calendar className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="font-mono text-slate-300">
            {formatDateTime(checkpoint.estimated_arrival_time)}
          </span>
        </div>
        <div className="flex items-center space-x-1.5 truncate">
          <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="font-mono text-slate-300">
            {checkpoint.latitude.toFixed(4)}°, {checkpoint.longitude.toFixed(4)}°
          </span>
        </div>
      </div>

      {/* Conditions Breakdown Grid */}
      {weather && weather.is_available ? (
        <div className="grid grid-cols-3 gap-1.5 text-center">
          {/* Wind */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <Wind className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Wind</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {weather.wind_mph !== null ? `${weather.wind_mph} mph` : 'N/A'}
            </span>
            <span className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${getRiskBadgeClasses(weather.wind_risk).bg} ${getRiskBadgeClasses(weather.wind_risk).text} ${getRiskBadgeClasses(weather.wind_risk).border}`}>
              {weather.wind_risk}
            </span>
          </div>

          {/* Rain */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <CloudRain className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Rain</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {weather.rain_in_hr !== null ? `${weather.rain_in_hr} in/h` : '0 in/h'}
            </span>
            <span className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${getRiskBadgeClasses(weather.rain_risk).bg} ${getRiskBadgeClasses(weather.rain_risk).text} ${getRiskBadgeClasses(weather.rain_risk).border}`}>
              {weather.rain_risk}
            </span>
          </div>

          {/* Snow */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <CloudSnow className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Snow</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {weather.snow_in_hr !== null ? `${weather.snow_in_hr} in/h` : '0 in/h'}
            </span>
            <span className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${getRiskBadgeClasses(weather.snow_risk).bg} ${getRiskBadgeClasses(weather.snow_risk).text} ${getRiskBadgeClasses(weather.snow_risk).border}`}>
              {weather.snow_risk}
            </span>
          </div>
        </div>
      ) : (
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-700/60 text-slate-400 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-[11px] leading-tight">
            Weather forecast data unavailable for this estimated arrival time.
          </span>
        </div>
      )}

      {/* Load Weight Rule Notice (if wind elevated) */}
      {truckWeightLbs && weather?.wind_mph && weather.wind_mph >= 35 && (
        <div className="text-[10px] font-mono text-slate-400 bg-dark-surface/80 p-1.5 rounded border border-dark-border/40">
          <span className="text-amber-accent font-medium">Load Rule Applied: </span>
          Truck weight {truckWeightLbs.toLocaleString()} lbs evaluated against wind safety threshold.
        </div>
      )}
    </div>
  );
};
