import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface StatusBannerProps {
  message: string;
  detail?: string;
  onDismiss?: () => void;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ message, detail, onDismiss }) => {
  if (!message) return null;

  return (
    <div className="mx-4 mt-3 p-3 rounded bg-rose-950/40 border border-rose-800/60 text-xs text-rose-200 flex items-start space-x-2.5">
      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="font-semibold text-rose-200">{message}</p>
        {detail && <p className="text-[11px] text-rose-300/80 mt-0.5 leading-relaxed">{detail}</p>}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="text-rose-400 hover:text-rose-200 p-0.5"
          title="Dismiss"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
