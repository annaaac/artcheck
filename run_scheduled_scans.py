# run_scheduled_scans.py
from database import start_db, SessionLocal, Artwork
from google.cloud import vision
import similarity
from scan import get_candidate_urls, run_scan


MAX_SCANS_PER_RUN = 900  # stay under the 1000/month free tier with buffer for manual testing

def run_all_scheduled_scans():
    start_db()
    vision_client = vision.ImageAnnotatorClient()
    model, preprocess = similarity.load_clip_model()

    db = SessionLocal()
    try:
        artworks = db.query(Artwork).all()
        if len(artworks) > MAX_SCANS_PER_RUN:
            print(f"Warning: {len(artworks)} artworks exceeds MAX_SCANS_PER_RUN, truncating this run.")
            artworks = artworks[:MAX_SCANS_PER_RUN]

        print(f"Scanning {len(artworks)} artworks...")
        for artwork in artworks:
            try:
                with open(artwork.filepath, "rb") as f:
                    content = f.read()
                candidate_urls = get_candidate_urls(vision_client, content)
                run_scan(artwork.id, candidate_urls, artwork.filepath, model, preprocess)
                print(f"  Scanned artwork {artwork.id}: {len(candidate_urls)} candidates")
            except Exception as e:
                print(f"  Failed to scan artwork {artwork.id}: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_all_scheduled_scans()