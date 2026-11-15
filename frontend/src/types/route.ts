export interface GeocodedLocation {
  name: string;
  lat: number;
  lon: number;
  display_name: string;
}

export interface Checkpoint {
  id: string;
  sequence: number;
  latitude: number;
  longitude: number;
  distance_miles: number;
  distance_meters: number;
  estimated_elapsed_seconds: number;
  estimated_arrival_time: string;
}

export interface RouteGeometry {
  type: 'LineString';
  coordinates: [number, number][]; // [lon, lat]
}

export interface RouteOption {
  route_id: string;
  name: string;
  distance_meters: number;
  distance_miles: number;
  duration_seconds: number;
  duration_hours: number;
  geometry: RouteGeometry;
  checkpoints: Checkpoint[];
  checkpoint_count: number;
  is_mock: boolean;
  provider: string;
}

export interface RoutePlanRequest {
  origin: string;
  destination: string;
  departure_time: string; // ISO 8601
  weight_lbs: number;
  checkpoint_interval_miles: 10 | 25 | 50;
}

export interface RoutePlanResponse {
  origin: GeocodedLocation;
  destination: GeocodedLocation;
  departure_time: string;
  weight_lbs: number;
  checkpoint_interval_miles: number;
  routes: RouteOption[];
  total_routes_found: number;
}

export interface ApiErrorResponse {
  error: string;
  detail?: string;
  details?: Record<string, string | string[]>;
  code?: string;
  provider?: string;
}
