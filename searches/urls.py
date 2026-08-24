from rest_framework.routers import DefaultRouter
from .views import JobMatchViewSet, SearchProfileViewSet

router = DefaultRouter()
router.register("profiles", SearchProfileViewSet, basename="profile")
router.register("matches", JobMatchViewSet, basename="match")

urlpatterns = router.urls
