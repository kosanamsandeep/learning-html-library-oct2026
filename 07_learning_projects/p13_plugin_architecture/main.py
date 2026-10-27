"""
PROJECT 13: PLUGIN ARCHITECTURE - Extensible CLI Text Processor
================================================================
Patterns: Plugin System, Hook/Event System, Dependency Injection, Topological Sort
Inspired by: pytest (pluggy), VS Code Extensions, WordPress Hooks, Flask Extensions

Story: You're building a text processing CLI tool. Instead of hardcoding features,
you design a plugin system where third-party developers can extend functionality
by hooking into well-defined extension points.

Key Concepts Demonstrated:
  1. Hook System (Action & Filter hooks)
  2. Plugin Discovery & Loading
  3. Dependency Resolution (Topological Sort)
  4. Plugin Lifecycle (discover -> load -> activate -> deactivate)
  5. Filter Pipeline (data transformation chain)
"""

import sys
import os

# Ensure proper encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from hooks.hook_system import HookRegistry
from core.plugin_manager import PluginManager
from core.app import TextProcessorApp

# Import all plugins
from plugins.word_count import WordCountPlugin
from plugins.text_transform import TextTransformPlugin
from plugins.emoji_plugin import EmojiPlugin
from plugins.statistics_plugin import StatisticsPlugin
from plugins.profanity_filter import ProfanityFilterPlugin


def print_header():
    """Perform the print header step used by this project."""
    print("=" * 70)
    print("#  PROJECT 13: PLUGIN ARCHITECTURE - Extensible CLI Text Processor")
    print("#  Patterns: Plugin System, Hooks, Dependency Resolution, Pipelines")
    print("#  Inspired by: pytest/pluggy, VS Code, WordPress, Flask Extensions")
    print("=" * 70)


def demo_1_plugin_discovery():
    """Demo: Plugin discovery and dependency resolution."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Plugin Discovery & Dependency Resolution")
    print("=" * 70)

    hook_registry = HookRegistry()
    # App defines hooks (extension points) that plugins will register to
    app = TextProcessorApp(hook_registry)
    manager = PluginManager(hook_registry)

    # Simulate discovering plugins (in real app, this would scan directories)
    all_plugins = [
        WordCountPlugin,
        TextTransformPlugin,
        EmojiPlugin,  # depends on text_transform
        StatisticsPlugin,  # depends on word_count
        ProfanityFilterPlugin,  # depends on text_transform
    ]

    print("\n  Registered plugins (unordered):")
    for cls in all_plugins:
        temp = cls(hook_registry)
        deps = temp.meta.dependencies or ["(none)"]
        print(f"    - {temp.meta.name} v{temp.meta.version} | deps: {deps}")

    print("\n  Resolving dependencies (topological sort)...")
    order = manager.discover_and_load(all_plugins)

    print(f"\n  Activation order (dependencies first):")
    for i, name in enumerate(order, 1):
        plugin = manager.get_plugin(name)
        print(f"    {i}. {name} [{plugin.state.value}]")

    print("\n  Key insight: text_transform loads BEFORE emoji & profanity_filter")
    print("  because they depend on it. word_count loads BEFORE statistics.")


def demo_2_hook_system():
    """Demo: How hooks connect plugins to the app."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Hook System (Action & Filter Hooks)")
    print("=" * 70)

    # Bootstrap full app
    hook_registry = HookRegistry()
    app = TextProcessorApp(hook_registry)
    manager = PluginManager(hook_registry)

    plugins = [
        WordCountPlugin,
        TextTransformPlugin,
        EmojiPlugin,
        StatisticsPlugin,
        ProfanityFilterPlugin,
    ]
    manager.discover_and_load(plugins)
    app.startup()

    print("\n  Defined Hooks (extension points):")
    for hook in hook_registry.get_hooks():
        regs = hook_registry.get_registrations(hook.name)
        print(
            f"    {hook.hook_type.value:8s} | {hook.name:25s} | {len(regs)} subscribers"
        )

    print("\n  Hook 'command.register' subscribers (who adds commands):")
    for reg in hook_registry.get_registrations("command.register"):
        print(f"    - {reg.plugin_name} (priority: {reg.priority})")

    print("\n  Hook 'text.pre_process' subscribers (filter chain):")
    for reg in hook_registry.get_registrations("text.pre_process"):
        print(f"    - {reg.plugin_name} (priority: {reg.priority})")

    print("\n  Hook 'text.post_process' subscribers (filter chain):")
    for reg in hook_registry.get_registrations("text.post_process"):
        print(f"    - {reg.plugin_name} (priority: {reg.priority})")


def demo_3_command_execution():
    """Demo: Plugins adding commands and executing them."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Plugin Commands in Action")
    print("=" * 70)

    # Bootstrap
    hook_registry = HookRegistry()
    app = TextProcessorApp(hook_registry)
    manager = PluginManager(hook_registry)

    plugins = [
        WordCountPlugin,
        TextTransformPlugin,
        EmojiPlugin,
        StatisticsPlugin,
        ProfanityFilterPlugin,
    ]
    manager.discover_and_load(plugins)
    app.startup()

    commands_to_run = [
        "help",
        "wc The quick brown fox jumps over the lazy dog",
        "upper hello world from plugin system",
        "reverse Python is amazing",
        "freq the cat sat on the mat the cat is happy",
        "emojis",
        "title hello world this is title case",
    ]

    for cmd in commands_to_run:
        print(f"\n  > {cmd}")
        result = app.execute(cmd)
        for line in result.split("\n"):
            print(f"    {line}")


def demo_4_filter_pipeline():
    """Demo: Filter hooks transforming data through pipeline."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Filter Pipeline (Text Processing Chain)")
    print("=" * 70)

    # Bootstrap
    hook_registry = HookRegistry()
    app = TextProcessorApp(hook_registry)
    manager = PluginManager(hook_registry)

    plugins = [
        WordCountPlugin,
        TextTransformPlugin,
        EmojiPlugin,
        StatisticsPlugin,
        ProfanityFilterPlugin,
    ]
    manager.discover_and_load(plugins)
    app.startup()

    test_texts = [
        "Hello :happy: world :rocket:",
        "This is a spam message about a scam",
        "I :heart: Python and :fire: code",
        "Warning: virus detected :warning:",
    ]

    print("\n  Text flows through filter pipeline:")
    print("    Input -> [emoji substitution] -> [profanity filter] -> Output")
    print()

    for text in test_texts:
        # Use 'echo' command which applies filters
        result = app.execute(f"echo {text}")
        print(f"    Input:  '{text}'")
        print(f"    Output: '{result}'")
        print()

    print("  Key insight: Emoji plugin (priority 5) runs BEFORE")
    print("  profanity filter (priority 99). Order matters in filter chains!")


def demo_5_statistics_audit():
    """Demo: Statistics plugin tracking via ACTION hooks."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Statistics & Audit Trail (Action Hooks)")
    print("=" * 70)

    # Bootstrap
    hook_registry = HookRegistry()
    app = TextProcessorApp(hook_registry)
    manager = PluginManager(hook_registry)

    plugins = [
        WordCountPlugin,
        TextTransformPlugin,
        EmojiPlugin,
        StatisticsPlugin,
        ProfanityFilterPlugin,
    ]
    manager.discover_and_load(plugins)
    app.startup()

    # Execute various commands silently
    commands = [
        "wc hello world",
        "upper foo bar",
        "wc one two three four",
        "reverse abcdef",
        "upper ALREADY UPPER",
        "wc testing the word counter",
        "echo :happy: day",
        "help",
    ]

    print("\n  Executing 8 commands silently...")
    for cmd in commands:
        app.execute(cmd)

    # Now show stats
    print(f"\n  > stats")
    result = app.execute("stats")
    for line in result.split("\n"):
        print(f"    {line}")

    print(f"\n  > audit")
    result = app.execute("audit")
    for line in result.split("\n"):
        print(f"    {line}")

    print("\n  Key insight: The statistics plugin uses ACTION hooks to")
    print("  observe command execution without modifying behavior.")
    print("  This is the Observer pattern implemented via hooks!")


def print_summary():
    """Perform the print summary step used by this project."""
    print("\n" + "=" * 70)
    print("  LEARNING SUMMARY")
    print("=" * 70)
    print("""
  PLUGIN ARCHITECTURE:
     - Core defines EXTENSION POINTS (hooks)
     - Plugins REGISTER callbacks at those points
     - Core TRIGGERS hooks at the right time
     - Plugins are ISOLATED - they don't know about each other

  HOOK TYPES:
     - ACTION: Side effects (logging, tracking, notifications)
     - FILTER: Data transformation pipeline (like Unix pipes)
     - Priority controls execution order

  DEPENDENCY RESOLUTION:
     - Plugins declare dependencies on other plugins
     - Topological sort ensures correct load order
     - Circular dependencies are detected and rejected

  REAL-WORLD EXAMPLES:
     - pytest: @pytest.hookimpl decorators, pluggy library
     - VS Code: extension.activate(), contributes in package.json
     - WordPress: add_action(), add_filter(), do_action(), apply_filters()
     - Flask: app.before_request, @app.route decorators
     - Webpack: tapable hooks (SyncHook, AsyncSeriesHook)
    """)


if __name__ == "__main__":
    print_header()
    demo_1_plugin_discovery()
    demo_2_hook_system()
    demo_3_command_execution()
    demo_4_filter_pipeline()
    demo_5_statistics_audit()
    print_summary()
