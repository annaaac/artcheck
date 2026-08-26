#main.py

from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from google.cloud import vision
from PIL import Image
from database import SimilarArtwork, SessionLocal, Artwork
from scan import get_candidate_urls, run_scan
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware

import requests
import similarity

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model, preprocess = similarity.load_clip_model()
vision_client = vision.ImageAnnotatorClient()

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


@app.get("/artworks")
async def get_artworks_list():
    db = SessionLocal()
    try:
        artworks = db.query(Artwork).order_by(Artwork.id.desc()).all()

        result = []

        for a in artworks:
            total = db.query(SimilarArtwork).filter(
                SimilarArtwork.artwork_id == a.id,
                SimilarArtwork.status != "dismissed",
            ).count()

            new_count = db.query(SimilarArtwork).filter(
                SimilarArtwork.artwork_id == a.id,
                SimilarArtwork.status == "new",
            ).count()
            
            result.append({
                "id": a.id,
                "filename": a.filename,
                "user_id": a.user_id,
                "match_count": total,
                "new_match_count": new_count,
            })

        return result
    finally:
        db.close()


@app.get("/artworks/{artwork_id}/image")
async def get_artwork_image(artwork_id: int):
    db = SessionLocal()
    try:
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            raise HTTPException(status_code=404, detail=f"No artwork found with id: {artwork_id}")
        return FileResponse(artwork.filepath)
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


@app.post("/artworks/{artwork_id}/scan")
async def scan_artwork(artwork_id: int, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            raise HTTPException(status_code=404, detail=f"No artwork found with id: {artwork_id}")

        with open(artwork.filepath, "rb") as f:
            content = f.read()

        candidate_urls = get_candidate_urls(vision_client, content)

        background_tasks.add_task(run_scan, artwork_id, candidate_urls, artwork.filepath, model, preprocess)

        return {"artwork_id": artwork_id, "status": "scan_started", "candidate_count": len(candidate_urls)}
    finally:
        db.close()


@app.get("/artworks/{artwork_id}/scan")
async def get_scan_results(artwork_id: int):
    db = SessionLocal()
    try:
        # Step 1: find the most recent time_scanned for each unique url
        latest_per_url = (
            db.query(
                SimilarArtwork.url,
                func.max(SimilarArtwork.time_scanned).label("latest_time")
            )
            .filter(SimilarArtwork.artwork_id == artwork_id)
            .group_by(SimilarArtwork.url)
            .subquery()
        )

        # Step 2: join back to get the full row matching that latest timestamp
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
                    "id": r.id,
                    "url": r.url,
                    "similarity_score": r.similarity_score,
                    "time_scanned": r.time_scanned.isoformat(),
                    "status": r.status,
                }
                for r in results
            ],
        }
    finally:
        db.close()


@app.patch("/matches/{match_id}")
async def update_match_status(match_id: int, status: str):
    if status not in ("new", "reviewed", "dismissed"):
        raise HTTPException(status_code=400, detail="Invalid status")
    db = SessionLocal()
    try:
        match = db.query(SimilarArtwork).filter(SimilarArtwork.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail=f"No match found with id: {match_id}")
        match.status = status
        db.commit()
        return {"id": match.id, "status": match.status}
    finally:
        db.close()


# @app.post("/compare")
# async def compare_images(file_a: UploadFile, file_b: UploadFile):
#     image_a = Image.open(BytesIO(await file_a.read()))
#     image_b = Image.open(BytesIO(await file_b.read()))

#     is_similar, similarity_score = similarity.compare_images(image_a, image_b, model, preprocess)

#     return {"is_similar": is_similar, "similarity_score": similarity_score}
