import os
import time

import yt_dlp
from loguru import logger
from ytmusicapi import YTMusic

from db import SongDatabase

db = SongDatabase()

if not os.path.exists("./data/browser.json"):
    logger.error("Couldn't find browser.json")
    logger.info("Please authenticate using `ytmusicapi browser`")
    time.sleep(60)
    exit(1)

ytm = YTMusic("./data/browser.json")

def download_song(video_id: str, title: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            'key': 'EmbedThumbnail',
        }, {
            'key': 'FFmpegMetadata',
        }],
        'outtmpl': os.path.join("./data/downloads/", '%(title)s.%(ext)s'),
        'quiet': True,
    }

    video_url = f"https://music.youtube.com/watch?v={video_id}"

    try:
        logger.info(f"Downloading {video_id} | {title}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        logger.success(f"Successfully downloaded {video_id} | {title}")
        return "saved"
    except Exception as e:
        logger.error(f"Failed to download {video_id}: {str(e)}")
        if "premium" in str(e).lower() or "sign in" in str(e).lower():
            return "failed_noretry"
        return "failed"


while True:
    logger.info("Getting liked songs...")
    current_likes = ytm.get_liked_songs(limit=None)

    new_songs = 0
    logger.info("Saving liked songs...")
    for song in current_likes["tracks"]:
        if not db.is_song_saved(song["videoId"]):
            db.save_song(song["videoId"], song["title"])
            new_songs += 1

    logger.info(f"Added {new_songs} new songs to the database")

    failed_songs = db.get_songs_with_status("failed")
    pending_songs = db.get_songs_with_status("pending")
    to_download = failed_songs + pending_songs
    logger.info(f"About to download {len(to_download)} songs ({len(failed_songs)} prev. failed and {len(pending_songs)} pending)")

    for song in to_download:
        new_status = download_song(song[0], song[1])
        db.update_song_status(song[0], new_status)

    time.sleep(3600)

