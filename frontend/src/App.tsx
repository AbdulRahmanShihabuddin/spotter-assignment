import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { TripForm } from './components/TripForm';
import { RouteComparison } from './components/RouteComparison';
import { RouteMap } from './components/RouteMap';
import { StatusBanner } from './components/StatusBanner';
import { planRoute, checkBackendHealth, ApiError } from './services/api';
import { RoutePlanRequest, RoutePlanResponse } from './types/route';

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

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then((status) => {
      setBackendStatus(status);
    });
  }, []);

  const handleTripSubmit = async (params: RoutePlanRequest) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await planRoute(params);
      setRoutePlan(response);

      if (response.routes && response.routes.length > 0) {
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

  const routes = routePlan?.routes || [];

  return (
    <div className="h-screen w-screen flex flex-col bg-dark-bg text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        providerName={backendStatus.routing_provider}
        isMock={backendStatus.is_mock}
      />

      {/* Main Workspace (Side Panel + Interactive Map) */}
      <main className="flex-1 flex flex-col md:flex-row min-h-0 relative">
        {/* Left Side Panel: Trip Form + Route Comparison */}
        <aside className="w-full md:w-[380px] lg:w-[410px] h-full flex flex-col bg-dark-surface border-r border-dark-border shrink-0 z-10 overflow-y-auto">
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

          {/* Route Comparison Section */}
          {routes.length > 0 && (
            <RouteComparison
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
              colors={ROUTE_COLORS}
            />
          )}
        </aside>

        {/* Right Main Area: Large Interactive Map */}
        <section className="flex-1 h-full relative overflow-hidden bg-dark-bg">
          <RouteMap
            origin={routePlan?.origin || null}
            destination={routePlan?.destination || null}
            routes={routes}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
            colors={ROUTE_COLORS}
            isLoading={isLoading}
          />
        </section>
      </main>
    </div>
  );
}

export default App;
