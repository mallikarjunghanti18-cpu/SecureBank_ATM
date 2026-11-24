
import secrets
from decimal import Decimal, InvalidOperation

from backend.database.connection import get_db_connection


def generate_transaction_reference():
    """Generate a unique transaction reference."""

    return "SB" + secrets.token_hex(10).upper()


def deposit_money(customer_id, account_number, amount):
    """Deposit money into an active bank account."""

    # Validate deposit amount
    try:
        deposit_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return "Invalid deposit amount"

    if not deposit_amount.is_finite():
        return "Invalid deposit amount"

    if deposit_amount <= 0:
        return "Deposit amount must be greater than zero"

    if deposit_amount.as_tuple().exponent < -2:
        return "Deposit amount cannot have more than 2 decimal places"

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        # Start database transaction
        connection.start_transaction()

        # Find account belonging to customer and lock it
        cursor.execute(
            """
            SELECT account_id, balance, account_status
            FROM accounts
            WHERE account_number = %s
            AND customer_id = %s
            FOR UPDATE
            """,
            (account_number, customer_id)
        )

        account = cursor.fetchone()

        # Validate account
        if account is None:
            connection.rollback()
            return "Account not found or access denied"

        if account["account_status"] != "ACTIVE":
            connection.rollback()
            return "Account is blocked"

        # Calculate balance
        balance_before = Decimal(str(account["balance"]))
        balance_after = balance_before + deposit_amount

        # Update account balance
        cursor.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
            """,
            (balance_after, account["account_id"])
        )

        # Generate transaction reference
        transaction_reference = generate_transaction_reference()

        # Insert deposit transaction
        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_reference,
                account_id,
                transaction_type,
                amount,
                balance_before,
                balance_after,
                description,
                transaction_status
            )
            VALUES (%s, %s, 'DEPOSIT', %s, %s, %s, %s, 'SUCCESS')
            """,
            (
                transaction_reference,
                account["account_id"],
                deposit_amount,
                balance_before,
                balance_after,
                "Cash deposit"
            )
        )

        # Commit both changes
        connection.commit()

        return {
            "message": "Deposit successful",
            "transaction_reference": transaction_reference,
            "account_number": account_number,
            "amount_deposited": float(deposit_amount),
            "balance_before": float(balance_before),
            "balance_after": float(balance_after),
            "status": "SUCCESS"
        }

    except Exception as error:
        connection.rollback()
        return f"Deposit failed: {error}"

    finally:
        cursor.close()
        connection.close()