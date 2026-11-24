from backend.banking.deposit import deposit_money

account_number = "807596612992"

test_amounts = [
    0,
    -100,
    "abc",
    100.123,
    "NaN",
    "Infinity"
]

for amount in test_amounts:
    print(f"\nTesting deposit amount: {amount}")
    result = deposit_money(account_number, amount)
    print("Result:", result)