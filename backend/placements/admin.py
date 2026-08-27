from django.contrib import admin

from .models import Appeal, Placement, PlacementRun, School, Student


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "county", "capacity", "filled_slots", "performance_rating"]
    list_filter = ["category", "county"]
    search_fields = ["name", "county"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["user", "county", "exam_score", "has_results", "parent"]
    list_filter = ["county"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]


@admin.register(PlacementRun)
class PlacementRunAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "started_at", "students_placed", "average_distance_km", "is_stable"]
    list_filter = ["status"]


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ["student", "school", "distance_km", "run"]
    list_filter = ["school__category"]


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ["student", "status", "created_at", "resolved_by"]
    list_filter = ["status"]
