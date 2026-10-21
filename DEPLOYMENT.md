# Deployment Checklist — Smart School Placement Optimization System

This project is **complete and demo-ready**, not yet production-deployed. This
document is the ordered checklist for taking it live. Sections 1-5 are required;
Section 6 lists the optional integrations the proposal already flags as future
work.

Current status on the dev machine: Django 5 + DRF (SQLite) and a Vite dev
server, running locally at `127.0.0.1:8000` and `localhost:5173` for the demo.

---

## 1. Server & environment

- [ ] Provision a Linux VPS (or use a PaaS: Railway / Render / PythonAnywhere)
- [ ] Point a **domain** at the server (required for HTTPS)
- [ ] Install Python 3.10+ and Node.js 18+ (build machine), plus system build deps

## 2. PostgreSQL (the proposal's database of record)

- [ ] Install PostgreSQL 14+ and create the app database + user, e.g.:

```sql
CREATE ROLE placement_admin WITH LOGIN PASSWORD 'STRONG_PASSWORD';
CREATE DATABASE smart_school_placement OWNER placement_admin;
```

- [ ] Point Django at it via environment variables (never hardcode in code):

```bash
export DB_ENGINE=postgres
export DB_NAME=smart_school_placement
export DB_USER=placement_admin
export DB_PASSWORD=STRONG_PASSWORD
export DB_HOST=localhost
export DB_PORT=5432
```

## 3. Secrets & hardening

- [ ] Generate a real `DJANGO_SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
- [ ] Set production values in the server environment (`.env` / systemd / PaaS env):

```bash
export DJANGO_SECRET_KEY='<generated>'
export DJANGO_DEBUG=false
export DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
export CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

- [ ] **Remove the MD5 password fallback** from `backend/config/settings.py`
      (dev/demo-only) and re-seed with real hashes so production accounts use PBKDF2.
- [ ] Confirm `DEBUG` is `False` and no secrets exist in the repo.
      (Keep this outside the repo: `.env` must be git-ignored.)

## 4. Backend (Django + DRF)

- [ ] Ensure `backend/placements/management/commands/seed_demo_data.py` only runs
      with production-real data (it currently creates synthetic demo records).
- [ ] Production build steps on the server:

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

- [ ] Replace `runserver` with Gunicorn, run behind nginx or a PaaS web service:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

- [ ] nginx: reverse-proxy `/` to gunicorn, `/static/` to the collected statics,
      and `/api/` to gunicorn as well.
- [ ] Enforce HTTPS (Let's Encrypt) and redirect HTTP → HTTPS.

## 5. Frontend (React + Vite)

- [ ] Build production assets:

```bash
cd frontend
npm install
npm run build        # produces frontend/dist/
```

- [ ] Serve `frontend/dist/` from nginx (same domain), or deploy to a static host
      (Netlify / Vercel / GitHub Pages) and point it at the Django API.
- [ ] The Vite dev proxy (`localhost:5173` → `127.0.0.1:8000`) is **dev-only**
      — production traffic goes straight to the Django API via nginx.
- [ ] Verify end-to-end on the live domain: login, placement run, analytics,
      appeals, and the three role portals (student / parent, school admin,
      ministry admin).
- [ ] **"Use my current location" needs HTTPS in production.** The browser only
      grants geolocation on a secure origin (`https://`, or `localhost` during
      development). On a plain-HTTP public domain the button will be blocked by
      the browser and the manual coordinate entry remains the fallback. So make
      sure the live site is served over TLS.
- [ ] No map account, API key or third-party map service is required at any
      point: the offline schematic map is drawn from the coordinates already in
      the database, and the optional "map" links point at OpenStreetMap
      (free, no sign-in).

## 6. Optional — flagged as future work in the proposal

- [ ] **Google Maps Distance Matrix:** implement a real
      `googlemaps.Client(...).distance_matrix(...)` call in
      `placement_algorithm/distance.py` (`GoogleMapsDistanceProvider._call_api`),
      set the API key, and swap the provider in `services.py`.
- [ ] **Real KNEC/NEMIS data:** replace the synthetic data generator
      (`placement_algorithm/data_gen.py`) and `seed_demo_data` with actual
      exam-result and school imports. Not accessible for this project (see the
      proposal's Limitations section) — synthetic data is the documented stand-in.

---

## One-line summary for the defense

> *The system is fully built and demo-ready — all four modules working against a
> seeded dataset. Taking it to production means: PostgreSQL, Gunicorn behind
> nginx with HTTPS, a production build of the React app, proper secrets, and the
> Google Maps + KNEC/NEMIS integrations the proposal lists as future work.*