"""
Application Core - A simple text processing CLI that plugins extend.

The 'app' defines hooks (extension points) that plugins can use to:
  - Add new commands
  - Transform text before/after processing
  - React to events (file loaded, text saved, etc.)

Think of this as the WordPress/VS Code/pytest core that plugins extend.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from hooks.hook_system import HookRegistry, HookType


@dataclass
class Command:
    """A CLI command that can be executed."""

    name: str
    description: str
    handler: Callable[[list[str]], str]
    plugin_name: str = "core"


class TextProcessorApp:
    """
    A text processing CLI application with plugin extension points.

    Hooks defined:
      - app.startup (ACTION): Fired when app starts
      - app.shutdown (ACTION): Fired when app shuts down
      - text.pre_process (FILTER): Transform text before processing
      - text.post_process (FILTER): Transform text after processing
      - command.register (ACTION): Opportunity for plugins to register commands
      - command.not_found (ACTION): When unknown command is entered
    """

    def __init__(self, hook_registry: HookRegistry):
        """Initialize the object with the dependencies or starting values it needs."""
        self._hooks = hook_registry
        self._commands: dict[str, Command] = {}
        self._history: list[str] = []

        # Define all extension points (hooks)
        self._define_hooks()

        # Register built-in commands
        self._register_builtin_commands()

    def _define_hooks(self) -> None:
        """Define all available hooks that plugins can use."""
        hooks = [
            ("app.startup", HookType.ACTION, "Fired when application starts"),
            ("app.shutdown", HookType.ACTION, "Fired when application shuts down"),
            ("text.pre_process", HookType.FILTER, "Transform text before processing"),
            ("text.post_process", HookType.FILTER, "Transform text after processing"),
            ("command.register", HookType.ACTION, "Plugins register their commands"),
            ("command.not_found", HookType.ACTION, "Fired when command is not found"),
            ("command.before_execute", HookType.ACTION, "Before a command executes"),
            ("command.after_execute", HookType.ACTION, "After a command executes"),
        ]
        for name, hook_type, desc in hooks:
            self._hooks.define_hook(name, hook_type, desc)

    def _register_builtin_commands(self) -> None:
        """Register core commands."""
        self.register_command(
            Command(
                name="help",
                description="Show available commands",
                handler=self._cmd_help,
                plugin_name="core",
            )
        )
        self.register_command(
            Command(
                name="history",
                description="Show command history",
                handler=self._cmd_history,
                plugin_name="core",
            )
        )
        self.register_command(
            Command(
                name="echo",
                description="Echo text (with plugin filters applied)",
                handler=self._cmd_echo,
                plugin_name="core",
            )
        )

    # ─── Public API ───────────────────────────────────────────────

    def register_command(self, command: Command) -> None:
        """Register a command (used by core and plugins)."""
        self._commands[command.name] = command

    def startup(self) -> None:
        """Start the application - triggers startup hooks."""
        self._hooks.trigger_action("app.startup", app=self)
        # Let plugins register commands
        self._hooks.trigger_action("command.register", app=self)

    def shutdown(self) -> None:
        """Shutdown the application."""
        self._hooks.trigger_action("app.shutdown", app=self)

    def execute(self, command_line: str) -> str:
        """Parse and execute a command string."""
        parts = command_line.strip().split()
        if not parts:
            return ""

        cmd_name = parts[0]
        args = parts[1:]

        self._history.append(command_line)

        if cmd_name not in self._commands:
            self._hooks.trigger_action("command.not_found", command=cmd_name, app=self)
            return f"Unknown command: '{cmd_name}'. Type 'help' for available commands."

        # Before execute hook
        self._hooks.trigger_action(
            "command.before_execute", command=cmd_name, args=args
        )

        # Execute
        result = self._commands[cmd_name].handler(args)

        # After execute hook
        self._hooks.trigger_action(
            "command.after_execute", command=cmd_name, result=result
        )

        return result

    def process_text(self, text: str) -> str:
        """Process text through the filter pipeline."""
        # Pre-process filters
        text = self._hooks.apply_filter("text.pre_process", text)
        # Post-process filters
        text = self._hooks.apply_filter("text.post_process", text)
        return text

    # ─── Built-in Command Handlers ────────────────────────────────

    def _cmd_help(self, args: list[str]) -> str:
        """Perform the cmd help step used by this project."""
        lines = ["Available Commands:"]
        for name, cmd in sorted(self._commands.items()):
            lines.append(f"  {name:15s} {cmd.description} [{cmd.plugin_name}]")
        return "\n".join(lines)

    def _cmd_history(self, args: list[str]) -> str:
        """Perform the cmd history step used by this project."""
        if not self._history:
            return "No commands in history."
        lines = ["Command History:"]
        for i, cmd in enumerate(self._history, 1):
            lines.append(f"  {i}. {cmd}")
        return "\n".join(lines)

    def _cmd_echo(self, args: list[str]) -> str:
        """Perform the cmd echo step used by this project."""
        text = " ".join(args) if args else ""
        return self.process_text(text)
