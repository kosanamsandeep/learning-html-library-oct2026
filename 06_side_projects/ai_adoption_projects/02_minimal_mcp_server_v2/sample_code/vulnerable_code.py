"""
SAMPLE: Vulnerable Python Code
────────────────────────────────
This file has deliberate issues that the MCP tools + LangGraph agent
will detect during the code review demo.

Issues seeded:
  1. BARE EXCEPT clause (line 30)  ── hides all errors
  2. PICKLE import (line 3)        ── unsafe deserialization
  3. EVAL usage (line 37)          ── code injection risk
  4. Wrong naming conventions      ── class snake_case, func PascalCase
  5. Line too long (line 46)       ── exceeds 100 chars
  6. Trailing whitespace           ── see line 15
"""
import pickle
import json


class user_data_handler:
    """Violation: class name should be PascalCase (UserDataHandler)."""

    def __init__(self, username):
        self.username = username
        self.cache = {}

    def SaveToCache(self, key, value):
        """Violation: function name should be snake_case (save_to_cache).

        Also uses a bare except — hides ALL errors silently.
        """
        try:
            self.cache[key] = value
        except:
            # BARE except — catches MemoryError, KeyboardInterrupt, everything
            pass

    def LoadConfig(self, config_str):
        """Violation: function name should be snake_case (load_config).

        Uses eval() on a string — code injection risk.
        """
        try:
            return eval(config_str)  # DANGEROUS: eval with arbitrary string
        except:
            return {}

    def SaveSession(self, data):
        """Uses pickle for serialization — unsafe with untrusted data."""
        with open(f"{self.username}_session.pkl", "wb") as f:
            pickle.dump(data, f)


def process_transaction(amount, currency, user_id):
    """A well-formed function to show some passing checks.

    This function is correctly structured (snake_case, proper error handling).
    The long docstring and the print statement below are the only issues.
    """
    if amount <= 0:
        raise ValueError("Transaction amount must be positive")

    # This line is over 100 characters to trigger a style warning — it exceeds
    # our maximum allowed line length of one hundred characters
    print(f"Processing transaction: {amount} {currency} for user {user_id} via secure gateway with full audit trail")

    return {
        "status": "completed",
        "transaction_id": f"TXN-{user_id}-{amount}",
        "currency": currency
    }


def get_user_profile(user_id):
    """Simple data retrieval — no issues here."""
    return json.dumps({"id": user_id, "name": "Jane Doe", "role": "admin"})
