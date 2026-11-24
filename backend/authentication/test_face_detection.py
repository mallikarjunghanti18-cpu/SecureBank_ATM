
from backend.authentication.face_registration import generate_face_embedding

image_path = r"C:\Users\MALLIKARJUN\OneDrive\Pictures\Camera Roll\test_face.jpg"

print("Starting face detection...")

embedding = generate_face_embedding(image_path)

if embedding is not None:
    print("Face detected successfully!")
    print("Embedding length:", len(embedding))
    print("First 5 values:", embedding[:5])
else:
    print("Face detection failed")
