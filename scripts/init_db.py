import os
import sys
from dotenv import load_dotenv
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


def init_database():
    conn = connection()
    if conn is None:
        print("Database connection failed. Cannot initialize schema.")
        return

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id SERIAL PRIMARY KEY,
                video_id VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                channel_name VARCHAR(255),
                duration INT,
                views INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transcripts (
                id SERIAL PRIMARY KEY,
                video_id VARCHAR(255) NOT NULL REFERENCES videos(video_id),
                text TEXT NOT NULL,
                start_time FLOAT,
                duration FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transcript_enrichments (
                id SERIAL PRIMARY KEY,
                video_id VARCHAR(255) NOT NULL REFERENCES videos(video_id),
                summary TEXT,
                keywords TEXT,
                sentiment VARCHAR(50),
                language VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        print("Database tables created successfully")

    except psycopg2.Error as e:
        print("Error creating schema:")
        print(e)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_database()
