"""
=============================================================================
PROJECT 2: BANKING SYSTEM
=============================================================================
FILE: models/account.py
PURPOSE: Base Account class - the PARENT that all account types inherit from

WHAT YOU LEARN HERE:
- INHERITANCE: Creating specialized versions of a general concept
- BASE CLASS: The "template" that child classes extend
- The IS-A relationship: SavingsAccount IS-A Account

WHY INHERITANCE?
- All accounts share: owner, balance, deposit(), withdraw()
- But each type has SPECIAL behavior (interest, overdraft, etc.)
- Without inheritance: copy-paste the same code in every account type
- With inheritance: write common code ONCE, specialize as needed

REAL WORLD ANALOGY:
- "Vehicle" is a base class
- "Car", "Truck", "Motorcycle" are specialized children
- All vehicles have wheels and can move, but each moves differently
=============================================================================
"""

from datetime import datetime


class Account:
    """
    Base class for all bank accounts.

    This is ABSTRACT in spirit - you shouldn't create a plain Account,
    but rather a SavingsAccount or CheckingAccount.

    WHAT'S INHERITED BY CHILDREN:
    - All attributes (account_number, owner_name, _balance)
    - All methods (deposit, get_balance, get_transaction_history)
    - Children can OVERRIDE methods to customize behavior
    """

    def __init__(
        self, account_number: str, owner_name: str, initial_balance: float = 0.0
    ) -> None:
        """
        Initialize base account.

        WHY IS THIS IN THE BASE CLASS?
        - Every account needs these fields
        - By putting it here, SavingsAccount and CheckingAccount get it for FREE
        - DRY principle: Don't Repeat Yourself
        """
        self.account_number: str = account_number
        self.owner_name: str = owner_name

        # Protected attribute (single underscore = "use carefully")
        self._balance: float = initial_balance

        # Transaction history - every account needs this
        self._transactions: list[dict] = []

        # Record the initial deposit if any
        if initial_balance > 0:
            self._record_transaction("INITIAL_DEPOSIT", initial_balance)

    def deposit(self, amount: float) -> bool:
        """
        Add money to the account.

        WHY NOT OVERRIDE THIS IN CHILDREN?
        - Depositing works the same way for ALL accounts
        - Only withdraw behavior differs between account types
        - This is the Template Method pattern in miniature
        """
        if amount <= 0:
            return False  # Can't deposit negative/zero amount

        self._balance += amount
        self._record_transaction("DEPOSIT", amount)
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Remove money from the account.

        THIS METHOD IS DESIGNED TO BE OVERRIDDEN!
        - Base behavior: simple "do you have enough?" check
        - SavingsAccount: might add withdrawal limits
        - CheckingAccount: might allow overdraft

        This is POLYMORPHISM: same method name, different behavior
        depending on which TYPE of account you're using.
        """
        if amount <= 0:
            return False

        if amount > self._balance:
            return False  # Insufficient funds

        self._balance -= amount
        self._record_transaction("WITHDRAWAL", -amount)
        return True

    def get_balance(self) -> float:
        """Return current balance. Read-only access to protected data."""
        return self._balance

    def _record_transaction(self, transaction_type: str, amount: float) -> None:
        """
        Record a transaction in history.

        WHY PROTECTED (single underscore)?
        - Children need access (to record their special transactions)
        - But external code shouldn't call this directly
        - It's an INTERNAL mechanism shared across the family
        """
        self._transactions.append(
            {
                "type": transaction_type,
                "amount": amount,
                "balance_after": self._balance,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_transaction_history(self) -> list[dict]:
        """Get a copy of transaction history (defensive copy)."""
        return self._transactions.copy()

    def get_account_type(self) -> str:
        """
        Return the type of account.

        POLYMORPHISM: Each child overrides this to return its own type.
        This is how you can ask "what kind of account is this?" without
        needing isinstance() checks everywhere.
        """
        return "BASE_ACCOUNT"

    def __str__(self) -> str:
        """Perform the str step used by this project."""
        return (
            f"{self.get_account_type()}("
            f"number={self.account_number}, "
            f"owner={self.owner_name}, "
            f"balance=${self._balance:.2f})"
        )
