#!/usr/bin/env python3
import argparse
import os
import psycopg2
from dotenv import load_dotenv
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
        return conn
    except psycopg2.Error as e:
        print("Database connection error:", e)
        return None


def search_transcripts(keyword):
    """Search transcripts for a keyword (case-insensitive)"""
    conn = connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        query = sql.SQL("SELECT video_id, text FROM transcripts WHERE text ILIKE %s")
        cursor.execute(query, (f"%{keyword}%",))  # parameterized query
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} matching transcript lines:")
            for vid, text in results:
                print(f"[{vid}] {text}")
        else:
            print("No matching transcripts found.")
    finally:
        cursor.close()
        conn.close()


def show_stats():
    """Show database stats: videos, transcripts, total characters"""
    conn = connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), SUM(LENGTH(text)) FROM transcripts")
        transcript_count, total_chars = cursor.fetchone()

        print(f"Videos: {video_count}")
        print(f"Transcript lines: {transcript_count}")
        print(f"Total characters in transcripts: {total_chars}")
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Query YouTube transcripts DB")
    parser.add_argument("--search", type=str, help="Search transcripts by keyword")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    args = parser.parse_args()

    if args.search:
        search_transcripts(args.search)
    if args.stats:
        show_stats()
    if not args.search and not args.stats:
        parser.print_help()


if __name__ == "__main__":
    main()
