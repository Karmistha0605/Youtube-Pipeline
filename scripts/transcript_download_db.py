from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql


load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "youtube_transcripts")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        print("Database successfully connected")
        return conn

    except psycopg2.Error as e:
        print("Error connecting to the database")
        print(e)
        return None


api_key = "AIzaSyAE_KGm548qbM7kpvN_3x1wPjxdLaA3Bvg"

PLAYLIST_ID = "PLhQjrBD2T383q7Vn8QnTsVgSvyLpsqL_R"

youtube = build("youtube", "v3", developerKey=api_key)


def get_all_playlist_video_ids(playlist_id):
    video_ids = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        # Extract IDs
        for item in response["items"]:
            video_ids.append(item["contentDetails"]["videoId"])

        # Pagination
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids

def fetch_transcript(video_id):
    try:
        # Create an instance and use fetch() method
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return video_id, transcript, None
    except TranscriptsDisabled:
        return video_id, None, "Transcripts disabled for this video"
    except NoTranscriptFound:
        return video_id, None, "No transcript available"
    except Exception as e:
        return video_id, None, f"Error fetching transcript: {str(e)}"


def store_transcript(video_id, transcript):
    conn = connection()
    if not conn:
        return False
    
    cursor = conn.cursor()

    try:
        # insert video into database
        cursor.execute(
            """
                INSERT INTO videos (video_id, title, channel_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (video_id) DO NOTHING
            """,
            (video_id, f"Video {video_id}", "Unknown"),
        )

        # insert transcript into database
        for item in transcript:  # multiple lines of transcript thats why use loop
            # Handle both dict and object formats
            text = item.get("text") if isinstance(item, dict) else item.text
            start = item.get("start") if isinstance(item, dict) else item.start
            duration = item.get("duration") if isinstance(item, dict) else item.duration
            
            cursor.execute(
                """INSERT INTO transcripts (video_id, text, start_time, duration)
                    VALUES (%s, %s, %s, %s)
                    """,
                (video_id, text, start, duration),
            )

        conn.commit()
        print("Transcript stored successfully")
        return True

    except psycopg2.Error as e:
        print("Error connecting to the database")
        print(e)
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()

def main():
    print("Fetching playlist video IDs...")
    video_ids = get_all_playlist_video_ids(PLAYLIST_ID)
    print(f"Found {len(video_ids)} videos.\n")

    # Step 2: Process each video one by one
    for vid in video_ids:
        print(f"Fetching transcript for: {vid}")
        video_id, transcript, error = fetch_transcript(vid)

        if error:
            print(f"[{video_id}] Error: {error}")
        else:
            store_transcript(video_id, transcript)
            print(f"[{video_id}] Video transcript stored successfully.")

    print("\nProcessing successful.")


if __name__ == "__main__":
    main()
