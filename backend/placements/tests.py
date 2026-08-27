from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Appeal, Placement, School, Student
from .services import run_placement

User = get_user_model()


def make_school(**kwargs):
    defaults = dict(
        name="Test School", category="county", county="Nairobi",
        latitude=-1.29, longitude=36.82, capacity=5, performance_rating=60.0,
    )
    defaults.update(kwargs)
    return School.objects.create(**defaults)


def make_student_with_user(username, exam_score=None, lat=-1.29, lon=36.82, county="Nairobi", parent=None):
    user = User.objects.create_user(username=username, email=f"{username}@example.com", password="pw", role="student")
    return Student.objects.create(
        user=user, county=county, home_latitude=lat, home_longitude=lon, exam_score=exam_score, parent=parent
    )


class SchoolAPITests(APITestCase):
    def setUp(self):
        self.ministry_admin = User.objects.create_user(
            username="min", email="min@example.com", password="pw", role="ministry_admin"
        )
        self.school_admin_a = User.objects.create_user(
            username="admin_a", email="a@example.com", password="pw", role="school_admin"
        )
        self.school_admin_b = User.objects.create_user(
            username="admin_b", email="b@example.com", password="pw", role="school_admin"
        )
        self.school_a = make_school(name="School A", administrator=self.school_admin_a)

    def test_authenticated_user_can_list_schools(self):
        student = User.objects.create_user(username="s1", email="s1@example.com", password="pw", role="student")
        self.client.force_authenticate(user=student)
        response = self.client.get("/api/schools/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_unauthenticated_cannot_list_schools(self):
        response = self.client.get("/api/schools/")
        self.assertEqual(response.status_code, 401)

    def test_school_admin_can_create_school_owned_by_self(self):
        self.client.force_authenticate(user=self.school_admin_b)
        response = self.client.post("/api/schools/", {
            "name": "School B", "category": "sub_county", "county": "Kiambu",
            "latitude": -1.1, "longitude": 36.9, "capacity": 50, "performance_rating": 55.0,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["administrator"], self.school_admin_b.id)

    def test_school_admin_cannot_edit_another_admins_school(self):
        self.client.force_authenticate(user=self.school_admin_b)
        response = self.client.patch(f"/api/schools/{self.school_a.id}/", {"capacity": 999})
        self.assertEqual(response.status_code, 403)

    def test_school_admin_can_edit_own_school(self):
        self.client.force_authenticate(user=self.school_admin_a)
        response = self.client.patch(f"/api/schools/{self.school_a.id}/", {"capacity": 200})
        self.assertEqual(response.status_code, 200)
        self.school_a.refresh_from_db()
        self.assertEqual(self.school_a.capacity, 200)

    def test_ministry_admin_can_edit_any_school(self):
        self.client.force_authenticate(user=self.ministry_admin)
        response = self.client.patch(f"/api/schools/{self.school_a.id}/", {"capacity": 300})
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_create_school(self):
        student = User.objects.create_user(username="s2", email="s2@example.com", password="pw", role="student")
        self.client.force_authenticate(user=student)
        response = self.client.post("/api/schools/", {
            "name": "Bad", "category": "county", "county": "X",
            "latitude": 0, "longitude": 0, "capacity": 1, "performance_rating": 1,
        })
        self.assertEqual(response.status_code, 403)


class StudentRegistrationTests(APITestCase):
    def test_student_can_register_own_profile(self):
        user = User.objects.create_user(username="stu", email="stu@example.com", password="pw", role="student")
        self.client.force_authenticate(user=user)
        response = self.client.post("/api/students/me/", {
            "county": "Nairobi", "home_latitude": -1.29, "home_longitude": 36.82,
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Student.objects.filter(user=user).exists())

    def test_student_cannot_register_twice(self):
        user = User.objects.create_user(username="stu", email="stu@example.com", password="pw", role="student")
        Student.objects.create(user=user, county="Nairobi", home_latitude=-1.29, home_longitude=36.82)
        self.client.force_authenticate(user=user)
        response = self.client.post("/api/students/me/", {
            "county": "Nairobi", "home_latitude": -1.29, "home_longitude": 36.82,
        })
        self.assertEqual(response.status_code, 400)

    def test_ministry_admin_can_upload_results(self):
        min_admin = User.objects.create_user(username="min", email="m@example.com", password="pw", role="ministry_admin")
        student = make_student_with_user("stu2")
        self.client.force_authenticate(user=min_admin)
        response = self.client.post(f"/api/students/{student.id}/upload_results/", {"exam_score": 320})
        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.exam_score, 320)
        self.assertIsNotNone(student.results_uploaded_at)

    def test_non_admin_cannot_upload_results(self):
        student = make_student_with_user("stu3")
        self.client.force_authenticate(user=student.user)
        response = self.client.post(f"/api/students/{student.id}/upload_results/", {"exam_score": 320})
        self.assertEqual(response.status_code, 403)

    def test_student_sees_only_own_profile_in_list(self):
        s1 = make_student_with_user("stu4")
        make_student_with_user("stu5")
        self.client.force_authenticate(user=s1.user)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], s1.id)

    def test_parent_sees_only_their_children(self):
        parent = User.objects.create_user(username="parent1", email="p1@example.com", password="pw", role="parent")
        own_child = make_student_with_user("child1", parent=parent)
        make_student_with_user("otherkid")
        self.client.force_authenticate(user=parent)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], own_child.id)


class PlacementRunTests(APITestCase):
    """End-to-end: real database rows through the real matching engine."""

    def setUp(self):
        self.ministry_admin = User.objects.create_user(
            username="min", email="min@example.com", password="pw", role="ministry_admin"
        )
        # Two schools close to two different clusters of students, one seat each,
        # so the outcome is deterministic enough to assert on directly.
        self.school_near_a = make_school(name="Near A", capacity=1, latitude=-1.29, longitude=36.82, performance_rating=70)
        self.school_near_b = make_school(name="Near B", capacity=1, latitude=0.51, longitude=35.27, performance_rating=70)
        self.student_a = make_student_with_user("stu_a", exam_score=300, lat=-1.30, lon=36.83, county="Nairobi")
        self.student_b = make_student_with_user("stu_b", exam_score=280, lat=0.52, lon=35.28, county="Uasin Gishu")

    def test_run_placement_service_places_students_near_their_home(self):
        run = run_placement(triggered_by=self.ministry_admin, max_candidates=5)
        self.assertEqual(run.status, run.Status.COMPLETED)
        self.assertEqual(run.students_placed, 2)
        self.assertTrue(run.is_stable)

        placement_a = Placement.objects.get(student=self.student_a)
        placement_b = Placement.objects.get(student=self.student_b)
        self.assertEqual(placement_a.school, self.school_near_a)
        self.assertEqual(placement_b.school, self.school_near_b)
        self.assertLess(placement_a.distance_km, 5)
        self.assertLess(placement_b.distance_km, 5)

    def test_trigger_endpoint_requires_ministry_admin(self):
        self.client.force_authenticate(user=self.student_a.user)
        response = self.client.post("/api/placement-runs/trigger/", {})
        self.assertEqual(response.status_code, 403)

    def test_trigger_endpoint_runs_and_persists(self):
        self.client.force_authenticate(user=self.ministry_admin)
        response = self.client.post("/api/placement-runs/trigger/", {})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["students_placed"], 2)
        self.assertEqual(Placement.objects.count(), 2)

    def test_student_can_view_own_placement_after_run(self):
        run_placement(triggered_by=self.ministry_admin, max_candidates=5)
        self.client.force_authenticate(user=self.student_a.user)
        response = self.client.get("/api/placements/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school"]["id"], self.school_near_a.id)

    def test_student_without_placement_gets_404(self):
        # No run has happened yet.
        self.client.force_authenticate(user=self.student_a.user)
        response = self.client.get("/api/placements/me/")
        self.assertEqual(response.status_code, 404)

    def test_run_placement_skips_students_without_results(self):
        make_student_with_user("no_results", exam_score=None)
        run = run_placement(triggered_by=self.ministry_admin, max_candidates=5)
        self.assertEqual(run.students_considered, 2)  # the no-results student is excluded


class AppealTests(APITestCase):
    def setUp(self):
        self.ministry_admin = User.objects.create_user(
            username="min", email="min@example.com", password="pw", role="ministry_admin"
        )
        self.student = make_student_with_user("appellant")

    def test_student_can_submit_own_appeal(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post("/api/appeals/", {"student": self.student.id, "reason": "Too far from home."})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")

    def test_student_cannot_submit_appeal_for_someone_else(self):
        other = make_student_with_user("someone_else")
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post("/api/appeals/", {"student": other.id, "reason": "Not mine."})
        self.assertEqual(response.status_code, 403)

    def test_ministry_admin_can_resolve_appeal(self):
        appeal = Appeal.objects.create(student=self.student, submitted_by=self.student.user, reason="Too far.")
        self.client.force_authenticate(user=self.ministry_admin)
        response = self.client.post(f"/api/appeals/{appeal.id}/resolve/", {
            "status": "approved", "resolution_notes": "Reassigned to closer school.",
        })
        self.assertEqual(response.status_code, 200)
        appeal.refresh_from_db()
        self.assertEqual(appeal.status, "approved")
        self.assertEqual(appeal.resolved_by, self.ministry_admin)

    def test_student_cannot_resolve_appeal(self):
        appeal = Appeal.objects.create(student=self.student, submitted_by=self.student.user, reason="Too far.")
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post(f"/api/appeals/{appeal.id}/resolve/", {"status": "approved"})
        self.assertEqual(response.status_code, 403)


class DistanceEndpointTests(APITestCase):
    def setUp(self):
        self.near = make_school(name="Near", latitude=-1.30, longitude=36.83)
        self.far = make_school(name="Far", latitude=1.0, longitude=40.0)
        self.student = make_student_with_user("stu", lat=-1.29, lon=36.82)

    def test_distance_query_by_student_id_orders_nearest_first(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post("/api/distance/", {"student_id": self.student.id, "max_candidates": 5})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data]
        self.assertEqual(names[0], "Near")

    def test_distance_query_by_raw_coordinates(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post("/api/distance/", {"latitude": -1.29, "longitude": 36.82, "max_candidates": 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Near")

    def test_student_cannot_query_distance_for_another_student(self):
        other = make_student_with_user("other_stu")
        self.client.force_authenticate(user=other.user)
        response = self.client.post("/api/distance/", {"student_id": self.student.id})
        self.assertEqual(response.status_code, 403)
