"""
=============================================================================
PROJECT 2: BANKING SYSTEM
=============================================================================
FILE: services/bank_service.py
PURPOSE: Business logic for managing multiple bank accounts

WHAT YOU LEARN HERE:
- The service works with the BASE TYPE (Account)
- It doesn't care if it's Savings or Checking - POLYMORPHISM!
- This is "programming to an interface, not an implementation"
=============================================================================
"""

from models.account import Account
from models.savings_account import SavingsAccount
from models.checking_account import CheckingAccount


class BankService:
    """
    Manages all bank accounts and operations.

    KEY DESIGN: This service works with Account (base type).
    It doesn't need special handling for each account type.
    When it calls account.withdraw(), polymorphism ensures the
    correct behavior runs automatically.
    """

    def __init__(self) -> None:
        # Store all accounts (regardless of type) in one collection
        # The KEY insight: dict value type is Account (base class)
        # But actual objects can be SavingsAccount or CheckingAccount
        """Initialize the object with the dependencies or starting values it needs."""
        self._accounts: dict[str, Account] = {}

    def create_savings_account(
        self,
        account_number: str,
        owner_name: str,
        initial_balance: float = 0.0,
        interest_rate: float = 0.04,
    ) -> SavingsAccount:
        """Create a new savings account."""
        if account_number in self._accounts:
            raise ValueError(f"Account {account_number} already exists")

        account = SavingsAccount(
            account_number=account_number,
            owner_name=owner_name,
            initial_balance=initial_balance,
            interest_rate=interest_rate,
        )
        self._accounts[account_number] = account
        return account

    def create_checking_account(
        self,
        account_number: str,
        owner_name: str,
        initial_balance: float = 0.0,
        overdraft_limit: float = 500.0,
    ) -> CheckingAccount:
        """Create a new checking account."""
        if account_number in self._accounts:
            raise ValueError(f"Account {account_number} already exists")

        account = CheckingAccount(
            account_number=account_number,
            owner_name=owner_name,
            initial_balance=initial_balance,
            overdraft_limit=overdraft_limit,
        )
        self._accounts[account_number] = account
        return account

    def get_account(self, account_number: str) -> Account | None:
        """Get any account by number (returns base type)."""
        return self._accounts.get(account_number)

    def deposit(self, account_number: str, amount: float) -> bool:
        """
        Deposit to any account.

        POLYMORPHISM NOTE:
        - We don't check account type here
        - deposit() works the same for all accounts (inherited from Account)
        """
        account = self._accounts.get(account_number)
        if account is None:
            raise ValueError(f"Account {account_number} not found")
        return account.deposit(amount)

    def withdraw(self, account_number: str, amount: float) -> bool:
        """
        Withdraw from any account.

        THIS IS WHERE POLYMORPHISM SHINES:
        - We call account.withdraw(amount) regardless of account type
        - If it's SavingsAccount → checks withdrawal limit
        - If it's CheckingAccount → allows overdraft
        - We don't need if/elif/else here!
        """
        account = self._accounts.get(account_number)
        if account is None:
            raise ValueError(f"Account {account_number} not found")
        return account.withdraw(amount)

    def transfer(self, from_account: str, to_account: str, amount: float) -> bool:
        """
        Transfer money between accounts.

        BUSINESS LOGIC: A transfer is just a withdrawal + deposit
        But we need to ensure atomicity (both succeed or neither does)
        """
        source = self._accounts.get(from_account)
        destination = self._accounts.get(to_account)

        if source is None:
            raise ValueError(f"Source account {from_account} not found")
        if destination is None:
            raise ValueError(f"Destination account {to_account} not found")

        # Try to withdraw from source
        if not source.withdraw(amount):
            return False  # Insufficient funds (or withdrawal limit reached)

        # Deposit to destination (always succeeds for valid amounts)
        destination.deposit(amount)
        return True

    def get_total_deposits(self) -> float:
        """Get total balance across all accounts."""
        return sum(acc.get_balance() for acc in self._accounts.values())

    def get_all_accounts(self) -> list[Account]:
        """Get all accounts."""
        return list(self._accounts.values())

    def get_accounts_by_type(self, account_type: str) -> list[Account]:
        """
        Get accounts filtered by type.

        USES POLYMORPHISM: get_account_type() returns different strings
        depending on the actual class.
        """
        return [
            acc
            for acc in self._accounts.values()
            if acc.get_account_type() == account_type
        ]
