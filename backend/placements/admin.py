"""Django admin for the placement system.

The admin site (http://127.0.0.1:8000/admin/) is the developer/operator's
back office: browse and edit every record, approve or reject appeals in
bulk, and run the placement algorithm with a single button. The React
portals remain the interface for students, parents and administrators.
"""

from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Appeal, Placement, PlacementRun, School, Student
from .services import run_placement

admin.site.site_header = "Smart School Placement — Administration"
admin.site.site_title = "Smart School Placement admin"
admin.site.index_title = "Back office"
admin.site.index_template = "admin/ssp_index.html"

BADGE_COLOURS = {
    # status -> (background, text)
    "completed": ("#e8f5ee", "#1d6f42"),
    "approved": ("#e8f5ee", "#1d6f42"),
    "running": ("#e8f0fd", "#1b4fa0"),
    "under_review": ("#e8f0fd", "#1b4fa0"),
    "pending": ("#fff6e5", "#8a5a00"),
    "failed": ("#fdecea", "#b3261e"),
    "rejected": ("#fdecea", "#b3261e"),
}


def badge(value, label=None):
    bg, fg = BADGE_COLOURS.get(value, ("#eef2f0", "#374151"))
    return format_html(
        '<span style="background:{};color:{};padding:2px 9px;border-radius:999px;font-weight:600;'
        'font-size:11px;white-space:nowrap">{}</span>',
        bg, fg, label or str(value).replace("_", " ").capitalize(),
    )


def meter(fraction):
    pct = max(0, min(100, round((fraction or 0) * 100)))
    colour = "#1d6f42" if pct < 85 else ("#d4a017" if pct < 100 else "#b3261e")
    return format_html(
        '<div style="display:flex;align-items:center;gap:6px;min-width:120px">'
        '<div style="flex:1;height:8px;background:#e5ece8;border-radius:999px;overflow:hidden">'
        '<div style="width:{}%;height:100%;background:{}"></div></div><span>{}%</span></div>',
        pct, colour, pct,
    )


# ---------------------------------------------------------------- schools


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "category_label", "county", "capacity", "filled", "available", "utilisation", "performance_rating"]
    list_editable = ["capacity"]
    list_filter = ["category", "county"]
    search_fields = ["name", "county"]
    list_per_page = 50
    readonly_fields = ["filled_slots", "available_slots", "created_at", "updated_at"]
    autocomplete_fields = ["administrator"]
    fieldsets = [
        ("School", {"fields": ["name", "category", "county", "administrator"]}),
        ("Location (used for distance calculation)", {"fields": ["latitude", "longitude"]}),
        ("Capacity and performance", {"fields": ["capacity", "performance_rating", "filled_slots", "available_slots"]}),
        ("Record", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_filled=Count("placements"))

    @admin.display(description="Category", ordering="category")
    def category_label(self, obj):
        return obj.get_category_display()

    @admin.display(description="Filled", ordering="_filled")
    def filled(self, obj):
        return obj._filled

    @admin.display(description="Available")
    def available(self, obj):
        return max(obj.capacity - obj._filled, 0)

    @admin.display(description="Capacity used")
    def utilisation(self, obj):
        return meter(obj._filled / obj.capacity if obj.capacity else 0)


# ---------------------------------------------------------------- students


class HasResultsFilter(admin.SimpleListFilter):
    title = "exam results"
    parameter_name = "results"

    def lookups(self, request, model_admin):
        return [("yes", "Uploaded"), ("no", "Awaiting results")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(exam_score__isnull=False)
        if self.value() == "no":
            return queryset.filter(exam_score__isnull=True)
        return queryset


class PlacedFilter(admin.SimpleListFilter):
    title = "placement"
    parameter_name = "placed"

    def lookups(self, request, model_admin):
        return [("yes", "Placed"), ("no", "Not placed")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(placement__isnull=False)
        if self.value() == "no":
            return queryset.filter(placement__isnull=True)
        return queryset


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["full_name", "username", "county", "exam_score", "results_status", "placed_school", "distance", "parent"]
    list_filter = [HasResultsFilter, PlacedFilter, "county"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "county"]
    list_select_related = ["user", "parent", "placement__school"]
    list_per_page = 50
    autocomplete_fields = ["user", "parent"]
    readonly_fields = ["results_uploaded_by", "results_uploaded_at", "created_at", "placed_school", "distance"]
    fieldsets = [
        ("Student", {"fields": ["user", "parent", "county"]}),
        ("Home location (used for distance calculation)", {"fields": ["home_latitude", "home_longitude"]}),
        ("Examination results", {"fields": ["exam_score", "results_uploaded_by", "results_uploaded_at"]}),
        ("Placement", {"fields": ["placed_school", "distance"]}),
    ]

    def save_model(self, request, obj, form, change):
        if "exam_score" in form.changed_data:
            obj.results_uploaded_by = request.user
            obj.results_uploaded_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.display(description="Name", ordering="user__last_name")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Username", ordering="user__username")
    def username(self, obj):
        return obj.user.username

    @admin.display(description="Results")
    def results_status(self, obj):
        return badge("approved", "Uploaded") if obj.exam_score is not None else badge("pending", "Awaiting")

    @admin.display(description="Placed school")
    def placed_school(self, obj):
        placement = getattr(obj, "placement", None)
        return placement.school.name if placement else "—"

    @admin.display(description="Distance")
    def distance(self, obj):
        placement = getattr(obj, "placement", None)
        return f"{placement.distance_km:.1f} km" if placement else "—"


# ---------------------------------------------------------- placement runs


class RunPlacementForm(forms.Form):
    merit_weight = forms.FloatField(min_value=0, max_value=1, initial=0.6,
                                    help_text="Proximity weight is set to 1 − merit weight.")
    max_distance_km = forms.FloatField(min_value=1, initial=300, label="Max search distance (km)")
    max_candidates = forms.IntegerField(min_value=1, initial=15, label="Candidate schools per student")


@admin.register(PlacementRun)
class PlacementRunAdmin(admin.ModelAdmin):
    change_list_template = "admin/placements/placementrun/change_list.html"
    list_display = ["run_label", "status_badge", "started_at", "weights", "placed", "average_distance", "baseline_distance", "reduction", "within_50", "stable"]
    list_filter = ["status", "is_stable"]
    date_hierarchy = "started_at"

    def has_add_permission(self, request):
        return False  # runs are created by running the algorithm, not typed in

    def has_change_permission(self, request, obj=None):
        return False  # a run is an audit record

    def get_urls(self):
        return [path("run/", self.admin_site.admin_view(self.run_view), name="placements_placementrun_run")] + super().get_urls()

    def run_view(self, request):
        form = RunPlacementForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            merit = form.cleaned_data["merit_weight"]
            try:
                run = run_placement(
                    triggered_by=request.user,
                    merit_weight=merit,
                    proximity_weight=round(1 - merit, 4),
                    max_distance_km=form.cleaned_data["max_distance_km"],
                    max_candidates=form.cleaned_data["max_candidates"],
                )
            except Exception as exc:  # noqa: BLE001 -- shown to the operator
                messages.error(request, f"Placement run failed: {exc}")
                return redirect("admin:placements_placementrun_changelist")
            if run.status == PlacementRun.Status.COMPLETED:
                messages.success(
                    request,
                    f"Run #{run.id} completed: {run.students_placed} of {run.students_considered} students placed, "
                    f"average distance {run.average_distance_km} km (baseline {run.baseline_average_distance_km} km).",
                )
            else:
                messages.error(request, f"Run #{run.id} failed: {run.error_message}")
            return redirect("admin:placements_placementrun_changelist")
        context = {**self.admin_site.each_context(request), "title": "Run the placement algorithm", "form": form,
                   "opts": self.model._meta, "students_with_results": Student.objects.filter(exam_score__isnull=False).count(),
                   "schools": School.objects.count()}
        return render(request, "admin/placements/placementrun/run.html", context)

    @admin.display(description="Run", ordering="id")
    def run_label(self, obj):
        return f"#{obj.id}"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return badge(obj.status)

    @admin.display(description="Merit / proximity")
    def weights(self, obj):
        return f"{obj.merit_weight:.2f} / {obj.proximity_weight:.2f}"

    @admin.display(description="Placed")
    def placed(self, obj):
        return f"{obj.students_placed}/{obj.students_considered}"

    @admin.display(description="Avg. distance")
    def average_distance(self, obj):
        return "—" if obj.average_distance_km is None else f"{obj.average_distance_km:.1f} km"

    @admin.display(description="Baseline avg.")
    def baseline_distance(self, obj):
        return "—" if obj.baseline_average_distance_km is None else f"{obj.baseline_average_distance_km:.1f} km"

    @admin.display(description="Reduction")
    def reduction(self, obj):
        if not obj.baseline_average_distance_km or obj.average_distance_km is None:
            return "—"
        return f"{(1 - obj.average_distance_km / obj.baseline_average_distance_km) * 100:.1f}%"

    @admin.display(description="Within 50 km")
    def within_50(self, obj):
        return "—" if obj.proportion_within_threshold is None else f"{obj.proportion_within_threshold * 100:.1f}%"

    @admin.display(description="Stable", boolean=True)
    def stable(self, obj):
        return obj.is_stable


# --------------------------------------------------------------- placements


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ["student_name", "student_county", "school", "school_category", "distance", "match", "run"]
    list_filter = ["school__category", "student__county"]
    search_fields = ["student__user__username", "student__user__first_name", "student__user__last_name", "school__name"]
    list_select_related = ["student__user", "school", "run"]
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Student", ordering="student__user__last_name")
    def student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @admin.display(description="Home county", ordering="student__county")
    def student_county(self, obj):
        return obj.student.county

    @admin.display(description="Category", ordering="school__category")
    def school_category(self, obj):
        return obj.school.get_category_display()

    @admin.display(description="Distance", ordering="distance_km")
    def distance(self, obj):
        return f"{obj.distance_km:.1f} km"

    @admin.display(description="Match score", ordering="composite_score")
    def match(self, obj):
        return f"{obj.composite_score * 100:.0f}%"


# ------------------------------------------------------------------ appeals


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ["student_name", "short_reason", "status_badge", "created_at", "resolved_by", "resolved_at"]
    list_filter = ["status"]
    search_fields = ["student__user__username", "student__user__first_name", "student__user__last_name", "reason"]
    list_select_related = ["student__user", "resolved_by"]
    readonly_fields = ["submitted_by", "created_at", "resolved_by", "resolved_at"]
    autocomplete_fields = ["student"]
    actions = ["approve", "reject", "mark_under_review"]
    fieldsets = [
        ("Appeal", {"fields": ["student", "submitted_by", "reason", "created_at"]}),
        ("Decision", {"fields": ["status", "resolution_notes", "resolved_by", "resolved_at"]}),
    ]

    def save_model(self, request, obj, form, change):
        if "status" in form.changed_data and obj.status in (Appeal.Status.APPROVED, Appeal.Status.REJECTED):
            obj.resolved_by = request.user
            obj.resolved_at = timezone.now()
        if not change and not obj.submitted_by_id:
            obj.submitted_by = request.user
        super().save_model(request, obj, form, change)

    def _set_status(self, request, queryset, status, resolved):
        updates = {"status": status}
        if resolved:
            updates.update(resolved_by=request.user, resolved_at=timezone.now())
        n = queryset.update(**updates)
        self.message_user(request, f"{n} appeal(s) marked {status.replace('_', ' ')}.", messages.SUCCESS)

    @admin.action(description="Approve selected appeals")
    def approve(self, request, queryset):
        self._set_status(request, queryset, Appeal.Status.APPROVED, True)

    @admin.action(description="Reject selected appeals")
    def reject(self, request, queryset):
        self._set_status(request, queryset, Appeal.Status.REJECTED, True)

    @admin.action(description="Mark selected appeals as under review")
    def mark_under_review(self, request, queryset):
        self._set_status(request, queryset, Appeal.Status.UNDER_REVIEW, False)

    @admin.display(description="Student", ordering="student__user__last_name")
    def student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @admin.display(description="Reason")
    def short_reason(self, obj):
        text = obj.reason if len(obj.reason) <= 90 else obj.reason[:87] + "…"
        return format_html('<div style="min-width:260px;max-width:380px">{}</div>', text)

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return badge(obj.status)


def admin_summary():
    """Figures for the admin home page dashboard."""
    latest = PlacementRun.objects.filter(status=PlacementRun.Status.COMPLETED).first()
    return {
        "students": Student.objects.count(),
        "with_results": Student.objects.filter(exam_score__isnull=False).count(),
        "schools": School.objects.count(),
        "placements": Placement.objects.count(),
        "pending_appeals": Appeal.objects.filter(status__in=[Appeal.Status.PENDING, Appeal.Status.UNDER_REVIEW]).count(),
        "latest_run": latest,
        "run_url": reverse("admin:placements_placementrun_run"),
    }
