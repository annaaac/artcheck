from google.cloud import vision

def test_web_detection(image_path: str):
    COUNT = 0
    print(image_path)
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.web_detection(image=image)
    annotations = response.web_detection

    print("=== Full matching images ===")
    for match in annotations.full_matching_images:
        print(match.url)
        COUNT += 1

    print("\n=== Partial matching images ===")
    for match in annotations.partial_matching_images:
        print(match.url)
        COUNT += 1

    print("\n=== Visually similar images ===")
    for match in annotations.visually_similar_images:
        print(match.url)
        COUNT += 1

    print("\n=== Pages with matching images ===")
    for page in annotations.pages_with_matching_images:
        print(page.url)
        COUNT += 1
    
    print(COUNT)


if __name__ == "__main__":
    test_web_detection("test_images/actualdrawing4.png")