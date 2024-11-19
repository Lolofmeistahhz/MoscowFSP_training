from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestViewSet, UserRoleViewSet, UserAccountViewSet, TestPDFView

router = DefaultRouter()
router.register(r'tests', TestViewSet)
router.register(r'user-roles', UserRoleViewSet)
router.register(r'user-accounts', UserAccountViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tests/<int:id>/pdf/', TestPDFView.as_view(), name='test-pdf'),
]
