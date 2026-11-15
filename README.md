# Weather-Aware Truck Routing

A specialized commercial route-planning platform designed for freight dispatchers and truck drivers to evaluate corridor alternatives and plan routes against weather risks.

This repository contains the complete implementation through **Phase 2: Weather Integration, Checkpoint Sampling and Risk Classification**.

---

## System Architecture

```
spotter-assignment/
├── backend/
│   ├── core/                  # Django project settings, WSGI, URLs, CORS
│   ├── routing/               # Route planning, weather & geocoding app
│   │   ├── services/          # Isolated service layer
│   │   │   ├── geocoding.py        # Nominatim OpenStreetMap geocoder & in-memory cache
│   │   │   ├── routing_provider.py # OSRM & OpenRouteService routing providers
│   │   │   ├── sampler.py          # Great-circle polyline waypoint sampler
│   │   │   ├── weather.py          # Open-Meteo weather provider (batch, caching)
│   │   │   ├── risk_engine.py      # Risk classification engine (wind/rain/snow + load rules)
│   │   │   └── mock_data.py        # Offline test corridors
│   │   ├── serializers.py     # Request/response validation incl. weather & risk
│   │   ├── views.py           # RoutePlanView & HealthCheckView
│   │   └── tests/             # Unit and integration test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx               # Minimal status bar & engine indicator
│   │   │   ├── TripForm.tsx             # Trip inputs, presets, and validation
│   │   │   ├── RouteMap.tsx             # Leaflet interactive map with risk-colored checkpoints
│   │   │   ├── RouteComparison.tsx      # Route cards with risk assessment banners
│   │   │   ├── CheckpointInspector.tsx  # Per-checkpoint weather detail panel
│   │   │   └── StatusBanner.tsx         # Accessible error notifications
│   │   ├── services/api.ts         # Type-safe API client
│   │   ├── types/route.ts          # GeoJSON, Route, Checkpoint, and Weather interfaces
│   │   ├── utils/risk.ts           # Risk color mapping utilities
│   │   └── __tests__/              # Vitest & Testing Library test suite
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

---

## Design Philosophy

Built according to the project's visual direction:
- **Restrained dark interface**: Charcoal surfaces (`#0B0D10`, `#12151B`, `#171B22`), muted borders, and subtle amber accents (`#F59E0B`).
- **Typography hierarchy**: Inter for interface controls; IBM Plex Mono for technical measurements (miles, durations, weights, checkpoints).
- **Single workspace flow**:
  1. User enters trip details.
  2. User generates routes.
  3. User compares routes on the interactive map.
- **No artificial dashboard fluff**: Zero decorative charts, unnecessary sidebars, or generic SaaS widgets.

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.11)
- **Node.js**: 18+ (tested on Node 25)
- **npm**: 9+

---

## Getting Started

### 1. Backend Setup (Django + Django REST Framework)

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Create local environment configuration
cp .env.example .env

# Run database migrations (SQLite)
python manage.py migrate

# Run backend test suite
python manage.py test

# Start the Django development server
python manage.py runserver 127.0.0.1:8000
```

The backend API will be available at `http://127.0.0.1:8000`.

### 2. Frontend Setup (React + Vite + TypeScript)

```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run frontend tests
npm run test

# Run production build
npm run build

# Start the Vite development server (proxies /api to 127.0.0.1:8000)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django security key |
| `DEBUG` | `True` | Debug mode (`True`/`False`) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed HTTP hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |
| `ROUTING_PROVIDER` | `osrm` | Active routing engine: `osrm`, `openrouteservice`, or `mock` |
| `OSRM_BASE_URL` | `https://router.project-osrm.org` | OSRM routing endpoint |
| `OPENROUTESERVICE_API_KEY` | `""` | Optional API key if using OpenRouteService truck routing |
| `GEOCODING_USER_AGENT` | `spotter-weather-aware-truck-routing/1.0` | Custom User-Agent for Nominatim geocoding |
| `USE_MOCK_ROUTING` | `False` | Offline mock routes for development (strictly rejected when `DEBUG=False`) |
| `WEATHER_PROVIDER` | `open_meteo` | Active weather provider: `open_meteo` or `mock` |
| `OPENMETEO_API_KEY` | `""` | Reserved — Open-Meteo free tier requires no API key |
| `USE_MOCK_WEATHER` | `False` | Offline mock weather for development (strictly rejected when `DEBUG=False`) |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | Base URL for backend routing API |

---

## API Reference

### Health Check

`GET /api/health/`

Returns server status and active routing provider configuration.

```json
{
  "status": "healthy",
  "service": "weather-aware-truck-routing",
  "phase": "Phase 2: Weather Integration, Checkpoint Sampling and Risk Classification",
  "routing_provider": "osrm",
  "is_mock": false,
  "debug": true
}
```

### Route Planning

`POST /api/routes/plan/`

**Request Payload:**

```json
{
  "origin": "Chicago, IL",
  "destination": "Dallas, TX",
  "departure_time": "2026-11-16T08:00:00Z",
  "weight_lbs": 42000,
  "checkpoint_interval_miles": 25
}
```

**Response Payload:**

```json
{
  "origin": {
    "name": "Chicago, IL",
    "lat": 41.8755616,
    "lon": -87.6244212,
    "display_name": "Chicago, Cook County, Illinois, United States"
  },
  "destination": {
    "name": "Dallas, TX",
    "lat": 32.7762719,
    "lon": -96.7968559,
    "display_name": "Dallas, Dallas County, Texas, United States"
  },
  "departure_time": "2026-11-16T08:00:00Z",
  "weight_lbs": 42000.0,
  "checkpoint_interval_miles": 25,
  "total_routes_found": 2,
  "routes": [
    {
      "route_id": "route_1",
      "name": "Route 1: Primary Highway",
      "distance_meters": 1556111.9,
      "distance_miles": 966.9,
      "duration_seconds": 68415.9,
      "duration_hours": 19.0,
      "geometry": {
        "type": "LineString",
        "coordinates": [[-87.624351, 41.875563], ...]
      },
      "checkpoint_count": 40,
      "max_risk_level": "LOW",
      "risk_counts": {
        "low": 40,
        "moderate": 0,
        "high": 0,
        "severe": 0,
        "no_travel": 0,
        "unavailable": 0
      },
      "checkpoints": [
        {
          "id": "cp_0",
          "sequence": 0,
          "latitude": 41.875563,
          "longitude": -87.624351,
          "distance_miles": 0.0,
          "estimated_elapsed_seconds": 0.0,
          "estimated_arrival_time": "2026-11-16T08:00:00Z",
          "weather": {
            "wind_speed_mph": 3.4,
            "rain_intensity_in_hr": 0.0,
            "snow_intensity_in_hr": 0.0,
            "forecast_time": "2026-11-16T08:00:00Z",
            "is_available": true,
            "wind_risk": "LOW",
            "rain_risk": "LOW",
            "snow_risk": "LOW",
            "combined_risk": "LOW",
            "load_rule_applied": false,
            "load_rule_description": null
          }
        }
      ],
      "is_mock": false,
      "provider": "osrm"
    }
  ]
}
```

---

## Testing

- **Backend tests** (40 total):
  ```bash
  cd backend && python manage.py test
  ```
  Covers risk engine thresholds, load-weight rules, boundary conditions, Open-Meteo weather provider batching & caching, weather serializers, geocoding error conditions, polyline sampling math, routing provider integrations, and API endpoints.

- **Frontend tests** (13 total):
  ```bash
  cd frontend && npm run test
  ```
  Runs Vitest component tests verifying user input validation, corridor swapping, interval selection, route comparison with risk badges, checkpoint inspector rendering (unavailable state, load rule notices), and DOM accessibility.

---

## Weather Provider

**Open-Meteo** (free, no API key required)

- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Forecast window: 72-hour hourly forecasts
- Batch queries: up to 30 coordinates per request
- Cache: 30-minute in-memory cache (keyed on coordinates rounded to 2 decimal places)
- Units: `wind_speed_unit=mph`, `precipitation_unit=inch`
- Fields used: `wind_speed_10m`, `rain`, `snowfall`

Checkpoint arrival matching uses the **closest available hourly slot within 90 minutes** of the estimated arrival time. If the arrival falls outside the 72-hour forecast window, the checkpoint is marked `is_available: false` — it is **never silently classified as Low risk**.

---

## Risk Classification Methodology

Risk is assessed independently for wind, rain and snow at each checkpoint, then the **most severe condition** wins as the combined risk.

### Wind

| Speed (mph) | Risk |
|---|---|
| Below 25 | Low |
| 25–34 | Moderate |
| 35–44 | High |
| 45–54 | Severe |
| 55+ | No Travel |

### Rain

| Intensity (in/hr) | Risk |
|---|---|
| Below 0.10 | Low |
| 0.10–0.249 | Moderate |
| 0.25–0.499 | High |
| 0.50–1.00 | Severe |
| Above 1.00 | No Travel |

### Snow

| Intensity (in/hr) | Risk |
|---|---|
| Below 0.5 | Low |
| 0.5–0.99 | Moderate |
| 1.0–1.99 | High |
| 2.0–3.0 | Severe |
| Above 3.0 | No Travel |

### Load-Weight Adjustments

Applied in addition to the base wind thresholds using the truck gross weight supplied by the user:

| Condition | Load Threshold | Resulting Risk |
|---|---|---|
| Wind ≥ 55 mph | Any load | No Travel |
| Wind 45–54 mph | Load > 30,000 lb | No Travel |
| Wind 35–44 mph | Load > 40,000 lb | Severe |

### Unit Conversions

All incoming weather measurements are converted to canonical units before classification:
- Wind: km/h → mph (Open-Meteo is configured to return mph directly)
- Rainfall: mm/hr → in/hr (Open-Meteo returns inches when `precipitation_unit=inch`)
- Snowfall: cm/hr → in/hr (Open-Meteo snowfall is in cm; divided by 2.54)

---

## Known Limitations & Phase 3 Roadmap

- **OSRM Public Server Alternatives**: OSRM returns valid highway alternatives found in the OpenStreetMap routing graph (typically 1 to 2 alternatives depending on geographical road density). Artificial duplicate routes are never fabricated.
- **72-Hour Forecast Horizon**: Departures more than ~3 days in the future will have checkpoints marked `is_available: false`. Never silently classified as Low.
- **Phase 3 Planned**: Route ranking and recommendation engine — a composite weighted score across all checkpoints to recommend the safest corridor, plus a forecast heatmap slider for time-of-day weather visualization.
