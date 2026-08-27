"""
Synthetic data generation for students and schools.

Per the proposal's Data Collection Methods (3.3) and Limitations (1.7 (ii)),
live KNEC exam records and NEMIS placement data are not accessible for this
project. This module generates synthetic student records (exam scores paired
with home coordinates within realistic Kenyan county boundaries) and a
synthetic school database, standing in for the real data sources until those
integrations exist.

The county bounding boxes below are deliberately approximate (a handful of
representative counties, not all 47) -- good enough to produce realistic
urban/rural distance spreads for testing the algorithm, not a substitute for
real administrative boundary data (which the proposal's feasibility study
points to OpenStreetMap / Google Maps Platform for for the production
system).
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from enum import Enum

from .distance import Coordinates


class SchoolCategory(str, Enum):
    """Mirrors Kenya's actual four-tier secondary school categorisation
    described in the proposal's Background (1.2): national schools draw from
    the whole country, extra-county from beyond one county, county schools
    from one county, and sub-county schools from a local catchment."""

    NATIONAL = "national"
    EXTRA_COUNTY = "extra_county"
    COUNTY = "county"
    SUB_COUNTY = "sub_county"


# (county name, lat_min, lat_max, lon_min, lon_max, urban_weight)
# urban_weight biases both student density and the concentration of
# national/extra-county schools -- reflecting the literature review's point
# (2.1) that higher-category schools cluster in urban centres.
COUNTIES = [
    ("Nairobi", -1.444, -1.163, 36.650, 37.103, 1.00),
    ("Kiambu", -1.171, -0.734, 36.652, 37.096, 0.70),
    ("Mombasa", -4.120, -3.950, 39.550, 39.750, 0.85),
    ("Kisumu", -0.250, 0.150, 34.550, 35.050, 0.65),
    ("Uasin Gishu", 0.350, 0.750, 34.900, 35.500, 0.55),
    ("Nakuru", -1.098, 0.350, 35.280, 36.350, 0.55),
    ("Kericho", -0.650, -0.050, 35.050, 35.550, 0.35),
    ("Bomet", -1.000, -0.500, 34.900, 35.400, 0.30),
    ("Machakos", -1.700, -0.900, 37.000, 37.900, 0.35),
    ("Turkana", 1.000, 4.500, 34.500, 36.500, 0.08),
    ("Garissa", -1.000, 2.000, 38.500, 41.500, 0.08),
    ("Kilifi", -3.900, -2.700, 39.400, 40.150, 0.20),
]


def _random_point_in_county(county, rng: random.Random) -> Coordinates:
    _, lat_min, lat_max, lon_min, lon_max, _ = county
    return Coordinates(rng.uniform(lat_min, lat_max), rng.uniform(lon_min, lon_max))


def _weighted_county_choice(rng: random.Random, weight_index: int = 5):
    weights = [c[weight_index] for c in COUNTIES]
    return rng.choices(COUNTIES, weights=weights, k=1)[0]


@dataclass
class Student:
    student_id: str
    exam_score: float  # KCPE-style score, 0-500
    home: Coordinates
    county: str


@dataclass
class School:
    school_id: str
    name: str
    category: SchoolCategory
    location: Coordinates
    county: str
    capacity: int
    performance_rating: float  # 0-100, higher = better mean KCSE performance


CAPACITY_RANGES = {
    SchoolCategory.NATIONAL: (160, 240),
    SchoolCategory.EXTRA_COUNTY: (120, 200),
    SchoolCategory.COUNTY: (80, 160),
    SchoolCategory.SUB_COUNTY: (40, 120),
}

# Mean/stdev of performance_rating by category -- national schools rate
# highest on average but distributions overlap, since a well-run sub-county
# school can outperform a poorly run extra-county one.
PERFORMANCE_PARAMS = {
    SchoolCategory.NATIONAL: (85, 6),
    SchoolCategory.EXTRA_COUNTY: (72, 8),
    SchoolCategory.COUNTY: (60, 10),
    SchoolCategory.SUB_COUNTY: (48, 12),
}


def generate_students(n: int, seed: int | None = None) -> list[Student]:
    """Generate n synthetic students with KCPE-like exam scores (normal,
    mean 250/500, clipped) and home coordinates drawn from the county table,
    weighted by population density so rural counties are represented but
    outnumbered -- matching Kenya's actual population distribution shape."""
    rng = random.Random(seed)
    students = []
    for i in range(n):
        county = _weighted_county_choice(rng, weight_index=5)
        score = rng.normalvariate(250, 60)
        score = max(0.0, min(500.0, score))
        students.append(
            Student(
                student_id=f"STU-{i+1:06d}",
                exam_score=round(score, 1),
                home=_random_point_in_county(county, rng),
                county=county[0],
            )
        )
    return students


def generate_schools(
    n_national: int = 5,
    n_extra_county: int = 15,
    n_county: int = 30,
    n_sub_county: int = 50,
    seed: int | None = None,
) -> list[School]:
    """Generate a synthetic school database across the four categories.
    National/extra-county schools are drawn preferentially from
    higher-urban-weight counties; county/sub-county schools are spread more
    evenly, including into the low-weight (rural/remote) counties -- this is
    what produces the urban-concentration effect the proposal's literature
    review (2.1) describes as the structural cause of long-distance
    placement."""
    rng = random.Random(seed)
    schools: list[School] = []
    counter = 1

    plan = [
        (SchoolCategory.NATIONAL, n_national, 5),  # weight_index 5 = urban_weight
        (SchoolCategory.EXTRA_COUNTY, n_extra_county, 5),
        (SchoolCategory.COUNTY, n_county, None),  # None => uniform choice
        (SchoolCategory.SUB_COUNTY, n_sub_county, None),
    ]

    for category, count, weight_index in plan:
        mean, stdev = PERFORMANCE_PARAMS[category]
        cap_lo, cap_hi = CAPACITY_RANGES[category]
        for _ in range(count):
            county = (
                _weighted_county_choice(rng, weight_index)
                if weight_index is not None
                else rng.choice(COUNTIES)
            )
            rating = rng.normalvariate(mean, stdev)
            rating = max(0.0, min(100.0, rating))
            schools.append(
                School(
                    school_id=f"SCH-{counter:05d}",
                    name=f"{county[0]} {category.value.replace('_', ' ').title()} School {counter}",
                    category=category,
                    location=_random_point_in_county(county, rng),
                    county=county[0],
                    capacity=rng.randint(cap_lo, cap_hi),
                    performance_rating=round(rating, 1),
                )
            )
            counter += 1

    return schools
