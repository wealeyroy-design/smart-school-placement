/* Offline schematic map.
 *
 * Draws the user's position and the nearby schools on an SVG canvas using
 * plain equirectangular maths. No map provider, no API key, no sign-in and
 * no internet connection are required -- the coordinates already live in
 * our own database, so the map keeps working in a demo hall with bad WiFi
 * (or none at all). It is a schematic distance diagram, not a navigation
 * map, which is also why it carries no third-party attribution.
 *
 * Radial distances use a square-root scale so that schools close to the
 * user are spread out and stay readable; each ring is still labelled with
 * its true distance in km.
 */

const KM_PER_DEG = 111.32;
const WIDTH = 340;
const HEIGHT = 280;
const PADDING = 26;
const MIN_FIRST_RING_PX = 22; // keep the first ring clear of the "You" marker
const MIN_RING_GAP_PX = 13; // keep ring labels from overlapping

function project(lat, lon, lat0, lon0) {
  return {
    x: (lon - lon0) * KM_PER_DEG * Math.cos((lat0 * Math.PI) / 180),
    y: (lat0 - lat) * KM_PER_DEG,
  };
}

// Pick only as many "nice" rings as can be labelled legibly.
function chooseRings(maxKm, radiusFor) {
  const candidates = [1, 2, 5, 10, 20, 25, 50, 100, 200];
  const chosen = [];
  let lastPx = MIN_FIRST_RING_PX - MIN_RING_GAP_PX;
  for (const km of candidates) {
    if (km > maxKm) break;
    const px = radiusFor(km);
    if (px - lastPx >= MIN_RING_GAP_PX) {
      chosen.push({ km, px });
      lastPx = px;
    }
  }
  return chosen;
}

// Text with a light outline behind it, drawn as two elements so it renders
// the same in every browser.
function HaloText({ className, children, ...props }) {
  return (
    <>
      <text
        {...props}
        className={className}
        fill="#f7fbf9"
        stroke="#f7fbf9"
        strokeWidth="3.5"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        {children}
      </text>
      <text {...props} className={className}>
        {children}
      </text>
    </>
  );
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
  const cx = WIDTH / 2;
  const cy = HEIGHT / 2;

  // Square-root radial scale: true distance km -> pixels from the centre.
  const radiusFor = (km) => usable * Math.sqrt(km / maxKm);

  const toScreen = (p) => {
    if (p.km === 0) return { x: cx, y: cy };
    const k = radiusFor(p.km) / p.km;
    return { x: cx + p.x * k, y: cy + p.y * k };
  };

  const rings = chooseRings(maxKm, radiusFor);

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
        {rings.map(({ km, px }) => (
          <circle
            key={km}
            cx={cx}
            cy={cy}
            r={px}
            fill="none"
            stroke="#1d6f42"
            strokeOpacity="0.22"
            strokeDasharray="4 4"
          />
        ))}

        {/* schools */}
        {points.map((p) => {
          const s = toScreen(p);
          const r = Math.max(4, Math.min(9, 9 - p.km * 0.12));
          return (
            <g key={p.school_id}>
              <title>{`${p.name} - ${p.distance_km} km`}</title>
              <circle cx={s.x} cy={s.y} r={r} fill="#1d6f42" fillOpacity="0.85" />
              <circle cx={s.x} cy={s.y} r={r + 2.5} fill="none" stroke="#ffffff" strokeWidth="1.5" />
            </g>
          );
        })}

        {/* ring labels: one per ring, at the top of the ring, drawn above the dots */}
        {rings.map(({ km, px }) => (
          <HaloText
            key={`label-${km}`}
            x={cx}
            y={cy - px - 3}
            textAnchor="middle"
            className="map-ring-label"
          >
            {km} km
          </HaloText>
        ))}

        {/* the user */}
        <g>
          <circle cx={cx} cy={cy} r="11" fill="#d4a017" fillOpacity="0.22" />
          <circle cx={cx} cy={cy} r="6" fill="#d4a017" stroke="#ffffff" strokeWidth="2" />
          <HaloText x={cx} y={cy + 24} textAnchor="middle" className="map-you-label">
            You
          </HaloText>
        </g>

        {/* north arrow */}
        <g transform={`translate(${WIDTH - 26} 26)`}>
          <path d="M0 -12 L5 6 L0 2 L-5 6 Z" fill="#124a2b" />
          <text x="0" y="20" textAnchor="middle" className="map-ring-label">
            N
          </text>
        </g>
      </svg>
      <p className="muted map-caption">
        Schematic distance map drawn from our own school database - no map account or internet
        connection needed. Rings show true distance; spacing is compressed so nearby schools stay
        readable. Not to scale for navigation.
      </p>
    </div>
  );
}