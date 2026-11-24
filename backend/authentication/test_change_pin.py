
from backend.authentication.pin_auth import (
    change_customer_pin,
    authenticate_pin
)

customer_id = 2

# Test 1: Change PIN using correct current PIN
result = change_customer_pin(
    customer_id,
    "2580",
    "3691",
    "3691"
)
print("Correct current PIN:", result)

# Test 2: Verify new PIN
result = authenticate_pin(customer_id, "3691")
print("New PIN verification:", result)

# Test 3: Verify old PIN no longer works
result = authenticate_pin(customer_id, "2580")
print("Old PIN verification:", result)

# Test 4: Incorrect current PIN
result = change_customer_pin(
    customer_id,
    "1111",
    "4567",
    "4567"
)
print("Incorrect current PIN:", result)

# Test 5: PIN confirmation mismatch
result = change_customer_pin(
    customer_id,
    "3691",
    "5678",
    "8765"
)
print("Confirmation mismatch:", result)
