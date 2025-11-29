# transcripts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaylistSearchJobViewSet, VideoRecordViewSet, index, job_detail

# Create router
router = DefaultRouter()
router.register(r'playlists', PlaylistSearchJobViewSet, basename='playlist')
router.register(r'videos', VideoRecordViewSet, basename='video')

urlpatterns = [

    #  Create API routes
    path('api/', include(router.urls)),

    # Create HTML routes
    path('', index, name='index'),
    path('job/<int:pk>/', job_detail, name='job_detail'),
]