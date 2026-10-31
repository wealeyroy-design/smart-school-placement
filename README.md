# Smart School Placement Optimization System

Final year project — Kabarak University, Department of Computer Science.
Student: Kibiwott Roy Kipkoech (CS/MK/0693/09/23). Supervisor: Dr Andrew Kipkebut.

A full-stack web system that places students into secondary schools using a
proximity-weighted, merit-aware matching algorithm, instead of Kenya's current
merit-only, geography-blind KCPE placement process. It implements all four
modules from the project proposal (section 3.4.4):

| Module | What it is | Where it lives |
|---|---|---|
| Module 1 | Student registration and results management | `backend/placements`, `frontend/src/pages/student` |
| Module 2 | School database and capacity management | `backend/placements`, `frontend/src/pages/school_admin` |
| Module 3 | Proximity-weighted placement algorithm | `placement_algorithm/` |
| Module 4 | Student, parent and administrator portals | `backend/accounts`, `frontend/src` |

**Stack:** Django 5 + Django REST Framework + JWT auth on the backend, React 19
+ Vite on the frontend, PostgreSQL as the database (with a zero-setup SQLite
fallback for quick review), and a standalone, independently-tested Python
package for the matching algorithm itself.

---

## 1. What's in this folder

```
smart-school-placement/
    placement_algorithm/   The Module 3 matching engine — pure Python, no
                            Django dependency. Distance, scoring, Gale-Shapley
                            matching, evaluation metrics. See its own section
                            below; the original README for it is folded into
                            this one.
    tests/                 pytest suite for placement_algorithm (46 tests).
    demo.py                Standalone CLI demo of the algorithm alone (no
                            database/servers needed) — generates synthetic
                            data and compares against a merit-only baseline.
    backend/                Django project.
        config/             settings.py, urls.py, wsgi.py
        accounts/            Custom user model with roles + JWT auth endpoints
        placements/           Schools, students, placement runs, appeals,
                              analytics — the REST API used by the frontend
    frontend/               React (Vite) single-page app.
        src/pages/student/         Student + parent portal (Module 1, 4)
        src/pages/school_admin/    School administrator portal (Module 2, 4)
        src/pages/ministry_admin/  Ministry administrator portal (Module 3, 4)
    requirements.txt        Dependencies for placement_algorithm/tests/demo.py
                            (not the Django backend — see backend/requirements.txt)
```

## 2. Prerequisites

- Python 3.10+ (backend and algorithm both use modern type-hint syntax)
- Node.js 18+ and npm (frontend)
- PostgreSQL 14+ — optional. If you don't want to install Postgres, skip
  straight to SQLite mode in step 4; everything works the same either way.

## 3. Quick start — the algorithm alone (no database, no servers)

If you just want to see Module 3 working on its own, exactly as it was
developed and tested before being wired into the web app:

```bash
cd smart-school-placement
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

pytest -v                       # 46 tests
python3 demo.py                 # compares against a merit-only baseline
```

Expect output ending in something like:

```
Average placement distance reduced by 95.7% (286.8km -> 12.31km)
```

Useful flags: `--students 5000 --seed 7`, `--merit-weight 0.8
--proximity-weight 0.2`, `--max-distance-km 100 --max-candidates 10`,
`--skip-stability-check`. Run `python3 demo.py --help` for the full list.

## 4. Running the full system (backend + frontend)

### 4a. Database

**Option A — PostgreSQL (matches the proposal's tech stack):**

```bash
sudo service postgresql start      # or however Postgres is managed on your OS
sudo -u postgres psql -c "CREATE USER placement_admin WITH PASSWORD 'placement_dev_pw';"
sudo -u postgres psql -c "CREATE DATABASE smart_school_placement OWNER placement_admin;"
```

The backend reads connection details from environment variables (`DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), defaulting to the values
above on `localhost:5432`. Override them if your setup differs.

**Option B — SQLite (zero setup, good for a quick look):**

```bash
export DB_ENGINE=sqlite
```

Set this before running any `manage.py` command below. Functionally
equivalent for development — same models, same API, same frontend.

### 4b. Backend (Django)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python3 manage.py migrate
python3 manage.py seed_demo_data     # creates demo users, schools, students
python3 manage.py run_placement      # runs the algorithm once over the seed data

python3 manage.py runserver 127.0.0.1:8000
```

`seed_demo_data` creates a ministry admin, a school admin, a parent account
(`parent_demo`, linked to two students), 100 schools, 600 students and a few
sample appeals across several Kenyan counties, all with exam scores and
coordinates generated by `placement_algorithm.data_gen`. Every seeded account
uses the password `demo-pass-1234`; usernames are printed to the console when
the command runs (e.g. `ministry_admin`, `school_admin`, `parent_demo`, `student0001`).
School capacities are scaled so total slots are about 1.5x the cohort
(`--capacity-ratio`), and student names are synthetic combinations of common
Kenyan names, not real people.

`run_placement` invokes the same `match_students_to_schools` engine from
`placement_algorithm/` against the real database via
`backend/placements/services.py` — this is the bridge between Module 3 and
the rest of the app. You can also trigger a run from the Ministry
Administrator portal in the browser instead of the command line.

Open `http://127.0.0.1:8000/` for a backend status page: whether the
database is connected, how many records it holds, links to the web app, the
admin back office and the API, the demo accounts, and the most useful
commands.

The admin back office at `http://127.0.0.1:8000/admin/` (log in as
`ministry_admin`) has a dashboard of key figures, a **Run placement
algorithm** button, searchable and filterable lists of students, schools,
placements, runs and appeals with colour-coded statuses, inline capacity
editing for schools, and bulk *approve / reject / under review* actions for
appeals.

The backend serves the API at `http://127.0.0.1:8000/api/`. Django admin is
at `http://127.0.0.1:8000/admin/` (create a superuser with
`python3 manage.py createsuperuser` if you want to use it).

To run the backend test suite (35 tests, exercises the full API including
permissions and an end-to-end placement run):

```bash
python3 manage.py test
```

### 4c. Frontend (React)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The dev server proxies `/api` requests to the
Django backend at `127.0.0.1:8000`, so both servers need to be running
together. Log in with any of the seeded accounts from `seed_demo_data`
(password `demo-pass-1234`), or register a new student account from the
login page.

### 4d. Everyday use once both servers are up

- **Ministry administrator** (`ministry_admin`): trigger placement runs with
  adjustable merit/proximity weights and see each run compared against the
  merit-only baseline, review the run history, upload or correct exam
  results, view analytics (by school category, by student county, appeals by
  status), resolve appeals.
- **School administrator** (`school_admin_N`): manage a school's details and
  capacity, view its placed students.
- **Student / parent** (`studentNNNN`, or register a new account): view exam
  results and placement, see nearby schools, submit appeals. Parent accounts
  see all of their linked children.

## 5. How the pieces fit together

`backend/placements/services.py` is the seam between the web app and the
algorithm package: it reads `Student`/`School` rows out of Postgres,
translates them into the plain dataclasses `placement_algorithm` expects
(`_to_algo_student`/`_to_algo_school`), calls
`match_students_to_schools()` unchanged, then writes the resulting
`Placement` rows back to the database inside a transaction. The algorithm
package itself has zero Django dependency — it's imported via a `sys.path`
adjustment in `backend/config/settings.py` rather than duplicated, so
`placement_algorithm/` stays the single source of truth and can still be
tested and demoed completely on its own (section 3 above).

### Module 3 in more detail — how the matching engine works

This is a **student-proposing deferred acceptance** algorithm (the "college
admissions" variant of Gale-Shapley) — the many-to-one generalisation of the
original Gale & Shapley (1962) algorithm, needed because each school has
multiple slots, not just one.

1. Every student gets an ordered preference list over nearby, eligible
   schools, ranked by a composite score combining academic merit and inverse
   distance (weights are tunable — `ScoreWeights`, exposed in the Ministry
   Administrator portal as a slider).
2. Every school ranks the students who might apply to it by the same
   composite score.
3. Students propose to their top remaining choice; schools tentatively hold
   their best `capacity` applicants and reject the rest; rejected students
   propose to their next choice; repeat until no one has an unanswered
   proposal outstanding.

The result is provably **stable**: no student-school pair exists where both
the student would rather switch to that school *and* the school would rather
admit that student over one of its current admits. `matching.is_stable`
independently verifies this rather than just trusting the algorithm.

`matching.baseline_merit_only_allocation` is a deliberately simple simulation
of *the current system* — students ranked strictly by exam score, filling
national schools first, then extra-county, county, sub-county, with zero
regard for distance — used purely to produce the before/after comparison
that section 2.3 of the proposal calls for.

### Why synthetic data

The proposal's own Limitations section (1.7) notes that live KNEC/NEMIS
examination and placement records are not accessible for this project.
`data_gen.py` generates synthetic students and schools within realistic
Kenyan county boundaries, standing in for the real data sources — the
"simulated placement datasets" approach described in the proposal's Data
Collection Methods (3.3). Every run is seeded, so results are reproducible.

### Swapping in the real Google Maps API later

`distance.py` defines a `DistanceProvider` interface. `HaversineDistanceProvider`
(the default used everywhere) needs no API key and no network access.
`GoogleMapsDistanceProvider` is stubbed with the shape it needs but
deliberately raises `NotImplementedError` in `_call_api` — fill that in with
a real `googlemaps.Client(...).distance_matrix(...)` call once an API key is
available, and every other module keeps working unchanged, since they only
depend on the `DistanceProvider` interface, not on Haversine specifically.

## 6. Troubleshooting

- **`ModuleNotFoundError: placement_algorithm`** when running Django
  commands: make sure you're running `manage.py` from inside `backend/`, not
  from the repo root — `settings.py` adds the parent directory to
  `sys.path` relative to its own location.
- **Postgres connection refused**: either start Postgres (see 4a) or set
  `export DB_ENGINE=sqlite` to skip it entirely.
- **CORS errors in the browser console**: make sure you're opening
  `http://127.0.0.1:5173` (the Vite dev server), not `8000` directly, and
  that both servers are running. `CORS_ALLOWED_ORIGINS` in `settings.py`
  only allows the Vite dev origin.
- **Port already in use**: another process is already bound to 8000 or 5173;
  stop it or pass a different port (`runserver 127.0.0.1:8001`, `npm run dev
  -- --port 5174` — remember to update `vite.config.js`'s proxy target and
  `CORS_ALLOWED_ORIGINS` accordingly if you change the backend port).

## 7. Project status against the proposal

All four modules (section 3.4.4) are implemented and working end-to-end:
registration, results upload, school/capacity management, the matching
algorithm itself, and role-based portals for students, parents, school
administrators and the ministry administrator — verified via the Django/pytest
test suites (81 tests total) and a full browser walkthrough of every role.

Not yet implemented (left as future work, consistent with the proposal's
scope statement in 1.6): a live Google Maps Distance Matrix integration
(stubbed, see section 5 above), and integration with real KNEC/NEMIS data
sources (the proposal's own Limitations section notes these aren't
accessible for this project — see "Why synthetic data" above).
