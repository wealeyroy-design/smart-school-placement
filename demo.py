#!/usr/bin/env python3
"""
Demo script for the Smart School Placement Optimization System's core
placement algorithm (proposal Module 3).

Generates a synthetic cohort of students and a synthetic school database,
then compares two allocation strategies:

  1. baseline_merit_only_allocation -- a geography-blind, category-tiered,
     strict-merit allocation standing in for Kenya's current centralized
     system (see matching.py's docstring).
  2. match_students_to_schools -- the proposal's proximity-weighted
     Gale-Shapley matching engine.

This is the comparison section 2.3 of the proposal calls for: "a reduction
in average placement distance, without sacrificing academic placement
quality, would be strong evidence of impact."

Usage:
    python3 demo.py                          # defaults: 1000 students, seed 42
    python3 demo.py --students 5000 --seed 7
    python3 demo.py --merit-weight 0.8 --proximity-weight 0.2
    python3 demo.py --max-distance-km 100 --max-candidates 10
"""

from __future__ import annotations

import argparse

from placement_algorithm.data_gen import generate_schools, generate_students
from placement_algorithm.evaluate import print_summary, summarize
from placement_algorithm.matching import baseline_merit_only_allocation, is_stable, match_students_to_schools
from placement_algorithm.scoring import ScoreWeights, composite_score, eligible_schools


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--students", type=int, default=1000, help="number of synthetic students (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="random seed, for reproducible runs (default: 42)")
    parser.add_argument("--merit-weight", type=float, default=0.6, help="weight on academic merit, 0-1 (default: 0.6)")
    parser.add_argument("--proximity-weight", type=float, default=0.4, help="weight on proximity, 0-1 (default: 0.4)")
    parser.add_argument("--decay-km", type=float, default=50.0, help="distance at which proximity score hits 0.5 (default: 50)")
    parser.add_argument("--max-distance-km", type=float, default=300.0, help="hard cutoff on candidate schools (default: 300)")
    parser.add_argument("--max-candidates", type=int, default=15, help="candidate schools considered per student (default: 15)")
    parser.add_argument("--threshold-km", type=float, default=50.0, help="proximity threshold for evaluation (default: 50)")
    parser.add_argument("--skip-stability-check", action="store_true", help="skip the (slower) stability verification pass")
    return parser.parse_args()


def verify_stability(students, schools, run, weights, decay_km, max_distance_km, max_candidates):
    """Independently rebuild the preference/rank structures used by the
    matching run and confirm no blocking pairs exist -- see matching.is_stable
    for what this actually checks."""
    student_preferences = {}
    applicant_rank = {s.school_id: {} for s in schools}
    for student in students:
        candidates = eligible_schools(
            student, schools, max_distance_km=max_distance_km, max_candidates=max_candidates
        )
        scored = [
            (school, dist, composite_score(student, school, dist, weights=weights, decay_km=decay_km))
            for school, dist in candidates
        ]
        scored.sort(key=lambda t: t[2], reverse=True)
        student_preferences[student.student_id] = [school.school_id for school, _, _ in scored]
        for school, _, score in scored:
            applicant_rank[school.school_id][student.student_id] = score

    school_capacity = {s.school_id: s.capacity for s in schools}
    return is_stable(student_preferences, school_capacity, applicant_rank, run.result)


def main() -> None:
    args = parse_args()
    weights = ScoreWeights(merit=args.merit_weight, proximity=args.proximity_weight)

    print(f"Generating {args.students} synthetic students and a synthetic school database "
          f"(seed={args.seed})...")
    students = generate_students(args.students, seed=args.seed)
    schools = generate_schools(seed=args.seed)
    total_capacity = sum(s.capacity for s in schools)
    print(f"  {len(students)} students, {len(schools)} schools, {total_capacity} total school slots\n")

    print("Running baseline (merit-only, geography-blind) allocation -- simulates the "
          "current centralized system...")
    baseline_run = baseline_merit_only_allocation(students, schools)

    print("Running proximity-weighted Gale-Shapley matching "
          f"(merit={weights.merit}, proximity={weights.proximity})...")
    proximity_run = match_students_to_schools(
        students,
        schools,
        weights=weights,
        decay_km=args.decay_km,
        max_distance_km=args.max_distance_km,
        max_candidates=args.max_candidates,
    )

    stability_check = None
    if not args.skip_stability_check:
        print("Verifying the proximity-weighted matching is stable "
              "(no student-school pair would rather have each other)...")
        stability_check = verify_stability(
            students, schools, proximity_run, weights, args.decay_km, args.max_distance_km, args.max_candidates
        )

    baseline_summary = summarize(baseline_run, len(students), schools, threshold_km=args.threshold_km)
    proximity_summary = summarize(
        proximity_run, len(students), schools, threshold_km=args.threshold_km, stability_check=stability_check
    )

    print()
    print_summary("Baseline: merit-only, geography-blind (current system)", baseline_summary)
    print()
    print_summary("Proximity-weighted Gale-Shapley (proposed system)", proximity_summary)

    print()
    improvement = (
        (baseline_summary.average_distance_km - proximity_summary.average_distance_km)
        / baseline_summary.average_distance_km
        * 100
        if baseline_summary.average_distance_km
        else 0.0
    )
    print(f"Average placement distance reduced by {improvement:.1f}% "
          f"({baseline_summary.average_distance_km}km -> {proximity_summary.average_distance_km}km)")


if __name__ == "__main__":
    main()
