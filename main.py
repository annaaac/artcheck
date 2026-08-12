#main.py

from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from google.cloud import vision
from PIL import Image
from database import SimilarArtwork, start_db, SessionLocal, Artwork
from sqlalchemy import func

import requests
import similarity


app = FastAPI()
model, preprocess = similarity.load_clip_model()
vision_client = vision.ImageAnnotatorClient()

start_db()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


@app.post("/artworks")
async def register_artwork(user_id: str, file: UploadFile):
    file_bytes = await file.read()
    image = Image.open(BytesIO(file_bytes))

    embedding = similarity.get_clip_embedding(model, preprocess, image)
    embedding_bytes = similarity.embedding_to_bytes(embedding)
    
    db = SessionLocal()

    try:
        artwork = Artwork(
            user_id=user_id, 
            filename=file.filename,
            filepath="", 
            embedding=embedding_bytes
        )
        db.add(artwork)
        db.commit()
        db.refresh(artwork)

        extension = Path(file.filename).suffix or ".png"
        file_path = UPLOADS_DIR / f"{artwork.id}{extension}"
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        artwork.filepath = str(file_path)
        db.commit()

        return {"id": artwork.id, "filename": artwork.filename}
    
    finally:
        db.close()


@app.post("/artworks/{artwork_id}/scan")
async def scan_artwork(artwork_id: int, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            raise HTTPException(status_code=404, detail=f"No artwork found with id: {artwork_id}")

        with open(artwork.filepath, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)
        response = vision_client.web_detection(image=image)
        annotations = response.web_detection

        candidate_urls = set()
        for match in annotations.full_matching_images:
            candidate_urls.add(match.url)
        for match in annotations.partial_matching_images:
            candidate_urls.add(match.url)
        for match in annotations.visually_similar_images:
            candidate_urls.add(match.url)

        background_tasks.add_task(run_scan, artwork_id, list(candidate_urls), artwork.filepath)

        return {"artwork_id": artwork_id, "status": "scan_started", "candidate_count": len(candidate_urls)}
    finally:
        db.close()


@app.post("/artworks/{artwork_id}/compare")
async def compare_with_artwork(artwork_id: int, file: UploadFile):
    db = SessionLocal()

    try:
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            raise HTTPException(status_code=404, detail=f"No artwork found with id: {artwork_id}")

        uploaded_image = Image.open(BytesIO(await file.read()))
        stored_image = Image.open(artwork.filepath)

        is_similar, similarity_score = similarity.compare_images(
            uploaded_image, stored_image, model, preprocess
        )

        return {
            "artwork_id": artwork_id,
            "artwork_filename": artwork.filename,
            "is_similar": is_similar,
            "similarity_score": similarity_score
        }

    finally:
        db.close()


@app.get("/artworks/{artwork_id}/scan")
async def get_scan_results(artwork_id: int):
    db = SessionLocal()
    try:
        latest_per_url = (
            db.query(
                SimilarArtwork.url,
                func.max(SimilarArtwork.time_scanned).label("latest_time")
            )
            .filter(SimilarArtwork.artwork_id == artwork_id)
            .group_by(SimilarArtwork.url)
            .subquery()
        )

        results = (
            db.query(SimilarArtwork)
            .join(
                latest_per_url,
                (SimilarArtwork.url == latest_per_url.c.url)
                & (SimilarArtwork.time_scanned == latest_per_url.c.latest_time)
            )
            .filter(SimilarArtwork.artwork_id == artwork_id)
            .order_by(SimilarArtwork.similarity_score.desc())
            .all()
        )

        return {
            "artwork_id": artwork_id,
            "matches": [
                {
                    "url": r.url,
                    "similarity_score": r.similarity_score,
                    "time_scanned": r.time_scanned.isoformat(),
                }
                for r in results
            ],
        }
    finally:
        db.close()


@app.post("/compare")
async def compare_images(file_a: UploadFile, file_b: UploadFile):
    image_a = Image.open(BytesIO(await file_a.read()))
    image_b = Image.open(BytesIO(await file_b.read()))

    is_similar, similarity_score = similarity.compare_images(image_a, image_b, model, preprocess)

    return {"is_similar": is_similar, "similarity_score": similarity_score}


def run_scan(artwork_id: int, candidate_urls: list[str], stored_image_path: str):
    stored_image = Image.open(stored_image_path)
    db = SessionLocal()
    try:
        checked_count = 0
        for url in candidate_urls:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                candidate_image = Image.open(BytesIO(response.content))
            except Exception:
                continue

            checked_count += 1
            is_similar, similarity_score = similarity.compare_images(
                stored_image, candidate_image, model, preprocess
            )

            print(f"Artwork {artwork_id}: checked {checked_count} candidates, found match: {is_similar} (score: {similarity_score}), url: {url}")

            if not is_similar:
                continue
            else:
                db.add(SimilarArtwork(
                    artwork_id=artwork_id,
                    url=url,
                    similarity_score=similarity_score,
                    is_similar=is_similar,
                ))

        db.commit()
        print(f"Artwork {artwork_id}: checked {checked_count} candidates, saved matches above")
    finally:
        db.close()