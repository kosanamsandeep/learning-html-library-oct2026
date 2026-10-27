"""
Text Transform Plugin - Adds filters that transform text in the pipeline.
Demonstrates: FILTER hooks (data transformation pipeline).
"""

from core.plugin_manager import PluginBase, PluginMeta


class TextTransformPlugin(PluginBase):
    """Adds text transformation filters and commands."""

    @property
    def meta(self) -> PluginMeta:
        """Perform the meta step used by this project."""
        return PluginMeta(
            name="text_transform",
            version="1.0.0",
            description="Text transformations: upper, lower, reverse, title",
            author="TextTools Inc",
            dependencies=[],
            provides=["text_transform"],
        )

    def activate(self) -> None:
        """Register commands and a default filter."""
        self._hooks.register(
            "command.register",
            self._on_register_commands,
            priority=10,
            plugin_name=self.meta.name,
        )

    def _on_register_commands(self, app) -> None:
        """Perform the on register commands step used by this project."""
        from core.app import Command

        app.register_command(
            Command(
                name="upper",
                description="Convert text to UPPERCASE",
                handler=lambda args: " ".join(args).upper(),
                plugin_name=self.meta.name,
            )
        )
        app.register_command(
            Command(
                name="lower",
                description="Convert text to lowercase",
                handler=lambda args: " ".join(args).lower(),
                plugin_name=self.meta.name,
            )
        )
        app.register_command(
            Command(
                name="reverse",
                description="Reverse the text",
                handler=lambda args: " ".join(args)[::-1],
                plugin_name=self.meta.name,
            )
        )
        app.register_command(
            Command(
                name="title",
                description="Convert text to Title Case",
                handler=lambda args: " ".join(args).title(),
                plugin_name=self.meta.name,
            )
        )
