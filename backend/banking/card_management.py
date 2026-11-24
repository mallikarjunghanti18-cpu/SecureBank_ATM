import secrets
from datetime import date
from dateutil.relativedelta import relativedelta
from argon2 import PasswordHasher

from backend.database.connection import get_db_connection

ph = PasswordHasher()


def generate_card_number():
    return "".join(str(secrets.randbelow(10)) for _ in range(16))


def generate_card_pin_hash(pin):
    return ph.hash(pin)


def generate_expiry_date():
    return date.today() + relativedelta(years=5)


def create_debit_card(customer_id, account_number, card_holder_name, pin):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Step 1: Verify account ownership and status
        cursor.execute(
            """
            SELECT account_number, customer_id, account_status
            FROM accounts
            WHERE account_number = %s AND customer_id = %s
            """,
            (account_number, customer_id)
        )

        account = cursor.fetchone()

        if not account:
            raise ValueError("Account not found or unauthorized.")

        if account["account_status"] != "ACTIVE":
            raise ValueError("Account is not active.")

        # Step 2: Check whether card already exists
        cursor.execute(
            """
            SELECT card_id
            FROM bank_cards
            WHERE account_number = %s
            """,
            (account_number,)
        )

        existing_card = cursor.fetchone()

        if existing_card:
            raise ValueError("A debit card already exists for this account.")

        # Step 3: Generate card details
        card_number = generate_card_number()
        pin_hash = generate_card_pin_hash(pin)
        expiry_date = generate_expiry_date()

        # Step 4: Store card details
        cursor.execute(
            """
            INSERT INTO bank_cards (
                customer_id,
                account_number,
                card_number,
                card_holder_name,
                card_pin_hash,
                expiry_date,
                card_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
            """,
            (
                customer_id,
                account_number,
                card_number,
            card_holder_name,
                pin_hash,
                expiry_date
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Debit card generated successfully.",
            "card_number": card_number,
            "expiry_date": expiry_date.strftime("%m/%Y"),
            "card_status": "ACTIVE"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def get_debit_card(customer_id, account_number):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT card_holder_name, card_number, expiry_date, card_status
            FROM bank_cards
            WHERE customer_id = %s AND account_number = %s
            """,
            (customer_id, account_number)
        )

        card = cursor.fetchone()

        if not card:
            raise ValueError("No debit card found for this account.")

        return {
            "card_holder_name": card["card_holder_name"],
            "card_number": "**** **** **** " + card["card_number"][-4:],
            "expiry_date": card["expiry_date"].strftime("%m/%Y"),
            "card_status": card["card_status"]
        }

    except Exception:
        raise

    finally:
        cursor.close()
        connection.close()

def update_card_status(customer_id, account_number, new_status):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Step 1: Validate status
        if new_status not in ["ACTIVE", "BLOCKED"]:
            raise ValueError("Invalid card status.")

        # Step 2: Find customer's card
        cursor.execute(
            """
            SELECT card_id, card_status, expiry_date
            FROM bank_cards
            WHERE customer_id = %s AND account_number = %s
            """,
            (customer_id, account_number)
        )

        card = cursor.fetchone()

        if not card:
            raise ValueError("Debit card not found.")

        # Step 3: Prevent expired card activation
        if card["expiry_date"] < date.today():
            raise ValueError("Card has expired and cannot be activated.")

        # Step 4: Check current status
        if card["card_status"] == new_status:
            raise ValueError(f"Card is already {new_status}.")

        # Step 5: Update card status
        cursor.execute(
            """
            UPDATE bank_cards
            SET card_status = %s
            WHERE card_id = %s
            """,
            (new_status, card["card_id"])
        )

        connection.commit()

        return {
            "success": True,
            "message": f"Card successfully {new_status.lower()}.",
            "card_status": new_status
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()