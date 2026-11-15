export interface GeocodedLocation {
  name: string;
  lat: number;
  lon: number;
  display_name: string;
}

export type RiskLevelType = 'Low' | 'Moderate' | 'High' | 'Severe' | 'No Travel' | 'Unavailable';

export interface CheckpointWeather {
  is_available: boolean;
  wind_mph: number | null;
  rain_in_hr: number | null;
  snow_in_hr: number | null;
  forecast_time?: string | null;
  wind_risk: RiskLevelType;
  rain_risk: RiskLevelType;
  snow_risk: RiskLevelType;
  risk_level: RiskLevelType;
}

export interface HourlyForecastItem {
  time: string;
  wind_mph: number | null;
  rain_in_hr: number | null;
  snow_in_hr: number | null;
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
  weather?: CheckpointWeather;
  hourly_forecast?: HourlyForecastItem[];
}

export interface RouteGeometry {
  type: 'LineString';
  coordinates: [number, number][]; // [lon, lat]
}

export interface RiskCounts {
  low: number;
  moderate: number;
  high: number;
  severe: number;
  no_travel: number;
  unavailable: number;
}

export interface RiskSummary {
  severe_risk_miles: number;
  high_risk_miles: number;
  moderate_risk_miles: number;
  low_risk_miles: number;
  no_travel_miles: number;
  unavailable_miles: number;
  average_risk: number;
  has_no_travel: boolean;
  has_unavailable: boolean;
  total_distance_miles: number;
  travel_duration_hours: number;
  evaluated_segments_count: number;
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
  max_risk_level?: RiskLevelType;
  risk_counts?: RiskCounts;
  risk_summary?: RiskSummary;
  is_recommended?: boolean;
  recommendation_reason?: string | null;
  is_eligible?: boolean;
  ineligibility_reason?: string | null;
  rank?: number | null;
}

export interface RouteRecommendation {
  recommended_route_id: string | null;
  has_recommendation: boolean;
  reason: string;
  evaluated_routes_count: number;
  eligible_routes_count: number;
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
  recommendation?: RouteRecommendation;
}

export interface ApiErrorResponse {
  error: string;
  detail?: string;
  details?: Record<string, string | string[]>;
  code?: string;
  provider?: string;
}
