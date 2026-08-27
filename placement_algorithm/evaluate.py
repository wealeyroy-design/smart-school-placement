"""
Evaluation metrics for a placement run.

Mirrors the metrics named in the proposal's section 2.3 (Evaluating the
Efficiency of the Proposed School Placement Optimization System) and
Objective (iv): the proportion of students placed within a defined
proximity threshold, average placement distance versus the existing system,
matching stability, and school slot utilization.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data_gen import School
from .matching import MatchRun, Placement, is_stable


@dataclass
class EvaluationSummary:
    n_students: int
    n_placed: int
    n_unmatched: int
    average_distance_km: float
    median_distance_km: float
    proportion_within_threshold: float
    threshold_km: float
    overall_slot_utilization: float
    per_school_utilization: dict[str, float]
    is_stable: bool | None  # None if stability wasn't checked


def average_placement_distance(placements: list[Placement]) -> float:
    if not placements:
        return 0.0
    return sum(p.distance_km for p in placements) / len(placements)


def median_placement_distance(placements: list[Placement]) -> float:
    if not placements:
        return 0.0
    distances = sorted(p.distance_km for p in placements)
    n = len(distances)
    mid = n // 2
    if n % 2 == 1:
        return distances[mid]
    return (distances[mid - 1] + distances[mid]) / 2.0


def proportion_within_threshold(placements: list[Placement], threshold_km: float = 50.0) -> float:
    """Fraction of placed students whose school is within `threshold_km` of
    home -- the 50km example threshold named in section 2.3."""
    if not placements:
        return 0.0
    within = sum(1 for p in placements if p.distance_km <= threshold_km)
    return within / len(placements)


def slot_utilization(schools: list[School], school_fill: dict[str, list[str]]) -> tuple[float, dict[str, float]]:
    """Overall and per-school fraction of capacity filled."""
    per_school: dict[str, float] = {}
    total_capacity = 0
    total_filled = 0
    for school in schools:
        filled = len(school_fill.get(school.school_id, []))
        per_school[school.school_id] = filled / school.capacity if school.capacity else 0.0
        total_capacity += school.capacity
        total_filled += filled
    overall = total_filled / total_capacity if total_capacity else 0.0
    return overall, per_school


def summarize(
    run: MatchRun,
    students_total: int,
    schools: list[School],
    threshold_km: float = 50.0,
    stability_check: tuple[bool, list] | None = None,
) -> EvaluationSummary:
    """Build the standard evaluation summary for one placement run.

    `stability_check` is optional (pass the tuple returned by
    `matching.is_stable`) since it requires rebuilding the preference/rank
    structures and is only needed when you specifically want to confirm
    stability, not on every call.
    """
    overall_util, per_school_util = slot_utilization(schools, run.result.school_fill)
    return EvaluationSummary(
        n_students=students_total,
        n_placed=len(run.placements),
        n_unmatched=len(run.unmatched_students),
        average_distance_km=round(average_placement_distance(run.placements), 2),
        median_distance_km=round(median_placement_distance(run.placements), 2),
        proportion_within_threshold=round(proportion_within_threshold(run.placements, threshold_km), 4),
        threshold_km=threshold_km,
        overall_slot_utilization=round(overall_util, 4),
        per_school_utilization=per_school_util,
        is_stable=stability_check[0] if stability_check is not None else None,
    )


def print_summary(label: str, summary: EvaluationSummary) -> None:
    print(f"--- {label} ---")
    print(f"  students placed:        {summary.n_placed}/{summary.n_students} "
          f"({summary.n_unmatched} unmatched)")
    print(f"  average distance:       {summary.average_distance_km} km")
    print(f"  median distance:        {summary.median_distance_km} km")
    print(f"  within {summary.threshold_km:.0f}km of home:    "
          f"{summary.proportion_within_threshold * 100:.1f}%")
    print(f"  overall slot utilization: {summary.overall_slot_utilization * 100:.1f}%")
    if summary.is_stable is not None:
        print(f"  stable matching:        {summary.is_stable}")
