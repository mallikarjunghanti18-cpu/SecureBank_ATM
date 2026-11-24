from fastapi import FastAPI, HTTPException, UploadFile, File, Form 
import cv2
import numpy as np
import tempfile
import os

from pydantic import BaseModel

from backend.authentication.security import get_current_customer
from backend.banking import account
from backend.banking.account import get_account_details
from backend.banking.deposit import deposit_money
from fastapi import Depends
from backend.authentication.security import get_current_customer




app = FastAPI(
    title="SecureBank ATM API",
    description="Backend API for the SecureBank Advanced ATM Simulation",
    version="1.0.0"
)

class CardRequest(BaseModel):
    account_number: str
    card_holder_name: str
    pin: str

class CardStatusRequest(BaseModel):
    account_number: str
    new_status: str
    password: str



@app.get("/")
def home():
    return {
        "message": "SecureBank ATM API is running",
        "status": "success"
    }
@app.get("/auth-test")
def auth_test(customer: dict = Depends(get_current_customer)):
    return {
        "success": True,
        "message": "JWT authentication successful",
        "customer": customer
    }
@app.post("/register")
def register(full_name: str, email: str, password: str, phone: str):
    from backend.authentication.register import register_customer
    result = register_customer(full_name, email, password, phone)

    return {
        "data": result
    }


@app.post("/login")
def login(email: str, password: str):

    from backend.authentication.login import login_customer
    from backend.authentication.security import create_access_token
    from backend.database.connection import get_db_connection

    # Step 1: Verify customer credentials
    result = login_customer(email, password)

    if result != "Login successful":
        return {
            "success": False,
            "message": result
        }

    # Step 2: Retrieve customer ID
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Database connection failed"
        }

    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT customer_id FROM customers WHERE email = %s",
            (email,)
        )

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "message": "Customer not found"
            }

        customer_id = customer[0]

        # Step 3: Generate JWT token
        token = create_access_token(
            customer_id=customer_id,
            email=email
        )

        # Step 4: Return token
        return {
            "success": True,
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        cursor.close()
        connection.close()

@app.post("/verify_password")
def verify(email: str, password: str):
    from backend.authentication.register import verify_password
    result = verify_password(email, password)

    return {
        "data": result
    }

@app.post("/change-password")
def change_password(email: str, old_password: str, new_password: str):
    from backend.authentication.register import change_password
    result = change_password(email, old_password, new_password)

    return {
        "data": result
    }

@app.post("/face-registration")
async def face_registration(
    email: str = Form(...),
    consent: bool = Form(...),
    image: UploadFile = File(...)
):
    from backend.authentication.face_registration import register_customer_face

    # Check customer consent
    if consent is not True:
        return {
            "success": False,
            "message": "Face registration requires customer consent"
        }

    # Read uploaded image
    image_bytes = await image.read()

    if not image_bytes:
        return {
            "success": False,
            "message": "Uploaded image is empty"
        }

    # Validate image
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return {
            "success": False,
            "message": "Invalid image file"
        }

    # Save image temporarily for DeepFace
    suffix = ".png" if image.content_type == "image/png" else ".jpg"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        ) as temp_file:

            temp_path = temp_file.name
            temp_file.write(image_bytes)

        # Register face
        result = register_customer_face(
            email,
            temp_path,
            consent
        )

        return {
            "success": "registered" in str(result).lower(),
            "email": email,
            "message": result
        }

    except Exception as error:
        return {
            "success": False,
            "message": "Face registration failed"
        }

    finally:
        # Delete temporary image
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/face-authentication")
async def face_authentication(
    email: str = Form(...),
    face_image: UploadFile = File(...)
):
    from backend.authentication.face_auth import authenticate_face

    image_bytes = await face_image.read()

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)

    image_frame = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image_frame is None:
        return {
            "status": "failed",
            "message": "Invalid image uploaded"
        }

    result = authenticate_face(email, image_frame)

    return {
        "data": result
    }

@app.post("/live-face-authentication")
def live_face_authentication(email: str = Form(...)):

    from backend.authentication.combined_face_auth import authenticate_customer
    from backend.authentication.security import create_access_token
    from backend.database.connection import get_db_connection

    # Step 1: Perform live face authentication
    result, message = authenticate_customer(email)

    if not result:
        return {
            "authenticated": False,
            "message": message
        }

    # Step 2: Retrieve customer ID
    connection = get_db_connection()

    if connection is None:
        return {
            "authenticated": False,
            "message": "Database connection failed"
        }

    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT customer_id FROM customers WHERE email = %s",
            (email,)
        )

        customer = cursor.fetchone()

        if customer is None:
            return {
                "authenticated": False,
                "message": "Customer not found"
            }

        customer_id = customer[0]

        # Step 3: Generate JWT token
        token = create_access_token(
            customer_id=customer_id,
            email=email
        )

        # Step 4: Return token after successful face verification
        return {
            "authenticated": True,
            "message": message,
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        cursor.close()
        connection.close()



@app.get("/account-details")
def account_details(
    account_number: str,
    customer: dict = Depends(get_current_customer)
):
    customer_id = customer["customer_id"]

    result = get_account_details(customer_id, account_number)

    return {"data": result}

@app.post("/deposit")
def deposit(
    account_number: str,
    amount: float,
    customer: dict = Depends(get_current_customer)
):
    customer_id = customer["customer_id"]

    result = deposit_money(customer_id, account_number, amount)

    return {"data": result}

@app.post("/withdraw")
def withdraw(
    account_number: str,
    amount: float,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.withdrawal import withdraw_money

    customer_id = customer["customer_id"]

    result = withdraw_money(customer_id, account_number, amount)

    return {"data": result}


@app.post("/fund-transfer")
def fund_transfer(
    from_account_number: str,
    to_account_number: str,
    amount: float,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.fund_transfer import transfer_money

    customer_id = customer["customer_id"]

    result = transfer_money(
        customer_id,
        from_account_number,
        to_account_number,
        amount
    )

    return {"data": result}


@app.get("/transactions")
def transaction_history(
    account_number: str,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.transactions import get_transaction_history

    customer_id = customer["customer_id"]

    result = get_transaction_history(
        customer_id,
        account_number
    )

    return {"data": result}

@app.post("/generate-card")
def generate_card(
    request: CardRequest,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.card_management import create_debit_card

    customer_id = customer["customer_id"]

    try:
        result = create_debit_card(
            customer_id=customer_id,
            account_number=request.account_number,
            card_holder_name=request.card_holder_name,
            pin=request.pin
        )

        return {"data": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/my-card")
def my_card(
    account_number: str,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.card_management import get_debit_card

    customer_id = customer["customer_id"]

    try:
        result = get_debit_card(
            customer_id,
            account_number
        )

        return {"data": result}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/card-status")
def change_card_status(
    request: CardStatusRequest,
    customer: dict = Depends(get_current_customer)
):
    from backend.banking.card_management import update_card_status
    from backend.database.connection import get_db_connection
    from backend.authentication.register import verify_password

    customer_id = customer["customer_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch customer's stored password hash
        cursor.execute(
            """
            SELECT password_hash
            FROM customers
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Verify password
        if not verify_password(request.password, result["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect password. Card status not changed."
            )

    finally:
        cursor.close()
        connection.close()

    try:
        result = update_card_status(
            customer_id=customer_id,
            account_number=request.account_number,
            new_status=request.new_status
        )

        return {"data": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))