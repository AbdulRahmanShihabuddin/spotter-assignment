import React from 'react';
import { AlertTriangle, Calendar, Clock, CloudRain, CloudSnow, MapPin, Wind, X } from 'lucide-react';
import { Checkpoint, CheckpointWeather, RiskLevelType } from '../types/route';
import { getForecastAtOffset, getRiskBadgeClasses } from '../utils/risk';

interface CheckpointInspectorProps {
  checkpoint: Checkpoint | null;
  onClose: () => void;
  truckWeightLbs?: number;
  departureTime?: string;
  forecastOffsetHours?: number | null;
}

export const CheckpointInspector: React.FC<CheckpointInspectorProps> = ({
  checkpoint,
  onClose,
  truckWeightLbs = 35000,
  departureTime,
  forecastOffsetHours = null,
}) => {
  if (!checkpoint) return null;

  const isOffsetMode = forecastOffsetHours !== null && Boolean(departureTime);

  // Active weather to display based on mode
  const displayedWeather: CheckpointWeather | undefined = isOffsetMode && departureTime
    ? getForecastAtOffset(checkpoint, departureTime, forecastOffsetHours!, truckWeightLbs)
    : checkpoint.weather;

  const overallRisk: RiskLevelType = displayedWeather?.risk_level || 'Low';
  const badge = getRiskBadgeClasses(overallRisk);

  const etaRisk: RiskLevelType = checkpoint.weather?.risk_level || 'Low';
  const etaBadge = getRiskBadgeClasses(etaRisk);

  const formatDateTime = (isoStr?: string | null) => {
    if (!isoStr) return 'N/A';
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], {
        weekday: 'short',
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
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded border ${badge.bg} ${badge.text} ${badge.border}`}
          >
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

      {/* Mode Indicator & Timestamps */}
      <div className="space-y-1 bg-dark-surface p-2 rounded border border-dark-border/60 text-[11px]">
        {/* Active View Time */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-slate-300 truncate">
            <Clock className="w-3 h-3 text-amber-accent shrink-0" />
            <span className="text-slate-400">
              {isOffsetMode ? `Forecast (+${forecastOffsetHours}h):` : 'Estimated ETA:'}
            </span>
            <span className="font-mono text-slate-100 font-semibold truncate">
              {isOffsetMode
                ? formatDateTime(displayedWeather?.forecast_time)
                : formatDateTime(checkpoint.estimated_arrival_time)}
            </span>
          </div>

          {isOffsetMode && (
            <span className="text-[9px] font-mono px-1 rounded bg-amber-950/80 text-amber-300 border border-amber-800/80">
              SLIDER
            </span>
          )}
        </div>

        {/* If in Offset mode, also show baseline ETA weather comparison */}
        {isOffsetMode && (
          <div className="flex items-center justify-between pt-1 border-t border-dark-border/40 text-[10px] text-slate-400">
            <div className="flex items-center space-x-1 truncate">
              <Calendar className="w-2.5 h-2.5 text-slate-500 shrink-0" />
              <span>Truck Arrival ETA: {formatDateTime(checkpoint.estimated_arrival_time)}</span>
            </div>
            <span
              className={`font-mono px-1 rounded border text-[9px] ${etaBadge.bg} ${etaBadge.text} ${etaBadge.border}`}
            >
              ETA: {etaRisk}
            </span>
          </div>
        )}

        {/* Coordinates */}
        <div className="flex items-center space-x-1.5 text-slate-400 text-[10px] pt-0.5">
          <MapPin className="w-2.5 h-2.5 text-slate-500 shrink-0" />
          <span className="font-mono text-slate-400">
            {checkpoint.latitude.toFixed(4)}°, {checkpoint.longitude.toFixed(4)}°
          </span>
        </div>
      </div>

      {/* Conditions Breakdown Grid */}
      {displayedWeather && displayedWeather.is_available ? (
        <div className="grid grid-cols-3 gap-1.5 text-center">
          {/* Wind */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <Wind className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Wind</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {displayedWeather.wind_mph !== null ? `${displayedWeather.wind_mph} mph` : 'N/A'}
            </span>
            <span
              className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${
                getRiskBadgeClasses(displayedWeather.wind_risk).bg
              } ${getRiskBadgeClasses(displayedWeather.wind_risk).text} ${
                getRiskBadgeClasses(displayedWeather.wind_risk).border
              }`}
            >
              {displayedWeather.wind_risk}
            </span>
          </div>

          {/* Rain */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <CloudRain className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Rain</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {displayedWeather.rain_in_hr !== null ? `${displayedWeather.rain_in_hr} in/h` : '0 in/h'}
            </span>
            <span
              className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${
                getRiskBadgeClasses(displayedWeather.rain_risk).bg
              } ${getRiskBadgeClasses(displayedWeather.rain_risk).text} ${
                getRiskBadgeClasses(displayedWeather.rain_risk).border
              }`}
            >
              {displayedWeather.rain_risk}
            </span>
          </div>

          {/* Snow */}
          <div className="p-2 rounded bg-dark-surface border border-dark-border/60 flex flex-col items-center">
            <div className="flex items-center space-x-1 text-slate-400 mb-1">
              <CloudSnow className="w-3 h-3" />
              <span className="text-[10px] uppercase tracking-wider">Snow</span>
            </div>
            <span className="font-mono text-slate-100 font-semibold text-xs">
              {displayedWeather.snow_in_hr !== null ? `${displayedWeather.snow_in_hr} in/h` : '0 in/h'}
            </span>
            <span
              className={`text-[9px] font-mono mt-1 px-1.5 py-0.2 rounded border ${
                getRiskBadgeClasses(displayedWeather.snow_risk).bg
              } ${getRiskBadgeClasses(displayedWeather.snow_risk).text} ${
                getRiskBadgeClasses(displayedWeather.snow_risk).border
              }`}
            >
              {displayedWeather.snow_risk}
            </span>
          </div>
        </div>
      ) : (
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-700/60 text-slate-400 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-[11px] leading-tight">
            Weather forecast data unavailable for this timestamp.
          </span>
        </div>
      )}

      {/* Load Weight Rule Notice (if wind elevated) */}
      {truckWeightLbs && displayedWeather?.wind_mph && displayedWeather.wind_mph >= 35 && (
        <div className="text-[10px] font-mono text-slate-400 bg-dark-surface/80 p-1.5 rounded border border-dark-border/40">
          <span className="text-amber-accent font-medium">Load Rule Applied: </span>
          Truck weight {truckWeightLbs.toLocaleString()} lbs evaluated against wind safety threshold.
        </div>
      )}
    </div>
  );
};
