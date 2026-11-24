
from backend.database.connection import get_db_connection

connection = get_db_connection()

if connection:
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM customers")

    customers = cursor.fetchall()

    print("\nCUSTOMER DETAILS")

    for customer in customers:
        print(customer)

    cursor.close()
    connection.close()
