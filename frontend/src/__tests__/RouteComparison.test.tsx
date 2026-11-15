import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RouteComparison } from '../components/RouteComparison';
import { RouteOption } from '../types/route';

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
    },
  ];

  const colors = {
    route_1: '#F59E0B',
    route_2: '#38BDF8',
  };

  it('renders all route options with distances and durations', () => {
    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
        selectedRouteId="route_1"
        onSelectRoute={handleSelect}
        colors={colors}
      />
    );

    expect(screen.getByText(/Route 1: via I-55 S/i)).toBeInTheDocument();
    expect(screen.getByText(/Route 2: via I-57 S, I-40 W/i)).toBeInTheDocument();
    expect(screen.getByText('963.1')).toBeInTheDocument();
    expect(screen.getByText('994.2')).toBeInTheDocument();
    expect(screen.getByText(/FASTEST/i)).toBeInTheDocument();
  });

  it('calls onSelectRoute when a route card is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <RouteComparison
        routes={mockRoutes}
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
