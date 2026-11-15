# Weather-Aware Truck Routing

A specialized commercial route-planning platform designed for freight dispatchers and truck drivers to evaluate corridor alternatives and plan routes against weather risks.

This repository contains the complete implementation for **Phase 1: Project Foundation and Route Generation**.

---

## System Architecture

```
spotter-assignment/
├── backend/
│   ├── core/                  # Django project settings, WSGI, URLs, CORS
│   ├── routing/               # Route planning & geocoding app
│   │   ├── services/          # Isolated service layer
│   │   │   ├── geocoding.py   # Nominatim OpenStreetMap geocoder & in-memory cache
│   │   │   ├── routing_provider.py # OSRM & OpenRouteService routing providers
│   │   │   ├── sampler.py     # Great-circle polyline waypoint sampler
│   │   │   └── mock_data.py   # Offline test corridors
│   │   ├── serializers.py     # Request/response validation
│   │   ├── views.py           # RoutePlanView & HealthCheckView
│   │   └── tests/             # Unit and integration test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx          # Minimal status bar & engine indicator
│   │   │   ├── TripForm.tsx        # Trip inputs, presets, and validation
│   │   │   ├── RouteMap.tsx        # Leaflet CartoDB Dark Matter interactive map
│   │   │   ├── RouteComparison.tsx # Alternative route cards & metrics
│   │   │   └── StatusBanner.tsx    # Accessible error notifications
│   │   ├── services/api.ts         # Type-safe API client
│   │   ├── types/route.ts          # GeoJSON, Route, and Checkpoint interfaces
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
  "phase": "Phase 1: Project Foundation and Route Generation",
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
      "checkpoints": [
        {
          "id": "cp_0",
          "sequence": 0,
          "latitude": 41.875563,
          "longitude": -87.624351,
          "distance_miles": 0.0,
          "estimated_elapsed_seconds": 0.0,
          "estimated_arrival_time": "2026-11-16T08:00:00Z"
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

- **Backend tests**:
  ```bash
  cd backend && python manage.py test
  ```
  Runs 25 unit and integration tests covering serializers, geocoding error conditions, polyline sampling math, routing provider integrations, and API endpoints.

- **Frontend tests**:
  ```bash
  cd frontend && npm run test
  ```
  Runs Vitest component tests verifying user input validation, corridor swapping, interval selection, route comparison switching, and DOM accessibility.

---

## Known Limitations & Phase 2 Roadmap

- **Phase 1 Scope**: This phase implements foundation, geocoding, multi-route alternative generation, checkpoint sampling along the road geometry, and interactive map comparison.
- **Weather Forecasts**: Per assignment instructions, live weather risk analysis, radar overlays, and checkpoint forecast evaluation are excluded from Phase 1 and will be introduced in subsequent phases.
- **OSRM Public Server Alternatives**: OSRM returns valid highway alternatives found in the OpenStreetMap routing graph (typically 1 to 3 alternatives depending on geographical road density). As instructed, artificial duplicate routes are never fabricated if the road network only yields 1 or 2 distinct paths.
