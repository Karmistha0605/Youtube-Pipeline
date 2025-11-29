from rest_framework import serializers
from .models import PlaylistSearchJob, VideoRecord

class VideoRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoRecord
        fields = ['id', 'video_id', 'title', 'channel_name', 'duration', 'transcript_fetched', 'created_at']

class PlaylistSearchJobSerializer(serializers.ModelSerializer):
    videos = VideoRecordSerializer(many=True, read_only=True)

    class Meta:
        model = PlaylistSearchJob
        fields = ['id', 'playlist_id', 'playlist_title', 'video_count', 'status', 'error_message', 'videos', 'created_at', 'completed_at']