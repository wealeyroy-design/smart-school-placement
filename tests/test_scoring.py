import pytest

from placement_algorithm.data_gen import School, SchoolCategory, Student
from placement_algorithm.distance import Coordinates
from placement_algorithm.scoring import (
    ScoreWeights,
    composite_score,
    eligible_schools,
    normalized_merit,
    proximity_score,
)


def make_student(score=250.0):
    return Student(student_id="STU-1", exam_score=score, home=Coordinates(0.0, 36.0), county="Test")


def make_school(sid="SCH-1", lat=0.0, lon=36.0, capacity=100, rating=70.0, category=SchoolCategory.COUNTY):
    return School(
        school_id=sid, name="Test School", category=category,
        location=Coordinates(lat, lon), county="Test", capacity=capacity, performance_rating=rating,
    )


def test_normalized_merit_range():
    assert normalized_merit(make_student(0)) == 0.0
    assert normalized_merit(make_student(500)) == 1.0
    assert normalized_merit(make_student(250)) == pytest.approx(0.5)


def test_normalized_merit_clips_out_of_range_scores():
    assert normalized_merit(make_student(-50)) == 0.0
    assert normalized_merit(make_student(9000)) == 1.0


def test_proximity_score_bounds():
    assert proximity_score(0) == 1.0
    assert proximity_score(50, decay_km=50) == pytest.approx(0.5)
    assert 0 < proximity_score(1_000_000) < 0.01


def test_proximity_score_rejects_negative_distance():
    with pytest.raises(ValueError):
        proximity_score(-1)


def test_proximity_score_rejects_nonpositive_decay():
    with pytest.raises(ValueError):
        proximity_score(10, decay_km=0)


def test_score_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        ScoreWeights(merit=0.5, proximity=0.6)


def test_score_weights_reject_negative():
    with pytest.raises(ValueError):
        ScoreWeights(merit=-0.1, proximity=1.1)


def test_composite_score_is_monotonic_in_merit():
    school = make_school()
    weak = make_student(100)
    strong = make_student(400)
    assert composite_score(strong, school, distance_km=10) > composite_score(weak, school, distance_km=10)


def test_composite_score_is_monotonic_in_distance():
    student = make_student(300)
    school = make_school()
    near = composite_score(student, school, distance_km=1)
    far = composite_score(student, school, distance_km=200)
    assert near > far


def test_composite_score_weights_extremes():
    student = make_student(500)  # max merit
    school = make_school()
    merit_only = ScoreWeights(merit=1.0, proximity=0.0)
    # With zero proximity weight, distance shouldn't move the score at all.
    s_near = composite_score(student, school, distance_km=1, weights=merit_only)
    s_far = composite_score(student, school, distance_km=500, weights=merit_only)
    assert s_near == pytest.approx(s_far)
    assert s_near == pytest.approx(1.0)


def test_eligible_schools_sorted_nearest_first():
    student = make_student()
    near = make_school("NEAR", lat=0.01, lon=36.0)
    far = make_school("FAR", lat=2.0, lon=36.0)
    result = eligible_schools(student, [far, near])
    assert [s.school_id for s, _ in result] == ["NEAR", "FAR"]


def test_eligible_schools_respects_max_distance():
    student = make_student()
    near = make_school("NEAR", lat=0.01, lon=36.0)
    far = make_school("FAR", lat=5.0, lon=36.0)
    result = eligible_schools(student, [far, near], max_distance_km=50)
    assert [s.school_id for s, _ in result] == ["NEAR"]


def test_eligible_schools_respects_max_candidates():
    student = make_student()
    schools = [make_school(f"SCH-{i}", lat=0.01 * i, lon=36.0) for i in range(10)]
    result = eligible_schools(student, schools, max_candidates=3)
    assert len(result) == 3
    assert [s.school_id for s, _ in result] == ["SCH-0", "SCH-1", "SCH-2"]
