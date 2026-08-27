"""
Smart School Placement Optimization System
--------------------------------------------
Core placement algorithm package (Module 3 of the proposal: "Proximity-Weighted
Placement Algorithm Module").

This package is deliberately independent of Django/React/PostgreSQL so it can be
developed, tested and evaluated on its own before being wired into the web
application described in Chapter 3 of the proposal. It implements:

  - distance:    geographic distance between a student's home and a school
                 (Haversine by default; swappable for a real Google Maps
                 Distance Matrix API client later).
  - scoring:     the weighted composite score combining academic merit and
                 inverse distance for each student-school pair.
  - matching:    a capacitated Gale-Shapley (deferred acceptance / "college
                 admissions") engine that produces a stable, conflict-free
                 allocation of students to schools.
  - data_gen:    synthetic student/school data generation, standing in for the
                 real KNEC exam results and school database (see proposal
                 section 3.3, "Data Collection Methods").
  - evaluate:    the metrics used to judge placement quality (section 2.3 and
                 Objective iv): average placement distance, proximity-threshold
                 coverage, slot utilization and matching stability.
"""

__version__ = "0.1.0"
