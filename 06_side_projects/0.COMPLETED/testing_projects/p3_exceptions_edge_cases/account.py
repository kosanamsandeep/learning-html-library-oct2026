"""A bank account with overdraft protection. P3 uses this to teach exception testing."""

from __future__ import annotations

from dataclasses import dataclass, field


class BankError(Exception):
    """Base error for the bank domain."""


class InsufficientFundsError(BankError):
    pass


class InvalidAmountError(BankError):
    pass


class AccountFrozenError(BankError):
    pass


@dataclass
class BankAccount:
    owner: str
    balance: float = 0.0
    overdraft_limit: float = 0.0
    frozen: bool = False
    history: list[str] = field(default_factory=list)

    def deposit(self, amount: float) -> None:
        self._ensure_active()
        self._ensure_positive(amount)
        self.balance = round(self.balance + amount, 2)
        self.history.append(f"deposit {amount:.2f}")

    def withdraw(self, amount: float) -> None:
        self._ensure_active()
        self._ensure_positive(amount)
        if self.balance - amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"cannot withdraw {amount:.2f}; would exceed overdraft limit"
            )
        self.balance = round(self.balance - amount, 2)
        self.history.append(f"withdraw {amount:.2f}")

    def freeze(self) -> None:
        self.frozen = True
        self.history.append("frozen")

    def unfreeze(self) -> None:
        self.frozen = False
        self.history.append("unfrozen")

    def _ensure_active(self) -> None:
        if self.frozen:
            raise AccountFrozenError(f"account for {self.owner} is frozen")

    @staticmethod
    def _ensure_positive(amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError("amount must be greater than zero")
