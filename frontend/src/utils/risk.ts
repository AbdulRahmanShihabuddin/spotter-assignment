import { Checkpoint, CheckpointWeather, HourlyForecastItem, RiskLevelType } from '../types/route';

export const RISK_COLORS: Record<RiskLevelType, string> = {
  Low: '#10B981',        // Emerald
  Moderate: '#F59E0B',   // Amber
  High: '#F97316',       // Orange
  Severe: '#EF4444',     // Red
  'No Travel': '#DC2626',// Crimson
  Unavailable: '#64748B',// Slate
};

export const RISK_SEVERITY_ORDER: Record<RiskLevelType, number> = {
  Unavailable: 0,
  Low: 1,
  Moderate: 2,
  High: 3,
  Severe: 4,
  'No Travel': 5,
};

export function getRiskBadgeClasses(risk: RiskLevelType = 'Low'): {
  bg: string;
  text: string;
  border: string;
} {
  switch (risk) {
    case 'No Travel':
      return {
        bg: 'bg-rose-950/80',
        text: 'text-rose-300 font-bold',
        border: 'border-rose-700',
      };
    case 'Severe':
      return {
        bg: 'bg-red-950/70',
        text: 'text-red-300 font-semibold',
        border: 'border-red-800',
      };
    case 'High':
      return {
        bg: 'bg-orange-950/70',
        text: 'text-orange-300 font-medium',
        border: 'border-orange-800',
      };
    case 'Moderate':
      return {
        bg: 'bg-amber-950/60',
        text: 'text-amber-300 font-medium',
        border: 'border-amber-800/80',
      };
    case 'Unavailable':
      return {
        bg: 'bg-slate-900/60',
        text: 'text-slate-400',
        border: 'border-slate-700',
      };
    case 'Low':
    default:
      return {
        bg: 'bg-emerald-950/50',
        text: 'text-emerald-400 font-medium',
        border: 'border-emerald-800/60',
      };
  }
}

export function classifyWindRisk(windMph: number | null | undefined, weightLbs: number): RiskLevelType {
  if (windMph === null || windMph === undefined) return 'Unavailable';
  if (windMph >= 55.0) return 'No Travel';
  if (windMph >= 45.0) {
    return weightLbs > 30000 ? 'No Travel' : 'Severe';
  }
  if (windMph >= 35.0) {
    return weightLbs > 40000 ? 'Severe' : 'High';
  }
  if (windMph >= 25.0) return 'Moderate';
  return 'Low';
}

export function classifyRainRisk(rainInHr: number | null | undefined): RiskLevelType {
  if (rainInHr === null || rainInHr === undefined) return 'Unavailable';
  if (rainInHr > 1.00) return 'No Travel';
  if (rainInHr >= 0.50) return 'Severe';
  if (rainInHr >= 0.25) return 'High';
  if (rainInHr >= 0.10) return 'Moderate';
  return 'Low';
}

export function classifySnowRisk(snowInHr: number | null | undefined): RiskLevelType {
  if (snowInHr === null || snowInHr === undefined) return 'Unavailable';
  if (snowInHr > 3.0) return 'No Travel';
  if (snowInHr >= 2.0) return 'Severe';
  if (snowInHr >= 1.0) return 'High';
  if (snowInHr >= 0.5) return 'Moderate';
  return 'Low';
}

export function calculateCombinedRisk(
  windRisk: RiskLevelType,
  rainRisk: RiskLevelType,
  snowRisk: RiskLevelType
): RiskLevelType {
  const risks = [windRisk, rainRisk, snowRisk];
  if (risks.includes('No Travel')) return 'No Travel';
  if (risks.includes('Severe')) return 'Severe';
  if (risks.includes('High')) return 'High';
  if (risks.includes('Unavailable')) {
    if (risks.includes('Moderate')) return 'Moderate';
    return 'Unavailable';
  }
  if (risks.includes('Moderate')) return 'Moderate';
  return 'Low';
}

/**
 * Evaluates weather conditions and risk at a specific forecast offset (in hours from departure)
 * using the checkpoint's pre-fetched hourly forecast timeline.
 */
export function getForecastAtOffset(
  checkpoint: Checkpoint,
  departureTimeIso: string,
  offsetHours: number,
  weightLbs: number
): CheckpointWeather {
  const timeline = checkpoint.hourly_forecast;
  if (!timeline || timeline.length === 0) {
    return {
      is_available: false,
      wind_mph: null,
      rain_in_hr: null,
      snow_in_hr: null,
      wind_risk: 'Unavailable',
      rain_risk: 'Unavailable',
      snow_risk: 'Unavailable',
      risk_level: 'Unavailable',
    };
  }

  const baseDt = new Date(departureTimeIso);
  const targetTimeMs = baseDt.getTime() + offsetHours * 3600 * 1000;

  let closestItem: HourlyForecastItem | null = null;
  let minDiffMs = Infinity;

  for (const item of timeline) {
    const itemDt = new Date(item.time);
    const diff = Math.abs(itemDt.getTime() - targetTimeMs);
    if (diff < minDiffMs) {
      minDiffMs = diff;
      closestItem = item;
    }
  }

  // Must match within 90 minutes (5400000 ms)
  if (!closestItem || minDiffMs > 5400000) {
    return {
      is_available: false,
      wind_mph: null,
      rain_in_hr: null,
      snow_in_hr: null,
      wind_risk: 'Unavailable',
      rain_risk: 'Unavailable',
      snow_risk: 'Unavailable',
      risk_level: 'Unavailable',
    };
  }

  const windRisk = classifyWindRisk(closestItem.wind_mph, weightLbs);
  const rainRisk = classifyRainRisk(closestItem.rain_in_hr);
  const snowRisk = classifySnowRisk(closestItem.snow_in_hr);
  const combined = calculateCombinedRisk(windRisk, rainRisk, snowRisk);

  return {
    is_available: true,
    wind_mph: closestItem.wind_mph,
    rain_in_hr: closestItem.rain_in_hr,
    snow_in_hr: closestItem.snow_in_hr,
    forecast_time: closestItem.time,
    wind_risk: windRisk,
    rain_risk: rainRisk,
    snow_risk: snowRisk,
    risk_level: combined,
  };
}
