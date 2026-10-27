"""
Statistics Plugin - Adds text statistics with audit trail.
Demonstrates: ACTION hooks (side effects/logging), depends on word_count.
"""

from core.plugin_manager import PluginBase, PluginMeta


class StatisticsPlugin(PluginBase):
    """Tracks command execution statistics and provides audit trail."""

    @property
    def meta(self) -> PluginMeta:
        """Perform the meta step used by this project."""
        return PluginMeta(
            name="statistics",
            version="1.0.0",
            description="Command execution statistics and audit logging",
            author="Analytics Corp",
            dependencies=["word_count"],  # Uses word_count's analysis
            provides=["statistics", "audit"],
        )

    def activate(self) -> None:
        """Register hooks for tracking."""
        self._command_stats: dict[str, int] = {}
        self._audit_log: list[str] = []

        # Track command execution (ACTION hook)
        self._hooks.register(
            "command.before_execute",
            self._track_command,
            priority=1,  # High priority - track before anything else
            plugin_name=self.meta.name,
        )

        # Register our commands
        self._hooks.register(
            "command.register",
            self._on_register_commands,
            priority=10,
            plugin_name=self.meta.name,
        )

    def _track_command(self, command: str, args: list = None, **kwargs) -> None:
        """Track every command execution."""
        self._command_stats[command] = self._command_stats.get(command, 0) + 1
        self._audit_log.append(f"{command} {' '.join(args or [])}")

    def _on_register_commands(self, app) -> None:
        """Perform the on register commands step used by this project."""
        from core.app import Command

        app.register_command(
            Command(
                name="stats",
                description="Show command usage statistics",
                handler=self._cmd_stats,
                plugin_name=self.meta.name,
            )
        )
        app.register_command(
            Command(
                name="audit",
                description="Show audit log of all commands",
                handler=self._cmd_audit,
                plugin_name=self.meta.name,
            )
        )

    def _cmd_stats(self, args: list[str]) -> str:
        """Perform the cmd stats step used by this project."""
        if not self._command_stats:
            return "No commands executed yet."
        lines = ["Command Usage Statistics:"]
        for cmd, count in sorted(
            self._command_stats.items(), key=lambda x: x[1], reverse=True
        ):
            bar = "#" * count
            lines.append(f"  {cmd:15s} {count:3d} {bar}")
        total = sum(self._command_stats.values())
        lines.append(f"\n  Total executions: {total}")
        return "\n".join(lines)

    def _cmd_audit(self, args: list[str]) -> str:
        """Perform the cmd audit step used by this project."""
        if not self._audit_log:
            return "Audit log is empty."
        lines = ["Audit Log:"]
        for i, entry in enumerate(self._audit_log, 1):
            lines.append(f"  [{i:03d}] {entry}")
        return "\n".join(lines)
