
from backend.authentication.register import hash_password, verify_password

# Registration
password = "Bank@12345"

stored_hash = hash_password(password)

print("Password hashed successfully!")

# Login with correct password
result1 = verify_password("Bank@12345", stored_hash)

print("Correct password:", result1)

# Login with incorrect password
result2 = verify_password("WrongPassword", stored_hash)

print("Wrong password:", result2)