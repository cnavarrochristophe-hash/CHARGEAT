 "use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [location, setLocation] = useState(null);
  const [minPower, setMinPower] = useState(150);
  const [maxWalk, setMaxWalk] = useState(5);
  const [radius, setRadius] = useState(20);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Autorise la localisation ou utilise la démo Lyon.");

  function useDemo() {
    setLocation({ lat: 45.764, lng: 4.835, label: "Lyon (démo)" });
    setMessage("Position de démonstration sélectionnée.");
  }

  function locate() {
    if (!navigator.geolocation) {
      setMessage("La géolocalisation n'est pas disponible sur cet appareil.");
      return;
    }
    setMessage("Recherche de ta position…");
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setLocation({ lat: p.coords.latitude, lng: p.coords.longitude, label: "Ma position" });
        setMessage("Position récupérée.");
      },
      () => setMessage("Impossible d'obtenir la position. Tu peux utiliser la démo Lyon.")
    );
  }

  async function search() {
    if (!location) {
      setMessage("Choisis d'abord ta position.");
      return;
    }
    setLoading(true);
    setMessage("Recherche des meilleurs spots…");
    try {
      const url = new URL(`${API}/api/search`);
      url.searchParams.set("lat", location.lat);
      url.searchParams.set("lng", location.lng);
      url.searchParams.set("min_power_kw", minPower);
      url.searchParams.set("max_walk_minutes", maxWalk);
      url.searchParams.set("radius_km", radius);
      const res = await fetch(url);
      const data = await res.json();
      setResults(data.results || []);
      setMessage(`${data.results?.length || 0} spot(s) trouvé(s).`);
    } catch {
      setMessage("Erreur de connexion au serveur.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <div className="logo">⚡ Charge & Eat</div>
          <h1>Recharge rapide.<br/>Mange à côté.</h1>
          <p>Trouve une borne HPC avec un restaurant accessible à pied en quelques minutes.</p>
        </div>
      </header>

      <section className="panel">
        <div className="locationRow">
          <button className="primary" onClick={locate}>📍 Ma position</button>
          <button className="secondary" onClick={useDemo}>🧪 Démo Lyon</button>
        </div>
        <div className="location">{location ? `📍 ${location.label}` : "📍 Aucune position sélectionnée"}</div>

        <div className="filters">
          <label>Puissance minimale
            <select value={minPower} onChange={e=>setMinPower(Number(e.target.value))}>
              <option value="50">50 kW+</option>
              <option value="100">100 kW+</option>
              <option value="150">150 kW+</option>
              <option value="200">200 kW+</option>
              <option value="300">300 kW+</option>
            </select>
          </label>

          <label>Marche maximale
            <select value={maxWalk} onChange={e=>setMaxWalk(Number(e.target.value))}>
              <option value="3">3 min</option>
              <option value="5">5 min</option>
              <option value="7">7 min</option>
              <option value="10">10 min</option>
            </select>
          </label>

          <label>Rayon de recherche
            <select value={radius} onChange={e=>setRadius(Number(e.target.value))}>
              <option value="5">5 km</option>
              <option value="10">10 km</option>
              <option value="20">20 km</option>
              <option value="50">50 km</option>
            </select>
          </label>
        </div>

        <button className="search" onClick={search} disabled={loading}>
          {loading ? "Recherche…" : "🔎 Trouver les spots"}
        </button>
        <p className="message">{message}</p>
      </section>

      <section className="results">
        {results.map((r) => (
          <article className="card" key={r.id}>
            <div className="score">{r.score}<span>/100</span></div>
            <div className="charger">
              <div className="chargerTitle">⚡ {r.name}</div>
              <div className="muted">{r.operator} · {r.distance_from_user_km} km</div>
              <div className="specs"><b>{r.power_kw} kW</b><span>•</span><b>{r.points} points</b></div>
            </div>

            <div className="foodHeader">🍽️ À pied ≤ {maxWalk} min</div>
            {r.restaurants.length === 0 ? (
              <div className="empty">Aucun établissement trouvé dans la limite.</div>
            ) : (
              <div className="foodList">
                {r.restaurants.map((x) => (
                  <div className="food" key={x.id}>
                    <div>
                      <b>{x.name}</b>
                      <div className="muted">{x.category} {x.rating ? `· ⭐ ${x.rating}` : ""}</div>
                    </div>
                    <div className="walk">🚶 {x.walking_minutes} min</div>
                  </div>
                ))}
              </div>
            )}
            {r.live_restaurant_data && <div className="live">● Données restaurants en direct</div>}
          </article>
        ))}
      </section>

      <footer>
        V1 prototype · Les bornes affichées sans import IRVE sont des données de démonstration.
      </footer>
    </main>
  );
}
