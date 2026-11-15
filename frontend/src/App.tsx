import { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { TripForm } from './components/TripForm';
import { RouteComparison } from './components/RouteComparison';
import { CheckpointInspector } from './components/CheckpointInspector';
import { RouteMap } from './components/RouteMap';
import { StatusBanner } from './components/StatusBanner';
import { planRoute, checkBackendHealth, ApiError } from './services/api';
import { Checkpoint, RoutePlanRequest, RoutePlanResponse } from './types/route';

const ROUTE_COLORS: Record<string, string> = {
  route_1: '#F59E0B', // Primary Amber
  route_2: '#38BDF8', // Cyan / Sky
  route_3: '#A78BFA', // Violet / Lavender
  mock_route_1: '#F59E0B',
  mock_route_2: '#38BDF8',
  mock_route_3: '#A78BFA',
};

export function App() {
  const [routePlan, setRoutePlan] = useState<RoutePlanResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<Checkpoint | null>(null);
  const [truckWeightLbs, setTruckWeightLbs] = useState<number>(42000);
  const [forecastOffsetHours, setForecastOffsetHours] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<{ message: string; detail?: string } | null>(null);
  const [backendStatus, setBackendStatus] = useState<{
    status: string;
    routing_provider: string;
    is_mock: boolean;
  }>({
    status: 'checking',
    routing_provider: 'osrm',
    is_mock: false,
  });

  const inspectorRef = useRef<HTMLDivElement>(null);

  // Auto-scroll inspector into view when a checkpoint is clicked
  useEffect(() => {
    if (selectedCheckpoint && inspectorRef.current) {
      inspectorRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [selectedCheckpoint]);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then((status) => {
      setBackendStatus(status);
    });
  }, []);

  const handleTripSubmit = async (params: RoutePlanRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    setSelectedCheckpoint(null);
    setForecastOffsetHours(null);
    setTruckWeightLbs(params.weight_lbs);

    try {
      const response = await planRoute(params);
      setRoutePlan(response);

      // Prefer the recommended route as the initial active selection
      if (response.recommendation?.recommended_route_id) {
        setSelectedRouteId(response.recommendation.recommended_route_id);
      } else if (response.routes && response.routes.length > 0) {
        setSelectedRouteId(response.routes[0].route_id);
      } else {
        setSelectedRouteId(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage({
          message: err.message,
          detail: err.detail,
        });
      } else {
        setErrorMessage({
          message: 'Failed to calculate route alternatives.',
          detail: err instanceof Error ? err.message : 'Unknown error occurred.',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectRoute = (routeId: string) => {
    setSelectedRouteId(routeId);
    setSelectedCheckpoint(null);
  };

  const routes = routePlan?.routes || [];
  const activeRoute = routes.find((r) => r.route_id === selectedRouteId) || routes[0] || null;

  return (
    <div className="h-screen w-screen flex flex-col bg-dark-bg text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        providerName={backendStatus.routing_provider}
        isMock={backendStatus.is_mock}
      />

      {/* Main Workspace (Side Panel + Interactive Map) */}
      <main className="flex-1 flex flex-col md:flex-row min-h-0 relative">
        {/* Left Side Panel: Trip Form + Route Comparison + Checkpoint Inspector */}
        <aside className="w-full md:w-[390px] lg:w-[420px] h-full flex flex-col bg-dark-surface border-r border-dark-border shrink-0 z-10 overflow-y-auto">
          {/* Error Banner */}
          {errorMessage && (
            <StatusBanner
              message={errorMessage.message}
              detail={errorMessage.detail}
              onDismiss={() => setErrorMessage(null)}
            />
          )}

          {/* Trip Configuration Section */}
          <TripForm
            onSubmit={handleTripSubmit}
            isLoading={isLoading}
          />

          {/* Route Comparison & Recommendation Section */}
          {routes.length > 0 && (
            <RouteComparison
              routes={routes}
              recommendation={routePlan?.recommendation}
              selectedRouteId={selectedRouteId}
              onSelectRoute={handleSelectRoute}
              colors={ROUTE_COLORS}
            />
          )}

          {/* Checkpoint Inspector Panel */}
          {selectedCheckpoint && (
            <div ref={inspectorRef}>
              <CheckpointInspector
                checkpoint={selectedCheckpoint}
                onClose={() => setSelectedCheckpoint(null)}
                truckWeightLbs={truckWeightLbs}
                departureTime={routePlan?.departure_time}
                forecastOffsetHours={forecastOffsetHours}
              />
            </div>
          )}

          {/* Instruction hint if checkpoints are loaded but none selected */}
          {routes.length > 0 && !selectedCheckpoint && activeRoute && (
            <div className="p-3 text-[11px] font-mono text-slate-400 border-t border-dark-border/40 bg-dark-panel/40 text-center">
              Click any circular checkpoint on the map to inspect wind, rain, and snow risk.
            </div>
          )}
        </aside>

        {/* Right Main Area: Large Interactive Map & Weather Heatmap */}
        <section className="flex-1 h-full relative overflow-hidden bg-dark-bg">
          <RouteMap
            origin={routePlan?.origin || null}
            destination={routePlan?.destination || null}
            routes={routes}
            selectedRouteId={selectedRouteId}
            onSelectRoute={handleSelectRoute}
            selectedCheckpointId={selectedCheckpoint?.id || null}
            onSelectCheckpoint={setSelectedCheckpoint}
            colors={ROUTE_COLORS}
            isLoading={isLoading}
            departureTime={routePlan?.departure_time}
            forecastOffsetHours={forecastOffsetHours}
            onChangeForecastOffset={setForecastOffsetHours}
            truckWeightLbs={truckWeightLbs}
          />
        </section>
      </main>
    </div>
  );
}

export default App;
