from fastapi import FastAPI
import os
import uuid
import threading
import time
from urllib.parse import urlparse
from yt_dlp import YoutubeDL

app = FastAPI()

DOWNLOAD_BASE = "/downloads"
JOB_TTL = 172800  # 2 hari
jobs = {}

# =============================
# 🔍 DETECT DOMAIN
# =============================
def detect_domain(url: str):
    try:
        host = urlparse(url).hostname.replace("www.", "")
        return host.split(".")[-2]
    except:
        return "other"

# =============================
# 🧹 CLEANUP JOB
# =============================
def cleanup_job(job_id):
    time.sleep(JOB_TTL)
    jobs.pop(job_id, None)

# =============================
# 📥 PROGRESS
# =============================
def progress_hook(d, job_id):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        jobs[job_id]["progress"] = f"{percent} @ {speed}"

    elif d["status"] == "finished":
        jobs[job_id]["progress"] = "processing..."

# =============================
# 🚀 DOWNLOAD CORE
# =============================
def run_download(job_id, url, mode):
    try:
        domain = detect_domain(url)

        base_folder = os.path.join(DOWNLOAD_BASE, domain, mode)
        os.makedirs(base_folder, exist_ok=True)

        print(f"[DEBUG] MODE: {mode}")

        # =============================
        # 🎧 AUDIO (SINGLE)
        # =============================
        if mode == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{base_folder}/%(title)s.%(ext)s",
                "noplaylist": True,
                "progress_hooks": [lambda d: progress_hook(d, job_id)],

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {
                        "key": "FFmpegMetadata"
                    }
                ],

                "prefer_ffmpeg": True,
                "keepvideo": False,

                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                }
            }

        # =============================
        # 📺 PLAYLIST VIDEO (MP4)
        # =============================
        elif mode == "playlist":
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",

                # 🔥 numbering otomatis
                "outtmpl": f"{base_folder}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s",

                "progress_hooks": [lambda d: progress_hook(d, job_id)],

                # 🔥 force MP4
                "merge_output_format": "mp4",

                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4"
                    }
                ],
            }

        # =============================
        # 🎧 PLAYLIST AUDIO (MP3)
        # =============================
        elif mode == "playlist_audio":
            ydl_opts = {
                "format": "bestaudio/best",

                # 🔥 numbering otomatis
                "outtmpl": f"{base_folder}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s",

                "progress_hooks": [lambda d: progress_hook(d, job_id)],

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {
                        "key": "FFmpegMetadata"
                    }
                ],

                "prefer_ffmpeg": True,
                "keepvideo": False,

                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                }
            }

        # =============================
        # 🎬 VIDEO (MP4)
        # =============================
        else:
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": f"{base_folder}/%(title)s.%(ext)s",
                "noplaylist": True,
                "progress_hooks": [lambda d: progress_hook(d, job_id)],

                # 🔥 force MP4
                "merge_output_format": "mp4",

                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4"
                    }
                ],
            }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            jobs[job_id].update({
                "status": "done",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "filesize": info.get("filesize") or info.get("filesize_approx"),
                "path": base_folder
            })

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

    threading.Thread(target=cleanup_job, args=(job_id,)).start()

# =============================
# 🚀 START DOWNLOAD
# =============================
@app.get("/download")
def download(url: str, mode: str = "video"):
    """
    mode:
    - video
    - audio
    - playlist
    - playlist_audio
    """

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "downloading",
        "progress": "starting...",
        "mode": mode,
    }

    threading.Thread(
        target=run_download,
        args=(job_id, url, mode)
    ).start()

    return {
        "job_id": job_id,
        "status": "started",
        "mode": mode
    }

# =============================
# 📊 PROGRESS
# =============================
@app.get("/progress")
def progress(job_id: str):
    return jobs.get(job_id, {"error": "job not found"})

# =============================
# ❤️ HEALTH CHECK
# =============================
@app.get("/")
def root():
    return {"status": "yt-dlp API jalan"}