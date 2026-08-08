#main.py

import os
from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException
from PIL import Image
from database import start_db, SessionLocal, Artwork

import similarity


app = FastAPI()
model, preprocess = similarity.load_clip_model()

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
        print("FILEPATH HERE!!!!!: " + str(file_path))
        db.commit()

        return {"id": artwork.id, "filename": artwork.filename}
    
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


@app.post("/compare")
async def compare_images(file_a: UploadFile, file_b: UploadFile):
    image_a = Image.open(BytesIO(await file_a.read()))
    image_b = Image.open(BytesIO(await file_b.read()))

    is_similar, similarity_score = similarity.compare_images(image_a, image_b, model, preprocess)

    return {"is_similar": is_similar, "similarity_score": similarity_score}