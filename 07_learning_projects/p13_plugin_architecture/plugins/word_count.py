"""
Word Count Plugin - Adds a 'wc' command to count words/chars/lines.
Demonstrates: Simple command registration via hook system.
"""

from core.plugin_manager import PluginBase, PluginMeta


class WordCountPlugin(PluginBase):
    """Adds text analysis commands."""

    @property
    def meta(self) -> PluginMeta:
        """Perform the meta step used by this project."""
        return PluginMeta(
            name="word_count",
            version="1.0.0",
            description="Text analysis - word count, char count, line count",
            author="TextTools Inc",
            dependencies=[],
            provides=["text_analysis"],
        )

    def activate(self) -> None:
        """Register our command via the hook system."""
        self._hooks.register(
            "command.register",
            self._on_register_commands,
            priority=10,
            plugin_name=self.meta.name,
        )

    def _on_register_commands(self, app) -> None:
        """Called when app fires 'command.register' hook."""
        from core.app import Command

        app.register_command(
            Command(
                name="wc",
                description="Count words/chars/lines in text",
                handler=self._cmd_wc,
                plugin_name=self.meta.name,
            )
        )

        app.register_command(
            Command(
                name="freq",
                description="Show word frequency analysis",
                handler=self._cmd_freq,
                plugin_name=self.meta.name,
            )
        )

    def _cmd_wc(self, args: list[str]) -> str:
        """Perform the cmd wc step used by this project."""
        text = " ".join(args)
        if not text:
            return "Usage: wc <text>"
        words = len(text.split())
        chars = len(text)
        lines = text.count("\n") + 1
        return f"Words: {words} | Chars: {chars} | Lines: {lines}"

    def _cmd_freq(self, args: list[str]) -> str:
        """Perform the cmd freq step used by this project."""
        text = " ".join(args).lower()
        if not text:
            return "Usage: freq <text>"
        words = text.split()
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        lines = ["Word Frequency:"]
        for word, count in sorted_freq[:10]:
            bar = "#" * count
            lines.append(f"  {word:15s} {count:3d} {bar}")
        return "\n".join(lines)
