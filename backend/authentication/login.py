
from backend.database.connection import get_db_connection
from backend.authentication.register import verify_password


def login_customer(email, password):

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        # Start a database transaction
        connection.start_transaction()

        # Find customer and lock the row during login processing
        cursor.execute(
            """
            SELECT *,
                   CASE
                       WHEN locked_until > NOW() THEN 1
                       ELSE 0
                   END AS is_locked
            FROM customers
            WHERE email = %s
            FOR UPDATE
            """,
            (email,)
        )

        customer = cursor.fetchone()

        if customer is None:
            connection.rollback()
            return "Invalid email or password"

        # Check whether admin has blocked the account
        if customer["account_status"] != "ACTIVE":
            connection.rollback()
            return "Your account is blocked"

        # Check temporary account lock
        if customer["is_locked"]:
            connection.rollback()
            return "Account temporarily locked. Try again after 15 minutes."

        # Reset expired lock, if any
        if customer["locked_until"] is not None:
            cursor.execute(
                """
                UPDATE customers
                SET failed_login_attempts = 0,
                    locked_until = NULL
                WHERE customer_id = %s
                """,
                (customer["customer_id"],)
            )

        # Verify password
        if verify_password(password, customer["password_hash"]):

            cursor.execute(
                """
                UPDATE customers
                SET failed_login_attempts = 0,
                    locked_until = NULL
                WHERE customer_id = %s
                """,
                (customer["customer_id"],)
            )

            connection.commit()
            return "Login successful"

        # Incorrect password: increase failed attempts
        cursor.execute(
            """
            UPDATE customers
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE customer_id = %s
            """,
            (customer["customer_id"],)
        )

        # Get updated failed attempt count
        cursor.execute(
            """
            SELECT failed_login_attempts
            FROM customers
            WHERE customer_id = %s
            """,
            (customer["customer_id"],)
        )

        attempts = cursor.fetchone()["failed_login_attempts"]

        # Lock account after 3 failed attempts
        if attempts >= 3:

            cursor.execute(
                """
                UPDATE customers
                SET locked_until = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                WHERE customer_id = %s
                """,
                (customer["customer_id"],)
            )

            connection.commit()
            return "Account locked for 15 minutes after 3 failed attempts"

        connection.commit()

        return f"Invalid email or password. Attempts: {attempts}/3"

    except Exception:
        connection.rollback()
        return "Login could not be completed. Please try again."

    finally:
        cursor.close()
        connection.close()
