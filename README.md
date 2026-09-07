# Charge & Eat — V1

Prototype web app/PWA for finding fast EV chargers near restaurants/cafés/snacks.

## What is included

- Next.js frontend
- FastAPI backend
- Local demo charger dataset (no external API key required)
- Optional Google Places integration for restaurants + routing summaries
- Browser geolocation
- Mobile-first UI suitable for iPhone Safari
- Docker Compose setup

## Quick start

### 1. Requirements

- Docker Desktop
- An iPhone and computer on the same Wi‑Fi for phone testing

### 2. Configure

Copy `.env.example` to `.env`.

For the first demo, you can leave `GOOGLE_MAPS_API_KEY` empty: the app uses demo restaurant data.

For live restaurant data, create a Google Maps Platform API key and enable Places API (New). Put it in `.env`.

### 3. Start

```bash
docker compose up --build
```

Then on the computer open:

http://localhost:3000

To test on an iPhone connected to the same Wi-Fi, find your computer's local IP (for example `192.168.1.25`) and open:

http://192.168.1.25:3000

If browser geolocation is blocked on a plain LAN HTTP address, use the "Demo Lyon" button or run the frontend behind HTTPS.

## API

Backend:
http://localhost:8000/docs

Health:
http://localhost:8000/api/health

Search:
GET /api/search?lat=45.764&lng=4.835&min_power_kw=150&max_walk_minutes=5

## Live data

The V1 intentionally separates charger discovery from restaurant discovery.

- Chargers: the included demo repository can later be replaced by an IRVE/data.gouv.fr importer.
- Restaurants: Google Places (New) is used when `GOOGLE_MAPS_API_KEY` is configured.
- Walking time: Google Places routing summaries can be used as an estimate. For exact turn-by-turn walking routes, the backend can be extended with Google Routes API.

## Next production steps

1. Add the national IRVE importer and scheduled refresh.
2. Add persistent PostgreSQL/PostGIS.
3. Add user accounts/favorites.
4. Add charger availability/pricing feeds where licensing permits.
5. Add a proper map provider and navigation deep links.
6. Add caching/rate limits and API cost monitoring.
