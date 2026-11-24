from backend.banking.deposit import deposit_money

print("\nTEST 2: Blocked account")

result = deposit_money(
    customer_id=2,
    account_number="807596612992",
    amount=1000
)

print("Result:", result)