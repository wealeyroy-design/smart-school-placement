import pytest

from placement_algorithm.data_gen import School, SchoolCategory, Student, generate_schools, generate_students
from placement_algorithm.distance import Coordinates
from placement_algorithm.matching import (
    MatchResult,
    baseline_merit_only_allocation,
    is_stable,
    match_students_to_schools,
    run_gale_shapley,
)


# ---------------------------------------------------------------------------
# Pure algorithm: run_gale_shapley / is_stable, with small hand-built cases
# ---------------------------------------------------------------------------

def test_two_students_one_seat_each_no_conflict():
    prefs = {"A": ["X", "Y"], "B": ["Y", "X"]}
    capacity = {"X": 1, "Y": 1}
    rank = {"X": {"A": 2, "B": 1}, "Y": {"A": 1, "B": 2}}
    result = run_gale_shapley(prefs, capacity, rank)
    assert result.assignments == {"A": "X", "B": "Y"}
    assert result.unmatched_students == []


def test_school_rejects_weaker_applicant_when_full():
    # Both A and B prefer X first; X has one seat and ranks A over B.
    # B should be bumped to their second choice, Y.
    prefs = {"A": ["X", "Y"], "B": ["X", "Y"]}
    capacity = {"X": 1, "Y": 1}
    rank = {"X": {"A": 2, "B": 1}, "Y": {"A": 2, "B": 1}}
    result = run_gale_shapley(prefs, capacity, rank)
    assert result.assignments == {"A": "X", "B": "Y"}


def test_a_stronger_late_proposal_displaces_a_weaker_held_offer():
    # C proposes to X after B is already tentatively held there; C outranks B,
    # so C should displace B, and B should end up rejected from X.
    prefs = {"B": ["X"], "C": ["Y", "X"]}
    capacity = {"X": 1, "Y": 1}
    rank = {"X": {"B": 1, "C": 5}, "Y": {"C": 1}}
    # C prefers Y first but Y has capacity for C, so C never even reaches X in
    # this setup -- construct instead so C's first choice is unavailable.
    prefs = {"B": ["X"], "C": ["X"]}
    rank = {"X": {"B": 1, "C": 5}}
    capacity = {"X": 1}
    result = run_gale_shapley(prefs, capacity, rank)
    assert result.assignments == {"C": "X"}
    assert "B" in result.unmatched_students


def test_unmatched_when_demand_exceeds_capacity():
    prefs = {"A": ["X"], "B": ["X"], "C": ["X"]}
    capacity = {"X": 1}
    rank = {"X": {"A": 3, "B": 2, "C": 1}}
    result = run_gale_shapley(prefs, capacity, rank)
    assert result.assignments == {"A": "X"}
    assert set(result.unmatched_students) == {"B", "C"}


def test_capacity_never_exceeded():
    prefs = {f"S{i}": ["X"] for i in range(10)}
    capacity = {"X": 3}
    rank = {"X": {f"S{i}": i for i in range(10)}}
    result = run_gale_shapley(prefs, capacity, rank)
    assert len(result.school_fill["X"]) == 3
    # The three highest-ranked (S9, S8, S7) should be the ones admitted.
    assert set(result.school_fill["X"]) == {"S9", "S8", "S7"}


def test_hand_built_case_is_stable():
    prefs = {"A": ["X", "Y"], "B": ["X", "Y"]}
    capacity = {"X": 1, "Y": 1}
    rank = {"X": {"A": 2, "B": 1}, "Y": {"A": 2, "B": 1}}
    result = run_gale_shapley(prefs, capacity, rank)
    stable, blocking = is_stable(prefs, capacity, rank, result)
    assert stable
    assert blocking == []


def test_is_stable_detects_a_deliberately_broken_matching():
    prefs = {"A": ["X", "Y"], "B": ["X", "Y"]}
    capacity = {"X": 1, "Y": 1}
    rank = {"X": {"A": 2, "B": 1}, "Y": {"A": 2, "B": 1}}
    # Deliberately wrong matching: B holds X (which prefers A), A holds Y --
    # (A, X) is a blocking pair since A prefers X to Y and X prefers A to B.
    bad_result = MatchResult(
        assignments={"A": "Y", "B": "X"},
        unmatched_students=[],
        school_fill={"X": ["B"], "Y": ["A"]},
    )
    stable, blocking = is_stable(prefs, capacity, rank, bad_result)
    assert not stable
    assert ("A", "X") in blocking


# ---------------------------------------------------------------------------
# match_students_to_schools / baseline_merit_only_allocation, at scale with
# synthetic data
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_data():
    students = generate_students(200, seed=101)
    schools = generate_schools(seed=101)
    return students, schools


def test_match_students_to_schools_respects_capacity(synthetic_data):
    students, schools = synthetic_data
    run = match_students_to_schools(students, schools, max_candidates=15, max_distance_km=300)
    capacity_by_id = {s.school_id: s.capacity for s in schools}
    for school_id, roster in run.result.school_fill.items():
        assert len(roster) <= capacity_by_id[school_id]


def test_match_students_to_schools_no_student_placed_twice(synthetic_data):
    students, schools = synthetic_data
    run = match_students_to_schools(students, schools, max_candidates=15, max_distance_km=300)
    placed_ids = [p.student_id for p in run.placements]
    assert len(placed_ids) == len(set(placed_ids))


def test_match_students_to_schools_produces_stable_matching(synthetic_data):
    from placement_algorithm.scoring import ScoreWeights, composite_score, eligible_schools

    students, schools = synthetic_data
    run = match_students_to_schools(students, schools, max_candidates=15, max_distance_km=300)

    weights = ScoreWeights()
    student_preferences = {}
    applicant_rank = {s.school_id: {} for s in schools}
    for student in students:
        cands = eligible_schools(student, schools, max_distance_km=300, max_candidates=15)
        scored = [(sch, d, composite_score(student, sch, d, weights=weights)) for sch, d in cands]
        scored.sort(key=lambda t: t[2], reverse=True)
        student_preferences[student.student_id] = [sch.school_id for sch, _, _ in scored]
        for sch, _, sc in scored:
            applicant_rank[sch.school_id][student.student_id] = sc

    school_capacity = {s.school_id: s.capacity for s in schools}
    stable, blocking = is_stable(student_preferences, school_capacity, applicant_rank, run.result)
    assert stable, f"found {len(blocking)} blocking pairs"


def test_proximity_weighted_beats_baseline_on_average_distance(synthetic_data):
    students, schools = synthetic_data
    proximity_run = match_students_to_schools(students, schools, max_candidates=15, max_distance_km=300)
    baseline_run = baseline_merit_only_allocation(students, schools)

    prox_avg = sum(p.distance_km for p in proximity_run.placements) / len(proximity_run.placements)
    base_avg = sum(p.distance_km for p in baseline_run.placements) / len(baseline_run.placements)
    assert prox_avg < base_avg


def test_baseline_ignores_distance_prioritizes_merit():
    # A far-away top scorer should still beat a nearby low scorer for the
    # single national-school seat, since the baseline is merit-only.
    far_top_scorer = Student("STU-FAR", exam_score=490, home=Coordinates(4.0, 40.0), county="Turkana")
    near_low_scorer = Student("STU-NEAR", exam_score=150, home=Coordinates(0.0, 36.0), county="Nairobi")
    national_school = School(
        "SCH-NAT", "Elite National School", SchoolCategory.NATIONAL,
        Coordinates(0.0, 36.0), "Nairobi", capacity=1, performance_rating=90.0,
    )
    run = baseline_merit_only_allocation([far_top_scorer, near_low_scorer], [national_school])
    assert run.result.assignments["STU-FAR"] == "SCH-NAT"
    assert "STU-NEAR" in run.unmatched_students
