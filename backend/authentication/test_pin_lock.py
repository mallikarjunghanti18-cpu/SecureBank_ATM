
from backend.authentication.pin_auth import authenticate_pin
from backend.database.connection import get_db_connection

customer_id = 2

# Reset PIN attempts before testing
connection = get_db_connection()
cursor = connection.cursor()

cursor.execute(
    """
    UPDATE customer_pins
    SET failed_pin_attempts = 0,
        locked_until = NULL
    WHERE customer_id = %s
    """,
    (customer_id,)
)

connection.commit()
cursor.close()
connection.close()

# Test three incorrect PIN attempts
for attempt in range(1, 4):
    print(f"\nAttempt {attempt}:")
    result = authenticate_pin(customer_id, "1234")
    print(result)

# Try correct PIN after locking
print("\nFourth attempt with correct PIN:")
print(authenticate_pin(customer_id, "2580"))
