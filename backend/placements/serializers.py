from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Appeal, Placement, PlacementRun, School, Student

User = get_user_model()


class SchoolSerializer(serializers.ModelSerializer):
    filled_slots = serializers.ReadOnlyField()
    available_slots = serializers.ReadOnlyField()

    class Meta:
        model = School
        fields = [
            "id", "name", "category", "county", "latitude", "longitude",
            "capacity", "performance_rating", "administrator",
            "filled_slots", "available_slots", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "administrator", "created_at", "updated_at"]


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    has_results = serializers.ReadOnlyField()

    class Meta:
        model = Student
        fields = [
            "id", "user", "username", "full_name", "parent", "county",
            "home_latitude", "home_longitude", "exam_score", "has_results",
            "results_uploaded_at", "created_at",
        ]
        read_only_fields = ["id", "user", "exam_score", "results_uploaded_at", "created_at"]

    def get_full_name(self, obj: Student) -> str:
        return obj.user.get_full_name() or obj.user.username


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """Used by a logged-in user with role=student to create their own
    Student profile (Module 1: 'students to register by providing personal
    details including home address and GPS coordinates')."""

    class Meta:
        model = Student
        fields = ["county", "home_latitude", "home_longitude", "parent"]


class UploadResultsSerializer(serializers.Serializer):
    exam_score = serializers.FloatField(min_value=0, max_value=500)


class PlacementSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Placement
        fields = ["id", "student", "student_name", "school", "run", "distance_km", "composite_score", "created_at"]

    def get_student_name(self, obj: Placement) -> str:
        return obj.student.user.get_full_name() or obj.student.user.username


class PlacementRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementRun
        fields = [
            "id", "triggered_by", "status", "merit_weight", "proximity_weight",
            "students_considered", "students_placed", "average_distance_km",
            "median_distance_km", "proportion_within_threshold",
            "overall_slot_utilization", "is_stable", "error_message",
            "started_at", "completed_at",
        ]
        read_only_fields = fields


class TriggerPlacementRunSerializer(serializers.Serializer):
    merit_weight = serializers.FloatField(default=0.6, min_value=0, max_value=1)
    proximity_weight = serializers.FloatField(default=0.4, min_value=0, max_value=1)
    max_distance_km = serializers.FloatField(default=300.0, min_value=1)
    max_candidates = serializers.IntegerField(default=15, min_value=1)

    def validate(self, data):
        total = data["merit_weight"] + data["proximity_weight"]
        if abs(total - 1.0) > 1e-6:
            raise serializers.ValidationError("merit_weight and proximity_weight must sum to 1.0")
        return data


class AppealSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Appeal
        fields = [
            "id", "student", "student_name", "submitted_by", "reason", "status",
            "resolved_by", "resolution_notes", "created_at", "resolved_at",
        ]
        read_only_fields = ["id", "submitted_by", "status", "resolved_by", "created_at", "resolved_at"]

    def get_student_name(self, obj: Appeal) -> str:
        return obj.student.user.get_full_name() or obj.student.user.username


class AppealResolutionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Appeal.Status.APPROVED, Appeal.Status.REJECTED, Appeal.Status.UNDER_REVIEW])
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class DistanceQuerySerializer(serializers.Serializer):
    """Backs the 'calculate distance to schools' use case named explicitly
    for both the Student and Ministry Administrator actors in the proposal's
    Use Case Diagram (3.4.3.4)."""

    student_id = serializers.IntegerField(required=False)
    latitude = serializers.FloatField(required=False, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=False, min_value=-180, max_value=180)
    max_candidates = serializers.IntegerField(default=10, min_value=1, max_value=100)

    def validate(self, data):
        has_student = "student_id" in data
        has_coords = "latitude" in data and "longitude" in data
        if has_student == has_coords:
            raise serializers.ValidationError(
                "Provide either student_id, or both latitude and longitude -- not neither, not both."
            )
        return data
