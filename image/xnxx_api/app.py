from fastapi import FastAPI
from xnxx_api.xnxx_api import Client
import requests

app = FastAPI()

client = Client()

@app.get("/")
def root():
    return {"status": "API jalan"}

# 🔍 SEARCH
@app.get("/search")
def search(q: str):
    try:
        results = client.search(q)

        data = []
        for video in results.videos(pages=1):
            data.append({
                "title": video.title,
                "url": video.url,
                "thumbnail": video.thumbnail_url[0] if video.thumbnail_url else None,
                "views": video.views
            })

        return data

    except Exception as e:
        return {"error": str(e)}


# 🎬 VIDEO DETAIL
@app.get("/video")
def video(url: str):
    try:
        v = client.get_video(url)

        return {
            "title": v.title,
            "video": v.content_url,
            "thumbnail": v.thumbnail_url[0] if v.thumbnail_url else None,
            "views": v.views
        }

    except Exception as e:
        return {"error": str(e)}


# 🔥 OPTIONAL: PROXY DOWNLOAD (ADVANCED)
@app.get("/download")
def download(url: str):
    try:
        v = client.get_video(url)
        video_url = v.content_url

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.xnxx.com/"
        }

        # cuma return info (biar aman)
        return {
            "title": v.title,
            "video": video_url,
            "note": "Gunakan link ini untuk download di client"
        }

    except Exception as e:
        return {"error": str(e)}