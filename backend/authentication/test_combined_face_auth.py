from backend.authentication.combined_face_auth import authenticate_customer

email = "Arjun@gmail.com"

success, message = authenticate_customer(email, captured_frame=None)

print("\nFinal Authentication Result:", success)
print("Message:", message)