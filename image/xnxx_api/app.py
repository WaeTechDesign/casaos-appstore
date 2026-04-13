from fastapi import FastAPI
from xnxx_api.xnxx_api import Client

app = FastAPI()

client = Client()

@app.get("/")
def root():
    return {"status": "API jalan"}

@app.get("/search")
def search(q: str):
    results = client.search(q)

    # karena ini object generator, kita convert ke list sederhana
    data = []

    for video in results.videos(pages=1):
        data.append({
            "title": video.title,
            "url": video.url,
            "thumbnail": video.thumbnail_url,
            "views": video.views
        })

    return data