import pytest

from placement_algorithm.data_gen import School, SchoolCategory
from placement_algorithm.matching import MatchResult, MatchRun, Placement
from placement_algorithm.evaluate import (
    average_placement_distance,
    median_placement_distance,
    proportion_within_threshold,
    slot_utilization,
    summarize,
)


def make_school(sid, capacity, category=SchoolCategory.COUNTY):
    from placement_algorithm.distance import Coordinates
    return School(sid, f"School {sid}", category, Coordinates(0, 36), "Test", capacity, 60.0)


def test_average_placement_distance_empty():
    assert average_placement_distance([]) == 0.0


def test_average_placement_distance_basic():
    placements = [
        Placement("S1", "SCH1", distance_km=10.0, composite=0.5),
        Placement("S2", "SCH1", distance_km=20.0, composite=0.5),
    ]
    assert average_placement_distance(placements) == pytest.approx(15.0)


def test_median_placement_distance_odd_and_even():
    odd = [Placement(f"S{i}", "SCH1", d, 0.5) for i, d in enumerate([10, 5, 20])]
    assert median_placement_distance(odd) == pytest.approx(10.0)
    even = [Placement(f"S{i}", "SCH1", d, 0.5) for i, d in enumerate([10, 20, 30, 40])]
    assert median_placement_distance(even) == pytest.approx(25.0)


def test_proportion_within_threshold():
    placements = [
        Placement("S1", "SCH1", distance_km=10.0, composite=0.5),
        Placement("S2", "SCH1", distance_km=60.0, composite=0.5),
        Placement("S3", "SCH1", distance_km=49.9, composite=0.5),
    ]
    assert proportion_within_threshold(placements, threshold_km=50.0) == pytest.approx(2 / 3)


def test_proportion_within_threshold_empty():
    assert proportion_within_threshold([], threshold_km=50.0) == 0.0


def test_slot_utilization_full_and_partial():
    schools = [make_school("A", capacity=10), make_school("B", capacity=4)]
    school_fill = {"A": [f"s{i}" for i in range(10)], "B": ["s10", "s11"]}
    overall, per_school = slot_utilization(schools, school_fill)
    assert per_school["A"] == pytest.approx(1.0)
    assert per_school["B"] == pytest.approx(0.5)
    assert overall == pytest.approx(12 / 14)


def test_slot_utilization_handles_zero_capacity_school():
    schools = [make_school("A", capacity=0)]
    overall, per_school = slot_utilization(schools, {"A": []})
    assert per_school["A"] == 0.0


def test_summarize_end_to_end():
    schools = [make_school("A", capacity=2), make_school("B", capacity=2)]
    placements = [
        Placement("S1", "A", distance_km=5.0, composite=0.9),
        Placement("S2", "A", distance_km=15.0, composite=0.8),
        Placement("S3", "B", distance_km=80.0, composite=0.4),
    ]
    result = MatchResult(
        assignments={"S1": "A", "S2": "A", "S3": "B"},
        unmatched_students=["S4"],
        school_fill={"A": ["S1", "S2"], "B": ["S3"]},
    )
    run = MatchRun(placements=placements, unmatched_students=["S4"], result=result)
    summary = summarize(run, students_total=4, schools=schools, threshold_km=50.0)

    assert summary.n_students == 4
    assert summary.n_placed == 3
    assert summary.n_unmatched == 1
    assert summary.average_distance_km == pytest.approx((5 + 15 + 80) / 3, abs=0.01)
    assert summary.proportion_within_threshold == pytest.approx(2 / 3, abs=0.001)
    assert summary.overall_slot_utilization == pytest.approx(3 / 4)
