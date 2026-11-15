import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CheckpointInspector } from '../components/CheckpointInspector';
import { Checkpoint } from '../types/route';

describe('CheckpointInspector', () => {
  const mockCheckpoint: Checkpoint = {
    id: 'cp_5',
    sequence: 5,
    latitude: 39.7817,
    longitude: -89.6501,
    distance_miles: 125.0,
    distance_meters: 201168.0,
    estimated_elapsed_seconds: 7200.0,
    estimated_arrival_time: '2026-11-16T12:00:00Z',
    weather: {
      is_available: true,
      wind_mph: 36.5,
      rain_in_hr: 0.15,
      snow_in_hr: 0.0,
      forecast_time: '2026-11-16T12:00Z',
      wind_risk: 'High',
      rain_risk: 'Moderate',
      snow_risk: 'Low',
      risk_level: 'High',
    },
  };

  it('renders checkpoint details, weather metrics, and risk badges', () => {
    const handleClose = vi.fn();
    render(
      <CheckpointInspector
        checkpoint={mockCheckpoint}
        onClose={handleClose}
        truckWeightLbs={35000}
      />
    );

    expect(screen.getByText(/CP #5/i)).toBeInTheDocument();
    expect(screen.getByText(/125.0 mi/i)).toBeInTheDocument();
    expect(screen.getByText(/36.5 mph/i)).toBeInTheDocument();
    expect(screen.getByText(/0.15 in\/h/i)).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('displays load rule alert when heavy truck is exposed to elevated wind', () => {
    const handleClose = vi.fn();
    render(
      <CheckpointInspector
        checkpoint={mockCheckpoint}
        onClose={handleClose}
        truckWeightLbs={45000}
      />
    );

    expect(screen.getByText(/Load Rule Applied/i)).toBeInTheDocument();
    expect(screen.getByText(/45,000 lbs/i)).toBeInTheDocument();
  });

  it('handles unavailable weather gracefully', () => {
    const unavailCp: Checkpoint = {
      ...mockCheckpoint,
      weather: {
        is_available: false,
        wind_mph: null,
        rain_in_hr: null,
        snow_in_hr: null,
        wind_risk: 'Unavailable',
        rain_risk: 'Unavailable',
        snow_risk: 'Unavailable',
        risk_level: 'Unavailable',
      },
    };

    render(
      <CheckpointInspector
        checkpoint={unavailCp}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText(/Weather forecast data unavailable/i)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <CheckpointInspector
        checkpoint={mockCheckpoint}
        onClose={handleClose}
      />
    );

    const closeBtn = screen.getByTitle('Close inspector');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
