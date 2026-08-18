# scan.py
from io import BytesIO
import requests
from PIL import Image
from google.cloud import vision

from database import SessionLocal, SimilarArtwork
import similarity


def get_candidate_urls(vision_client, image_bytes: bytes) -> list[str]:
    image = vision.Image(content=image_bytes)
    response = vision_client.web_detection(image=image)
    annotations = response.web_detection

    candidate_urls = set()
    for match in annotations.full_matching_images:
        candidate_urls.add(match.url)
    for match in annotations.partial_matching_images:
        candidate_urls.add(match.url)
    for match in annotations.visually_similar_images:
        candidate_urls.add(match.url)

    return list(candidate_urls)


def run_scan(artwork_id: int, candidate_urls: list[str], stored_image_path: str, model, preprocess):
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

            if not is_similar:
                continue

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