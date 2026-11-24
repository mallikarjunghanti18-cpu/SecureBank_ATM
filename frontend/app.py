import streamlit as st
import requests

# ==========================================================
# CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="SecureBank ATM",
    page_icon="🏦",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# ==========================================================
# SESSION STATE
# ==========================================================

if "token" not in st.session_state:
    st.session_state.token = None

if "customer_email" not in st.session_state:
    st.session_state.customer_email = None

if "account_data" not in st.session_state:
    st.session_state.account_data = None

if "account_number" not in st.session_state:
    st.session_state.account_number = None

if "show_register" not in st.session_state:
    st.session_state.show_register = False

if "face_registration_pending" not in st.session_state:
    st.session_state.face_registration_pending = False

if "face_registration_email" not in st.session_state:
    st.session_state.face_registration_email = ""

# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}

h1, h2, h3 {
    color: #60a5fa;
}

div.stButton > button {
    border-radius: 8px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# LOGIN PAGE
# ==========================================================

def login_page():

    st.title("🏦 SecureBank")
    st.subheader("🔐 Customer Login")

    email = st.text_input(
        "Email Address",
        key="login_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    if st.button("Login", key="login_submit"):

        if not email or not password:

            st.warning("Please enter your email and password.")

        else:

            try:

                response = requests.post(
                    f"{API_URL}/login",
                    params={
                        "email": email,
                        "password": password
                    },
                    timeout=15
                )

                result = response.json()

                if response.status_code == 200:

                    # Support direct or wrapped API response
                    data = result.get("data", result)

                    token = data.get("access_token")

                    if token:

                        st.session_state.token = token
                        st.session_state.customer_email = email
                        st.session_state.account_data = None
                        st.session_state.show_register = False

                        st.success("Login successful!")
                        st.rerun()

                    else:

                        st.error(
                            result.get("message", "Token not received from server.")
                        )

                else:

                    st.error(
                        result.get("detail", "Login failed. Check your credentials.")
                    )

            except requests.exceptions.RequestException:

                st.error("Unable to connect to SecureBank backend.")

            except Exception as e:

                st.error(f"Login error: {e}")

    st.markdown("---")

    st.write("Don't have an account?")

    if st.button(
        "📝 New Customer? Create Account",
        key="go_to_register"
    ):

        st.session_state.show_register = True
        st.rerun()

    st.markdown("---")
    st.subheader("🧑 Face Authentication Login")

    st.info("Login using live face verification and blink detection.")

    if st.button("📷 Login with Face", key="face_login_submit"):

        if not email:
            st.warning("Please enter your registered email address first.")

        else:
            try:
                with st.spinner("Starting live face authentication... Check the camera."):

                    response = requests.post(
                        f"{API_URL}/live-face-authentication",
                        data={"email": email},
                        timeout=180
                    )

                    result = response.json()

                if response.status_code == 200 and result.get("authenticated"):

                    token = result.get("access_token")

                    if token:

                        st.session_state.token = token
                        st.session_state.customer_email = email
                        st.session_state.account_data = None
                        st.session_state.show_register = False

                        st.success("Face authentication successful!")
                        st.rerun()

                    else:
                        st.error("Authentication succeeded, but no access token was received.")

                else:
                    st.error(
                        result.get("message", "Face authentication failed.")
                    )

            except requests.exceptions.Timeout:
                st.error("Face authentication timed out.")

            except requests.exceptions.RequestException:
                st.error("Unable to connect to SecureBank backend.")

            except Exception as e:
                st.error(f"Face login error: {e}")


# ==========================================================
# REGISTRATION PAGE
# ==========================================================

def register_page():

    st.title("🏦 SecureBank")
    st.subheader("📝 New Customer Registration")

    # --------------------------------
    # STEP 2: FACE REGISTRATION
    # --------------------------------
    if st.session_state.get("face_registration_pending"):

        pending_email = st.session_state.face_registration_email

        st.success("Bank account registration successful!")
        st.subheader("📸 Register Your Face")
        st.write("Register your face to enable secure live face login.")

        consent = st.checkbox(
            "I consent to face registration and biometric verification."
        )

        face_image = st.camera_input(
            "Capture your face",
            key="face_registration_camera"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button("Register Face", use_container_width=True):

                if not consent:
                    st.warning("Consent is required for face registration.")

                elif face_image is None:
                    st.warning("Please capture your face first.")

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/face-registration",
                            data={
                                "email": pending_email,
                                "consent": "true"
                            },
                            files={
                                "image": (
                                    "face.png",
                                    face_image.getvalue(),
                                    "image/png"
                                )
                            },
                            timeout=120
                        )

                        result = response.json()

                        if response.status_code == 200 and result.get("success"):

                            st.success("Face registered successfully!")

                            st.session_state.face_registration_pending = False
                            st.session_state.face_registration_email = ""

                            st.info("You can now log in using your password or face authentication.")

                            st.session_state.show_register = False
                            st.rerun()

                        else:
                            st.error(
                                result.get(
                                    "message",
                                    "Face registration failed."
                                )
                            )

                    except requests.exceptions.RequestException:
                        st.error("Unable to connect to SecureBank backend.")

        with col2:

            if st.button("Skip Face Registration", use_container_width=True):

                st.session_state.face_registration_pending = False
                st.session_state.face_registration_email = ""
                st.session_state.show_register = False

                st.info("You can register your face later.")
                st.rerun()

        return

    # --------------------------------
    # STEP 1: CUSTOMER REGISTRATION
    # --------------------------------

    full_name = st.text_input(
        "Full Name",
        key="register_full_name"
    )

    email = st.text_input(
        "Email Address",
        key="register_email"
    )

    phone = st.text_input(
        "Phone Number",
        key="register_phone"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="register_password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        key="register_confirm_password"
    )

    if st.button("Register", key="register_submit"):

        if not full_name or not email or not phone or not password:

            st.warning("Please fill in all fields.")

        elif password != confirm_password:

            st.error("Passwords do not match.")

        else:

            try:

                response = requests.post(
                    f"{API_URL}/register",
                    params={
                        "full_name": full_name,
                        "email": email,
                        "password": password,
                        "phone": phone
                    },
                    timeout=15
                )

                result = response.json()

                if response.status_code == 200:

                    st.session_state.face_registration_pending = True
                    st.session_state.face_registration_email = email

                    st.success("Account created successfully!")
                    st.rerun()

                else:

                    st.error(
                        result.get("detail", "Registration failed.")
                    )

            except requests.exceptions.RequestException:

                st.error("Unable to connect to SecureBank backend.")

            except Exception as e:

                st.error(f"Registration error: {e}")

    st.markdown("---")

    if st.button(
        "↩ Already have an account? Login",
        key="go_to_login"
    ):

        st.session_state.show_register = False
        st.rerun()
# ==========================================================
# FETCH ACCOUNT DETAILS
# ==========================================================

def fetch_account_details(account_number):

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    try:

        response = requests.get(
            f"{API_URL}/account-details",
            params={
                "account_number": account_number
            },
            headers=headers,
            timeout=15
        )

        result = response.json()

        if response.status_code == 200:

            st.session_state.account_data = result

            return True, result

        else:

            if response.status_code == 401:

                st.session_state.token = None
                st.session_state.customer_email = None
                st.session_state.account_data = None

                return False, "Session expired. Please log in again."

            return False, result.get("detail", "Failed to fetch account details.")

    except requests.exceptions.RequestException:

        return False, "Unable to connect to SecureBank backend."

    except Exception as e:

        return False, str(e)


# ==========================================================
# CUSTOMER DASHBOARD
# ==========================================================

def dashboard_page():

    st.title("🏦 SecureBank")

    st.success(
        f"Logged in as {st.session_state.customer_email}"
    )

    st.markdown("---")

    st.subheader("📊 Customer Dashboard")

    account_number = st.text_input(
        "Enter your account number",
        placeholder="Enter your bank account number",
        key="dashboard_account_number"
    )

    if st.button(
        "View Account Details",
        key="view_account_details"
    ):

        if not account_number:

            st.warning("Please enter your account number.")

        else:

            success, result = fetch_account_details(account_number)

            if success:

                st.success("Account details loaded successfully.")

            else:

                st.error(result)

                if st.session_state.token is None:
                    st.rerun()

    # ------------------------------------------------------
    # DISPLAY ACCOUNT INFORMATION
    # ------------------------------------------------------

    if st.session_state.account_data is not None:

        data = st.session_state.account_data

        # Validate response
        if not isinstance(data, dict):

            st.error("Unexpected account data format.")
            st.stop()

        # Extract account information
        account = data.get("data", data)

        if not isinstance(account, dict):

            st.error("Invalid account data received.")
            st.stop()

        # Balance
        try:

            balance = float(account.get("balance", 0))

        except (ValueError, TypeError):

            balance = 0.0

                # Account summary

        st.markdown("---")
        st.subheader("💳 Account Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="💰 Available Balance",
                value=f"₹ {balance:,.2f}"
            )

        with col2:
            st.metric(
                label="🏦 Account Type",
                value=account.get("account_type", "N/A")
            )

        with col3:
            st.metric(
                label="🟢 Account Status",
                value=account.get("account_status", "N/A")
            )

        st.caption("SecureBank | Digital Banking")
        
        # Full account information
        st.markdown("---")
        st.subheader("📋 Account Details")

        st.write(
            "**Account Number:**",
            account.get("account_number", "N/A")
        )

        st.write(
            "**Account Type:**",
            account.get("account_type", "N/A")
        )

        st.write(
            "**Account Status:**",
            account.get("account_status", "N/A")
        )

        st.write(
            "**Account Created:**",
            account.get("created_at", "N/A")
        )

        # Debit Card Management

        st.markdown("---")
        st.subheader("💳 Debit Card Management")

        with st.form("generate_card_form"):

            card_holder_name = st.text_input(
                "Card Holder Name"
            )

            card_pin = st.text_input(
                "Create 4-digit PIN",
                type="password",
                max_chars=4
            )

            generate_card_button = st.form_submit_button(
                "Generate Debit Card"
            )

        if generate_card_button:

            if not card_holder_name.strip():
                st.error("Please enter card holder name.")

            elif not card_pin.isdigit() or len(card_pin) != 4:
                st.error("PIN must be exactly 4 digits.")

            else:

                headers = {
                    "Authorization": f"Bearer {st.session_state.token}"
                }

                payload = {
                    "account_number": account_number,
                    "card_holder_name": card_holder_name,
                    "pin": card_pin
                }

                try:

                    response = requests.post(
                        f"{API_URL}/generate-card",
                        json=payload,
                        headers=headers
                    )

                    if response.status_code == 200:

                        result = response.json()["data"]

                        st.success(result["message"])

                        st.markdown("### 💳 Your Debit Card")

                        st.code(
                            result["card_number"],
                            language=None
                        )

                        st.write(
                            "Expiry Date:",
                            result["expiry_date"]
                        )

                        st.write(
                            "Card Status:",
                            result["card_status"]
                        )

                    else:

                        try:
                            error_message = response.json().get(
                                "detail",
                                "Card generation failed."
                            )
                        except ValueError:
                            error_message = "Card generation failed."

                        st.error(error_message)

                except requests.exceptions.RequestException:

                    st.error("Unable to connect to SecureBank server.")

                # View Existing Debit Card

        st.markdown("---")

        if st.button("👁️ View My Debit Card"):

            headers = {
                "Authorization": f"Bearer {st.session_state.token}"
            }

            try:
                response = requests.get(
                    f"{API_URL}/my-card",
                    params={"account_number": account_number},
                    headers=headers
                )

                if response.status_code == 200:

                    card = response.json()["data"]

                    st.markdown("### 💳 My Debit Card")

                    st.markdown(
                        f"""
                        <div style="
                            background: linear-gradient(135deg, #0f172a, #1e40af);
                            padding: 25px;
                            border-radius: 18px;
                            color: white;
                            width: 100%;
                        ">
                            <h3>🏦 SecureBank</h3>
                            <p style="font-size:24px; letter-spacing:3px;">
                                {card['card_number']}
                            </p>
                            <p><b>CARD HOLDER</b></p>
                            <p>{card['card_holder_name']}</p>
                            <p>VALID THRU: {card['expiry_date']}</p>
                            <p>STATUS: {card['card_status']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:
                    try:
                        error_message = response.json().get(
                            "detail",
                            "Unable to retrieve card."
                        )
                    except ValueError:
                        error_message = "Unable to retrieve card."

                    st.error(error_message)

            except requests.exceptions.RequestException:
                st.error("Unable to connect to SecureBank server.")

        st.markdown("---")
        st.subheader("🔐 Card Security Controls")

        card_action_password = st.text_input(
            "Enter your login password to manage your debit card",
            type="password",
            key="card_action_password"
        )

        col1, col2 = st.columns(2)

        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        with col1:
            if st.button("🔒 Block Card", use_container_width=True):

                if not card_action_password:
                    st.warning("Please enter your password.")

                else:
                    try:
                        response = requests.put(
                            f"{API_URL}/card-status",
                            json={
                                "account_number": account_number,
                                "new_status": "BLOCKED",
                                "password": card_action_password
                            },
                            headers=headers
                        )

                        if response.status_code == 200:
                            st.success("Debit card blocked successfully!")
                        else:
                            st.error(response.json().get("detail", "Failed to block card."))

                    except requests.exceptions.RequestException:
                        st.error("Unable to connect to SecureBank server.")

        with col2:
            if st.button("🔓 Unblock Card", use_container_width=True):

                if not card_action_password:
                    st.warning("Please enter your password.")

                else:
                    try:
                        response = requests.put(
                            f"{API_URL}/card-status",
                            json={
                                "account_number": account_number,
                                "new_status": "ACTIVE",
                                "password": card_action_password
                            },
                            headers=headers
                        )

                        if response.status_code == 200:
                            st.success("Debit card activated successfully!")
                        else:
                            st.error(response.json().get("detail", "Failed to activate card."))

                    except requests.exceptions.RequestException:
                        st.error("Unable to connect to SecureBank server.")

                     # ------------------------------------------------------
        # DEPOSIT SECTION
        # ------------------------------------------------------

        st.markdown("---")
        st.subheader("💰 Deposit Money")

        deposit_amount = st.number_input(
            "Enter deposit amount (₹)",
            min_value=0.0,
            step=500.0,
            key="deposit_amount"
        )

        if st.button("Deposit Money", key="deposit_button"):

            if deposit_amount <= 0:
                st.error("Enter a valid deposit amount.")

            else:
                headers = {
                    "Authorization": f"Bearer {st.session_state.token}"
                }

                params = {
                    "account_number": account.get("account_number"),
                    "amount": deposit_amount
                }

                try:
                    response = requests.post(
                        f"{API_URL}/deposit",
                        params=params,
                        headers=headers
                    )

                    result = response.json()

                    if response.status_code == 200:
                        deposit_result = result.get("data", result)
                        if (
                            isinstance(deposit_result, dict)
                            and deposit_result.get("status") == "SUCCESS"
                        ):
                            st.success("✅ Deposit successful!")
                            st.write(
                                "Transaction Reference:",
                                deposit_result.get("transaction_reference", "N/A")
                            )
                            st.write(
                                "Amount Deposited: ₹",
                                deposit_result.get("amount_deposited", deposit_amount)
                            )
                            st.write(
                                "Previous Balance: ₹",
                                deposit_result.get("balance_before", "N/A")
                            )
                            st.write(
                                "Updated Balance: ₹",
                                deposit_result.get("balance_after", "N/A")
                            )

                            fetch_account_details(account.get("account_number"))
                        else:
                            st.error(f"Deposit failed: {deposit_result}")

                    else:
                        st.error(result)

                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")


 # WITHDRAWAL SECTION
        # ------------------------------------------------------

        st.markdown("---")
        st.subheader("💸 Withdraw Money")

        withdrawal_amount = st.number_input(
            "Enter withdrawal amount (₹)",
            min_value=0.0,
            step=500.0,
            key="withdrawal_amount"
        )

        if st.button("Withdraw Money", key="withdraw_button"):

            if withdrawal_amount <= 0:

                st.warning("Enter a valid withdrawal amount.")

            else:

                headers = {
                    "Authorization": f"Bearer {st.session_state.token}"
                }

                params = {
                    "account_number": account.get("account_number"),
                    "amount": withdrawal_amount
                }

                try:

                    response = requests.post(
                        f"{API_URL}/withdraw",
                        params=params,
                        headers=headers
                    )

                    result = response.json()

                    if response.status_code == 200:

                        st.success("Withdrawal successful!")
                        st.json(result)

                        # Refresh account balance
                        fetch_account_details(
                            account.get("account_number")
                        )

                    else:

                        st.error(result)

                except requests.exceptions.RequestException as e:

                    st.error(f"Connection error: {e}")

            # =========================
            # FUND TRANSFER
            # =========================

        st.divider()
        st.subheader("🔄 Fund Transfer")

        receiver_account = st.text_input(
            "Receiver Account Number",
            key="receiver_account"
        )

        transfer_amount = st.number_input(
            "Transfer Amount (₹)",
            min_value=0.0,
            step=500.0,
            key="transfer_amount"
        )

        if st.button("Transfer Money", key="transfer_button"):

            if not receiver_account:
                st.warning("Please enter receiver account number.")

            elif receiver_account == account.get("account_number"):
                st.error("You cannot transfer money to your own account.")

            elif transfer_amount <= 0:
                st.warning("Enter a valid transfer amount.")

            else:
    
                        headers = {
                            "Authorization": f"Bearer {st.session_state.token}"
                        }
    
                        params = {
                            "from_account_number": account.get("account_number"),
                            "to_account_number": receiver_account,
                            "amount": transfer_amount
                        }
    
                        try:
    
                            response = requests.post(
                                f"{API_URL}/fund-transfer",
                                params=params,
                                headers=headers,
                                timeout=15
                            )
    
                            result = response.json()
    
                            transfer_result = result.get("data", result)
    
                            if response.status_code == 200:
    
                                if isinstance(transfer_result, dict) and transfer_result.get("status") == "SUCCESS":
    
                                    st.success("✅ Fund Transfer Successful!")
    
                                    st.write("Transaction Reference:", transfer_result.get("transaction_reference", "N/A"))
                                    st.write("Amount Transferred: ₹", transfer_result.get("amount_transferred", transfer_amount))
                                    st.write("Sender Balance Before: ₹", transfer_result.get("sender_balance_before", "N/A"))
                                    st.write("Sender Balance After: ₹", transfer_result.get("sender_balance_after", "N/A"))
    
                                    fetch_account_details(account.get("account_number"))
    
                                else:
                                    st.error(f"Transfer failed: {transfer_result}")
    
                            else:
                                st.error(f"Transfer failed: {result}")
    
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {e}")
    
                        except (ValueError, TypeError) as e:
                            st.error(f"Invalid server response: {e}")
    
                        except Exception as e:
                            st.error(f"Error during fund transfer: {e}")

        # ------------------------------------------------------
        # LOGOUT
        # ------------------------------------------------------

        st.markdown("---")

        if st.button(
            "🚪 Logout",
            key="logout_button"
        ):

            st.session_state.token = None
            st.session_state.customer_email = None
            st.session_state.account_data = None
            st.session_state.account_number = None
            st.session_state.show_register = False

            st.rerun()

        # =========================
        # TRANSACTION HISTORY
        # =========================

        st.divider()

        st.subheader("📜 Transaction History")

        if st.button("View Transaction History", key="history_button"):

            headers = {
                "Authorization": f"Bearer {st.session_state.token}"
            }

            params = {
                "account_number": account.get("account_number")
            }

            try:
                response = requests.get(
                    f"{API_URL}/transactions",
                    params=params,
                    headers=headers
                )

                result = response.json()
                transaction_data = result.get("data", result)

                if response.status_code == 200 and isinstance(transaction_data, list):

                    if transaction_data:

                        st.success("Transaction history loaded successfully!")

                        # Convert to DataFrame
                        import pandas as pd

                        df = pd.DataFrame(transaction_data)

                        # Transaction type filter
                        transaction_types = ["All"] + list(
                            df["transaction_type"].unique()
                        )

                        selected_type = st.selectbox(
                            "Filter by Transaction Type",
                            transaction_types,
                            key="transaction_filter"
                        )

                        if selected_type != "All":
                            df = df[df["transaction_type"] == selected_type]

                        # Summary
                        col1, col2, col3 = st.columns(3)

                        col1.metric("Transactions", len(df))

                        deposits = df[df["transaction_type"] == "DEPOSIT"]["amount"].sum()
                        withdrawals = df[df["transaction_type"] == "WITHDRAWAL"]["amount"].sum()

                        col2.metric("Total Deposits", f"₹ {deposits:,.2f}")
                        col3.metric("Total Withdrawals", f"₹ {withdrawals:,.2f}")

                        # Format amount
                        df["amount"] = df["amount"].apply(
                            lambda x: f"₹ {float(x):,.2f}"
                        )

                        # Format dates
                        if "created_at" in df.columns:
                            df["created_at"] = pd.to_datetime(
                                df["created_at"]
                            ).dt.strftime("%d-%m-%Y %I:%M %p")

                        # Format and display the transaction table.
                        df = df.rename(columns={
                            "transaction_reference": "Transaction ID",
                            "transaction_type": "Type",
                            "amount": "Amount (₹)",
                            "balance_before": "Balance Before (₹)",
                            "balance_after": "Balance After (₹)",
                            "description": "Description",
                            "status": "Status",
                            "created_at": "Date & Time"
                        })

                        df["Type"] = df["Type"].replace({
                            "DEPOSIT": "🟢 Deposit",
                            "WITHDRAWAL": "🔴 Withdrawal",
                            "TRANSFER_OUT": "🔵 Transfer Sent",
                            "TRANSFER_IN": "🟣 Transfer Received"
                        })

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True
                        )

                    else:
                        st.info("No transactions found.")

                else:
                    st.error(f"Failed to fetch transactions: {result}")

            except Exception as e:
                st.error(f"Error fetching transactions: {e}")
# ==========================================================
# MAIN APPLICATION ROUTING
# ==========================================================

if st.session_state.token:

    dashboard_page()

elif st.session_state.show_register:

    register_page()

else:

    login_page()