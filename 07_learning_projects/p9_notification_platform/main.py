"""
=============================================================================
PROJECT 9: NOTIFICATION PLATFORM - MAIN DEMO
=============================================================================
This demonstrates the FACTORY + STRATEGY pattern combination.

KEY LEARNING:
- Factory Pattern: Centralized object creation
- Strategy Pattern: Interchangeable algorithms at runtime
- Together: Factory CREATES, Strategy EXECUTES

RUN THIS FILE:
    cd projects/p9_notification_platform
    python main.py
=============================================================================
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from factories.notification_factory import NotificationFactory
from strategies.notification_strategy import (
    NotificationStrategy,
    Notification,
    NotificationResult,
)


def print_header(title: str) -> None:
    """Print a formatted header for demo sections."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result: NotificationResult) -> None:
    """Pretty-print a notification result."""
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    print(f"  {status} | ID: {result.notification_id} | Channel: {result.channel}")
    if result.message:
        label = "Info" if result.success else "Error"
        print(f"         {label}: {result.message}")


def demo_factory_pattern():
    """
    DEMO 1: Factory Pattern - Creating notifications without knowing internals.

    The Factory handles:
    - ID generation
    - Default values
    - Validation
    - Consistent structure
    """
    print_header("DEMO 1: Factory Pattern - Object Creation")

    print("\n  Using NotificationFactory to create notifications:")
    print("  (No need to know internal structure or ID format)")

    # Create different notification types using the factory
    email = NotificationFactory.create_email(
        recipient="developer@company.com",
        subject="Build Failed",
        body="CI pipeline #432 failed on main branch.",
        priority="URGENT",
    )
    print(f"\n  📧 Email: id={email.notification_id}, to={email.recipient}")
    print(f"     Subject: {email.subject}")

    sms = NotificationFactory.create_sms(
        phone_number="+1-555-0123", message="Your verification code is 847291"
    )
    print(f"\n  📱 SMS: id={sms.notification_id}, to={sms.recipient}")
    print(f"     Body: {sms.body}")

    push = NotificationFactory.create_push(
        device_token="device_abc123xyz",
        title="New Message",
        body="You have 3 unread messages",
        metadata={"badge_count": 3},
    )
    print(f"\n  🔔 Push: id={push.notification_id}, to={push.recipient}")
    print(f"     Title: {push.subject}, Metadata: {push.metadata}")

    slack = NotificationFactory.create_slack(
        channel="#engineering", message="Deployment v2.1.0 completed successfully!"
    )
    print(f"\n  💬 Slack: id={slack.notification_id}, to={slack.recipient}")
    print(f"     Message: {slack.body}")

    # Template-based creation
    print("\n  --- Template-Based Factory ---")
    welcome = NotificationFactory.create_from_template(
        channel="EMAIL",
        recipient="newuser@email.com",
        template_name="welcome",
        template_vars={
            "app_name": "DevPlatform",
            "user_name": "Alice",
            "feature": "dashboards",
        },
    )
    print(f"\n  📧 Template Email: {welcome.subject}")
    print(f"     Body: {welcome.body}")


def demo_strategy_pattern():
    """
    DEMO 2: Strategy Pattern - Same interface, different behaviors.

    The Strategy handles:
    - HOW to send (algorithm selection)
    - Channel-specific logic
    - Error handling per channel
    """
    print_header("DEMO 2: Strategy Pattern - Sending via Different Channels")

    # Create the service (it registers all strategies internally)
    service = NotificationService()

    print(f"\n  Available channels: {service.get_available_channels()}")
    print("\n  Sending notifications through different strategies:")

    # Each call uses a DIFFERENT strategy internally
    result1 = service.send_email(
        "admin@company.com", "Daily Report", "All systems operational. 99.9% uptime."
    )
    print_result(result1)

    result2 = service.send_sms("+1-555-9876", "Alert: CPU usage at 95%")
    print_result(result2)

    result3 = service.send_push(
        "device_xyz789", "Reminder", "Team standup in 15 minutes"
    )
    print_result(result3)

    result4 = service.send_slack("#devops", "🚀 Production deployment starting...")
    print_result(result4)


def demo_open_closed_principle():
    """
    DEMO 3: Open/Closed Principle - Adding new channels WITHOUT modifying existing code.

    This is the POWER of Strategy + Factory:
    - Define a new strategy class
    - Register it
    - Use it
    - ZERO changes to existing code!
    """
    print_header("DEMO 3: Open/Closed Principle - Adding a New Channel")

    # Create a brand new strategy that didn't exist before
    class WebhookStrategy(NotificationStrategy):
        """A new channel added WITHOUT changing any existing code!"""

        def send(self, notification: Notification) -> NotificationResult:
            # In production: HTTP POST to webhook URL
            """Perform the send step used by this project."""
            print(
                f"    [Webhook] POST to {notification.recipient}: {notification.body}"
            )
            return NotificationResult(
                notification_id=notification.notification_id,
                success=True,
                channel="WEBHOOK",
            )

        def get_channel_name(self) -> str:
            """Return the requested item or information if it exists."""
            return "WEBHOOK"

        def validate_recipient(self, recipient: str) -> bool:
            """Validate input and raise or return an error when it is not acceptable."""
            return recipient.startswith("http")

    # Register the new strategy
    service = NotificationService()
    service.register_strategy("WEBHOOK", WebhookStrategy())

    print(
        f"\n  Available channels (after adding WEBHOOK): {service.get_available_channels()}"
    )

    # Use it - the service doesn't need any changes!
    webhook_notification = NotificationFactory.create_email(  # Reuse factory structure
        recipient="https://hooks.example.com/notify",
        subject="",
        body="New user signup: alice@email.com",
    )
    webhook_notification.channel = "WEBHOOK"  # Override channel

    result = service._send(webhook_notification)
    print_result(result)

    print("\n  ✨ Key insight: We added a WHOLE NEW CHANNEL with:")
    print("     - 0 changes to NotificationService")
    print("     - 0 changes to NotificationFactory")
    print("     - 0 changes to existing strategies")
    print("     - Just: 1 new class + 1 register call")


def demo_broadcast():
    """
    DEMO 4: Broadcast - Send to multiple channels at once.
    """
    print_header("DEMO 4: Broadcast - Multi-Channel Notification")

    service = NotificationService()

    print("\n  Broadcasting alert to EMAIL + SMS + SLACK simultaneously:")
    results = service.broadcast(
        message="🚨 Database connection pool exhausted! Immediate action required.",
        channels=["EMAIL", "SMS", "SLACK"],
        recipients={
            "EMAIL": "oncall@company.com",
            "SMS": "+1-555-ONCALL",
            "SLACK": "#incidents",
        },
        priority="URGENT",
    )

    for result in results:
        print_result(result)


def demo_template_sending():
    """
    DEMO 5: Template-based notifications using Factory.
    """
    print_header("DEMO 5: Template-Based Notifications")

    service = NotificationService()

    print("\n  Sending templated notifications:")

    # Welcome email
    result1 = service.send_from_template(
        channel="EMAIL",
        recipient="newuser@example.com",
        template_name="welcome",
        template_vars={
            "app_name": "CloudPlatform",
            "user_name": "Bob",
            "feature": "the API dashboard",
        },
    )
    print_result(result1)

    # Password reset
    result2 = service.send_from_template(
        channel="SMS",
        recipient="+1-555-4321",
        template_name="password_reset",
        template_vars={"user_name": "Bob", "reset_code": "X7K9M2"},
    )
    print_result(result2)

    # Alert
    result3 = service.send_from_template(
        channel="SLACK",
        recipient="#alerts",
        template_name="alert",
        template_vars={
            "alert_type": "High Memory Usage",
            "alert_message": "Server prod-03 memory at 92%. Auto-scaling triggered.",
        },
    )
    print_result(result3)


def demo_analytics():
    """
    DEMO 6: Analytics and history tracking.
    """
    print_header("DEMO 6: Analytics & Send History")

    service = NotificationService()

    # Send several notifications
    service.send_email("a@b.com", "Test 1", "Body 1")
    service.send_sms("+123", "Test 2")
    service.send_push("device1", "Test 3", "Body 3")
    service.send_slack("#test", "Test 4")
    service.send_email("c@d.com", "Test 5", "Body 5")

    # Get stats
    stats = service.get_stats()
    print(f"\n  Total notifications sent: {stats['total']}")
    print(f"  Successful: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print(f"\n  By channel:")
    for channel, data in stats["by_channel"].items():
        print(
            f"    {channel}: {data['total']} sent, {data['success']} ok, {data['failed']} failed"
        )


def main():
    """Run all demonstrations."""
    print("\n" + "█" * 70)
    print("█  PROJECT 9: NOTIFICATION PLATFORM                                █")
    print("█  Patterns: Factory + Strategy                                    █")
    print("█  Key: Factory CREATES objects, Strategy DECIDES behavior         █")
    print("█" * 70)

    # Run demos in sequence
    demo_factory_pattern()
    demo_strategy_pattern()
    demo_open_closed_principle()
    demo_broadcast()
    demo_template_sending()
    demo_analytics()

    # Final summary
    print_header("LEARNING SUMMARY")
    print("""
  🏭 FACTORY PATTERN:
     - Centralizes object creation
     - Encapsulates construction complexity
     - Ensures consistent initialization
     - Methods: create_email(), create_sms(), create_from_template()

  🎯 STRATEGY PATTERN:
     - Defines a family of algorithms (sending mechanisms)
     - Makes them interchangeable at runtime
     - Each strategy implements the same interface
     - Classes: EmailStrategy, SMSStrategy, PushStrategy, SlackStrategy

  🤝 HOW THEY WORK TOGETHER:
     Client → Service → Factory (creates Notification)
                      → Strategy Registry (selects HOW to send)
                      → Strategy.send(notification) (executes)

  🔑 PRINCIPLES DEMONSTRATED:
     - Single Responsibility: Each class has ONE job
     - Open/Closed: Add new channels without modifying existing code
     - Liskov Substitution: Any strategy works where NotificationStrategy is expected
     - Dependency Inversion: Service depends on abstractions, not concretions
    """)


if __name__ == "__main__":
    main()
