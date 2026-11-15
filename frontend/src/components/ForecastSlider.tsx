import React from 'react';
import { Calendar, Clock, RotateCcw, Sparkles } from 'lucide-react';

interface ForecastSliderProps {
  departureTime: string;
  forecastOffsetHours: number | null; // null = ETA Mode (default), 0..48 = Offset Mode
  onChangeOffset: (offset: number | null) => void;
  disabled?: boolean;
}

export const ForecastSlider: React.FC<ForecastSliderProps> = ({
  departureTime,
  forecastOffsetHours,
  onChangeOffset,
  disabled = false,
}) => {
  const isEtaMode = forecastOffsetHours === null;
  const currentOffset = forecastOffsetHours ?? 0;

  // Calculate formatted target date and time at offset
  const getFormattedTime = (offset: number) => {
    try {
      const baseMs = new Date(departureTime).getTime();
      const targetDate = new Date(baseMs + offset * 3600 * 1000);
      return targetDate.toLocaleString([], {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return `+${offset}h`;
    }
  };

  const formattedTargetTime = getFormattedTime(currentOffset);

  const quickJumpHours = [0, 6, 12, 24, 36, 48];

  return (
    <div className="bg-dark-panel/95 border border-dark-border shadow-xl backdrop-blur-md rounded-lg p-3 text-xs font-mono space-y-2.5">
      {/* Top Header: Mode & Timestamp Display */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Clock className="w-3.5 h-3.5 text-amber-accent" />
          <span className="font-semibold text-slate-200 uppercase tracking-wider text-[11px]">
            Forecast Horizon Slider
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {isEtaMode ? (
            <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 text-[10px] font-semibold flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>TRUCK ETA MODE</span>
            </span>
          ) : (
            <div className="flex items-center space-x-1.5">
              <span className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/80 text-[10px] font-semibold">
                +{currentOffset}h SNAPSHOT
              </span>
              <button
                type="button"
                onClick={() => onChangeOffset(null)}
                className="px-1.5 py-0.5 rounded bg-dark-surface border border-dark-border text-slate-300 hover:text-white flex items-center space-x-1 text-[10px] transition-colors"
                title="Return to Truck Arrival ETA conditions"
              >
                <RotateCcw className="w-2.5 h-2.5 text-slate-400" />
                <span>Reset to ETA</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Target Forecast Time Callout */}
      <div className="flex items-center justify-between px-2.5 py-1.5 rounded bg-dark-surface border border-dark-border/60 text-[11px]">
        <div className="flex items-center space-x-2 text-slate-300 truncate">
          <Calendar className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="text-slate-400">Target Time:</span>
          <span className="text-slate-100 font-semibold truncate">
            {isEtaMode ? 'Dynamic ETA per Checkpoint' : formattedTargetTime}
          </span>
        </div>
        <span className="text-[10px] text-slate-500 shrink-0">
          {isEtaMode ? 'Arrival conditions' : `Departure + ${currentOffset} hrs`}
        </span>
      </div>

      {/* Slider Bar */}
      <div className="space-y-1">
        <div className="relative flex items-center">
          <input
            type="range"
            min={0}
            max={48}
            step={1}
            value={currentOffset}
            disabled={disabled}
            onChange={(e) => onChangeOffset(Number(e.target.value))}
            className="w-full h-1.5 bg-dark-surface rounded-lg appearance-none cursor-pointer accent-amber-accent disabled:opacity-50"
            aria-label="Forecast hour offset from departure"
          />
        </div>

        {/* Ticks and Quick Buttons */}
        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-0.5">
          {quickJumpHours.map((h) => {
            const isActive = !isEtaMode && currentOffset === h;
            return (
              <button
                key={h}
                type="button"
                onClick={() => onChangeOffset(h)}
                className={`hover:text-amber-accent transition-colors px-1 py-0.5 rounded ${
                  isActive
                    ? 'text-amber-accent font-bold bg-dark-surface border border-amber-accent/40'
                    : 'text-slate-500'
                }`}
              >
                +{h}h
              </button>
            );
          })}
        </div>
      </div>

      {/* Notice regarding recommendation stability */}
      <div className="text-[10px] text-slate-500 flex items-center space-x-1 border-t border-dark-border/40 pt-1.5">
        <Sparkles className="w-3 h-3 text-amber-accent/70 shrink-0" />
        <span className="truncate">
          Inspects changing weather snapshots along corridor. Recommendation remains locked to Truck ETA.
        </span>
      </div>
    </div>
  );
};
