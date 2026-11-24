
import secrets

from backend.database.connection import get_db_connection


# 1. Generate a unique 12-digit account number
def generate_account_number():
    """Generate a random 12-digit account number."""

    return str(secrets.randbelow(900000000000) + 100000000000)


# 2. Create a new bank account
def create_account(customer_id, account_type, initial_deposit=0):
    """Create a bank account for an existing customer."""

    if account_type not in ("SAVINGS", "CURRENT"):
        return "Invalid account type"

    if initial_deposit < 0:
        return "Initial deposit cannot be negative"

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor()

    try:
        # Check whether the customer exists and is active
        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = %s
            AND account_status = 'ACTIVE'
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            return "Customer not found or blocked"

        # Generate a unique account number
        account_number = None

        for attempt in range(5):
            candidate = generate_account_number()

            cursor.execute(
                """
                SELECT account_id
                FROM accounts
                WHERE account_number = %s
                """,
                (candidate,)
            )

            if cursor.fetchone() is None:
                account_number = candidate
                break

        if account_number is None:
            return "Could not generate a unique account number"

        # Insert account into MySQL
        cursor.execute(
            """
            INSERT INTO accounts
            (customer_id, account_number, account_type, balance)
            VALUES (%s, %s, %s, %s)
            """,
            (customer_id, account_number, account_type, initial_deposit)
        )

        connection.commit()

        return {
            "message": "Bank account created successfully",
            "account_number": account_number,
            "account_type": account_type,
            "initial_balance": initial_deposit
        }

    except Exception as error:
        connection.rollback()
        return f"Account creation failed: {error}"

    finally:
        cursor.close()
        connection.close()


# 3. Retrieve account details and balance
def get_account_details(customer_id, account_number):
    """Retrieve account details belonging to a specific customer."""

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                account_number,
                account_type,
                balance,
                account_status,
                created_at
            FROM accounts
            WHERE customer_id = %s
            AND account_number = %s
            """,
            (customer_id, account_number)
        )

        account = cursor.fetchone()

        if account is None:
            return "Account not found or access denied"

        return account

    except Exception as error:
        return f"Unable to retrieve account details: {error}"

    finally:
        cursor.close()
        connection.close()
