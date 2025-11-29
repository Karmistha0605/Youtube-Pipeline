from django.db import models

# Create your models here

class PlaylistSearchJob(models.Model):
    choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
    
    playlist_id = models.CharField(max_length=100, unique=True)
    playlist_title = models.CharField(max_length=255, blank=True, null=True)
    video_count = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=choices,
        default="pending"
    )

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.playlist_title or self.playlist_id} ({self.status})"

class VideoRecord(models.Model):
    playlist_job = models.ForeignKey(
        PlaylistSearchJob,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=500)
    channel_name = models.CharField(max_length=255)
    duration = models.IntegerField()

    transcript_fetched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.video_id})"