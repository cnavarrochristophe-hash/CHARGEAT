import os
import math
from typing import Optional

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Charge & Eat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo chargers around Lyon. Replace with the national IRVE importer in the next iteration.
CHARGERS = [
    {"id":"demo-1","name":"HPC Lyon Nord","operator":"DemoCharge","lat":45.7940,"lng":4.8320,"power_kw":300,"points":8},
    {"id":"demo-2","name":"HPC Villeurbanne","operator":"DemoCharge","lat":45.7705,"lng":4.8900,"power_kw":250,"points":6},
    {"id":"demo-3","name":"HPC Bron","operator":"DemoCharge","lat":45.7340,"lng":4.9100,"power_kw":180,"points":4},
    {"id":"demo-4","name":"HPC Vénissieux","operator":"DemoCharge","lat":45.7065,"lng":4.8720,"power_kw":300,"points":10},
    {"id":"demo-5","name":"HPC Oullins","operator":"DemoCharge","lat":45.7150,"lng":4.8070,"power_kw":150,"points":4},
]

DEMO_RESTAURANTS = [
    {"id":"r1","name":"Brasserie Demo Nord","category":"Brasserie","lat":45.7952,"lng":4.8312,"rating":4.4},
    {"id":"r2","name":"Snack Demo Nord","category":"Snack","lat":45.7928,"lng":4.8332,"rating":4.1},
    {"id":"r3","name":"Café Demo Villeurbanne","category":"Café","lat":45.7696,"lng":4.8910,"rating":4.3},
    {"id":"r4","name":"Restaurant Demo Bron","category":"Restaurant","lat":45.7332,"lng":4.9088,"rating":4.2},
    {"id":"r5","name":"Boulangerie Demo Vénissieux","category":"Boulangerie","lat":45.7070,"lng":4.8709,"rating":4.5},
    {"id":"r6","name":"Restaurant Demo Oullins","category":"Restaurant","lat":45.7139,"lng":4.8065,"rating":4.0},
]

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def estimate_walk_minutes(distance_km):
    # Demo fallback: 4.8 km/h average walking speed.
    return max(1, math.ceil(distance_km / 4.8 * 60))

async def google_nearby(lat, lng, radius_m=600):
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return None

    url = "https://places.googleapis.com/v1/places:searchNearby"
    body = {
        "includedTypes": ["restaurant", "cafe", "bakery", "fast_food", "meal_takeaway"],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_m}
        },
        "routingParameters": {
            "origin": {"latitude": lat, "longitude": lng},
            "travelMode": "WALK"
        }
    }
    fields = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.primaryType",
        "places.googleMapsUri",
        "places.rating",
        "routingSummaries"
    ])
    headers = {"Content-Type":"application/json","X-Goog-Api-Key":key,"X-Goog-FieldMask":fields}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

@app.get("/api/health")
def health():
    return {"ok": True, "version": "1.0.0"}

@app.get("/api/search")
async def search(
    lat: float = Query(...),
    lng: float = Query(...),
    min_power_kw: int = Query(150, ge=0),
    max_walk_minutes: int = Query(5, ge=1, le=30),
    radius_km: float = Query(20, gt=0, le=100),
):
    nearby = []
    for c in CHARGERS:
        d = haversine_km(lat, lng, c["lat"], c["lng"])
        if d <= radius_km and c["power_kw"] >= min_power_kw:
            restaurants = []
            for r in DEMO_RESTAURANTS:
                wd = haversine_km(c["lat"], c["lng"], r["lat"], r["lng"])
                wm = estimate_walk_minutes(wd)
                if wm <= max_walk_minutes:
                    restaurants.append({**r, "walking_minutes": wm, "walking_distance_m": round(wd*1000)})
            score = min(100, round(
                35 * min(c["power_kw"]/350, 1)
                + 25 * min(c["points"]/12, 1)
                + 40 * min(len(restaurants)/4, 1)
            ))
            nearby.append({
                **c,
                "distance_from_user_km": round(d, 2),
                "restaurants": sorted(restaurants, key=lambda x: x["walking_minutes"]),
                "score": score,
                "live_restaurant_data": False
            })

    # If Google is configured, enrich each charger with live nearby places.
    if os.getenv("GOOGLE_MAPS_API_KEY"):
        for item in nearby:
            try:
                data = await google_nearby(item["lat"], item["lng"], 600)
                if data and data.get("places"):
                    live = []
                    summaries = data.get("routingSummaries", [])
                    # Google routingSummaries contains route data associated with returned places.
                    for idx, p in enumerate(data["places"]):
                        loc = p.get("location", {})
                        if "latitude" not in loc:
                            continue
                        duration = None
                        distance = None
                        if idx < len(summaries):
                            routes = summaries[idx].get("legs", [])
                            if routes:
                                leg = routes[0]
                                duration = leg.get("duration")
                                distance = leg.get("distanceMeters")
                        if duration:
                            try:
                                seconds = int(str(duration).rstrip("s"))
                                minutes = math.ceil(seconds/60)
                            except Exception:
                                minutes = None
                        else:
                            minutes = None
                        if minutes is None:
                            continue
                        if minutes <= max_walk_minutes:
                            live.append({
                                "id": p.get("id"),
                                "name": p.get("displayName", {}).get("text",""),
                                "category": p.get("primaryType",""),
                                "address": p.get("formattedAddress",""),
                                "lat": loc.get("latitude"),
                                "lng": loc.get("longitude"),
                                "rating": p.get("rating"),
                                "walking_minutes": minutes,
                                "walking_distance_m": distance,
                                "maps_url": p.get("googleMapsUri")
                            })
                    if live:
                        item["restaurants"] = sorted(live, key=lambda x: x["walking_minutes"])
                        item["live_restaurant_data"] = True
                        item["score"] = min(100, item["score"] + min(15, len(live)*3))
            except Exception as exc:
                item["google_error"] = str(exc)

    nearby.sort(key=lambda x: (-x["score"], x["distance_from_user_km"]))
    return {"origin": {"lat":lat,"lng":lng}, "results": nearby}
