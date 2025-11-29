from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript
)
from .models import PlaylistSearchJob, VideoRecord
from .serializers import PlaylistSearchJobSerializer, VideoRecordSerializer
import time

load_dotenv()

YOUTUBE_API_KEY = os.getenv('GOOGLE_DEVELOPER_API_KEY')


def get_youtube():

    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)


# REST API ViewSets
class PlaylistSearchJobViewSet(viewsets.ModelViewSet):
    queryset = PlaylistSearchJob.objects.all()
    serializer_class = PlaylistSearchJobSerializer

    @action(detail=False, methods=['post'])
    def search_playlist(self, request):
        playlist_id = request.data.get('playlist_id', '').strip()
        if not playlist_id:
            return Response({'error': 'Playlist ID required'}, status=400)

        # Check for existing pending/processing job
        existing_job = PlaylistSearchJob.objects.filter(
            playlist_id=playlist_id, status__in=['pending', 'processing']
        ).first()
        if existing_job:
            return Response({'error': 'Playlist already being processed'}, status=400)

        job = None
        try:
            job = PlaylistSearchJob.objects.create(
                playlist_id=playlist_id,
                status='processing'
            )

            youtube = get_youtube()

            # Fetch playlist info
            playlist_request = youtube.playlists().list(part='snippet', id=playlist_id)
            playlist_response = playlist_request.execute()

            if not playlist_response['items']:
                job.status = 'failed'
                job.error_message = 'Playlist not found'
                job.save()
                return Response({'error': 'Playlist not found'}, status=404)

            job.playlist_title = playlist_response['items'][0]['snippet']['title']
            job.save()

            # Fetch videos
            next_page_token = None
            video_count = 0
            while True:
                request = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                for item in response['items']:
                    video_id = item['snippet']['resourceId'].get('videoId')
                    if not video_id:
                        continue
                    VideoRecord.objects.create(
                        video_id=video_id,
                        title=item['snippet']['title'],
                        channel_name=item['snippet']['channelTitle'],
                        duration=0,
                        playlist_job=job
                    )
                    video_count += 1

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            job.video_count = video_count
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()

            return Response({'message': f'{video_count} videos added', 'job_id': job.id})

        except Exception as e:
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.save()
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def fetch_transcripts(self, request, pk=None):
        job = self.get_object()
        fetched_count = 0
        failed_count = 0

        for video in job.videos.all():
            try:
                for attempt in range(3):
                    try:
                        transcript = YouTubeTranscriptApi().fetch(video.video_id)
                        break
                    except CouldNotRetrieveTranscript:
                        if attempt < 2:
                            time.sleep(2)  # wait before retry
                        else:
                            raise
                video.transcript_fetched = True
                video.save()
                fetched_count += 1
            except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
                failed_count += 1
            except Exception:
                failed_count += 1

        return Response({'fetched': fetched_count, 'failed': failed_count})


class VideoRecordViewSet(viewsets.ModelViewSet):
    queryset = VideoRecord.objects.all()
    serializer_class = VideoRecordSerializer

    @action(detail=True, methods=['post'])
    def fetch_transcript(self, request, pk=None):
        video = self.get_object()
        try:
            # Retry 2 times
            for attempt in range(2):
                try:
                    transcript = YouTubeTranscriptApi().fetch(video.video_id)
                    break
                except CouldNotRetrieveTranscript:
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        raise
            video.transcript_fetched = True
            video.save()
            return Response({'message': f'Transcript fetched for {video.title}'})
        except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# HTML Views

def index(request):
    jobs = PlaylistSearchJob.objects.all()[:10]
    return render(request, 'transcripts/index.html', {'jobs': jobs})


def job_detail(request, pk):
    job = get_object_or_404(PlaylistSearchJob, pk=pk)
    videos = job.videos.all()
    return render(request, 'transcripts/job_detail.html', {'job': job, 'videos': videos})
