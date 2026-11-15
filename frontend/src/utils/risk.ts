import { RiskLevelType } from '../types/route';

export const RISK_COLORS: Record<RiskLevelType, string> = {
  Low: '#10B981',        // Emerald
  Moderate: '#F59E0B',   // Amber
  High: '#F97316',       // Orange
  Severe: '#EF4444',     // Red
  'No Travel': '#DC2626',// Crimson
  Unavailable: '#64748B',// Slate
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
