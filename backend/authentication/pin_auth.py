
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from backend.database.connection import get_db_connection

pin_hasher = PasswordHasher()


def hash_pin(pin):
    if not pin.isdigit() or len(pin) != 4:
        raise ValueError("ATM PIN must contain exactly 4 digits")

    return pin_hasher.hash(pin)


def verify_pin(pin, stored_hash):
    try:
        return pin_hasher.verify(stored_hash, pin)

    except (VerifyMismatchError, VerificationError):
        return False


def create_customer_pin(customer_id, pin):

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor()

    try:
        pin_hash = hash_pin(pin)

        cursor.execute(
            """
            INSERT INTO customer_pins (customer_id, pin_hash)
            VALUES (%s, %s)
            """,
            (customer_id, pin_hash)
        )

        connection.commit()
        return "ATM PIN created successfully"

    except ValueError as error:
        connection.rollback()
        return str(error)

    except Exception as error:
        connection.rollback()
        return f"PIN creation failed: {error}"

    finally:
        cursor.close()
        connection.close()



def authenticate_pin(customer_id, pin):

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        connection.start_transaction()

        # Get PIN details and lock the database row
        cursor.execute(
            """
            SELECT *,
                   CASE
                       WHEN locked_until > NOW() THEN 1
                       ELSE 0
                   END AS is_locked
            FROM customer_pins
            WHERE customer_id = %s
            FOR UPDATE
            """,
            (customer_id,)
        )

        result = cursor.fetchone()

        if result is None:
            connection.rollback()
            return False

        # Check temporary PIN lock
        if result["is_locked"]:
            connection.rollback()
            return "ATM PIN locked. Try again after 15 minutes."

        # Verify entered PIN
        if verify_pin(pin, result["pin_hash"]):

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
            return True

        # Incorrect PIN
        cursor.execute(
            """
            UPDATE customer_pins
            SET failed_pin_attempts = failed_pin_attempts + 1
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        cursor.execute(
            """
            SELECT failed_pin_attempts
            FROM customer_pins
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        attempts = cursor.fetchone()["failed_pin_attempts"]

        if attempts >= 3:

            cursor.execute(
                """
                UPDATE customer_pins
                SET locked_until = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                WHERE customer_id = %s
                """,
                (customer_id,)
            )

            connection.commit()
            return "ATM PIN locked for 15 minutes after 3 failed attempts"

        connection.commit()

        return f"Incorrect PIN. Attempts: {attempts}/3"

    except Exception as error:
        connection.rollback()
        print("PIN authentication error:", error)
        return False

    finally:
        cursor.close()
        connection.close()


def change_customer_pin(customer_id, current_pin, new_pin, confirm_pin):

    # Check whether new PIN and confirmation match
    if new_pin != confirm_pin:
        return "New PIN and confirmation do not match"

    # Validate the new PIN
    try:
        hash_pin(new_pin)
    except ValueError as error:
        return str(error)

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        connection.start_transaction()

        # Retrieve and lock the customer's PIN record
        cursor.execute(
            """
            SELECT *,
                   CASE
                       WHEN locked_until > NOW() THEN 1
                       ELSE 0
                   END AS is_locked
            FROM customer_pins
            WHERE customer_id = %s
            FOR UPDATE
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            connection.rollback()
            return "ATM PIN not found"

        # Do not allow changes during an active PIN lock
        if customer["is_locked"]:
            connection.rollback()
            return "ATM PIN is locked. Try again after 15 minutes."

        # Verify current PIN
        if not verify_pin(current_pin, customer["pin_hash"]):
            connection.rollback()
            return "Current PIN is incorrect"

        # Prevent using the same PIN again
        if verify_pin(new_pin, customer["pin_hash"]):
            connection.rollback()
            return "New PIN must be different from current PIN"

        # Generate new PIN hash
        new_pin_hash = hash_pin(new_pin)

        # Update PIN in database
        cursor.execute(
            """
            UPDATE customer_pins
            SET pin_hash = %s,
                failed_pin_attempts = 0,
                locked_until = NULL,
                created_at = CURRENT_TIMESTAMP
            WHERE customer_id = %s
            """,
            (new_pin_hash, customer_id)
        )

        connection.commit()

        return "ATM PIN changed successfully"

    except Exception as error:
        connection.rollback()
        print("PIN change error:", error)
        return "PIN change failed"

    finally:
        cursor.close()
        connection.close()

