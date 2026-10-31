"""
Database models for Modules 1, 2 and 4 of the proposal (Student Registration
and Results Management; School Database and Capacity Management; and the
placement/appeals side of the Portal module). Module 3, the placement
algorithm itself, lives in the standalone `placement_algorithm` package and
is invoked from `services.py` in this app rather than reimplemented here.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SchoolCategory(models.TextChoices):
    """Mirrors placement_algorithm.data_gen.SchoolCategory -- kept as a
    separate Django choices class (rather than importing the dataclass
    enum directly) so the web layer's schema doesn't depend on the
    algorithm package's internals, only on matching string values."""

    NATIONAL = "national", "National"
    EXTRA_COUNTY = "extra_county", "Extra-County"
    COUNTY = "county", "County"
    SUB_COUNTY = "sub_county", "Sub-County"


class School(models.Model):
    """Module 2: School Database and Capacity Management."""

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=SchoolCategory.choices)
    county = models.CharField(max_length=100)
    latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    capacity = models.PositiveIntegerField()
    performance_rating = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100 -- mean historical KCSE performance rating for this school.",
    )
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_schools",
        limit_choices_to={"role": "school_admin"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_display()})"

    @property
    def filled_slots(self) -> int:
        return self.placements.count()

    @property
    def available_slots(self) -> int:
        return max(0, self.capacity - self.filled_slots)


class Student(models.Model):
    """Module 1: Student Registration and Results Management."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"role": "parent"},
        help_text="Parent/guardian account linked to this student, if any.",
    )
    county = models.CharField(max_length=100)
    home_latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    home_longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    exam_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        help_text="KCPE-style exam score, 0-500. Null until results are uploaded.",
    )
    results_uploaded_at = models.DateTimeField(null=True, blank=True)
    results_uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_results",
        help_text="Which administrator uploaded/confirmed this student's exam score.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def has_results(self) -> bool:
        return self.exam_score is not None


class PlacementRun(models.Model):
    """One execution of the placement algorithm (Ministry Administrator use
    case: 'run placement algorithm'). Stores the configuration used and the
    resulting evaluation metrics, so past runs stay auditable/comparable."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="placement_runs",
        limit_choices_to={"role": "ministry_admin"},
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    merit_weight = models.FloatField(default=0.6)
    proximity_weight = models.FloatField(default=0.4)
    students_considered = models.PositiveIntegerField(default=0)
    students_placed = models.PositiveIntegerField(default=0)
    average_distance_km = models.FloatField(null=True, blank=True)
    median_distance_km = models.FloatField(null=True, blank=True)
    proportion_within_threshold = models.FloatField(null=True, blank=True)
    overall_slot_utilization = models.FloatField(null=True, blank=True)
    is_stable = models.BooleanField(null=True, blank=True)
    # Same cohort allocated by the merit-only, geography-blind baseline
    # (section 2.3's comparison), recorded alongside each run.
    baseline_average_distance_km = models.FloatField(null=True, blank=True)
    baseline_proportion_within_threshold = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Run #{self.pk} ({self.status}) at {self.started_at:%Y-%m-%d %H:%M}"


class Placement(models.Model):
    """A single student's resolved placement from a PlacementRun."""

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="placement")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="placements")
    run = models.ForeignKey(PlacementRun, on_delete=models.CASCADE, related_name="placements")
    distance_km = models.FloatField()
    composite_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.student} -> {self.school} ({self.distance_km:.1f}km)"


class Appeal(models.Model):
    """Module 4: appeal handling. A student or parent can appeal a
    placement result; a Ministry administrator resolves it."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="appeals")
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submitted_appeals"
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_appeals",
        limit_choices_to={"role": "ministry_admin"},
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Appeal by {self.student} ({self.status})"
