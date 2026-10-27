"""Tests focused on exceptions, edge cases, and state changes."""

import pytest

from account import (
    AccountFrozenError,
    BankAccount,
    InsufficientFundsError,
    InvalidAmountError,
)

# Happy path -----------------------------------------------------------------


def test_deposit_increases_balance(account):
    account.deposit(50)
    assert account.balance == 150.00


def test_withdraw_reduces_balance(account):
    account.withdraw(40)
    assert account.balance == 60.00


def test_history_records_every_movement(account):
    account.deposit(10)
    account.withdraw(5)
    assert account.history == ["deposit 10.00", "withdraw 5.00"]


# Edge cases -----------------------------------------------------------------


def test_can_withdraw_exact_balance(account):
    account.withdraw(100)
    assert account.balance == 0.00


def test_can_use_full_overdraft(account):
    account.withdraw(150)  # balance 100, overdraft 50 -> -50
    assert account.balance == -50.00


def test_overdraft_boundary_one_cent_too_far(account):
    with pytest.raises(InsufficientFundsError):
        account.withdraw(150.01)


# Error paths ----------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, -1, -0.01, -1000])
def test_deposit_rejects_non_positive(account, bad):
    with pytest.raises(InvalidAmountError):
        account.deposit(bad)


@pytest.mark.parametrize("bad", [0, -1, -0.01])
def test_withdraw_rejects_non_positive(account, bad):
    with pytest.raises(InvalidAmountError):
        account.withdraw(bad)


def test_withdraw_beyond_overdraft_raises(account):
    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(1000)
    # Inspect the exception payload, not just the type
    assert "overdraft" in str(exc_info.value).lower()


# State transitions ----------------------------------------------------------


def test_frozen_account_rejects_deposit(account):
    account.freeze()
    with pytest.raises(AccountFrozenError):
        account.deposit(10)


def test_frozen_account_rejects_withdraw(account):
    account.freeze()
    with pytest.raises(AccountFrozenError):
        account.withdraw(10)


def test_unfreeze_restores_operations(account):
    account.freeze()
    account.unfreeze()
    account.deposit(10)
    assert account.balance == 110.00


# Identity / construction ----------------------------------------------------


def test_default_account_has_no_overdraft():
    acct = BankAccount(owner="Solo")
    with pytest.raises(InsufficientFundsError):
        acct.withdraw(0.01)
