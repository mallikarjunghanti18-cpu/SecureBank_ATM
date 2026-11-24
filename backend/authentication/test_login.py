
from backend.authentication.login import login_customer

# Test 1: Correct email and password
result1 = login_customer(
    "arjun@gmail.com",
    "Arjun@12345"
)

print("Correct credentials:", result1)


# Test 2: Incorrect password
result2 = login_customer(
    "arjun@gmail.com",
    "WrongPassword123"
)

print("Wrong password:", result2)


# Test 3: Incorrect email
result3 = login_customer(
    "unknown@gmail.com",
    "Arjun@12345"
)

print("Wrong email:", result3)
