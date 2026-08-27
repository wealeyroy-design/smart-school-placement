from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyticsView,
    AppealViewSet,
    DistanceView,
    PlacementRunViewSet,
    PlacementViewSet,
    SchoolViewSet,
    StudentViewSet,
)

router = DefaultRouter()
router.register("schools", SchoolViewSet, basename="school")
router.register("students", StudentViewSet, basename="student")
router.register("placements", PlacementViewSet, basename="placement")
router.register("placement-runs", PlacementRunViewSet, basename="placement-run")
router.register("appeals", AppealViewSet, basename="appeal")

urlpatterns = [
    path("", include(router.urls)),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("distance/", DistanceView.as_view(), name="distance"),
]
