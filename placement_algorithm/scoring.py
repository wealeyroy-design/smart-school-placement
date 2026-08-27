"""
Composite scoring for student-school pairs.

Per the proposal's Module 3 functionality (3.4.4): "A weighted composite
score is calculated for each student-school pair, combining the student's
exam performance score and inverse distance to the school." The conclusion
also notes that "administrators can tune the weighting between merit and
proximity" -- so the weights here are a parameter, not a constant.

This module only produces scores; it does not decide who is admitted where
-- that's matching.py's job. Keeping the two separate means the scoring
formula can be tuned (or replaced) without touching the Gale-Shapley engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data_gen import School, Student
from .distance import DistanceProvider, HaversineDistanceProvider

MAX_EXAM_SCORE = 500.0  # KCPE-style scale used by data_gen.generate_students

# Distance (km) at which the proximity component has decayed to 0.5.
# 50km mirrors the "within 50 kilometres of home" proximity threshold the
# proposal names as an evaluation metric in section 2.3.
DEFAULT_DISTANCE_DECAY_KM = 50.0


@dataclass(frozen=True)
class ScoreWeights:
    """Tunable weighting between academic merit and proximity. Must sum to
    1.0 so composite scores stay on a comparable 0-1 scale regardless of the
    chosen split."""

    merit: float = 0.6
    proximity: float = 0.4

    def __post_init__(self) -> None:
        total = self.merit + self.proximity
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"weights must sum to 1.0, got {total}")
        if self.merit < 0 or self.proximity < 0:
            raise ValueError("weights must be non-negative")


def normalized_merit(student: Student) -> float:
    """Student's exam score rescaled to 0-1."""
    return max(0.0, min(1.0, student.exam_score / MAX_EXAM_SCORE))


def proximity_score(distance_km: float, decay_km: float = DEFAULT_DISTANCE_DECAY_KM) -> float:
    """Inverse-distance score on (0, 1]: 1.0 at zero distance, 0.5 at
    `decay_km`, asymptotically approaching 0 for very large distances. Never
    hard-cuts a school out -- that keeps the composite score smooth, which
    matters for Gale-Shapley producing a well-defined strict-ish preference
    ordering. Use a candidate-shortlist filter (see `eligible_schools`) if
    you want a hard proximity cutoff instead.
    """
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    if decay_km <= 0:
        raise ValueError("decay_km must be positive")
    return decay_km / (decay_km + distance_km)


def composite_score(
    student: Student,
    school: School,
    distance_km: float,
    weights: ScoreWeights = ScoreWeights(),
    decay_km: float = DEFAULT_DISTANCE_DECAY_KM,
) -> float:
    """The weighted composite score for one student-school pair, per Module 3
    (3.4.4). Combines the student's own academic merit with how close the
    school is to their home. Does NOT factor in the school's own performance
    rating -- that rating is used school-side, in how schools rank applicants
    (see matching.py), not in how a student's fit for a given school is
    scored."""
    return (
        weights.merit * normalized_merit(student)
        + weights.proximity * proximity_score(distance_km, decay_km)
    )


def eligible_schools(
    student: Student,
    schools: list[School],
    distance_provider: DistanceProvider | None = None,
    max_distance_km: float | None = None,
    max_candidates: int | None = None,
) -> list[tuple[School, float]]:
    """Return (school, distance_km) pairs a student may be matched to,
    nearest first. `max_distance_km` applies a hard proximity cutoff (schools
    farther than this are excluded outright); `max_candidates` caps the list
    to the N nearest eligible schools, which is what keeps the matching
    problem computationally tractable at national scale -- matching every
    student against every school in the country is neither realistic nor
    necessary once schools past a reasonable radius are dropped.
    """
    provider = distance_provider or HaversineDistanceProvider()
    ranked: list[tuple[School, float]] = []
    for school in schools:
        d = provider.distance_km(student.home, school.location)
        if max_distance_km is not None and d > max_distance_km:
            continue
        ranked.append((school, d))
    ranked.sort(key=lambda pair: pair[1])
    if max_candidates is not None:
        ranked = ranked[:max_candidates]
    return ranked
