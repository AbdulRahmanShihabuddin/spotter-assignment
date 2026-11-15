import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Layers, Navigation } from 'lucide-react';
import { Checkpoint, GeocodedLocation, RiskLevelType, RouteOption } from '../types/route';
import {
  getForecastAtOffset,
  RISK_COLORS,
  RISK_SEVERITY_ORDER,
} from '../utils/risk';
import { ForecastSlider } from './ForecastSlider';

interface RouteMapProps {
  origin: GeocodedLocation | null;
  destination: GeocodedLocation | null;
  routes: RouteOption[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  selectedCheckpointId?: string | null;
  onSelectCheckpoint?: (checkpoint: Checkpoint | null) => void;
  colors: Record<string, string>;
  isLoading?: boolean;
  departureTime?: string;
  forecastOffsetHours?: number | null;
  onChangeForecastOffset?: (offset: number | null) => void;
  truckWeightLbs?: number;
}

/**
 * Finds the index of the coordinate in coords array that is closest to (lat, lon).
 */
function findClosestCoordIndex(coords: [number, number][], lat: number, lon: number, startIndex = 0): number {
  let closestIdx = startIndex;
  let minSqDist = Infinity;

  for (let i = startIndex; i < coords.length; i++) {
    const [cLon, cLat] = coords[i];
    const dLat = cLat - lat;
    const dLon = cLon - lon;
    const sqDist = dLat * dLat + dLon * dLon;
    if (sqDist < minSqDist) {
      minSqDist = sqDist;
      closestIdx = i;
    }
  }

  return closestIdx;
}

function worseRisk(riskA: RiskLevelType, riskB: RiskLevelType): RiskLevelType {
  const rankA = RISK_SEVERITY_ORDER[riskA] ?? 1;
  const rankB = RISK_SEVERITY_ORDER[riskB] ?? 1;

  if (rankA >= rankB) {
    return riskA;
  }
  return riskB;
}

export const RouteMap: React.FC<RouteMapProps> = ({
  origin,
  destination,
  routes,
  selectedRouteId,
  onSelectRoute,
  selectedCheckpointId,
  onSelectCheckpoint,
  colors,
  isLoading = false,
  departureTime,
  forecastOffsetHours = null,
  onChangeForecastOffset,
  truckWeightLbs = 35000,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const routeLayersRef = useRef<L.FeatureGroup | null>(null);
  const heatmapLayersRef = useRef<L.FeatureGroup | null>(null);
  const checkpointLayersRef = useRef<L.FeatureGroup | null>(null);
  const markerLayersRef = useRef<L.FeatureGroup | null>(null);
  const prevRoutesRef = useRef<RouteOption[] | null>(null);

  const [showCheckpoints, setShowCheckpoints] = useState(true);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [39.5, -98.35],
      zoom: 4,
      zoomControl: false,
    });

    // Zoom control in bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // OpenStreetMap standard tiles with high-contrast dark CSS filter
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
      className: 'dark-tiles',
    }).addTo(map);

    const routeGroup = L.featureGroup().addTo(map);
    const heatmapGroup = L.featureGroup().addTo(map);
    const checkpointGroup = L.featureGroup().addTo(map);
    const markerGroup = L.featureGroup().addTo(map);

    routeLayersRef.current = routeGroup;
    heatmapLayersRef.current = heatmapGroup;
    checkpointLayersRef.current = checkpointGroup;
    markerLayersRef.current = markerGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Pre-calculate sliced geometry segments for the active route
  const activeRoute = routes.find((r) => r.route_id === selectedRouteId) || routes[0] || null;

  // Render Routes, Heatmap Segments, and Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const routeGroup = routeLayersRef.current;
    const heatmapGroup = heatmapLayersRef.current;
    const markerGroup = markerLayersRef.current;
    if (!map || !routeGroup || !heatmapGroup || !markerGroup) return;

    routeGroup.clearLayers();
    heatmapGroup.clearLayers();
    markerGroup.clearLayers();

    if (!routes || routes.length === 0) {
      prevRoutesRef.current = null;
      return;
    }

    const allLatLngs: L.LatLng[] = [];

    // 1. Render all unselected alternative routes with muted corridor colors
    routes.forEach((route) => {
      const isSelected = route.route_id === selectedRouteId;
      const latLngs = route.geometry.coordinates.map(([lon, lat]) => L.latLng(lat, lon));

      if (latLngs.length > 0) {
        allLatLngs.push(...latLngs);
      }

      if (!isSelected) {
        const altColor = colors[route.route_id] || '#F59E0B';
        const polyline = L.polyline(latLngs, {
          color: altColor,
          weight: 3.0,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round',
        });

        polyline.on('mouseover', () => {
          polyline.setStyle({ opacity: 0.75, weight: 4.5 });
        });
        polyline.on('mouseout', () => {
          polyline.setStyle({ opacity: 0.35, weight: 3.0 });
        });
        polyline.on('click', () => {
          onSelectRoute(route.route_id);
        });

        polyline.bindTooltip(
          `<div class="font-sans">
            <div class="font-semibold text-slate-100">${route.name}</div>
            <div class="text-[11px] font-mono text-slate-300">
              ${route.distance_miles.toFixed(1)} mi • ${(route.duration_hours).toFixed(1)} hrs • Max Risk: ${route.max_risk_level || 'Low'}
            </div>
            <div class="text-[10px] text-amber-400 font-mono">Click to select and view weather heatmap</div>
          </div>`,
          { sticky: true }
        );

        polyline.addTo(routeGroup);
      }
    });

    // 2. Render Selected Route with Weather Heatmap along Corridor
    if (activeRoute) {
      const coords = activeRoute.geometry.coordinates;
      const checkpoints = activeRoute.checkpoints || [];

      // Dark background underlay for high visual contrast
      const activeLatLngs = coords.map(([lon, lat]) => L.latLng(lat, lon));
      const underlay = L.polyline(activeLatLngs, {
        color: '#0B0D10',
        weight: 8.5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
      });
      underlay.addTo(heatmapGroup);

      // If route has checkpoints, slice the geometry into risk-colored segments
      if (checkpoints.length > 1 && coords.length > 1) {
        let lastCoordIdx = 0;

        for (let i = 0; i < checkpoints.length - 1; i++) {
          const cpStart = checkpoints[i];
          const cpEnd = checkpoints[i + 1];

          const startIdx = findClosestCoordIndex(coords, cpStart.latitude, cpStart.longitude, lastCoordIdx);
          const endIdx = findClosestCoordIndex(coords, cpEnd.latitude, cpEnd.longitude, startIdx);
          lastCoordIdx = endIdx;

          // Determine risk at this segment
          let riskStart: RiskLevelType = cpStart.weather?.risk_level || 'Low';
          let riskEnd: RiskLevelType = cpEnd.weather?.risk_level || 'Low';

          // If forecast offset is active, evaluate risk at target offset
          if (forecastOffsetHours !== null && departureTime) {
            const wStart = getForecastAtOffset(cpStart, departureTime, forecastOffsetHours, truckWeightLbs);
            const wEnd = getForecastAtOffset(cpEnd, departureTime, forecastOffsetHours, truckWeightLbs);
            riskStart = wStart.risk_level;
            riskEnd = wEnd.risk_level;
          }

          const segRisk = worseRisk(riskStart, riskEnd);
          const segColor = RISK_COLORS[segRisk] || '#10B981';

          // Slice coordinates for this segment
          const segCoords = coords.slice(startIdx, Math.max(endIdx + 1, startIdx + 2));
          const segLatLngs = segCoords.length >= 2
            ? segCoords.map(([lon, lat]) => L.latLng(lat, lon))
            : [L.latLng(cpStart.latitude, cpStart.longitude), L.latLng(cpEnd.latitude, cpEnd.longitude)];

          const segPolyline = L.polyline(segLatLngs, {
            color: segColor,
            weight: 5.5,
            opacity: 0.95,
            lineCap: 'round',
            lineJoin: 'round',
          });

          const segMiles = Math.max(0, cpEnd.distance_miles - cpStart.distance_miles).toFixed(1);

          segPolyline.bindTooltip(
            `<div class="font-mono text-[11px] leading-tight space-y-0.5">
              <div class="flex items-center justify-between space-x-2">
                <span class="font-bold text-slate-100">Segment ${i + 1}: ${cpStart.distance_miles.toFixed(0)}-${cpEnd.distance_miles.toFixed(0)} mi (${segMiles} mi)</span>
                <span style="color: ${segColor}; font-weight: 700;">${segRisk.toUpperCase()}</span>
              </div>
              <div class="text-slate-400 text-[10px]">
                ${forecastOffsetHours !== null ? `Forecast Offset: +${forecastOffsetHours}h` : 'Condition at Truck ETA'}
              </div>
            </div>`,
            { sticky: true }
          );

          segPolyline.addTo(heatmapGroup);
        }
      } else {
        // Fallback single polyline if no checkpoints
        const fallbackPolyline = L.polyline(activeLatLngs, {
          color: colors[activeRoute.route_id] || '#F59E0B',
          weight: 5.5,
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round',
        });
        fallbackPolyline.addTo(heatmapGroup);
      }
    }

    // Add Origin Marker (A)
    if (origin) {
      const originIcon = L.divIcon({
        className: 'custom-map-marker',
        html: `
          <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: #12151B;
            border: 2px solid #10B981;
            border-radius: 50%;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
            color: #10B981;
            font-size: 11px;
            font-weight: 700;
          ">
            A
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const originMarker = L.marker([origin.lat, origin.lon], { icon: originIcon });
      originMarker.bindPopup(`
        <div class="text-xs">
          <div class="text-[10px] uppercase tracking-wider text-emerald-400 font-bold mb-0.5">Origin</div>
          <div class="font-medium text-slate-100">${origin.display_name}</div>
        </div>
      `);
      originMarker.addTo(markerGroup);
      allLatLngs.push(L.latLng(origin.lat, origin.lon));
    }

    // Add Destination Marker (B)
    if (destination) {
      const destIcon = L.divIcon({
        className: 'custom-map-marker',
        html: `
          <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: #12151B;
            border: 2px solid #F43F5E;
            border-radius: 50%;
            box-shadow: 0 0 12px rgba(244, 63, 94, 0.4);
            color: #F43F5E;
            font-size: 11px;
            font-weight: 700;
          ">
            B
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const destMarker = L.marker([destination.lat, destination.lon], { icon: destIcon });
      destMarker.bindPopup(`
        <div class="text-xs">
          <div class="text-[10px] uppercase tracking-wider text-rose-400 font-bold mb-0.5">Destination</div>
          <div class="font-medium text-slate-100">${destination.display_name}</div>
        </div>
      `);
      destMarker.addTo(markerGroup);
      allLatLngs.push(L.latLng(destination.lat, destination.lon));
    }

    // Only fit map bounds when a new set of routes is computed
    const isNewRouteSet = prevRoutesRef.current !== routes;
    if (isNewRouteSet && allLatLngs.length > 0) {
      prevRoutesRef.current = routes;
      const bounds = L.latLngBounds(allLatLngs);
      map.fitBounds(bounds, {
        padding: [60, 60],
        maxZoom: 12,
        animate: true,
        duration: 0.6,
      });
    }
  }, [
    routes,
    selectedRouteId,
    activeRoute,
    origin,
    destination,
    colors,
    onSelectRoute,
    forecastOffsetHours,
    departureTime,
    truckWeightLbs,
  ]);

  // Render Risk-Coded Checkpoints along the selected route
  useEffect(() => {
    const checkpointGroup = checkpointLayersRef.current;
    if (!checkpointGroup) return;

    checkpointGroup.clearLayers();

    if (!showCheckpoints || !routes || routes.length === 0 || !activeRoute) {
      return;
    }

    const checkpoints = activeRoute.checkpoints || [];
    const isOffsetMode = forecastOffsetHours !== null && Boolean(departureTime);

    checkpoints.forEach((cp) => {
      // Evaluate weather: either at offset or at arrival ETA
      let weather = cp.weather;
      if (isOffsetMode && departureTime) {
        weather = getForecastAtOffset(cp, departureTime, forecastOffsetHours!, truckWeightLbs);
      }

      const riskLevel: RiskLevelType = weather?.risk_level || 'Low';
      const riskColor = RISK_COLORS[riskLevel] || '#10B981';
      const isSelectedCp = cp.id === selectedCheckpointId;

      const isElevated = riskLevel === 'Severe' || riskLevel === 'No Travel';
      const radius = isSelectedCp ? 7.0 : isElevated ? 5.5 : 4.0;

      const circle = L.circleMarker([cp.latitude, cp.longitude], {
        className: 'checkpoint-marker',
        radius: radius,
        fillColor: riskColor,
        color: isSelectedCp ? '#FFFFFF' : '#0B0D10',
        weight: isSelectedCp ? 2.5 : 1.5,
        opacity: 1.0,
        fillOpacity: 0.90,
      });

      const etaTime = new Date(cp.estimated_arrival_time).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });

      const windTxt = weather?.wind_mph !== null && weather?.wind_mph !== undefined ? `${weather.wind_mph} mph` : 'N/A';
      const rainTxt = weather?.rain_in_hr !== null && weather?.rain_in_hr !== undefined ? `${weather.rain_in_hr} in/h` : '0 in/h';

      circle.bindTooltip(
        `<div class="font-mono text-[11px] leading-tight space-y-0.5">
          <div class="flex items-center justify-between space-x-2">
            <span class="font-bold text-slate-100">CP #${cp.sequence} (${cp.distance_miles.toFixed(1)} mi)</span>
            <span style="color: ${riskColor}; font-weight: 700;">${riskLevel.toUpperCase()}</span>
          </div>
          <div class="text-slate-400 text-[10px]">
            ${isOffsetMode ? `Forecast: +${forecastOffsetHours}h` : `ETA: ${etaTime}`}
          </div>
          <div class="text-slate-300 text-[10px]">Wind: ${windTxt} • Rain: ${rainTxt}</div>
        </div>`,
        { direction: 'top', offset: [0, -6] }
      );

      circle.on('click', () => {
        if (onSelectCheckpoint) {
          onSelectCheckpoint(cp);
        }
      });

      circle.addTo(checkpointGroup);
    });
  }, [
    routes,
    activeRoute,
    showCheckpoints,
    selectedCheckpointId,
    onSelectCheckpoint,
    forecastOffsetHours,
    departureTime,
    truckWeightLbs,
  ]);

  return (
    <div className="relative w-full h-full bg-dark-bg overflow-hidden flex flex-col">
      {/* Map Leaflet Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 z-20 bg-dark-bg/60 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
          <div className="px-4 py-3 rounded bg-dark-panel border border-dark-border shadow-xl flex items-center space-x-3 text-xs font-mono text-slate-200">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-accent animate-ping" />
            <span>Calculating corridors, risk exposures & route recommendations...</span>
          </div>
        </div>
      )}

      {/* Empty State Overlay on Initial Load */}
      {!isLoading && routes.length === 0 && (
        <div className="absolute inset-0 z-10 flex items-center justify-center p-6 pointer-events-none">
          <div className="max-w-md w-full p-6 rounded bg-dark-panel/90 border border-dark-border backdrop-blur-sm text-center shadow-2xl pointer-events-auto">
            <div className="w-10 h-10 rounded-full bg-dark-elevated border border-dark-border text-amber-accent mx-auto flex items-center justify-center mb-3">
              <Navigation className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100 mb-1">
              Ready for Route Planning & Weather Analysis
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Enter your trip details in the left panel and click{' '}
              <strong className="text-slate-200">Analyze Route</strong> to compute corridors with weather risk evaluation, ranking, and recommendations.
            </p>
            <div className="grid grid-cols-3 gap-2 text-left text-[11px] border-t border-dark-border pt-3 text-slate-400">
              <div className="p-2 rounded bg-dark-surface/60 border border-dark-border/40">
                <span className="font-mono text-amber-accent font-semibold block">1. Origin</span>
                Street address or city
              </div>
              <div className="p-2 rounded bg-dark-surface/60 border border-dark-border/40">
                <span className="font-mono text-amber-accent font-semibold block">2. Weight</span>
                Truck load lbs (wind rules)
              </div>
              <div className="p-2 rounded bg-dark-surface/60 border border-dark-border/40">
                <span className="font-mono text-amber-accent font-semibold block">3. Sampling</span>
                10, 25 or 50 mi intervals
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Map Controls & Legends (Top Right) */}
      {routes.length > 0 && (
        <div className="absolute top-4 right-4 z-10 flex flex-col items-end space-y-2 pointer-events-auto max-w-[220px]">
          {/* Checkpoints Toggle Button */}
          <button
            type="button"
            onClick={() => setShowCheckpoints((prev) => !prev)}
            className={`px-2.5 py-1.5 rounded border text-xs font-mono flex items-center space-x-1.5 shadow-lg backdrop-blur-sm transition-colors ${
              showCheckpoints
                ? 'bg-dark-panel/95 border-amber-accent/70 text-slate-100'
                : 'bg-dark-panel/80 border-dark-border text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle checkpoint dots along the route"
          >
            <Layers className="w-3.5 h-3.5 text-amber-accent" />
            <span>Checkpoints {showCheckpoints ? 'ON' : 'OFF'}</span>
            {activeRoute && (
              <span className="text-[10px] text-slate-400">
                ({activeRoute.checkpoint_count})
              </span>
            )}
          </button>

          {/* Minimal Map Route Legend */}
          <div className="p-2.5 rounded bg-dark-panel/95 border border-dark-border shadow-lg backdrop-blur-sm text-[11px] font-mono space-y-2 w-full">
            <div>
              <span className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase block border-b border-dark-border/60 pb-1 mb-1.5">
                Corridors
              </span>
              {routes.map((route) => {
                const isSelected = route.route_id === selectedRouteId;
                const color = colors[route.route_id] || '#F59E0B';
                return (
                  <div
                    key={route.route_id}
                    onClick={() => onSelectRoute(route.route_id)}
                    className={`flex items-center justify-between cursor-pointer py-0.5 px-1 rounded transition-colors ${
                      isSelected ? 'bg-dark-elevated text-slate-100' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span className="truncate">{route.name.split(':')[0]}</span>
                    </div>
                    {route.is_recommended && (
                      <span className="text-amber-accent text-[10px] ml-1">★</span>
                    )}
                    <span className="text-[10px] ml-auto pl-1 font-medium shrink-0">
                      {route.distance_miles.toFixed(0)} mi
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Weather Risk Severity Scale */}
            <div className="border-t border-dark-border/60 pt-1.5">
              <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase block mb-1">
                Risk Scale
              </span>
              <div className="grid grid-cols-5 gap-1 text-center text-[9px]">
                <div className="flex flex-col items-center">
                  <span className="w-2 h-2 rounded-full mb-0.5" style={{ backgroundColor: RISK_COLORS.Low }} />
                  <span className="text-slate-400">Low</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="w-2 h-2 rounded-full mb-0.5" style={{ backgroundColor: RISK_COLORS.Moderate }} />
                  <span className="text-slate-400">Mod</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="w-2 h-2 rounded-full mb-0.5" style={{ backgroundColor: RISK_COLORS.High }} />
                  <span className="text-slate-400">High</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="w-2 h-2 rounded-full mb-0.5" style={{ backgroundColor: RISK_COLORS.Severe }} />
                  <span className="text-slate-400">Sev</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="w-2 h-2 rounded-full mb-0.5" style={{ backgroundColor: RISK_COLORS['No Travel'] }} />
                  <span className="text-rose-400 font-bold">NoTrv</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating 0-48 Hour Forecast Slider (Top Center or Bottom Right) */}
      {routes.length > 0 && departureTime && onChangeForecastOffset && (
        <div className="absolute top-4 left-4 z-10 pointer-events-auto max-w-[340px] sm:max-w-[420px] w-full">
          <ForecastSlider
            departureTime={departureTime}
            forecastOffsetHours={forecastOffsetHours}
            onChangeOffset={onChangeForecastOffset}
            disabled={isLoading}
          />
        </div>
      )}

      {/* Bottom Floating Stats Bar for Selected Route */}
      {activeRoute && (
        <div className="absolute bottom-4 left-4 z-10 pointer-events-auto">
          <div className="px-3 py-2 rounded bg-dark-panel/95 border border-dark-border shadow-xl backdrop-blur-sm flex items-center space-x-3 text-xs font-mono text-slate-300">
            <div className="flex items-center space-x-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: colors[activeRoute.route_id] }}
              />
              <span className="text-slate-100 font-semibold truncate max-w-[170px]">
                {activeRoute.name}
              </span>
            </div>

            {activeRoute.is_recommended && (
              <>
                <span className="text-dark-border">|</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold text-[10px]">
                  ★ RECOMMENDED
                </span>
              </>
            )}

            <span className="text-dark-border">|</span>
            <div>
              <span className="text-slate-400 text-[10px]">MAX RISK: </span>
              <span
                className="font-bold text-[11px]"
                style={{ color: RISK_COLORS[activeRoute.max_risk_level || 'Low'] }}
              >
                {(activeRoute.max_risk_level || 'Low').toUpperCase()}
              </span>
            </div>
            <span className="text-dark-border">|</span>
            <div>
              <span className="text-slate-400 text-[10px]">DISTANCE: </span>
              <span className="text-slate-100 font-medium">
                {activeRoute.distance_miles.toLocaleString()} mi
              </span>
            </div>
            <span className="text-dark-border">|</span>
            <div>
              <span className="text-slate-400 text-[10px]">TIME: </span>
              <span className="text-slate-100 font-medium">
                {Math.floor(activeRoute.duration_hours)}h{' '}
                {Math.round((activeRoute.duration_hours % 1) * 60)}m
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
