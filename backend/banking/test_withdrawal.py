from backend.banking.withdrawal import withdraw_money

print("\nTEST: NON-EXISTING ACCOUNT")

result = withdraw_money(
    customer_id="1234567890",
    account_number="807596612992",
    amount=1000
)

print("Result:", result)