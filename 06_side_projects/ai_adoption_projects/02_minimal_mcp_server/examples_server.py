#!/usr/bin/env python3
"""
examples_server.py — Progressive MCP examples from basic to intermediate.

This single server demonstrates multiple tools at different complexity levels.
Run it and connect any MCP client to explore all tools.

Usage:
    python examples_server.py

Connect via Claude Code:
    claude mcp add mcp-examples -- python /path/to/examples_server.py

Or test with the MCP Inspector:
    npx @modelcontextprotocol/inspector python examples_server.py
"""

from __future__ import annotations
import math
import json
import time
import random
from typing import Literal
from datetime import datetime, timezone
from pathlib import Path
from mcp.server import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP(
    name="MCP Examples Server",
    instructions="A collection of example MCP tools demonstrating different "
    "patterns: calculation, data lookup, transformation, simulation, "
    "and file operations. Use these as templates for your own tools.",
)


# ════════════════════════════════════════════════════════════════
#  BASIC EXAMPLES
# ════════════════════════════════════════════════════════════════

@mcp.tool(
    description="Perform arithmetic calculations. Supports +, -, *, /, **, %, sqrt, sin, cos."
)
def calculator(
    expression: str = Field(
        description="Math expression to evaluate (e.g., '2 + 2', 'sqrt(144)', 'sin(45) * 10')"
    )
) -> str:
    """
    Evaluate a mathematical expression safely.

    Uses a restricted eval context with only math functions available.
    """
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})

    try:
        # Safety: compile and check the AST before evaluating
        code = compile(expression.strip(), "<calc>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                return f"Error: '{name}' is not allowed in calculator expressions."
        result = eval(code, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


@mcp.tool(
    description="Get the current server time in a specified timezone."
)
def current_time(
    format: Literal["iso", "unix", "readable"] = "readable"
) -> str:
    """
    Return the current time in various formats.

    Parameters
    ----------
    format : str
        'iso'    — ISO 8601 format
        'unix'   — Unix epoch seconds
        'readable' — Human-readable date and time (default)
    """
    now = datetime.now(timezone.utc)
    if format == "iso":
        return now.isoformat()
    elif format == "unix":
        return str(int(now.timestamp()))
    else:
        return now.strftime("%A, %B %d, %Y at %I:%M:%S %p UTC")


# ════════════════════════════════════════════════════════════════
#  INTERMEDIATE EXAMPLES
# ════════════════════════════════════════════════════════════════

@mcp.tool(
    description="Simulate a weather check for a given city. Returns temperature, conditions, and humidity."
)
def get_weather(
    city: str = Field(description="City name (e.g., 'London', 'Tokyo', 'New York')"),
    units: Literal["celsius", "fahrenheit"] = "celsius",
) -> str:
    """
    Simulate fetching current weather for a city.

    NOTE: This is a DEMO using simulated data. In production, replace with
    a real weather API call (e.g., OpenWeatherMap, WeatherAPI).
    """
    # Simulated weather data keyed by city
    conditions = ["☀️ Sunny", "⛅ Partly Cloudy", "☁️ Overcast",
                  "🌧️ Light Rain", "⛈️ Thunderstorms", "🌫️ Foggy",
                  "🌤️ Mostly Clear", "🌦️ Scattered Showers"]

    city_lower = city.lower()

    # Deterministic "simulation" based on city name hash
    seed = hash(city_lower) & 0xFFFFFFFF
    rng = random.Random(seed)

    temp_base = {
        "london": 15, "paris": 18, "tokyo": 22, "new york": 20,
        "sydney": 26, "mumbai": 32, "berlin": 16, "toronto": 12,
        "dubai": 38, "singapore": 30, "moscow": 8, "cape town": 22,
    }
    base = temp_base.get(city_lower, 20)
    temp = base + rng.randint(-4, 4)

    if units == "fahrenheit":
        temp = round(temp * 9 / 5 + 32)
        unit = "°F"
    else:
        unit = "°C"

    condition = rng.choice(conditions)
    humidity = rng.randint(40, 90) if "rain" not in condition.lower() and "storm" not in condition.lower() else rng.randint(70, 100)
    wind_speed = rng.randint(5, 30)

    return (
        f"🌍 Weather for {city.title()}\n"
        f"   Temperature: {temp}{unit}\n"
        f"   Conditions: {condition}\n"
        f"   Humidity: {humidity}%\n"
        f"   Wind: {wind_speed} km/h\n"
        f"   (Simulated data — for demo purposes only)"
    )


@mcp.tool(
    description="Count words, characters, sentences, and estimated reading time in a text."
)
def text_stats(
    text: str = Field(description="The text to analyze")
) -> str:
    """
    Analyze a block of text and return statistics.

    Useful for content analysis, blog post planning, or quick readability checks.
    """
    words = text.split()
    chars = len(text)
    sentences = max(text.count(".") + text.count("!") + text.count("?"), 1)
    avg_word_len = round(chars / len(words), 1) if words else 0

    # Reading time: ~200 words per minute
    reading_time_min = len(words) / 200
    if reading_time_min < 1:
        reading_time = f"{round(reading_time_min * 60)} seconds"
    else:
        reading_time = f"{reading_time_min:.1f} minutes"

    # Vocabulary richness (unique words / total words)
    unique_words = len(set(w.lower().strip(".,!?;:'\"()") for w in words))
    richness = round(unique_words / len(words) * 100, 1) if words else 0

    return (
        f"📊 Text Statistics\n"
        f"   Words: {len(words):,}\n"
        f"   Characters: {chars:,}\n"
        f"   Sentences: {sentences:,}\n"
        f"   Avg word length: {avg_word_len} chars\n"
        f"   Unique words: {unique_words:,} ({richness}% richness)\n"
        f"   Estimated reading time: {reading_time}"
    )


@mcp.tool(
    description="Convert between different units of measurement (length, weight, temperature, volume)."
)
def unit_convert(
    value: float = Field(description="The numeric value to convert"),
    from_unit: str = Field(description="Source unit (e.g., 'km', 'lb', 'celsius', 'gallon')"),
    to_unit: str = Field(description="Target unit (e.g., 'mi', 'kg', 'fahrenheit', 'liter')"),
) -> str:
    """
    Convert a value between common measurement units.

    Supports:
      - Length: km, mi, m, ft, cm, in
      - Weight: kg, lb, oz, g
      - Temperature: celsius, fahrenheit, kelvin
      - Volume: liter, gallon, ml, cup
      - Speed: kmh, mph, ms (meters/sec)
    """
    conversions = {
        # Length (to meters, then from meters)
        ("km", "mi"): lambda v: v * 0.621371,
        ("mi", "km"): lambda v: v * 1.609344,
        ("m", "ft"): lambda v: v * 3.28084,
        ("ft", "m"): lambda v: v * 0.3048,
        ("cm", "in"): lambda v: v * 0.393701,
        ("in", "cm"): lambda v: v * 2.54,
        ("km", "m"): lambda v: v * 1000,
        ("m", "km"): lambda v: v / 1000,
        # Weight (to kg, then from kg)
        ("kg", "lb"): lambda v: v * 2.20462,
        ("lb", "kg"): lambda v: v * 0.453592,
        ("kg", "g"): lambda v: v * 1000,
        ("g", "kg"): lambda v: v / 1000,
        ("oz", "g"): lambda v: v * 28.3495,
        ("g", "oz"): lambda v: v * 0.035274,
        # Temperature
        ("celsius", "fahrenheit"): lambda v: v * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5/9,
        ("celsius", "kelvin"): lambda v: v + 273.15,
        ("kelvin", "celsius"): lambda v: v - 273.15,
        # Volume
        ("gallon", "liter"): lambda v: v * 3.78541,
        ("liter", "gallon"): lambda v: v * 0.264172,
        ("liter", "ml"): lambda v: v * 1000,
        ("ml", "liter"): lambda v: v / 1000,
        ("cup", "ml"): lambda v: v * 236.588,
        ("ml", "cup"): lambda v: v * 0.00422675,
        # Speed
        ("kmh", "mph"): lambda v: v * 0.621371,
        ("mph", "kmh"): lambda v: v * 1.609344,
    }

    key = (from_unit.lower().strip(), to_unit.lower().strip())
    if key not in conversions:
        available = sorted(set(k[0] for k in conversions.keys()))
        return (
            f"Conversion from '{from_unit}' to '{to_unit}' not supported.\n"
            f"Available units: {', '.join(available)}"
        )

    result = conversions[key](value)
    # Round to reasonable precision
    if abs(result) < 0.01:
        result_str = f"{result:.6f}"
    elif abs(result) < 1000:
        result_str = f"{result:.4f}"
    else:
        result_str = f"{result:,.2f}"

    return f"{value} {from_unit} = {result_str} {to_unit}"


# ════════════════════════════════════════════════════════════════
#  ADVANCED EXAMPLE: Pydantic model as tool input
# ════════════════════════════════════════════════════════════════

class CodeReviewInput(BaseModel):
    code: str = Field(description="The source code to review")
    language: str = Field(default="python", description="Programming language")
    severity: Literal["info", "warning", "critical"] = Field(
        default="warning", description="Minimum issue severity to report"
    )


@mcp.tool(
    description="Perform a basic static analysis review of code. "
    "Checks for common issues like hardcoded secrets, bare except clauses, "
    "missing docstrings, and oversized functions."
)
def review_code(input_data: CodeReviewInput) -> str:
    """
    Review code for common anti-patterns and issues.

    This demonstrates using a Pydantic model as structured input to an MCP tool.
    """
    code = input_data.code
    lang = input_data.language.lower()
    issues: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    lines = code.split("\n")
    line_count = len(lines)

    # Check line count
    if line_count > 200:
        issues.append(f"File is very long ({line_count} lines). Consider splitting into modules.")

    if lang == "python":
        # Bare except
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                issues.append(f"Line {i}: Bare 'except:' clause — catches all exceptions silently.")
            if stripped == "except Exception as e:" or stripped.startswith("except Exception,"):
                pass  # acceptable

        # Hardcoded secrets (basic pattern)
        secret_patterns = [
            ("password", '"password"'), ("secret", '"secret"'),
            ("api_key", '"api_key"'), ("token", '"token"'),
        ]
        for i, line in enumerate(lines, 1):
            lower = line.lower().strip()
            for pat, label in secret_patterns:
                if pat in lower and "=" in lower and not lower.startswith("#"):
                    warnings.append(f"Line {i}: Possible hardcoded {label} found.")
                    break

        # Missing docstrings in functions
        in_function = False
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("def ") and line.strip().endswith(":"):
                in_function = True
                # Check next non-blank line
                for j in range(i, min(i + 5, len(lines) + 1)):
                    next_line = lines[j - 1].strip()
                    if next_line and not next_line.startswith(('"""', "'''", "#")):
                        if j == i:
                            continue  # same line
                        info.append(f"Line {i}: Function missing docstring.")
                        break
                    elif next_line.startswith(('"""', "'''")):
                        break

        # Long lines
        long_lines = [(i, line) for i, line in enumerate(lines, 1)
                      if len(line) > 100 and not line.strip().startswith("#")]
        for i, line in long_lines[:5]:  # cap at 5
            info.append(f"Line {i}: Line too long ({len(line)} chars, max 100).")
        if len(long_lines) > 5:
            info.append(f"... and {len(long_lines) - 5} more long lines.")

    # Build report
    report = f"## 🔍 Code Review Report\n\n**File:** {line_count} lines of {lang}\n\n"

    if input_data.severity == "critical":
        report_items = [(i, "🔴 Critical") for i in issues]
    elif input_data.severity == "warning":
        report_items = (
            [(i, "🔴 Critical") for i in issues]
            + [(w, "🟡 Warning") for w in warnings]
        )
    else:
        report_items = (
            [(i, "🔴 Critical") for i in issues]
            + [(w, "🟡 Warning") for w in warnings]
            + [(inf, "🔵 Info") for inf in info]
        )

    if not report_items:
        report += "✅ No issues found. Code looks clean!\n"
    else:
        report += f"**Found {len(report_items)} issue(s):**\n\n"
        for item_text, level in report_items:
            report += f"- {level}: {item_text}\n"

    return report


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    print("🧩 MCP Examples Server starting...", file=sys.stderr)
    print("   Available tools: calculator, current_time, get_weather, text_stats, unit_convert, review_code", file=sys.stderr)
    print("   Connect: claude mcp add mcp-examples -- python examples_server.py", file=sys.stderr)
    mcp.run(transport="stdio")
