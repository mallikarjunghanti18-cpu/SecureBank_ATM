
from backend.banking.account import get_account_details

# Customer 3 tries to access Customer 2's account
customer_id = 3
account_number = "807596612992"

result = get_account_details(customer_id, account_number)

print("\nACCOUNT OWNERSHIP SECURITY TEST")
print(result)
