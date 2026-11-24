
from backend.authentication.pin_auth import (
    create_customer_pin,
    authenticate_pin
)

# Customer ID 2 belongs to Arjun Kumar
customer_id = 2

# Create a 4-digit ATM PIN
result = create_customer_pin(customer_id, "2580")
print("PIN creation:", result)

# Test correct PIN
result = authenticate_pin(customer_id, "2580")
print("Correct PIN:", result)

# Test incorrect PIN
result = authenticate_pin(customer_id, "1234")
print("Wrong PIN:", result)
