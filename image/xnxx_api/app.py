from fastapi import FastAPI
from xnxx_api.xnxx_api import Client

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
                "thumbnail": video.thumbnail_url,  # array
                "views": video.views
            })

        return data

    except Exception as e:
        return {"error": str(e)}

# 🎬 VIDEO DETAIL + DOWNLOAD LINK
@app.get("/video")
def video(url: str):
    try:
        v = client.get_video(url)

        return {
            "title": v.title,
            "video": v.content_url,        # 🔥 direct video link
            "thumbnail": v.thumbnail_url, # array
            "views": v.views
        }

    except Exception as e:
        return {"error": str(e)}