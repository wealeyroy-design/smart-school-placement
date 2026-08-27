"""
Capacitated Gale-Shapley (deferred acceptance) matching engine.

This is Module 3 of the proposal (3.4.4): "The Gale-Shapley stable matching
algorithm is then applied to produce a stable, fair allocation where no
student would prefer a school that also prefers them over their current
placement. Conflict detection prevents double allocation of school slots."

Two layers are provided:

  - `run_gale_shapley`: the pure, generic many-to-one deferred acceptance
    algorithm (the "college admissions" / "hospital-residents" variant of
    Gale & Shapley, 1962). It knows nothing about students, schools, exam
    scores or distance -- just preference lists, capacities and rankings --
    which makes it straightforward to unit-test and to reuse if the ranking
    logic changes later.

  - `match_students_to_schools`: the convenience wrapper that builds those
    preference lists and rankings from `scoring.composite_score` and the
    synthetic Student/School data, and returns a result annotated with
    distances -- what the demo script and evaluation module actually use.

  - `baseline_merit_only_allocation`: a geography-blind, category-tiered,
    strict-merit allocation standing in for Kenya's current centralized
    system (Background, 1.2: top scorers go to national/extra-county
    schools, average scorers to county/sub-county schools, with "no regard
    for how far any of these schools are from the student's home"). This is
    what the demo script and section 2.3's benchmarking approach compare the
    proximity-weighted result against.

Student-proposing deferred acceptance is used (students propose to schools,
not the other way around), which is the classical construction guaranteeing
the resulting matching is stable and student-optimal among all stable
matchings (Gale & Shapley, 1962; Roth, 2008).
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

from .data_gen import School, SchoolCategory, Student
from .distance import DistanceProvider, HaversineDistanceProvider
from .scoring import ScoreWeights, composite_score, eligible_schools


@dataclass
class MatchResult:
    """Generic result of `run_gale_shapley`: which student got which school,
    who was left unmatched, and the final roster per school."""

    assignments: dict[str, str]  # student_id -> school_id
    unmatched_students: list[str]
    school_fill: dict[str, list[str]]  # school_id -> [student_id, ...]


def run_gale_shapley(
    student_preferences: dict[str, list[str]],
    school_capacity: dict[str, int],
    applicant_rank: dict[str, dict[str, float]],
) -> MatchResult:
    """Student-proposing many-to-one deferred acceptance.

    Args:
        student_preferences: student_id -> ordered list of school_ids the
            student is willing to attend, most preferred first.
        school_capacity: school_id -> number of open slots.
        applicant_rank: school_id -> {student_id: rank_score}. Higher
            rank_score means the school prefers that student more. A school
            only needs entries for students who might propose to it (i.e.
            students who included it in their preference list).

    Returns:
        MatchResult with the stable, capacity-respecting assignment.
    """
    next_choice_idx: dict[str, int] = {sid: 0 for sid in student_preferences}
    free_students: deque[str] = deque(student_preferences.keys())
    # min-heap per school of (rank_score, student_id) -- heap[0] is the
    # worst-ranked student currently held, so it's cheap to test whether a
    # new proposal beats the weakest existing offer.
    school_heaps: dict[str, list[tuple[float, str]]] = {sid: [] for sid in school_capacity}
    held_school_of: dict[str, str] = {}

    while free_students:
        sid = free_students.popleft()
        prefs = student_preferences.get(sid, [])
        idx = next_choice_idx[sid]
        if idx >= len(prefs):
            # Exhausted every school on their list -- stays unmatched.
            continue
        school_id = prefs[idx]
        next_choice_idx[sid] = idx + 1

        rank_score = applicant_rank.get(school_id, {}).get(sid)
        if rank_score is None:
            # School doesn't rank this student (shouldn't happen if
            # preference lists were built from the same candidate set as the
            # rankings, but fail safe rather than crash) -- try next choice.
            free_students.append(sid)
            continue

        heap = school_heaps.setdefault(school_id, [])
        cap = school_capacity.get(school_id, 0)
        entry = (rank_score, sid)

        if cap <= 0:
            free_students.append(sid)
            continue

        if len(heap) < cap:
            heapq.heappush(heap, entry)
            held_school_of[sid] = school_id
        else:
            worst = heap[0]
            if entry > worst:
                heapq.heapreplace(heap, entry)
                held_school_of[sid] = school_id
                _, evicted_sid = worst
                del held_school_of[evicted_sid]
                free_students.append(evicted_sid)
            else:
                free_students.append(sid)

    assignments = dict(held_school_of)
    unmatched = [sid for sid in student_preferences if sid not in assignments]
    school_fill = {
        school_id: [sid for (_, sid) in heap] for school_id, heap in school_heaps.items()
    }
    return MatchResult(
        assignments=assignments, unmatched_students=unmatched, school_fill=school_fill
    )


def is_stable(
    student_preferences: dict[str, list[str]],
    school_capacity: dict[str, int],
    applicant_rank: dict[str, dict[str, float]],
    result: MatchResult,
) -> tuple[bool, list[tuple[str, str]]]:
    """Verify the no-blocking-pair stability property directly, independent
    of trusting the algorithm above: a matching is stable iff there is no
    (student, school) pair where the student prefers that school to their
    current assignment AND the school would rather have that student than
    its current weakest admit (or still has an empty slot).

    Returns (is_stable, blocking_pairs) so tests/debugging can see exactly
    which pair violates stability if any do.
    """
    blocking_pairs: list[tuple[str, str]] = []

    for sid, prefs in student_preferences.items():
        current = result.assignments.get(sid)
        current_idx = prefs.index(current) if current in prefs else len(prefs)
        # Every school the student prefers strictly more than their current
        # assignment (everything before current_idx in their list).
        for school_id in prefs[:current_idx]:
            roster = result.school_fill.get(school_id, [])
            cap = school_capacity.get(school_id, 0)
            rank_score = applicant_rank.get(school_id, {}).get(sid)
            if rank_score is None:
                continue  # school wouldn't take this student regardless
            if len(roster) < cap:
                blocking_pairs.append((sid, school_id))
                continue
            worst_admitted_score = min(
                applicant_rank[school_id][t] for t in roster if t in applicant_rank[school_id]
            )
            if rank_score > worst_admitted_score:
                blocking_pairs.append((sid, school_id))

    return (len(blocking_pairs) == 0, blocking_pairs)


@dataclass
class Placement:
    """One resolved student placement, with the distance/score context that
    produced it -- what evaluate.py and the demo script consume."""

    student_id: str
    school_id: str
    distance_km: float
    composite: float


@dataclass
class MatchRun:
    """Full output of `match_students_to_schools`: the raw MatchResult plus
    per-placement distance/score detail and the unmatched list."""

    placements: list[Placement]
    unmatched_students: list[str]
    result: MatchResult


def match_students_to_schools(
    students: list[Student],
    schools: list[School],
    weights: ScoreWeights = ScoreWeights(),
    decay_km: float = 50.0,
    max_distance_km: float | None = 300.0,
    max_candidates: int = 15,
    distance_provider: DistanceProvider | None = None,
    school_ranking: str = "composite",
) -> MatchRun:
    """Build preferences/rankings from composite_score and run deferred
    acceptance.

    Args:
        max_distance_km: hard cutoff -- schools farther than this from a
            student's home are never considered for them. Defaults to 300km,
            comfortably wider than the 50km proximity threshold used for
            evaluation (section 2.3), so it excludes only truly implausible
            matches rather than constraining the algorithm's choices.
        max_candidates: caps each student's candidate list to the N nearest
            eligible schools, keeping the problem tractable at scale (see
            scoring.eligible_schools).
        school_ranking: "composite" (default) ranks a school's applicants by
            the same merit+proximity composite score used for the student's
            own preference; "merit_only" ranks purely by exam score, for
            comparing how much the proximity weighting on the school side
            actually matters.
    """
    provider = distance_provider or HaversineDistanceProvider()
    schools_by_id = {s.school_id: s for s in schools}

    student_preferences: dict[str, list[str]] = {}
    applicant_rank: dict[str, dict[str, float]] = {s.school_id: {} for s in schools}
    distances: dict[tuple[str, str], float] = {}
    composites: dict[tuple[str, str], float] = {}

    for student in students:
        candidates = eligible_schools(
            student,
            schools,
            distance_provider=provider,
            max_distance_km=max_distance_km,
            max_candidates=max_candidates,
        )
        scored = []
        for school, dist in candidates:
            score = composite_score(student, school, dist, weights=weights, decay_km=decay_km)
            distances[(student.student_id, school.school_id)] = dist
            composites[(student.student_id, school.school_id)] = score
            scored.append((school, dist, score))

        # Student's own preference order: best composite score first (their
        # utility from a placement is exactly the same merit+proximity blend
        # the school uses to judge them -- see scoring.py's docstring).
        scored.sort(key=lambda t: t[2], reverse=True)
        student_preferences[student.student_id] = [school.school_id for school, _, _ in scored]

        for school, dist, score in scored:
            if school_ranking == "merit_only":
                rank_value = student.exam_score
            else:
                rank_value = score
            applicant_rank[school.school_id][student.student_id] = rank_value

    school_capacity = {s.school_id: s.capacity for s in schools}
    result = run_gale_shapley(student_preferences, school_capacity, applicant_rank)

    placements = [
        Placement(
            student_id=sid,
            school_id=school_id,
            distance_km=distances[(sid, school_id)],
            composite=composites[(sid, school_id)],
        )
        for sid, school_id in result.assignments.items()
    ]

    return MatchRun(
        placements=placements,
        unmatched_students=result.unmatched_students,
        result=result,
    )


CATEGORY_PRIORITY = [
    SchoolCategory.NATIONAL,
    SchoolCategory.EXTRA_COUNTY,
    SchoolCategory.COUNTY,
    SchoolCategory.SUB_COUNTY,
]


def baseline_merit_only_allocation(
    students: list[Student],
    schools: list[School],
    distance_provider: DistanceProvider | None = None,
) -> MatchRun:
    """Geography-blind, category-tiered, strict-merit allocation -- a
    simulation of Kenya's current centralized placement system as described
    in the proposal's Background (1.2): top scorers nationally fill national
    schools first (ranked by performance rating, ignoring where in the
    country either the student or the school is), then extra-county, then
    county, then sub-county, with no proximity consideration anywhere in the
    process.

    This exists purely as the comparison baseline section 2.3 calls for: "a
    reduction in average placement distance, without sacrificing academic
    placement quality, would be strong evidence of impact." Distances are
    computed after the fact, for evaluation only -- they play no role in
    this allocation itself, by design.
    """
    provider = distance_provider or HaversineDistanceProvider()
    students_by_id = {s.student_id: s for s in students}

    remaining_capacity = {s.school_id: s.capacity for s in schools}
    schools_by_category: dict[SchoolCategory, list[School]] = {cat: [] for cat in CATEGORY_PRIORITY}
    for school in schools:
        schools_by_category[school.category].append(school)
    for cat in CATEGORY_PRIORITY:
        schools_by_category[cat].sort(key=lambda s: s.performance_rating, reverse=True)

    ranked_students = sorted(students, key=lambda st: st.exam_score, reverse=True)

    assignments: dict[str, str] = {}
    school_fill: dict[str, list[str]] = {s.school_id: [] for s in schools}
    unmatched: list[str] = []

    for student in ranked_students:
        placed_school_id = None
        for cat in CATEGORY_PRIORITY:
            for school in schools_by_category[cat]:
                if remaining_capacity[school.school_id] > 0:
                    placed_school_id = school.school_id
                    break
            if placed_school_id:
                break
        if placed_school_id is None:
            unmatched.append(student.student_id)
            continue
        assignments[student.student_id] = placed_school_id
        school_fill[placed_school_id].append(student.student_id)
        remaining_capacity[placed_school_id] -= 1

    schools_by_id = {s.school_id: s for s in schools}
    placements = []
    for sid, school_id in assignments.items():
        student = students_by_id[sid]
        school = schools_by_id[school_id]
        dist = provider.distance_km(student.home, school.location)
        placements.append(
            Placement(
                student_id=sid,
                school_id=school_id,
                distance_km=dist,
                composite=composite_score(student, school, dist),
            )
        )

    result = MatchResult(assignments=assignments, unmatched_students=unmatched, school_fill=school_fill)
    return MatchRun(placements=placements, unmatched_students=unmatched, result=result)
