
from backend.authentication.face_registration import register_customer_face

# Test customer ID
email="Arjun@gmail.com"


# Test photograph
image_path = r"C:\Users\MALLIKARJUN\OneDrive\Pictures\Camera Roll\test_face.jpg"

# Customer consent
consent = True

print("Starting face registration...")

result = register_customer_face(
    email="Arjun@gmail.com",
    image_path=image_path,
    consent=consent
)

print(result)
