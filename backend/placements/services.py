"""
Bridges the Django ORM to the standalone `placement_algorithm` package
(Module 3). This is the only place in the web application that talks to
that package directly -- everything else (views, serializers) works with
Django models and never imports placement_algorithm itself.

Design note: the algorithm package's Student/School are plain dataclasses
with their own `distance.Coordinates` type, deliberately independent of any
web framework (see that package's own README). This module's job is purely
translation: Django rows in, dataclasses out, run the algorithm, dataclass
results in, Django rows out.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from placement_algorithm.data_gen import School as AlgoSchool
from placement_algorithm.data_gen import SchoolCategory as AlgoSchoolCategory
from placement_algorithm.data_gen import Student as AlgoStudent
from placement_algorithm.distance import Coordinates
from placement_algorithm.evaluate import summarize
from placement_algorithm.matching import is_stable, match_students_to_schools
from placement_algorithm.scoring import ScoreWeights, composite_score, eligible_schools

from .models import Placement, PlacementRun, School, Student


def _to_algo_student(student: Student) -> AlgoStudent:
    return AlgoStudent(
        student_id=str(student.pk),
        exam_score=student.exam_score,
        home=Coordinates(student.home_latitude, student.home_longitude),
        county=student.county,
    )


def _to_algo_school(school: School) -> AlgoSchool:
    return AlgoSchool(
        school_id=str(school.pk),
        name=school.name,
        category=AlgoSchoolCategory(school.category),
        location=Coordinates(school.latitude, school.longitude),
        county=school.county,
        capacity=school.capacity,
        performance_rating=school.performance_rating,
    )


def run_placement(
    triggered_by=None,
    merit_weight: float = 0.6,
    proximity_weight: float = 0.4,
    decay_km: float = 50.0,
    max_distance_km: float | None = 300.0,
    max_candidates: int = 15,
    threshold_km: float = 50.0,
    verify_stability: bool = True,
) -> PlacementRun:
    """Run the proximity-weighted Gale-Shapley placement algorithm against
    every student who has exam results on file, and every registered
    school. Replaces any previous placements (a placement run is a full
    reallocation, not an incremental update -- consistent with how the
    proposal describes the Ministry Administrator "run placement algorithm"
    use case as a discrete, auditable event, recorded here as a
    PlacementRun row)."""

    run = PlacementRun.objects.create(
        triggered_by=triggered_by,
        status=PlacementRun.Status.RUNNING,
        merit_weight=merit_weight,
        proximity_weight=proximity_weight,
    )

    try:
        db_students = list(Student.objects.filter(exam_score__isnull=False))
        db_schools = list(School.objects.all())
        run.students_considered = len(db_students)

        if not db_students or not db_schools:
            run.status = PlacementRun.Status.FAILED
            run.error_message = "No students with results, or no schools registered."
            run.completed_at = timezone.now()
            run.save()
            return run

        algo_students = [_to_algo_student(s) for s in db_students]
        algo_schools = [_to_algo_school(s) for s in db_schools]
        students_by_algo_id = {str(s.pk): s for s in db_students}
        schools_by_algo_id = {str(s.pk): s for s in db_schools}

        weights = ScoreWeights(merit=merit_weight, proximity=proximity_weight)
        match_run = match_students_to_schools(
            algo_students,
            algo_schools,
            weights=weights,
            decay_km=decay_km,
            max_distance_km=max_distance_km,
            max_candidates=max_candidates,
        )

        stability_result = None
        if verify_stability:
            student_preferences = {}
            applicant_rank = {s.school_id: {} for s in algo_schools}
            for algo_student in algo_students:
                candidates = eligible_schools(
                    algo_student, algo_schools, max_distance_km=max_distance_km, max_candidates=max_candidates
                )
                scored = [
                    (school, dist, composite_score(algo_student, school, dist, weights=weights, decay_km=decay_km))
                    for school, dist in candidates
                ]
                scored.sort(key=lambda t: t[2], reverse=True)
                student_preferences[algo_student.student_id] = [school.school_id for school, _, _ in scored]
                for school, _, score in scored:
                    applicant_rank[school.school_id][algo_student.student_id] = score
            school_capacity = {s.school_id: s.capacity for s in algo_schools}
            stability_result = is_stable(student_preferences, school_capacity, applicant_rank, match_run.result)

        summary = summarize(
            match_run,
            students_total=len(algo_students),
            schools=algo_schools,
            threshold_km=threshold_km,
            stability_check=stability_result,
        )

        with transaction.atomic():
            # A run replaces the previous allocation entirely.
            Placement.objects.filter(student__in=db_students).delete()
            new_placements = [
                Placement(
                    student=students_by_algo_id[p.student_id],
                    school=schools_by_algo_id[p.school_id],
                    run=run,
                    distance_km=p.distance_km,
                    composite_score=p.composite,
                )
                for p in match_run.placements
            ]
            Placement.objects.bulk_create(new_placements)

            run.status = PlacementRun.Status.COMPLETED
            run.students_placed = summary.n_placed
            run.average_distance_km = summary.average_distance_km
            run.median_distance_km = summary.median_distance_km
            run.proportion_within_threshold = summary.proportion_within_threshold
            run.overall_slot_utilization = summary.overall_slot_utilization
            run.is_stable = summary.is_stable
            run.completed_at = timezone.now()
            run.save()

        return run

    except Exception as exc:  # noqa: BLE001 -- surfaced to the API caller via PlacementRun.error_message
        run.status = PlacementRun.Status.FAILED
        run.error_message = str(exc)
        run.completed_at = timezone.now()
        run.save()
        raise
