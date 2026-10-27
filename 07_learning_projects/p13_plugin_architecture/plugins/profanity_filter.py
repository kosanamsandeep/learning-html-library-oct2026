"""
Profanity Filter Plugin - Demonstrates filter chain with censoring.
Shows: FILTER hooks that modify content, configurable behavior.
"""

from core.plugin_manager import PluginBase, PluginMeta

# Simple word list for demonstration (not real profanity)
BLOCKED_WORDS = {"spam", "scam", "hack", "virus", "malware"}


class ProfanityFilterPlugin(PluginBase):
    """Censors blocked words in text processing pipeline."""

    @property
    def meta(self) -> PluginMeta:
        """Perform the meta step used by this project."""
        return PluginMeta(
            name="profanity_filter",
            version="1.0.0",
            description="Content moderation - blocks inappropriate words",
            author="SafeText Inc",
            dependencies=["text_transform"],
            provides=["content_moderation"],
        )

    def activate(self) -> None:
        """Register as a post-process filter (runs after other transforms)."""
        self._hooks.register(
            "text.post_process",
            self._censor_text,
            priority=99,  # Low priority = runs last in filter chain
            plugin_name=self.meta.name,
        )

        self._hooks.register(
            "command.register",
            self._on_register_commands,
            priority=10,
            plugin_name=self.meta.name,
        )

    def _censor_text(self, text: str, **kwargs) -> str:
        """Replace blocked words with asterisks."""
        words = text.split()
        censored = []
        for word in words:
            if word.lower().strip(".,!?;:") in BLOCKED_WORDS:
                censored.append("*" * len(word))
            else:
                censored.append(word)
        return " ".join(censored)

    def _on_register_commands(self, app) -> None:
        """Perform the on register commands step used by this project."""
        from core.app import Command

        app.register_command(
            Command(
                name="blocked",
                description="Show blocked words list",
                handler=self._cmd_blocked,
                plugin_name=self.meta.name,
            )
        )

    def _cmd_blocked(self, args: list[str]) -> str:
        """Perform the cmd blocked step used by this project."""
        lines = ["Blocked Words:"]
        for word in sorted(BLOCKED_WORDS):
            lines.append(f"  - {word}")
        return "\n".join(lines)
