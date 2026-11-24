from backend.banking.transactions import get_transaction_history

print("\nTEST: NON-EXISTING ACCOUNT")

result = get_transaction_history(customer_id="1234567890", account_number="807596612992")

print("Result:", result)