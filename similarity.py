#similarity.py

import imagehash
from PIL import Image
import torch
import torch.nn.functional as F
import open_clip
from pathlib import Path
import numpy

PHASH_SIMILARITY_THRESHOLD = 20  # lower = more similar
CLIP_SIMILARITY_THRESHOLD = 0.80  # higher = more similar

TEST_IMAGES_PATH = Path("test_images")
ORIGINAL_PATH = TEST_IMAGES_PATH / "original.png"


def phash_distance(image_a: Image.Image, image_b: Image.Image) -> int:
    hash_a = imagehash.phash(_to_rgb(image_a))
    hash_b = imagehash.phash(_to_rgb(image_b))
    return hash_a - hash_b


def load_clip_model():
    print("LOADING CLIP MODEL...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    model.eval()
    return model, preprocess


def get_clip_embedding(model, preprocess, image: Image.Image):
    image_input = preprocess(_to_rgb(image)).unsqueeze(0)
    with torch.no_grad():
        embedding = model.encode_image(image_input)
    return embedding


def clip_cosine_similarity_from_embeddings(embedding_a, embedding_b) -> float:
    # accepts numpy arrays OR tensors, in any shape - normalizes both before comparing
    a = torch.as_tensor(embedding_a).flatten().unsqueeze(0)
    b = torch.as_tensor(embedding_b).flatten().unsqueeze(0)
    return F.cosine_similarity(a, b).item()


def clip_cosine_similarity_from_images(model, preprocess, image_a, image_b) -> float:
    emb_a = get_clip_embedding(model, preprocess, image_a)
    emb_b = get_clip_embedding(model, preprocess, image_b)
    return clip_cosine_similarity_from_embeddings(emb_a, emb_b)


def compare_images(image_a: Image.Image, image_b: Image.Image, model, preprocess) -> tuple[bool, int]:
    phash_dist = phash_distance(image_a, image_b)
    clip_sim = clip_cosine_similarity_from_images(model, preprocess, image_a, image_b)

    is_similar = bool(phash_dist <= PHASH_SIMILARITY_THRESHOLD or clip_sim >= CLIP_SIMILARITY_THRESHOLD)
    similarity_score = int(clip_sim * 100)

    print(f"  Perceptual hash distance: {phash_dist}")
    print(f"  CLIP cosine similarity:   {clip_sim:.4f}")
    print(f"  Is similar: {is_similar} (score: {similarity_score})")
    return is_similar, similarity_score


def compare_test_images():
    model, preprocess = load_clip_model()
    original = Image.open(ORIGINAL_PATH)

    for path in TEST_IMAGES_PATH.iterdir():
        if path.name == "original.png":
            continue
        print(f"\n{ORIGINAL_PATH} vs {path}:")
        candidate = Image.open(path)
        compare_images(original, candidate, model, preprocess)


def embedding_to_bytes(embedding_tensor) -> bytes:
    return embedding_tensor.detach().numpy().astype(numpy.float32).tobytes()


def bytes_to_embedding(data: bytes):
    return numpy.frombuffer(data, dtype=numpy.float32)


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


if __name__ == "__main__":
    compare_test_images()