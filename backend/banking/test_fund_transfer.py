
from backend.banking.fund_transfer import transfer_money

test_amounts = [0, -500, "abc", 100.123, "NaN", "Infinity"]

for amount in test_amounts:
    print(f"\nTEST: INVALID AMOUNT - {amount}")

    result = transfer_money(
        sender_account_number="807596612992",
        receiver_account_number="496446135054",
        amount=amount
    )

    print("Result:", result)

    
