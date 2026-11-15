# Weather-Aware Truck Routing

A specialized commercial route-planning platform designed for freight dispatchers and truck drivers to evaluate corridor alternatives, inspect hourly weather hazards, and recommend the safest route option for commercial vehicles.

This repository contains the complete implementation through **Phase 3: Route Recommendation, Weather Heatmap and Finalization**.

---

## System Architecture

```
spotter-assignment/
├── backend/
│   ├── core/                  # Django project settings, WSGI, URLs, CORS
│   ├── routing/               # Route planning, weather & recommendation app
│   │   ├── services/          # Isolated service layer
│   │   │   ├── geocoding.py        # Photon (OpenStreetMap) geocoder & in-memory cache
│   │   │   ├── routing_provider.py # OSRM & OpenRouteService routing providers
│   │   │   ├── sampler.py          # Great-circle polyline waypoint sampler
│   │   │   ├── weather.py          # Open-Meteo weather provider (batch, caching)
│   │   │   ├── risk_engine.py      # Risk classification engine (wind/rain/snow + load rules)
│   │   │   ├── recommendation.py   # Route risk exposure & lexicographical recommendation
│   │   │   └── mock_data.py        # Offline test corridors
│   │   ├── serializers.py     # Request/response validation incl. weather & recommendation
│   │   ├── views.py           # RoutePlanView & HealthCheckView
│   │   └── tests/             # Unit and integration test suite (52 tests)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx               # Minimal status bar & engine indicator
│   │   │   ├── TripForm.tsx             # Trip inputs, presets, and validation
│   │   │   ├── RouteMap.tsx             # Leaflet map with corridor weather heatmap
│   │   │   ├── ForecastSlider.tsx       # 0–48 hour forecast horizon slider
│   │   │   ├── RouteComparison.tsx      # Route alternatives with recommendation banner
│   │   │   ├── CheckpointInspector.tsx  # Checkpoint weather detail panel
│   │   │   └── StatusBanner.tsx         # Accessible error notifications
│   │   ├── services/api.ts         # Type-safe API client
│   │   ├── types/route.ts          # GeoJSON, Route, Checkpoint, and Weather interfaces
│   │   ├── utils/risk.ts           # Risk colors & client-side forecast evaluation
│   │   └── __tests__/              # Vitest & Testing Library test suite (19 tests)
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

---

## Technology Stack

- **Backend**:
  - Python 3.10+ (tested on Python 3.11)
  - Django 5.2 & Django REST Framework 3.16
  - Requests with session pooling, throttling, and in-memory TTL caching
  - Geographic math via Haversine great-circle sampling
- **Frontend**:
  - React 18 & TypeScript 5
  - Vite 6 build toolchain
  - Tailwind CSS with bespoke dark charcoal design system
  - Leaflet 1.9 with high-contrast inverted dark tiles
  - Lucide React icons
- **Testing**:
  - Django `TestCase` with DRF `APIClient` (52 tests)
  - Vitest & React Testing Library (19 tests)

---

## Design Philosophy

Built according to the project's visual direction:
- **Restrained dark interface**: Charcoal surfaces (`#0B0D10`, `#12151B`, `#171B22`), muted borders, and subtle amber accents (`#F59E0B`).
- **Typography hierarchy**: Inter for interface controls; IBM Plex Mono for technical measurements (miles, durations, weights, checkpoints).
- **Single workspace flow**:
  1. User enters trip details (Origin, Destination, Departure Time, Truck Weight, Checkpoint Interval).
  2. User generates alternative highway corridors.
  3. System evaluates hourly weather risks and recommends the optimal route.
  4. User inspects checkpoints and slides through the 0–48-hour forecast horizon.
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
| `GEOCODING_USER_AGENT` | `spotter-weather-aware-truck-routing/1.0` | Custom User-Agent for Photon geocoding |
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
  "phase": "Phase 3: Route Recommendation, Weather Heatmap and Finalization",
  "routing_provider": "osrm",
  "weather_provider": "open-meteo",
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

**Response Payload (truncated sample):**

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
  "recommendation": {
    "recommended_route_id": "route_1",
    "has_recommendation": true,
    "reason": "Selected for shortest travel time (19h 00m vs 19h 13m, 12m faster) among equally safe alternatives.",
    "evaluated_routes_count": 2,
    "eligible_routes_count": 2
  },
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
      "max_risk_level": "Low",
      "is_recommended": true,
      "recommendation_reason": "Selected for shortest travel time...",
      "is_eligible": true,
      "rank": 1,
      "risk_summary": {
        "severe_risk_miles": 0.0,
        "high_risk_miles": 0.0,
        "moderate_risk_miles": 0.0,
        "low_risk_miles": 966.9,
        "no_travel_miles": 0.0,
        "unavailable_miles": 0.0,
        "average_risk": 0.0,
        "has_no_travel": false,
        "has_unavailable": false,
        "total_distance_miles": 966.9,
        "travel_duration_hours": 19.0,
        "evaluated_segments_count": 39
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
            "wind_risk": "Low",
            "rain_risk": "Low",
            "snow_risk": "Low",
            "risk_level": "Low"
          },
          "hourly_forecast": [...]
        }
      ]
    }
  ]
}
```

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

Applied in addition to base wind thresholds using the truck gross weight:

| Condition | Load Threshold | Resulting Risk |
|---|---|---|
| Wind ≥ 55 mph | Any load | No Travel |
| Wind 45–54 mph | Load > 30,000 lb | No Travel |
| Wind 35–44 mph | Load > 40,000 lb | Severe |

---

## Route Recommendation Engine

### Strict Lexicographic Ranking Order

Routes are ranked using the exact four assignment priorities:

1. **Fewest Severe-risk miles**
2. **Fewest High-risk miles**
3. **Lowest Average risk score** (weighted by segment distance on a 0.0 to 4.0 scale: Low=0, Moderate=1, High=2, Severe=3, No Travel=4)
4. **Shortest Travel time**

This order is strictly lexicographic; travel time cannot outweigh weather risk.

### Distance-Weighted Segment Exposure

Segments between adjacent checkpoints $C_i$ and $C_{i+1}$ are assigned the **worse of the two endpoint risk classifications** (conservative safety rule). Segment length $d_i = \text{dist}_{i+1} - \text{dist}_i$ is accumulated into risk mile buckets.

### Fail-Safe Handling

- **No Travel**: Any route crossing a No Travel segment is marked `is_eligible: false` and is disqualified from recommendation.
- **Unavailable Weather**: Any route with missing forecast data is marked `is_eligible: false` and is never treated as safe.
- **No Safe Routes**: If all alternatives contain No Travel or missing data, the engine clearly reports that no safe recommendation is available with a detailed deterministic reason.

---

## Weather Heatmap & 0–48-Hour Forecast Horizon Slider

- **Corridor Weather Heatmap**: Route geometry is dynamically sliced into risk-colored segments (Emerald, Amber, Orange, Red, Crimson) reflecting real road weather conditions.
- **0–48-Hour Slider**:
  - Dragging the slider inspects corridor conditions at departure $+ X$ hours.
  - Updates polyline segment risk colors and checkpoint dots in real time.
  - Uses pre-fetched hourly forecast arrays (no round-trip backend calls during scrubbing).
  - **Stability guarantee**: Moving the slider does **not** alter the route recommendation, which remains locked to the truck's actual ETA arrival conditions.

---

## Testing

### Backend Test Suite (52 tests)

```bash
cd backend
python manage.py test routing --verbosity=1
```

Covers:
- Risk classification engine thresholds, boundary conditions, and load rules (10 tests)
- Open-Meteo weather provider, caching, batching, and error handling (5 tests)
- Route risk summaries, conservative segment weighting, lexicographic ranking, No Travel exclusions, and determinism (12 tests)
- Sampler math, geocoding service, serializers, and API endpoints (25 tests)

### Frontend Test Suite (19 tests)

```bash
cd frontend
npm run test -- --run
```

Covers:
- TripForm input validation, weights, intervals, and presets (5 tests)
- RouteComparison cards, ranking, recommendation banners, and No Travel warnings (4 tests)
- ForecastSlider tick jumps, offset mode, and ETA reset (4 tests)
- CheckpointInspector metrics, load rule alerts, and unavailable states (4 tests)
- StatusBanner error notifications (2 tests)

### Production Build

```bash
cd frontend
npm run build
```

TypeScript type checking and Vite production bundle generation with zero warnings or errors.

---

## Suggested Loom Walkthrough Outline (5–10 Minutes)

1. **Introduction & Motivation (1:00)**
   - Explain the commercial dispatch problem: commercial trucks cannot treat weather as a generic forecast; high crosswinds cause blowovers for light loads, and heavy loads suffer severe braking degradation in snow/rain.
2. **Trip Configuration & Geocoding (1:00)**
   - Demonstrate entering Origin (`Chicago, IL`) and Destination (`Dallas, TX`).
   - Highlight the truck gross weight input (`42,000 lbs`) and checkpoint sampling intervals (`25 mi`).
   - Click "Analyze Route" and observe sub-second corridor generation via OSRM and Open-Meteo.
3. **Route Comparison & Recommendation (1:30)**
   - Point out the **Recommended Corridor** banner with its deterministic explanation.
   - Explain the lexicographic priority order: Fewest Severe miles → Fewest High miles → Lowest Average risk → Shortest duration.
   - Show how Route 1 was selected over Route 2 due to faster travel time among equally safe options.
4. **Corridor Weather Heatmap (1:30)**
   - Zoom in on the Leaflet map and show the risk-colored polyline segments hugging actual highway curves.
   - Show the risk legend: Low (Emerald), Moderate (Amber), High (Orange), Severe (Red), No Travel (Crimson).
5. **0–48-Hour Forecast Horizon Slider (2:00)**
   - Scrub the forecast slider from Departure ETA to `+12h` and `+24h`.
   - Point out that the corridor heatmap and checkpoint markers dynamically react to changing atmospheric fronts.
   - Show that the recommendation card remains securely anchored to truck arrival ETA.
6. **Checkpoint Inspection (1:00)**
   - Click a checkpoint dot on the map.
   - Review wind speed, rain intensity, snowfall, and load-weight rule triggers.
   - Show the comparison between ETA arrival conditions and the active slider snapshot.
7. **Architecture & Test Suite (1:00)**
   - Highlight clean service isolation: `risk_engine.py`, `recommendation.py`, `weather.py`, `sampler.py`.
   - Show 52 Django tests and 19 React tests passing.

---

## Deployment Instructions

### Frontend (Static SPA)

The frontend is a static Vite single-page application built to `frontend/dist/`.

**Build Command:**
```bash
cd frontend
npm run build
```

**Deployment Options:**
- **Vercel / Netlify / Cloudflare Pages**: Connect the repository and configure:
  - Root directory: `frontend`
  - Build command: `npm run build`
  - Output directory: `dist`
  - Environment variable: `VITE_API_BASE_URL=https://<your-backend-domain>/api`
- **Reverse Proxy / Nginx**: Serve `frontend/dist` with `try_files $uri $uri/ /index.html;`.

### Backend (Django API)

**Production Settings:**
1. Configure `backend/.env`:
   ```ini
   DEBUG=False
   SECRET_KEY=<strong-random-production-key>
   ALLOWED_HOSTS=api.yourdomain.com,your-service.onrender.com
   CORS_ALLOWED_ORIGINS=https://app.yourdomain.com
   ROUTING_PROVIDER=osrm
   WEATHER_PROVIDER=open-meteo
   USE_MOCK_ROUTING=False
   USE_MOCK_WEATHER=False
   ```
2. Install production server (`gunicorn`):
   ```bash
   pip install gunicorn
   ```
3. Run migrations and collect static files:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
4. Start WSGI worker:
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```
- **Hosting Platforms**: Compatible with Render, Railway, Fly.io, AWS ECS, or Docker containers.

---

## Known Limitations

- **OSRM Public Server Routing**: The public OSRM demonstration server returns 1 to 2 alternatives for typical interstate corridors based on the OpenStreetMap graph. In compliance with the assignment rules, artificial duplicate routes are never fabricated.
- **Forecast Window**: Open-Meteo free tier provides hourly forecasts up to 72 hours out. Trips departing beyond this window will have checkpoints marked `Unavailable` and are safely disqualified from recommendation.
