import mysql.connector

def get_db_connection():
    try:
        connection=mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mallikarjun@07",
        database="securebank"
    )
        print("Database connection successful")
        return connection

    except mysql.connector.Error as error:
        print("Database connection failed:", error)
        return None



