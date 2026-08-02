#main.py

from io import BytesIO
from fastapi import FastAPI, UploadFile
from PIL import Image
from database import start_db, SessionLocal, Artwork

import compare

app = FastAPI()
model, preprocess = compare.load_clip_model()
start_db()


@app.post("/artworks")
async def register_artwork(user_id: str, file: UploadFile):
    image = Image.open(BytesIO(await file.read()))
    embedding = compare.get_clip_embedding(model, preprocess, image)
    embedding_bytes = compare.embedding_to_bytes(embedding)

    db = SessionLocal()
    artwork = Artwork(user_id=user_id, filename=file.filename, embedding=embedding_bytes)
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    db.close()

    return {"id": artwork.id, "filename": artwork.filename}


@app.post("/artworks/{artwork_id}/compare")
async def compare_with_artwork(artwork_id: int, file: UploadFile):
    db = SessionLocal()
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        db.close()
        return {"ERROR": f"No artwork found with id: {artwork_id}"}

    uploaded_image = Image.open(BytesIO(await file.read()))
    uploaded_embedding = compare.get_clip_embedding(model, preprocess, uploaded_image).detach().numpy()
    
    stored_embedding = compare.bytes_to_embedding(artwork.embedding)

    similarity_score = compare.clip_cosine_similarity_from_embeddings(uploaded_embedding, stored_embedding)
    is_similar = bool(similarity_score >= compare.CLIP_SIMILARITY_THRESHOLD)
    similarity_score = int(similarity_score * 100)

    return {"artwork_id": artwork_id, "artwork_filename": artwork.filename, "is_similar": is_similar, "similarity_score": similarity_score}


@app.post("/compare")
async def compare_images(file_a: UploadFile, file_b: UploadFile):
    image_a = Image.open(BytesIO(await file_a.read()))
    image_b = Image.open(BytesIO(await file_b.read()))

    is_similar, similarity_score = compare.compare_images(image_a, image_b, model, preprocess)

    return {"is_similar": is_similar, "similarity_score": similarity_score}