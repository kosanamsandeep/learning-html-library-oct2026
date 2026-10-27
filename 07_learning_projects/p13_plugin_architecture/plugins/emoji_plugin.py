"""
Emoji Plugin - Adds emoji substitution filter.
Demonstrates: Filter hooks that transform data in pipeline, plus dependencies.
Depends on: text_transform (to show dependency resolution).
"""

from core.plugin_manager import PluginBase, PluginMeta

# Emoji mapping for text substitution
EMOJI_MAP = {
    ":happy:": "[smile]",
    ":sad:": "[frown]",
    ":heart:": "[heart]",
    ":fire:": "[fire]",
    ":star:": "[star]",
    ":check:": "[checkmark]",
    ":x:": "[cross]",
    ":rocket:": "[rocket]",
    ":warning:": "[warning]",
    ":info:": "[info]",
}


class EmojiPlugin(PluginBase):
    """Adds emoji substitution to the text processing pipeline."""

    @property
    def meta(self) -> PluginMeta:
        """Perform the meta step used by this project."""
        return PluginMeta(
            name="emoji",
            version="1.2.0",
            description="Emoji shortcode substitution in text",
            author="Fun Labs",
            dependencies=["text_transform"],  # Requires text_transform loaded first
            provides=["emoji"],
        )

    def activate(self) -> None:
        """Register filter hook for emoji substitution."""
        # Register as a pre-process filter (priority 5 = runs early)
        self._hooks.register(
            "text.pre_process",
            self._substitute_emojis,
            priority=5,
            plugin_name=self.meta.name,
        )

        # Register command
        self._hooks.register(
            "command.register",
            self._on_register_commands,
            priority=10,
            plugin_name=self.meta.name,
        )

    def _substitute_emojis(self, text: str, **kwargs) -> str:
        """Replace emoji shortcodes with emoji symbols."""
        for code, emoji in EMOJI_MAP.items():
            text = text.replace(code, emoji)
        return text

    def _on_register_commands(self, app) -> None:
        """Perform the on register commands step used by this project."""
        from core.app import Command

        app.register_command(
            Command(
                name="emojis",
                description="List available emoji shortcodes",
                handler=self._cmd_emojis,
                plugin_name=self.meta.name,
            )
        )

    def _cmd_emojis(self, args: list[str]) -> str:
        """Perform the cmd emojis step used by this project."""
        lines = ["Available Emoji Shortcodes:"]
        for code, emoji in EMOJI_MAP.items():
            lines.append(f"  {code:12s} -> {emoji}")
        return "\n".join(lines)
