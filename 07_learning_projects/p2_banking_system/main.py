"""
=============================================================================
PROJECT 2: BANKING SYSTEM
=============================================================================
FILE: main.py
PURPOSE: Demonstrate inheritance and polymorphism in action
=============================================================================
"""

from services.bank_service import BankService


def main() -> None:
    """Demonstrate the Banking System with inheritance and polymorphism."""

    bank = BankService()
    print("=" * 60)
    print("     BANKING SYSTEM - Inheritance & Polymorphism Demo")
    print("=" * 60)

    # =========================================================================
    # Create accounts of different types
    # =========================================================================
    print("\n🏦 Creating accounts...")

    savings = bank.create_savings_account(
        "SAV001", "Alice Johnson", 1000.0, interest_rate=0.05
    )
    checking = bank.create_checking_account(
        "CHK001", "Bob Smith", 500.0, overdraft_limit=300.0
    )

    print(f"  Created: {savings}")
    print(f"  Created: {checking}")

    # =========================================================================
    # Demonstrate POLYMORPHISM: same method, different behavior
    # =========================================================================
    print("\n💰 Demonstrating Polymorphism (same action, different rules):")
    print("-" * 60)

    # Both accounts try to withdraw more than their balance
    print("\n  Withdrawing $800 from Savings (balance: $1000):")
    result = bank.withdraw("SAV001", 800)
    print(f"    Result: {'✅ Success' if result else '❌ Failed'}")
    print(f"    Balance: ${savings.get_balance():.2f}")

    print(f"\n  Withdrawing $700 from Checking (balance: $500, overdraft: $300):")
    result = bank.withdraw("CHK001", 700)
    print(f"    Result: {'✅ Success' if result else '❌ Failed'}")
    print(f"    Balance: ${checking.get_balance():.2f}")
    print(f"    (Note: Overdraft fee charged! Balance went below $0)")

    # =========================================================================
    # Savings-specific: Interest
    # =========================================================================
    print("\n📈 Applying monthly interest to Savings:")
    interest = savings.apply_interest()
    print(f"  Interest earned: ${interest:.2f}")
    print(f"  New balance: ${savings.get_balance():.2f}")

    # =========================================================================
    # Savings-specific: Withdrawal limit
    # =========================================================================
    print("\n🔒 Testing Savings withdrawal limit (max 6/month):")
    savings.deposit(500)  # Add money to cover withdrawals
    for i in range(7):
        result = savings.withdraw(10)
        status = "✅" if result else "❌ BLOCKED (limit reached)"
        print(
            f"  Withdrawal #{i+1}: {status} | Remaining: {savings.get_remaining_withdrawals()}"
        )

    # =========================================================================
    # Transfer between accounts (uses polymorphism internally)
    # =========================================================================
    print("\n🔄 Transfer $50 from Checking to Savings:")
    checking.deposit(200)  # Add funds first
    result = bank.transfer("CHK001", "SAV001", 50)
    print(f"  Result: {'✅ Success' if result else '❌ Failed'}")
    print(f"  Checking balance: ${checking.get_balance():.2f}")
    print(f"  Savings balance: ${savings.get_balance():.2f}")

    # =========================================================================
    # Polymorphic iteration (treating all accounts the same)
    # =========================================================================
    print("\n📊 All Accounts Summary (polymorphic iteration):")
    print("-" * 60)
    for account in bank.get_all_accounts():
        # get_account_type() returns different values based on actual type!
        print(
            f"  [{account.get_account_type():8}] {account.owner_name:15} | Balance: ${account.get_balance():.2f}"
        )

    print(f"\n  Total bank deposits: ${bank.get_total_deposits():.2f}")
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
