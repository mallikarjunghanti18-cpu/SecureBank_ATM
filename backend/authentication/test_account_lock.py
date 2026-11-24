
from backend.authentication.login import login_customer
from backend.database.connection import get_db_connection

email = "arjun@gmail.com"

# Reset previous attempts for testing
connection = get_db_connection()
cursor = connection.cursor()

cursor.execute(
    """
    UPDATE customers
    SET failed_login_attempts = 0,
        locked_until = NULL
    WHERE email = %s
    """,
    (email,)
)

connection.commit()
cursor.close()
connection.close()

# Test three incorrect password attempts
for attempt in range(1, 4):
    print(f"\nAttempt {attempt}:")
    result = login_customer(email, "WrongPassword123")
    print(result)

# Try login once more after locking
print("\nFourth attempt:")
print(login_customer(email, "Arjun@12345"))
