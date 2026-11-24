
from backend.authentication.face_auth import authenticate_face

email="Arjun@gmail.com"


# Use the same photograph used during registration
image_path = r"C:\Users\MALLIKARJUN\OneDrive\Pictures\Camera Roll\diff_face.jpg"

print("Starting face authentication...")

success, message = authenticate_face(
    email="Arjun@gmail.com",
    image_path=image_path
)

print("Authentication result:", success)
print("Message:", message)
