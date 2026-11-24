
from backend.authentication.register import register_customer

result = register_customer(
    full_name="Arjun Kumar",
    email="arjun@gmail.com",
    phone="9876501234",
    password="Arjun@12345"
)

print(result)
