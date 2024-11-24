import os
import sqlite3
from typing import Any

from loguru import logger


class SongDatabase:
    def __init__(self, path: str = "./data/songs.db"):
        needs_init = False
        if not os.path.exists(path):
            needs_init = True

        self.conn = sqlite3.connect(path)

        if needs_init:
            logger.info(f"Initializing songs database at {path}")
            self.conn.execute("CREATE TABLE IF NOT EXISTS songs (video_id TEXT PRIMARY KEY, title TEXT, status TEXT NOT NULL)")
            self.conn.commit()

    def save_song(self, video_id: str, title: str):
        self.conn.execute("INSERT INTO songs VALUES (?, ?, ?)", (video_id, title, 'pending'))
        self.conn.commit()

    def update_song_status(self, video_id: str, status: str):
        self.conn.execute("UPDATE songs SET status = ? WHERE video_id = ?", (status, video_id))
        self.conn.commit()

    def is_song_saved(self, video_id: str) -> bool:
        response = self.conn.execute("SELECT * FROM songs WHERE video_id = ?", (video_id,)).fetchone()
        if response:
            return True
        return False

    def get_songs_with_status(self, status: str) -> list[Any]:
        response = self.conn.execute("SELECT * FROM songs WHERE status = ?", (status,)).fetchall()
        return list(response)

