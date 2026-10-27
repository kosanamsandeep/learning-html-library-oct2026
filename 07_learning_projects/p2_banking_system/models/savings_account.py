"""
=============================================================================
PROJECT 2: BANKING SYSTEM
=============================================================================
FILE: models/savings_account.py
PURPOSE: SavingsAccount - a CHILD class that INHERITS from Account

WHAT YOU LEARN HERE:
- INHERITANCE IN ACTION: SavingsAccount IS-A Account
- METHOD OVERRIDING: Changing behavior of withdraw()
- super().__init__(): Calling the parent's constructor
- ADDING NEW FEATURES: interest_rate is unique to savings accounts

THE IS-A TEST:
- "Is a savings account an account?" → YES ✅ → Use inheritance
- "Is a savings account a checking account?" → NO ❌ → Don't inherit from each other

WHY NOT JUST MODIFY THE BASE ACCOUNT CLASS?
- Because checking accounts have DIFFERENT rules
- Base class = shared foundation
- Child classes = specialized behavior
- This is the Open/Closed Principle: open for extension, closed for modification
=============================================================================
"""

from .account import Account


class SavingsAccount(Account):
    """
    Savings account with interest and withdrawal limits.

    INHERITS FROM Account:
    - Gets account_number, owner_name, _balance for FREE
    - Gets deposit(), get_balance(), get_transaction_history() for FREE
    - OVERRIDES withdraw() to add withdrawal limit per month
    - ADDS new methods: apply_interest(), get_interest_rate()

    REAL-WORLD RULE:
    - Savings accounts earn interest but limit withdrawals
    - This encourages people to SAVE money
    """

    # CLASS VARIABLE - shared by ALL savings accounts
    # (Like a bank policy that applies to everyone)
    MAX_WITHDRAWALS_PER_MONTH: int = 6

    def __init__(
        self,
        account_number: str,
        owner_name: str,
        initial_balance: float = 0.0,
        interest_rate: float = 0.04,  # 4% annual interest by default
    ) -> None:
        """
        Initialize savings account.

        super().__init__() EXPLAINED:
        - Calls the PARENT (Account) constructor
        - Sets up account_number, owner_name, balance, transactions
        - Then we add savings-specific stuff (interest_rate, withdrawal_count)

        WHY CALL super()?
        - Without it: parent's __init__ never runs → no basic setup!
        - With it: parent handles the common stuff, we handle the special stuff
        - It's like saying "do the standard setup, PLUS these extras"
        """
        # STEP 1: Let parent set up the basics
        super().__init__(account_number, owner_name, initial_balance)

        # STEP 2: Set up savings-specific attributes
        self._interest_rate: float = interest_rate  # Annual rate (e.g., 0.04 = 4%)
        self._monthly_withdrawals: int = 0  # Track withdrawals this month

    def withdraw(self, amount: float) -> bool:
        """
        OVERRIDE: Withdraw with monthly limit check.

        THIS IS POLYMORPHISM IN ACTION:
        - The method has the SAME NAME as in Account
        - But the BEHAVIOR is different (adds withdrawal limit)
        - Code that works with any Account will automatically get
          the right behavior based on the actual object type

        Example of polymorphism:
            accounts = [savings_acc, checking_acc]
            for acc in accounts:
                acc.withdraw(100)  # Each behaves differently!
        """
        # SAVINGS-SPECIFIC RULE: Check withdrawal limit
        if self._monthly_withdrawals >= self.MAX_WITHDRAWALS_PER_MONTH:
            return False  # Too many withdrawals this month!

        # REUSE PARENT LOGIC: Call Account's withdraw for the actual withdrawal
        # This avoids duplicating the balance check and transaction recording
        success = super().withdraw(amount)

        if success:
            self._monthly_withdrawals += 1

        return success

    def apply_interest(self) -> float:
        """
        Apply monthly interest to the balance.

        THIS IS A NEW METHOD (not in Account):
        - Only savings accounts earn interest
        - Only checking accounts have overdraft
        - Each child adds its own special capabilities

        Monthly rate = Annual rate / 12
        """
        monthly_rate = self._interest_rate / 12
        interest_earned = self._balance * monthly_rate

        self._balance += interest_earned
        self._record_transaction("INTEREST", interest_earned)

        return interest_earned

    def reset_monthly_withdrawals(self) -> None:
        """Reset the withdrawal counter (called at start of new month)."""
        self._monthly_withdrawals = 0

    def get_interest_rate(self) -> float:
        """Get the annual interest rate."""
        return self._interest_rate

    def get_remaining_withdrawals(self) -> int:
        """How many withdrawals left this month?"""
        return max(0, self.MAX_WITHDRAWALS_PER_MONTH - self._monthly_withdrawals)

    def get_account_type(self) -> str:
        """OVERRIDE: Identify this as a savings account."""
        return "SAVINGS"
