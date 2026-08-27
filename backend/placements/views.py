from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from placement_algorithm.data_gen import School as AlgoSchool
from placement_algorithm.data_gen import SchoolCategory as AlgoSchoolCategory
from placement_algorithm.data_gen import Student as AlgoStudent
from placement_algorithm.distance import Coordinates
from placement_algorithm.scoring import eligible_schools

from .models import Appeal, Placement, PlacementRun, School, Student
from .permissions import (
    IsMinistryAdmin,
    IsMinistryOrSchoolAdmin,
    IsSchoolOwnerOrMinistryAdmin,
    IsStudentSelfParentOrAdmin,
)
from .serializers import (
    AppealResolutionSerializer,
    AppealSerializer,
    DistanceQuerySerializer,
    PlacementRunSerializer,
    PlacementSerializer,
    SchoolSerializer,
    StudentRegistrationSerializer,
    StudentSerializer,
    TriggerPlacementRunSerializer,
    UploadResultsSerializer,
)
from .services import run_placement


class SchoolViewSet(viewsets.ModelViewSet):
    """Module 2: School Database and Capacity Management. Any authenticated
    user can browse schools (students/parents comparing options); only the
    owning school_admin or a ministry_admin can create/update/delete."""

    queryset = School.objects.all()
    serializer_class = SchoolSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsMinistryOrSchoolAdmin(), IsSchoolOwnerOrMinistryAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        administrator = user if user.is_school_admin else None
        serializer.save(administrator=administrator)

    @action(detail=True, methods=["get"])
    def placed_students(self, request, pk=None):
        """School Administrator use case: 'view their placed students list'."""
        school = self.get_object()
        user = request.user
        if not (user.is_ministry_admin or (user.is_school_admin and school.administrator_id == user.id)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        placements = Placement.objects.filter(school=school).select_related("student__user")
        return Response(PlacementSerializer(placements, many=True).data)


class StudentViewSet(viewsets.ModelViewSet):
    """Module 1: Student Registration and Results Management."""

    serializer_class = StudentSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("upload_results",):
            return [permissions.IsAuthenticated(), IsMinistryAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        base = Student.objects.select_related("user", "parent")
        if user.is_ministry_admin:
            return base.all()
        if user.is_school_admin:
            return base.filter(placement__school__administrator=user)
        if user.is_parent:
            return base.filter(parent=user)
        if user.is_student:
            return base.filter(user=user)
        return base.none()

    def get_object(self):
        obj = super().get_object()
        if not IsStudentSelfParentOrAdmin().has_object_permission(self.request, self, obj):
            self.permission_denied(self.request)
        return obj

    @action(detail=False, methods=["get", "post"])
    def me(self, request):
        """GET: the logged-in student's own profile. POST: create it
        (Module 1's registration flow) if it doesn't exist yet."""
        if not request.user.is_student:
            return Response({"detail": "Only student accounts have a student profile."}, status=400)

        if request.method == "POST":
            if Student.objects.filter(user=request.user).exists():
                return Response({"detail": "Profile already exists."}, status=400)
            serializer = StudentRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            student = serializer.save(user=request.user)
            return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)

        student = get_object_or_404(Student, user=request.user)
        return Response(StudentSerializer(student).data)

    @action(detail=True, methods=["post"])
    def upload_results(self, request, pk=None):
        """Module 1: 'accepts exam score data from authorized administrative
        uploads' -- restricted to ministry_admin."""
        student = get_object_or_404(Student, pk=pk)
        serializer = UploadResultsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student.exam_score = serializer.validated_data["exam_score"]
        student.results_uploaded_by = request.user
        student.results_uploaded_at = timezone.now()
        student.save()
        return Response(StudentSerializer(student).data)


class PlacementViewSet(viewsets.ReadOnlyModelViewSet):
    """Student/Parent use case: 'view placement result'."""

    serializer_class = PlacementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base = Placement.objects.select_related("student__user", "school")
        if user.is_ministry_admin:
            return base.all()
        if user.is_school_admin:
            return base.filter(school__administrator=user)
        if user.is_parent:
            return base.filter(student__parent=user)
        if user.is_student:
            return base.filter(student__user=user)
        return base.none()

    @action(detail=False, methods=["get"])
    def me(self, request):
        if not request.user.is_student:
            return Response({"detail": "Only student accounts have their own placement."}, status=400)
        placement = Placement.objects.filter(student__user=request.user).select_related("school").first()
        if placement is None:
            return Response({"detail": "Not yet placed."}, status=404)
        return Response(PlacementSerializer(placement).data)


class PlacementRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Ministry Administrator use case: 'run placement algorithm'."""

    queryset = PlacementRun.objects.all()
    serializer_class = PlacementRunSerializer
    permission_classes = [permissions.IsAuthenticated, IsMinistryAdmin]

    @action(detail=False, methods=["post"])
    def trigger(self, request):
        serializer = TriggerPlacementRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        run = run_placement(
            triggered_by=request.user,
            merit_weight=data["merit_weight"],
            proximity_weight=data["proximity_weight"],
            max_distance_km=data["max_distance_km"],
            max_candidates=data["max_candidates"],
        )
        http_status = (
            status.HTTP_201_CREATED if run.status == PlacementRun.Status.COMPLETED else status.HTTP_400_BAD_REQUEST
        )
        return Response(PlacementRunSerializer(run).data, status=http_status)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        run = PlacementRun.objects.first()
        if run is None:
            return Response({"detail": "No placement runs yet."}, status=404)
        return Response(PlacementRunSerializer(run).data)


class AppealViewSet(viewsets.ModelViewSet):
    """Parent/Guardian use case: 'submit appeal'. Ministry Administrator use
    case: 'manage the appeals process'."""

    serializer_class = AppealSerializer
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base = Appeal.objects.select_related("student__user")
        if user.is_ministry_admin:
            return base.all()
        if user.is_parent:
            return base.filter(student__parent=user)
        if user.is_student:
            return base.filter(student__user=user)
        return base.none()

    def perform_create(self, serializer):
        student = serializer.validated_data["student"]
        user = self.request.user
        allowed = user.is_ministry_admin or student.user_id == user.id or student.parent_id == user.id
        if not allowed:
            self.permission_denied(self.request, message="You may only appeal your own or your child's placement.")
        serializer.save(submitted_by=user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsMinistryAdmin])
    def resolve(self, request, pk=None):
        appeal = get_object_or_404(Appeal, pk=pk)
        serializer = AppealResolutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appeal.status = serializer.validated_data["status"]
        appeal.resolution_notes = serializer.validated_data.get("resolution_notes", "")
        appeal.resolved_by = request.user
        appeal.resolved_at = timezone.now()
        appeal.save()
        return Response(AppealSerializer(appeal).data)


class AnalyticsView(APIView):
    """Ministry Administrator use case: 'monitor placement analytics' /
    'monitor equity metrics'. Section 2.3 of the proposal names average
    placement distance, slot utilization, and outcomes for vulnerable
    groups as the metrics that matter -- county is used here as the
    available proxy for the geographic-equity dimension."""

    permission_classes = [permissions.IsAuthenticated, IsMinistryAdmin]

    def get(self, request):
        latest_run = PlacementRun.objects.filter(status=PlacementRun.Status.COMPLETED).first()

        by_category = list(
            School.objects.values("category").annotate(schools=Count("id"), avg_rating=Avg("performance_rating"))
        )
        for row in by_category:
            category_schools = School.objects.filter(category=row["category"])
            total_capacity = sum(category_schools.values_list("capacity", flat=True))
            filled = Placement.objects.filter(school__category=row["category"]).count()
            row["filled_slots"] = filled
            row["total_capacity"] = total_capacity
            row["utilization"] = round(filled / total_capacity, 4) if total_capacity else 0.0

        by_county = list(
            Placement.objects.values("student__county")
            .annotate(placements=Count("id"), avg_distance_km=Avg("distance_km"))
            .order_by("-placements")
        )

        appeals_by_status = list(Appeal.objects.values("status").annotate(count=Count("id")))

        return Response({
            "latest_run": PlacementRunSerializer(latest_run).data if latest_run else None,
            "total_students": Student.objects.count(),
            "students_with_results": Student.objects.filter(exam_score__isnull=False).count(),
            "total_schools": School.objects.count(),
            "total_placements": Placement.objects.count(),
            "pending_appeals": Appeal.objects.filter(status=Appeal.Status.PENDING).count(),
            "by_school_category": by_category,
            "by_student_county": by_county,
            "appeals_by_status": appeals_by_status,
        })


class DistanceView(APIView):
    """Student and Ministry Administrator use case: 'calculate distance to
    schools'. Reuses placement_algorithm.scoring.eligible_schools directly
    rather than reimplementing distance sorting here."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DistanceQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "student_id" in data:
            student = get_object_or_404(Student, pk=data["student_id"])
            user = request.user
            allowed = (
                user.is_ministry_admin
                or user.is_school_admin
                or student.user_id == user.id
                or student.parent_id == user.id
            )
            if not allowed:
                return Response(status=status.HTTP_403_FORBIDDEN)
            home = Coordinates(student.home_latitude, student.home_longitude)
            algo_student = AlgoStudent(
                student_id=str(student.pk), exam_score=student.exam_score or 0.0, home=home, county=student.county
            )
        else:
            home = Coordinates(data["latitude"], data["longitude"])
            algo_student = AlgoStudent(student_id="query", exam_score=0.0, home=home, county="")

        db_schools = list(School.objects.all())
        algo_schools = [
            AlgoSchool(
                school_id=str(s.pk), name=s.name, category=AlgoSchoolCategory(s.category),
                location=Coordinates(s.latitude, s.longitude), county=s.county,
                capacity=s.capacity, performance_rating=s.performance_rating,
            )
            for s in db_schools
        ]
        schools_by_id = {str(s.pk): s for s in db_schools}

        candidates = eligible_schools(algo_student, algo_schools, max_candidates=data["max_candidates"])
        results = [
            {
                "school_id": schools_by_id[school.school_id].id,
                "name": schools_by_id[school.school_id].name,
                "category": schools_by_id[school.school_id].category,
                "county": schools_by_id[school.school_id].county,
                "available_slots": schools_by_id[school.school_id].available_slots,
                "distance_km": round(dist, 2),
            }
            for school, dist in candidates
        ]
        return Response(results)
