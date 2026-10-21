/* Offline schematic map.
 *
 * Draws the user's position and the nearby schools on an SVG canvas using
 * plain equirectangular maths. No map provider, no API key, no sign-in and
 * no internet connection are required -- the coordinates already live in
 * our own database, so the map keeps working in a demo hall with bad WiFi
 * (or none at all). It is a schematic distance diagram, not a navigation
 * map, which is also why it carries no third-party attribution.
 */

const KM_PER_DEG = 111.32;
const WIDTH = 340;
const HEIGHT = 280;
const PADDING = 26;

function project(lat, lon, lat0, lon0) {
  return {
    x: (lon - lon0) * KM_PER_DEG * Math.cos((lat0 * Math.PI) / 180),
    y: (lat0 - lat) * KM_PER_DEG,
  };
}

function niceRings(maxKm) {
  const candidates = [1, 2, 5, 10, 20, 25, 50, 100, 200];
  return candidates.filter((r) => r < maxKm);
}

export default function OfflineMap({ origin, schools }) {
  if (!origin) return null;

  const lat0 = origin.latitude;
  const lon0 = origin.longitude;
  const points = schools
    .filter((s) => s.latitude != null && s.longitude != null)
    .map((s) => {
      const p = project(s.latitude, s.longitude, lat0, lon0);
      return { ...s, ...p, km: Math.sqrt(p.x * p.x + p.y * p.y) };
    });

  const maxKm = Math.max(...points.map((p) => p.km), 1);
  const usable = Math.min(WIDTH, HEIGHT) / 2 - PADDING;
  const scale = usable / maxKm;
  const cx = WIDTH / 2;
  const cy = HEIGHT / 2;

  const toScreen = (p) => ({ x: cx + p.x * scale, y: cy - p.y * scale });

  const rings = niceRings(maxKm);
  const scaleBarKm = [1, 2, 5, 10, 20, 50].reverse().find((v) => v * scale <= 90) ?? 1;

  return (
    <div className="map-wrap">
      <svg
        className="offline-map"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="Schematic map of your position and the nearest schools"
      >
        <defs>
          <radialGradient id="map-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#eaf6ef" />
            <stop offset="100%" stopColor="#f7fbf9" />
          </radialGradient>
        </defs>

        <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="10" fill="url(#map-glow)" />
        <rect
          x="0.5"
          y="0.5"
          width={WIDTH - 1}
          height={HEIGHT - 1}
          rx="10"
          fill="none"
          stroke="#dde5e1"
        />

        {/* distance rings around the user */}
        {rings.map((r) => (
          <g key={r}>
            <circle
              cx={cx}
              cy={cy}
              r={r * scale}
              fill="none"
              stroke="#1d6f42"
              strokeOpacity="0.22"
              strokeDasharray="4 4"
            />
            <text x={cx + r * scale - 2} y={cy - 4} className="map-ring-label">
              {r} km
            </text>
          </g>
        ))}

        {/* schools */}
        {points.map((p) => {
          const s = toScreen(p);
          const r = Math.max(4, Math.min(11, 11 - p.km * 0.25));
          return (
            <g key={p.school_id}>
              <title>
                {p.name} - {p.distance_km} km
              </title>
              <circle cx={s.x} cy={s.y} r={r} fill="#1d6f42" fillOpacity="0.85" />
              <circle cx={s.x} cy={s.y} r={r + 2.5} fill="none" stroke="#ffffff" strokeWidth="1.5" />
            </g>
          );
        })}

        {/* the user */}
        <g>
          <circle cx={cx} cy={cy} r="11" fill="#d4a017" fillOpacity="0.22" />
          <circle cx={cx} cy={cy} r="6" fill="#d4a017" stroke="#ffffff" strokeWidth="2" />
          <text x={cx + 12} y={cy + 4} className="map-you-label">
            You
          </text>
        </g>

        {/* north arrow */}
        <g transform={`translate(${WIDTH - 26} 26)`}>
          <path d="M0 -12 L5 6 L0 2 L-5 6 Z" fill="#124a2b" />
          <text x="0" y="20" textAnchor="middle" className="map-ring-label">
            N
          </text>
        </g>

        {/* scale bar */}
        <g transform={`translate(18 ${HEIGHT - 20})`}>
          <line x1="0" y1="0" x2={scaleBarKm * scale} y2="0" stroke="#124a2b" strokeWidth="2" />
          <line x1="0" y1="-4" x2="0" y2="4" stroke="#124a2b" strokeWidth="2" />
          <line
            x1={scaleBarKm * scale}
            y1="-4"
            x2={scaleBarKm * scale}
            y2="4"
            stroke="#124a2b"
            strokeWidth="2"
          />
          <text x={scaleBarKm * scale + 6} y="4" className="map-ring-label">
            {scaleBarKm} km
          </text>
        </g>
      </svg>
      <p className="muted map-caption">
        Schematic distance map drawn from our own school database - no map account or internet
        connection needed. Not to scale for navigation.
      </p>
    </div>
  );
}
