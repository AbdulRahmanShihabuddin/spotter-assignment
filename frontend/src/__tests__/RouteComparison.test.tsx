import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RouteComparison } from '../components/RouteComparison';
import { RouteOption, RouteRecommendation } from '../types/route';

describe('RouteComparison', () => {
  const mockRoutes: RouteOption[] = [
    {
      route_id: 'route_1',
      name: 'Route 1: via I-55 S',
      distance_meters: 1550000,
      distance_miles: 963.1,
      duration_seconds: 68400,
      duration_hours: 19.0,
      geometry: { type: 'LineString', coordinates: [[-87.6, 41.8], [-96.8, 32.7]] },
      checkpoints: [],
      checkpoint_count: 20,
      is_mock: false,
      provider: 'osrm',
      max_risk_level: 'Low',
      risk_counts: { low: 20, moderate: 0, high: 0, severe: 0, no_travel: 0, unavailable: 0 },
      risk_summary: {
        severe_risk_miles: 0.0,
        high_risk_miles: 0.0,
        moderate_risk_miles: 0.0,
        low_risk_miles: 963.1,
        no_travel_miles: 0.0,
        unavailable_miles: 0.0,
        average_risk: 0.0,
        has_no_travel: false,
        has_unavailable: false,
        total_distance_miles: 963.1,
        travel_duration_hours: 19.0,
        evaluated_segments_count: 19,
      },
      is_recommended: true,
      recommendation_reason: 'Selected for shortest travel time among equally safe alternatives.',
      is_eligible: true,
      rank: 1,
    },
    {
      route_id: 'route_2',
      name: 'Route 2: via I-57 S, I-40 W',
      distance_meters: 1600000,
      distance_miles: 994.2,
      duration_seconds: 72000,
      duration_hours: 20.0,
      geometry: { type: 'LineString', coordinates: [[-87.6, 41.8], [-96.8, 32.7]] },
      checkpoints: [],
      checkpoint_count: 22,
      is_mock: false,
      provider: 'osrm',
      max_risk_level: 'Moderate',
      risk_counts: { low: 18, moderate: 4, high: 0, severe: 0, no_travel: 0, unavailable: 0 },
      risk_summary: {
        severe_risk_miles: 0.0,
        high_risk_miles: 0.0,
        moderate_risk_miles: 180.0,
        low_risk_miles: 814.2,
        no_travel_miles: 0.0,
        unavailable_miles: 0.0,
        average_risk: 0.18,
        has_no_travel: false,
        has_unavailable: false,
        total_distance_miles: 994.2,
        travel_duration_hours: 20.0,
        evaluated_segments_count: 21,
      },
      is_recommended: false,
      is_eligible: true,
      rank: 2,
    },
  ];

  const mockRecommendation: RouteRecommendation = {
    recommended_route_id: 'route_1',
    has_recommendation: true,
    reason: 'Selected for shortest travel time (19h 00m vs 20h 00m) among equally safe alternatives.',
    evaluated_routes_count: 2,
    eligible_routes_count: 2,
  };

  const colors = {
    route_1: '#F59E0B',
    route_2: '#38BDF8',
  };

  it('renders all route options with distances, durations, and risk badges', () => {
    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
        recommendation={mockRecommendation}
        selectedRouteId="route_1"
        onSelectRoute={handleSelect}
        colors={colors}
      />
    );

    expect(screen.getByText(/Route 1: via I-55 S/i)).toBeInTheDocument();
    expect(screen.getByText(/Route 2: via I-57 S, I-40 W/i)).toBeInTheDocument();
    expect(screen.getByText('963.1')).toBeInTheDocument();
    expect(screen.getByText('994.2')).toBeInTheDocument();
    expect(screen.getByText('LOW')).toBeInTheDocument();
    expect(screen.getByText('MODERATE')).toBeInTheDocument();
  });

  it('renders recommendation banner with deterministic explanation and badge', () => {
    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
        recommendation={mockRecommendation}
        selectedRouteId="route_1"
        onSelectRoute={handleSelect}
        colors={colors}
      />
    );

    expect(screen.getByText(/RECOMMENDED CORRIDOR/i)).toBeInTheDocument();
    expect(screen.getByText(mockRecommendation.reason)).toBeInTheDocument();
    expect(screen.getByText('RECOMMENDED')).toBeInTheDocument();
  });

  it('displays warning when no safe recommendation is available', () => {
    const noSafeRec: RouteRecommendation = {
      recommended_route_id: null,
      has_recommendation: false,
      reason: 'No safe corridor recommendation available: all alternative routes contain segments classified as No Travel.',
      evaluated_routes_count: 2,
      eligible_routes_count: 0,
    };

    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
        recommendation={noSafeRec}
        selectedRouteId="route_1"
        onSelectRoute={handleSelect}
        colors={colors}
      />
    );

    expect(screen.getByText(/NO SAFE RECOMMENDATION/i)).toBeInTheDocument();
    expect(screen.getByText(/all alternative routes contain segments classified as No Travel/i)).toBeInTheDocument();
  });

  it('calls onSelectRoute when a route card is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
        recommendation={mockRecommendation}
        selectedRouteId="route_1"
        onSelectRoute={handleSelect}
        colors={colors}
      />
    );

    const secondRouteCard = screen.getByText(/Route 2: via I-57 S/i).closest('[role="button"]')!;
    fireEvent.click(secondRouteCard);

    expect(handleSelect).toHaveBeenCalledWith('route_2');
  });
});
