
from backend.database.connection import get_db_connection


def get_transaction_history(customer_id, account_number):
    """Retrieve transaction history for an account owned by the customer."""

    # Step 1: Connect to database
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    try:
        # Step 2: Retrieve only transactions belonging to the authorized customer
        cursor.execute(
            """
            SELECT
                t.transaction_reference,
                t.transaction_type,
                t.amount,
                t.balance_before,
                t.balance_after,
                t.description,
                t.transaction_status,
                t.created_at
            FROM transactions t
            JOIN accounts a
                ON t.account_id = a.account_id
            WHERE a.account_number = %s
            AND a.customer_id = %s
            ORDER BY t.created_at DESC
            """,
            (account_number, customer_id)
        )

        # Step 3: Fetch transaction records
        transactions = cursor.fetchall()

        # Step 4: Return transaction history
        return transactions

    except Exception as error:
        print("Transaction history error:", error)
        return "Failed to retrieve transaction history"

    finally:
        cursor.close()
        connection.close()
