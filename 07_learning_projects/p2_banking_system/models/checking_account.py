"""
=============================================================================
PROJECT 2: BANKING SYSTEM
=============================================================================
FILE: models/checking_account.py
PURPOSE: CheckingAccount - another CHILD of Account with DIFFERENT behavior

WHAT YOU LEARN HERE:
- ANOTHER EXAMPLE of inheritance and overriding
- DIFFERENT SPECIALIZATION: overdraft (can go negative!) vs withdrawal limits
- POLYMORPHISM: Same interface (withdraw), completely different rules

COMPARING SIBLINGS:
- SavingsAccount: Limits withdrawals, earns interest
- CheckingAccount: Allows overdraft (borrow from bank), charges fees
- Both ARE accounts, but behave VERY differently

THIS IS THE POWER OF POLYMORPHISM:
- You can write code that works with ANY Account
- The CORRECT behavior is selected automatically at runtime
- No if/else chains needed!
=============================================================================
"""

from .account import Account


class CheckingAccount(Account):
    """
    Checking account with overdraft facility.

    REAL-WORLD MODEL:
    - Checking accounts are for daily transactions
    - They can go NEGATIVE up to an overdraft limit
    - But being in overdraft costs a fee
    - No interest earned (that's savings accounts)
    """

    def __init__(
        self,
        account_number: str,
        owner_name: str,
        initial_balance: float = 0.0,
        overdraft_limit: float = 500.0,  # How far you can go negative
        overdraft_fee: float = 35.0,  # Fee charged when using overdraft
    ) -> None:
        """
        Initialize checking account with overdraft facility.

        DESIGN DECISION: Default overdraft of $500
        - Real banks set this based on credit score
        - We use a sensible default for simplicity
        - Can be customized per account
        """
        # Parent handles the common setup
        super().__init__(account_number, owner_name, initial_balance)

        # Checking-specific attributes
        self._overdraft_limit: float = overdraft_limit
        self._overdraft_fee: float = overdraft_fee
        self._total_overdraft_fees: float = 0.0  # Track total fees charged

    def withdraw(self, amount: float) -> bool:
        """
        OVERRIDE: Allow withdrawal up to balance + overdraft limit.

        POLYMORPHISM EXAMPLE:

            account: Account = CheckingAccount("C001", "Bob", 100)
            account.withdraw(200)  # Works! Uses overdraft!

            account: Account = SavingsAccount("S001", "Alice", 100)
            account.withdraw(200)  # Fails! Not enough balance!

        Same method call, different behavior. The TYPE of object determines behavior.

        OVERDRAFT LOGIC:
        - If amount <= balance: normal withdrawal (no fee)
        - If amount <= balance + overdraft_limit: allowed but charges fee
        - If amount > balance + overdraft_limit: rejected
        """
        if amount <= 0:
            return False

        # Calculate total available (balance + overdraft)
        total_available = self._balance + self._overdraft_limit

        if amount > total_available:
            return False  # Exceeds even overdraft limit

        # Check if we're going into overdraft (using more than balance)
        going_into_overdraft = amount > self._balance

        # Perform the withdrawal
        self._balance -= amount
        self._record_transaction("WITHDRAWAL", -amount)

        # Charge overdraft fee if applicable
        if going_into_overdraft:
            self._balance -= self._overdraft_fee
            self._total_overdraft_fees += self._overdraft_fee
            self._record_transaction("OVERDRAFT_FEE", -self._overdraft_fee)

        return True

    def get_overdraft_limit(self) -> float:
        """Get the overdraft limit."""
        return self._overdraft_limit

    def get_total_overdraft_fees(self) -> float:
        """Get total overdraft fees charged so far."""
        return self._total_overdraft_fees

    def is_overdrawn(self) -> bool:
        """Check if account is currently in overdraft (negative balance)."""
        return self._balance < 0

    def get_available_balance(self) -> float:
        """Get total available amount (balance + unused overdraft)."""
        return self._balance + self._overdraft_limit

    def get_account_type(self) -> str:
        """OVERRIDE: Identify this as a checking account."""
        return "CHECKING"
