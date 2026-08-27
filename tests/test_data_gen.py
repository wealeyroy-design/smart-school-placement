from placement_algorithm.data_gen import SchoolCategory, generate_schools, generate_students


def test_generate_students_count_and_bounds():
    students = generate_students(50, seed=1)
    assert len(students) == 50
    ids = {s.student_id for s in students}
    assert len(ids) == 50  # all unique
    for s in students:
        assert 0.0 <= s.exam_score <= 500.0


def test_generate_students_reproducible_with_seed():
    a = generate_students(20, seed=42)
    b = generate_students(20, seed=42)
    assert [s.exam_score for s in a] == [s.exam_score for s in b]
    assert [(s.home.lat, s.home.lon) for s in a] == [(s.home.lat, s.home.lon) for s in b]


def test_generate_schools_counts_by_category():
    schools = generate_schools(n_national=3, n_extra_county=5, n_county=7, n_sub_county=9, seed=1)
    counts = {cat: 0 for cat in SchoolCategory}
    for s in schools:
        counts[s.category] += 1
    assert counts[SchoolCategory.NATIONAL] == 3
    assert counts[SchoolCategory.EXTRA_COUNTY] == 5
    assert counts[SchoolCategory.COUNTY] == 7
    assert counts[SchoolCategory.SUB_COUNTY] == 9


def test_generate_schools_unique_ids_and_valid_capacity():
    schools = generate_schools(seed=7)
    ids = {s.school_id for s in schools}
    assert len(ids) == len(schools)
    for s in schools:
        assert s.capacity > 0
        assert 0.0 <= s.performance_rating <= 100.0
