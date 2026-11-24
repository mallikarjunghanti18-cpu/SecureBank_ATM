
import secrets
from decimal import Decimal, InvalidOperation

from backend.database.connection import get_db_connection


# Maximum daily withdrawal limit per account
DAILY_WITHDRAWAL_LIMIT = Decimal("25000.00")


def generate_transaction_reference():
    """Generate a unique transaction reference."""
    return "SB" + secrets.token_hex(10).upper()


def withdraw_money(customer_id, account_number, amount):
    """Withdraw money from an active bank account."""

    # Step 1: Validate withdrawal amount
    try:
        withdrawal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return "Invalid withdrawal amount"

    if not withdrawal_amount.is_finite():
        return "Invalid withdrawal amount"

    if withdrawal_amount <= 0:
        return "Withdrawal amount must be greater than zero"

    if withdrawal_amount.as_tuple().exponent < -2:
        return "Withdrawal amount cannot have more than 2 decimal places"

    # Step 2: Connect to database
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        # Step 3: Start database transaction
        connection.start_transaction()

        # Step 4: Find and lock account
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

        if account is None:
            connection.rollback()
            return "Account not found"

        if account["account_status"] != "ACTIVE":
            connection.rollback()
            return "Account is blocked"

        # Step 5: Calculate today's successful withdrawals
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_withdrawn
            FROM transactions
            WHERE account_id = %s
            AND transaction_type = 'WITHDRAWAL'
            AND transaction_status = 'SUCCESS'
            AND DATE(created_at) = CURDATE()
            """,
            (account["account_id"],)
        )

        withdrawal_data = cursor.fetchone()

        total_withdrawn_today = Decimal(
            str(withdrawal_data["total_withdrawn"])
        )

        # Step 6: Check daily withdrawal limit
        if (
            total_withdrawn_today + withdrawal_amount
            > DAILY_WITHDRAWAL_LIMIT
        ):
            remaining_limit = (
                DAILY_WITHDRAWAL_LIMIT - total_withdrawn_today
            )

            connection.rollback()

            return (
                "Daily withdrawal limit exceeded. "
                f"Remaining limit: Rs. {remaining_limit}"
            )

        # Step 7: Check available balance
        balance_before = Decimal(str(account["balance"]))

        if withdrawal_amount > balance_before:
            connection.rollback()
            return "Insufficient balance"

        # Step 8: Calculate remaining balance
        balance_after = balance_before - withdrawal_amount

        # Step 9: Update account balance
        cursor.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
            """,
            (balance_after, account["account_id"])
        )

        # Step 10: Generate transaction reference
        transaction_reference = generate_transaction_reference()

        # Step 11: Save transaction history
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
            VALUES (%s, %s, 'WITHDRAWAL', %s, %s, %s, %s, 'SUCCESS')
            """,
            (
                transaction_reference,
                account["account_id"],
                withdrawal_amount,
                balance_before,
                balance_after,
                "ATM cash withdrawal"
            )
        )

        # Step 12: Commit database transaction
        connection.commit()

        return {
            "message": "Withdrawal successful",
            "transaction_reference": transaction_reference,
            "account_number": account_number,
            "amount_withdrawn": withdrawal_amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "status": "SUCCESS"
        }

    except Exception as error:
        connection.rollback()
        return f"Withdrawal failed: {error}"

    finally:
        cursor.close()
        connection.close()
