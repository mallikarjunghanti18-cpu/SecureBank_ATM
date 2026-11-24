
import secrets
from decimal import Decimal, InvalidOperation

from backend.database.connection import get_db_connection


def generate_transaction_reference():
    """Generate a unique-looking transaction reference."""
    return "SB" + secrets.token_hex(10).upper()


def transfer_money(
    customer_id,
    sender_account_number,
    receiver_account_number,
    amount
):
    """Transfer money between accounts belonging to authorized customers."""

    # Step 1: Validate amount
    try:
        amount = Decimal(str(amount))

        if not amount.is_finite():
            return "Invalid transfer amount"

        if amount <= 0:
            return "Transfer amount must be greater than zero"

        if amount.as_tuple().exponent < -2:
            return "Amount cannot have more than 2 decimal places"

    except (InvalidOperation, ValueError, TypeError):
        return "Invalid transfer amount"

    # Step 2: Prevent transfer to the same account
    if sender_account_number == receiver_account_number:
        return "Cannot transfer money to the same account"

    # Step 3: Connect to database
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:

        # Step 4: Start transaction
        connection.start_transaction()

        # Step 5: Lock both accounts in a consistent order
        account_numbers = sorted(
            [sender_account_number, receiver_account_number]
        )

        cursor.execute(
            """
            SELECT
                account_id,
                customer_id,
                account_number,
                balance,
                account_status
            FROM accounts
            WHERE account_number IN (%s, %s)
            ORDER BY account_number
            FOR UPDATE
            """,
            tuple(account_numbers)
        )

        accounts = cursor.fetchall()

        # Step 6: Verify both accounts exist
        if len(accounts) != 2:
            connection.rollback()
            return "Sender or receiver account not found"

        # Step 7: Create account lookup dictionary
        account_map = {
            account["account_number"]: account
            for account in accounts
        }

        sender = account_map[sender_account_number]
        receiver = account_map[receiver_account_number]

        # Step 8: Verify sender account ownership
        if sender["customer_id"] != customer_id:
            connection.rollback()
            return "Unauthorized access to sender account"

        # Step 9: Verify both accounts are active
        if sender["account_status"] != "ACTIVE":
            connection.rollback()
            return "Sender account is not active"

        if receiver["account_status"] != "ACTIVE":
            connection.rollback()
            return "Receiver account is not active"

        # Step 10: Check sender balance
        sender_balance = Decimal(str(sender["balance"]))
        receiver_balance = Decimal(str(receiver["balance"]))

        if sender_balance < amount:
            connection.rollback()
            return "Insufficient balance"

        # Step 11: Calculate new balances
        sender_balance_after = sender_balance - amount
        receiver_balance_after = receiver_balance + amount

        # Step 12: Update sender balance
        cursor.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
            """,
            (sender_balance_after, sender["account_id"])
        )

        # Step 13: Update receiver balance
        cursor.execute(
            """
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
            """,
            (receiver_balance_after, receiver["account_id"])
        )

        # Step 14: Generate separate transaction references
        sender_transaction_reference = generate_transaction_reference()
        receiver_transaction_reference = generate_transaction_reference()

        # Step 15: Record sender transaction
        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_reference,
                account_id,
                transaction_type,
                amount,
                balance_before,
                balance_after,
                transaction_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                sender_transaction_reference,
                sender["account_id"],
                "TRANSFER_OUT",
                amount,
                sender_balance,
                sender_balance_after,
                "SUCCESS"
            )
        )

        # Step 16: Record receiver transaction
        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_reference,
                account_id,
                transaction_type,
                amount,
                balance_before,
                balance_after,
                transaction_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                receiver_transaction_reference,
                receiver["account_id"],
                "TRANSFER_IN",
                amount,
                receiver_balance,
                receiver_balance_after,
                "SUCCESS"
            )
        )

        # Step 17: Commit transaction
        connection.commit()

        # Step 18: Return success response
        return {
            "message": "Fund transfer successful",
            "sender_transaction_reference": sender_transaction_reference,
            "receiver_transaction_reference": receiver_transaction_reference,
            "sender_account": sender_account_number,
            "receiver_account": receiver_account_number,
            "amount_transferred": str(amount),
            "sender_balance_before": str(sender_balance),
            "sender_balance_after": str(sender_balance_after),
            "receiver_balance_before": str(receiver_balance),
            "receiver_balance_after": str(receiver_balance_after),
            "status": "SUCCESS"
        }

    except Exception as e:
        connection.rollback()
        print("Fund transfer error:", e)
        return "Fund transfer failed"

    finally:
        cursor.close()
        connection.close()
