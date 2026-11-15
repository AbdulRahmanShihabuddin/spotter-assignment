import React, { useState } from 'react';
import {
  ArrowUpDown,
  Calendar,
  Crosshair,
  Gauge,
  MapPin,
  RotateCw,
  Search,
} from 'lucide-react';
import { RoutePlanRequest } from '../types/route';

interface TripFormProps {
  onSubmit: (params: RoutePlanRequest) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const TripForm: React.FC<TripFormProps> = ({ onSubmit, isLoading, disabled = false }) => {
  // Format current local datetime rounded to next full hour
  const getDefaultDateTime = () => {
    const d = new Date();
    d.setHours(d.getHours() + 1);
    d.setMinutes(0);
    d.setSeconds(0);
    // Format YYYY-MM-DDTHH:mm
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const [origin, setOrigin] = useState('Chicago, IL');
  const [destination, setDestination] = useState('Dallas, TX');
  const [departureTime, setDepartureTime] = useState(getDefaultDateTime());
  const [weightLbs, setWeightLbs] = useState(42000);
  const [intervalMiles, setIntervalMiles] = useState<10 | 25 | 50>(25);

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!origin.trim()) {
      errors.origin = 'Origin location is required.';
    }
    if (!destination.trim()) {
      errors.destination = 'Destination location is required.';
    }
    if (origin.trim().toLowerCase() === destination.trim().toLowerCase()) {
      errors.destination = 'Destination cannot match origin.';
    }
    if (!departureTime) {
      errors.departureTime = 'Departure date and time is required.';
    }
    if (!weightLbs || weightLbs <= 0) {
      errors.weightLbs = 'Weight must be greater than 0 lbs.';
    } else if (weightLbs > 120000) {
      errors.weightLbs = 'Weight cannot exceed 120,000 lbs.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate() || isLoading || disabled) return;

    // Convert local datetime to ISO string
    const isoDeparture = new Date(departureTime).toISOString();

    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      departure_time: isoDeparture,
      weight_lbs: Number(weightLbs),
      checkpoint_interval_miles: intervalMiles,
    });
  };

  const handleSwap = () => {
    setOrigin(destination);
    setDestination(origin);
    setValidationErrors((prev) => ({ ...prev, destination: '' }));
  };

  const applyPreset = (presetOrigin: string, presetDest: string) => {
    setOrigin(presetOrigin);
    setDestination(presetDest);
    setValidationErrors({});
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 space-y-4">
      {/* Section Title */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300 tracking-wide">
          TRIP CONFIGURATION
        </span>
        <div className="flex space-x-1">
          <button
            type="button"
            onClick={() => applyPreset('Chicago, IL', 'Dallas, TX')}
            className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-panel hover:bg-dark-elevated text-slate-400 hover:text-slate-200 border border-dark-border transition-colors"
            title="Chicago to Dallas corridor"
          >
            ORD → DFW
          </button>
          <button
            type="button"
            onClick={() => applyPreset('Atlanta, GA', 'Miami, FL')}
            className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-panel hover:bg-dark-elevated text-slate-400 hover:text-slate-200 border border-dark-border transition-colors"
            title="Atlanta to Miami corridor"
          >
            ATL → MIA
          </button>
        </div>
      </div>

      {/* Origin & Destination Inputs */}
      <div className="space-y-2 relative">
        {/* Origin */}
        <div>
          <label htmlFor="origin-input" className="block text-[11px] font-medium text-slate-400 mb-1">
            Origin
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-emerald-400">
              <MapPin className="w-3.5 h-3.5" />
            </div>
            <input
              id="origin-input"
              type="text"
              value={origin}
              onChange={(e) => {
                setOrigin(e.target.value);
                if (validationErrors.origin) {
                  setValidationErrors((prev) => ({ ...prev, origin: '' }));
                }
              }}
              placeholder="e.g. Chicago, IL or address"
              className={`w-full pl-8 pr-3 py-1.5 bg-dark-panel border text-xs text-slate-100 rounded focus:outline-none focus:border-amber-accent transition-colors ${
                validationErrors.origin ? 'border-rose-500/70' : 'border-dark-border'
              }`}
              disabled={isLoading}
            />
          </div>
          {validationErrors.origin && (
            <p className="text-[11px] text-rose-400 mt-1">{validationErrors.origin}</p>
          )}
        </div>

        {/* Swap button */}
        <div className="flex justify-end -my-1 pr-2">
          <button
            type="button"
            onClick={handleSwap}
            disabled={isLoading}
            className="p-1 rounded bg-dark-panel hover:bg-dark-elevated text-slate-400 hover:text-amber-accent border border-dark-border transition-colors"
            title="Swap Origin and Destination"
          >
            <ArrowUpDown className="w-3 h-3" />
          </button>
        </div>

        {/* Destination */}
        <div>
          <label htmlFor="destination-input" className="block text-[11px] font-medium text-slate-400 mb-1">
            Destination
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-rose-400">
              <Crosshair className="w-3.5 h-3.5" />
            </div>
            <input
              id="destination-input"
              type="text"
              value={destination}
              onChange={(e) => {
                setDestination(e.target.value);
                if (validationErrors.destination) {
                  setValidationErrors((prev) => ({ ...prev, destination: '' }));
                }
              }}
              placeholder="e.g. Dallas, TX or address"
              className={`w-full pl-8 pr-3 py-1.5 bg-dark-panel border text-xs text-slate-100 rounded focus:outline-none focus:border-amber-accent transition-colors ${
                validationErrors.destination ? 'border-rose-500/70' : 'border-dark-border'
              }`}
              disabled={isLoading}
            />
          </div>
          {validationErrors.destination && (
            <p className="text-[11px] text-rose-400 mt-1">{validationErrors.destination}</p>
          )}
        </div>
      </div>

      {/* Departure Time & Weight (2-column layout) */}
      <div className="grid grid-cols-2 gap-3">
        {/* Departure Time */}
        <div>
          <label htmlFor="departure-time-input" className="block text-[11px] font-medium text-slate-400 mb-1">
            Departure Time
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none text-slate-400">
              <Calendar className="w-3 h-3" />
            </div>
            <input
              id="departure-time-input"
              type="datetime-local"
              value={departureTime}
              onChange={(e) => {
                setDepartureTime(e.target.value);
                if (validationErrors.departureTime) {
                  setValidationErrors((prev) => ({ ...prev, departureTime: '' }));
                }
              }}
              className="w-full pl-7 pr-1 py-1.5 bg-dark-panel border border-dark-border text-[11px] font-mono text-slate-200 rounded focus:outline-none focus:border-amber-accent transition-colors"
              disabled={isLoading}
            />
          </div>
          {validationErrors.departureTime && (
            <p className="text-[10px] text-rose-400 mt-1">{validationErrors.departureTime}</p>
          )}
        </div>

        {/* Load Weight */}
        <div>
          <label htmlFor="weight-input" className="block text-[11px] font-medium text-slate-400 mb-1">
            Gross Weight (lbs)
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none text-slate-400">
              <Gauge className="w-3 h-3" />
            </div>
            <input
              id="weight-input"
              type="number"
              step="500"
              min="1000"
              max="120000"
              value={weightLbs}
              onChange={(e) => {
                setWeightLbs(Number(e.target.value));
                if (validationErrors.weightLbs) {
                  setValidationErrors((prev) => ({ ...prev, weightLbs: '' }));
                }
              }}
              className="w-full pl-7 pr-2 py-1.5 bg-dark-panel border border-dark-border text-[11px] font-mono text-slate-200 rounded focus:outline-none focus:border-amber-accent transition-colors"
              disabled={isLoading}
            />
          </div>
          {validationErrors.weightLbs && (
            <p className="text-[10px] text-rose-400 mt-1">{validationErrors.weightLbs}</p>
          )}
        </div>
      </div>

      {/* Sampling Interval Selector */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[11px] font-medium text-slate-400">
            Weather Sampling Interval
          </label>
          <span className="text-[10px] font-mono text-slate-500">
            Checkpoints every {intervalMiles} mi
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {([10, 25, 50] as const).map((interval) => (
            <button
              key={interval}
              type="button"
              onClick={() => setIntervalMiles(interval)}
              disabled={isLoading}
              className={`py-1.5 px-2 text-center text-xs font-mono rounded border transition-all ${
                intervalMiles === interval
                  ? 'bg-amber-muted border-amber-accent text-amber-300 font-semibold shadow-sm'
                  : 'bg-dark-panel border-dark-border text-slate-400 hover:text-slate-200 hover:bg-dark-elevated'
              }`}
            >
              {interval} mi
            </button>
          ))}
        </div>
      </div>

      {/* Submit Action */}
      <button
        type="submit"
        disabled={isLoading || disabled}
        className="w-full mt-2 py-2.5 px-4 rounded bg-amber-accent hover:bg-amber-hover text-slate-950 font-semibold text-xs tracking-wide flex items-center justify-center space-x-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-amber-950/20 active:translate-y-[0.5px]"
      >
        {isLoading ? (
          <>
            <RotateCw className="w-4 h-4 animate-spin text-slate-900" />
            <span>CALCULATING CORRIDORS...</span>
          </>
        ) : (
          <>
            <Search className="w-4 h-4 text-slate-900" />
            <span>ANALYZE ROUTE</span>
          </>
        )}
      </button>
    </form>
  );
};
