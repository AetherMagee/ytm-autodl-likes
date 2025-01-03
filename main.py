import os
import time
import traceback

import yt_dlp
from loguru import logger
from ytmusicapi import YTMusic

from db import SongDatabase

SLEEP_TIME = int(os.getenv("SLEEP_TIME", 3600))
PROXY_URL = os.getenv("PROXY_URL", None)

db = SongDatabase()

if not os.path.exists("./data/browser.json"):
    logger.error("Couldn't find browser.json")
    logger.info("Please authenticate using `ytmusicapi browser`")
    time.sleep(60)
    exit(1)

try:
    ytm = YTMusic("./data/browser.json")
except Exception as e:
    logger.error(e)
    logger.error("Failed to initialize YTMusic object.")
    time.sleep(30)
    exit(1)


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
        'writethumbnail': True,
    }

    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL

    video_url = f"https://music.youtube.com/watch?v={video_id}"

    try:
        logger.info(f"Downloading {video_id} | {title}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        logger.success(f"Successfully downloaded {video_id} | {title}")
        return "saved"
    except Exception as error:
        logger.error(f"Failed to download {video_id}: {str(error)}")
        noretry_indicators = ["premium", "sign in", "not available"]
        if any(indicator in str(error) for indicator in noretry_indicators):
            return "failed_noretry"
        return "failed"


while True:
    try:
        if os.path.exists("./data/reset-noretrys"):
            logger.info("Resetting noretrys...")
            db.reset_noretrys()
            try:
                os.remove("./data/reset-noretrys")
            except Exception:
                logger.warning("Failed to remove reset-noretrys indicator file!")

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

        if len(to_download) > 0:
            logger.info(
                f"About to download {len(to_download)} songs ({len(failed_songs)} prev. failed and {len(pending_songs)} pending)")

            for song in to_download:
                new_status = download_song(song[0], song[1])
                db.update_song_status(song[0], new_status)
    except Exception as e:
        traceback.print_exc()
        logger.error("Unable to complete cycle")

    logger.info(f"Sleeping for {SLEEP_TIME} seconds...")
    time.sleep(SLEEP_TIME)