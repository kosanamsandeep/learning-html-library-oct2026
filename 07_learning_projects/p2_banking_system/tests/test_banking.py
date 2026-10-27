"""
PROJECT 2: BANKING SYSTEM - Tests
"""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.savings_account import SavingsAccount
from models.checking_account import CheckingAccount
from services.bank_service import BankService


class TestSavingsAccount:
    """Represents TestSavingsAccount in this learning project."""
    def test_inheritance_deposit(self):
        """SavingsAccount inherits deposit() from Account."""
        acc = SavingsAccount("S001", "Alice", 100)
        assert acc.deposit(50) is True
        assert acc.get_balance() == 150

    def test_withdraw_within_limit(self):
        """Withdraw works within monthly limit."""
        acc = SavingsAccount("S001", "Alice", 1000)
        assert acc.withdraw(100) is True
        assert acc.get_balance() == 900

    def test_withdraw_exceeds_monthly_limit(self):
        """After 6 withdrawals, the 7th is blocked."""
        acc = SavingsAccount("S001", "Alice", 10000)
        for _ in range(6):
            assert acc.withdraw(10) is True
        assert acc.withdraw(10) is False  # 7th blocked!

    def test_apply_interest(self):
        """Interest is calculated correctly."""
        acc = SavingsAccount("S001", "Alice", 1200, interest_rate=0.12)
        interest = acc.apply_interest()
        # Monthly rate = 0.12/12 = 0.01, Interest = 1200 * 0.01 = 12
        assert interest == 12.0
        assert acc.get_balance() == 1212.0

    def test_account_type(self):
        """Polymorphism: get_account_type returns SAVINGS."""
        acc = SavingsAccount("S001", "Alice", 0)
        assert acc.get_account_type() == "SAVINGS"


class TestCheckingAccount:
    """Represents TestCheckingAccount in this learning project."""
    def test_normal_withdrawal(self):
        """Withdrawal within balance works normally."""
        acc = CheckingAccount("C001", "Bob", 500)
        assert acc.withdraw(200) is True
        assert acc.get_balance() == 300

    def test_overdraft_allowed(self):
        """Can withdraw more than balance if within overdraft limit."""
        acc = CheckingAccount("C001", "Bob", 100, overdraft_limit=200)
        assert acc.withdraw(250) is True  # 100 balance + 200 overdraft = 300 available
        assert acc.is_overdrawn() is True

    def test_overdraft_fee_charged(self):
        """Overdraft fee is charged when going negative."""
        acc = CheckingAccount("C001", "Bob", 100, overdraft_limit=500, overdraft_fee=35)
        acc.withdraw(150)  # Goes into overdraft
        # Balance = 100 - 150 - 35(fee) = -85
        assert acc.get_balance() == -85.0
        assert acc.get_total_overdraft_fees() == 35.0

    def test_overdraft_limit_exceeded(self):
        """Cannot withdraw beyond overdraft limit."""
        acc = CheckingAccount("C001", "Bob", 100, overdraft_limit=100)
        assert acc.withdraw(300) is False  # 100+100=200 available, can't take 300

    def test_account_type(self):
        """Polymorphism: get_account_type returns CHECKING."""
        acc = CheckingAccount("C001", "Bob", 0)
        assert acc.get_account_type() == "CHECKING"


class TestBankService:
    """Coordinates business logic and keeps the calling code focused on use cases instead of implementation details."""
    def test_transfer(self):
        """Transfer between accounts works."""
        bank = BankService()
        bank.create_savings_account("S001", "Alice", 1000)
        bank.create_checking_account("C001", "Bob", 500)

        result = bank.transfer("S001", "C001", 200)
        assert result is True
        assert bank.get_account("S001").get_balance() == 800
        assert bank.get_account("C001").get_balance() == 700

    def test_polymorphic_withdraw(self):
        """Bank service uses polymorphism for withdrawals."""
        bank = BankService()
        bank.create_savings_account("S001", "Alice", 100)
        bank.create_checking_account("C001", "Bob", 100, overdraft_limit=200)

        # Same amount, different results due to polymorphism
        bank.withdraw("S001", 150)  # Fails (insufficient funds)
        bank.withdraw("C001", 150)  # Succeeds (uses overdraft)

        assert bank.get_account("S001").get_balance() == 100  # Unchanged
        assert bank.get_account("C001").get_balance() < 0  # Overdrawn


if __name__ == "__main__":
    print("Running Savings Account tests...")
    t = TestSavingsAccount()
    t.test_inheritance_deposit()
    t.test_withdraw_within_limit()
    t.test_withdraw_exceeds_monthly_limit()
    t.test_apply_interest()
    t.test_account_type()
    print("✓ All Savings Account tests passed!\n")

    print("Running Checking Account tests...")
    t2 = TestCheckingAccount()
    t2.test_normal_withdrawal()
    t2.test_overdraft_allowed()
    t2.test_overdraft_fee_charged()
    t2.test_overdraft_limit_exceeded()
    t2.test_account_type()
    print("✓ All Checking Account tests passed!\n")

    print("Running Bank Service tests...")
    t3 = TestBankService()
    t3.test_transfer()
    t3.test_polymorphic_withdraw()
    print("✓ All Bank Service tests passed!\n")

    print("🎉 ALL TESTS PASSED!")
