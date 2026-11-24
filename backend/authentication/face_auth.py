
import json
import numpy as np

from backend.database.connection import get_db_connection
from backend.authentication.face_registration import fernet
from deepface import DeepFace


def authenticate_face(email, image_frame):

    # Step 1: Generate face embedding from the uploaded/live image
    try:
        result = DeepFace.represent(
            img_path=image_frame,
            model_name="Facenet512",
            detector_backend="opencv",
            enforce_detection=True
        )

        new_embedding = result[0]["embedding"]

    except Exception as error:
        print("Face detection failed:", error)
        return False, "Unable to detect face"

    # Step 2: Connect to database
    connection = get_db_connection()

    if connection is None:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:

        # Step 3: Find customer_id using email
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
            return False, "Customer not found"

        customer_id = customer[0]

        # Step 4: Retrieve registered face embedding
        cursor.execute(
            """
            SELECT face_embedding_encrypted, consent_given
            FROM customer_faces
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        record = cursor.fetchone()

        if record is None:
            return False, "Face not registered"

        encrypted_embedding, consent_given = record

        if not consent_given:
            return False, "Biometric consent not available"

        # Step 5: Decrypt registered embedding
        decrypted_data = fernet.decrypt(encrypted_embedding)

        stored_embedding = json.loads(
            decrypted_data.decode()
        )

        # Step 6: Convert embeddings into NumPy arrays
        new_vector = np.array(new_embedding)
        stored_vector = np.array(stored_embedding)

        # Step 7: Calculate cosine similarity
        denominator = (
            np.linalg.norm(new_vector) *
            np.linalg.norm(stored_vector)
        )

        if denominator == 0:
            return False, "Invalid face embedding"

        similarity = np.dot(
            new_vector,
            stored_vector
        ) / denominator

        print("Face similarity:", round(float(similarity), 4))

        # Step 8: Compare similarity score
        if similarity >= 0.70:
            return True, "Face authentication successful"

        return False, "Face does not match"

    except Exception as error:
        return False, f"Authentication failed: {error}"

    finally:
        cursor.close()
        connection.close()
