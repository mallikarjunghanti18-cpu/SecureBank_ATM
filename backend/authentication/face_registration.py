import os
import json

from dotenv import load_dotenv
from cryptography.fernet import Fernet
from deepface import DeepFace

from backend.database.connection import get_db_connection


# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

encryption_key = os.getenv("FACE_ENCRYPTION_KEY")

if not encryption_key:
    raise ValueError("FACE_ENCRYPTION_KEY is missing from .env file")

fernet = Fernet(encryption_key.encode())


# ==========================================
# GENERATE FACE EMBEDDING
# ==========================================

def generate_face_embedding(image_path):

    try:

        result = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=True
        )

        embedding = result[0]["embedding"]

        return embedding

    except Exception as error:

        print("Face detection failed:", error)

        return None


# ==========================================
# ENCRYPT FACE EMBEDDING
# ==========================================

def encrypt_embedding(embedding):

    embedding_json = json.dumps(embedding).encode()

    encrypted_data = fernet.encrypt(embedding_json)

    return encrypted_data


# ==========================================
# REGISTER CUSTOMER FACE
# ==========================================

def register_customer_face(email, image_path, consent):

    # Step 1: Check consent
    if consent is not True:

        return "Face registration requires customer consent"

    # Step 2: Database connection
    connection = get_db_connection()

    if connection is None:

        return "Database connection failed"

    cursor = connection.cursor()

    try:

        # Step 3: Find customer
        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE email = %s
            """,
            (email,)
        )

        customer = cursor.fetchone()

        if customer is None:

            return "Customer not found"

        customer_id = customer[0]

        # Step 4: Check existing face registration
        cursor.execute(
            """
            SELECT customer_id
            FROM customer_faces
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        existing_face = cursor.fetchone()

        if existing_face is not None:

            return "Face is already registered for this customer"

        # Step 5: Generate face embedding
        embedding = generate_face_embedding(image_path)

        if embedding is None:

            return "Face registration failed: No valid face detected"

        # Step 6: Encrypt embedding
        encrypted_embedding = encrypt_embedding(embedding)

        # Step 7: Store encrypted embedding
        cursor.execute(
            """
            INSERT INTO customer_faces
            (customer_id, face_embedding_encrypted, consent_given)
            VALUES (%s, %s, %s)
            """,
            (customer_id, encrypted_embedding, True)
        )

        # Step 8: Commit
        connection.commit()

        return "Face registered and encrypted successfully"

    except Exception as error:

        connection.rollback()

        return f"Face registration failed: {error}"

    finally:

        cursor.close()
        connection.close()