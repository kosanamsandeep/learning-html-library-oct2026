import pytest

from account import BankAccount


@pytest.fixture
def account() -> BankAccount:
    return BankAccount(owner="Asha", balance=100.00, overdraft_limit=50.00)
