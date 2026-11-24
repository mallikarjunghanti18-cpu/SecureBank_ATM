import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from backend.database.connection import get_db_connection


# ==========================================================
# PASSWORD HASHING
# ==========================================================

password_hasher = PasswordHasher()


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password, hashed_password):
    try:
        return password_hasher.verify(hashed_password, password)

    except (VerifyMismatchError, VerificationError):
        return False


# ==========================================================
# ACCOUNT NUMBER GENERATION
# ==========================================================

def generate_account_number(cursor):

    while True:

        # Generate a 12-digit account number
        account_number = str(secrets.randbelow(900000000000) + 100000000000)

        cursor.execute(
            "SELECT account_number FROM accounts WHERE account_number = %s",
            (account_number,)
        )

        existing_account = cursor.fetchone()

        if not existing_account:
            return account_number


# ==========================================================
# CUSTOMER REGISTRATION
# ==========================================================

def register_customer(full_name, email, password, phone):

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor()

    try:

        # Step 1: Check duplicate email or phone
        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE email = %s OR phone = %s
            """,
            (email, phone)
        )

        existing_customer = cursor.fetchone()

        if existing_customer:
            return "Email or phone already registered"

        # Step 2: Hash password
        hashed_password = hash_password(password)

        # Step 3: Insert customer
        cursor.execute(
            """
            INSERT INTO customers
            (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, email, phone, hashed_password)
        )

        # Retrieve newly generated customer ID
        customer_id = cursor.lastrowid

        # Step 4: Generate unique account number
        account_number = generate_account_number(cursor)

        # Step 5: Create savings account
        cursor.execute(
            """
            INSERT INTO accounts
            (account_number, customer_id, account_type, balance, account_status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                account_number,
                customer_id,
                "SAVINGS",
                0.00,
                "ACTIVE"
            )
        )

        # Step 6: Commit both customer and account
        connection.commit()

        return {
            "message": "Customer registered successfully",
            "customer_id": customer_id,
            "account_number": account_number,
            "account_type": "SAVINGS",
            "initial_balance": 0.00
        }

    except Exception as error:

        connection.rollback()

        return f"Registration failed: {error}"

    finally:

        cursor.close()
        connection.close()