#storage.py

from google.cloud import storage

storage_client = storage.Client()
ARTWORKS_BUCKET = "artcheck-artworks" #TODO separate bucket name?

def upload_blob(file_bytes, blob_name):
    bucket = storage_client.bucket(ARTWORKS_BUCKET)
    blob = bucket.blob(blob_name)
    generation_match_precondition = 0

    blob.upload_from_string(file_bytes, if_generation_match=generation_match_precondition)

    print(f"File uploaded to {blob_name}.")


def read_blob(blob_name):
    bucket = storage_client.bucket(ARTWORKS_BUCKET)

    blob = bucket.blob(blob_name)
    contents = blob.download_as_bytes()

    return contents


def delete_blob(blob_name):
    bucket = storage_client.bucket(ARTWORKS_BUCKET)

    blob = bucket.blob(blob_name)
    blob.delete()