from django.contrib import admin
from .models import PlaylistSearchJob, VideoRecord

# Register your models here.

@admin.register(PlaylistSearchJob)
class PlaylistSearchJobAdmin(admin.ModelAdmin):
    list_display = ('playlist_id','playlist_title','video_count','status','created_at','completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('playlist_id', 'playlist_title')


@admin.register(VideoRecord)
class VideoRecordAdmin(admin.ModelAdmin):
    list_display = ('video_id','title','channel_name','duration','transcript_fetched','created_at','playlist_job')
    list_filter = ('transcript_fetched', 'channel_name')
    search_fields = ('video_id', 'title', 'channel_name')
