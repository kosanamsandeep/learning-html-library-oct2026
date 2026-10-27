"""Weather notifier service.

Three pieces, on purpose:
- WeatherClient    : talks to the outside world (HTTP).
- Notifier         : sends a message (email/SMS in real life).
- WeatherService   : business rule that decides whether to notify.

The service depends on the two collaborators. In tests we replace those
collaborators with mocks, so we never touch the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import requests


@dataclass
class Forecast:
    city: str
    rain_chance: float  # 0.0 - 1.0
    temperature_c: float


class WeatherClient:
    """Real implementation. We will NOT call this in tests."""

    BASE_URL = "https://api.example-weather.test/v1/forecast"

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout = timeout_seconds

    def get_forecast(self, city: str) -> Forecast:
        response = requests.get(
            self.BASE_URL,
            params={"city": city},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return Forecast(
            city=city,
            rain_chance=data["rain_chance"],
            temperature_c=data["temperature_c"],
        )


class Notifier(Protocol):
    def send(self, recipient: str, message: str) -> None: ...


class EmailNotifier:
    """Real implementation. Also not used in tests."""

    def send(self, recipient: str, message: str) -> None:
        # In production this would call an email provider.
        raise NotImplementedError("wire your email provider here")


@dataclass
class WeatherService:
    client: WeatherClient
    notifier: Notifier
    rain_threshold: float = 0.6

    def notify_if_rain_expected(self, city: str, recipient: str) -> bool:
        forecast = self.client.get_forecast(city)
        if forecast.rain_chance >= self.rain_threshold:
            self.notifier.send(
                recipient,
                f"Bring an umbrella in {city}: {int(forecast.rain_chance * 100)}% chance of rain.",
            )
            return True
        return False
