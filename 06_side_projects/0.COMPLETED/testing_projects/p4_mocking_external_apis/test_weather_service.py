"""Tests that show three mocking techniques, in order of preference."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from weather_service import Forecast, WeatherClient, WeatherService

# ---------------------------------------------------------------------------
# Approach 1: inject mocks. Cleanest when the code is designed for it.
# ---------------------------------------------------------------------------


def make_service(rain_chance: float, threshold: float = 0.6):
    client = MagicMock(spec=WeatherClient)
    client.get_forecast.return_value = Forecast(
        city="Bengaluru", rain_chance=rain_chance, temperature_c=27.0
    )
    notifier = MagicMock()
    service = WeatherService(client=client, notifier=notifier, rain_threshold=threshold)
    return service, client, notifier


def test_notifies_when_rain_chance_is_above_threshold():
    service, client, notifier = make_service(rain_chance=0.8)

    sent = service.notify_if_rain_expected("Bengaluru", "asha@example.com")

    assert sent is True
    client.get_forecast.assert_called_once_with("Bengaluru")
    notifier.send.assert_called_once()
    args, _ = notifier.send.call_args
    assert args[0] == "asha@example.com"
    assert "80% chance of rain" in args[1]


def test_does_not_notify_when_rain_chance_is_below_threshold():
    service, _, notifier = make_service(rain_chance=0.2)

    sent = service.notify_if_rain_expected("Bengaluru", "asha@example.com")

    assert sent is False
    notifier.send.assert_not_called()


def test_threshold_boundary_is_inclusive():
    service, _, notifier = make_service(rain_chance=0.6, threshold=0.6)

    sent = service.notify_if_rain_expected("Bengaluru", "asha@example.com")

    assert sent is True
    notifier.send.assert_called_once()


# ---------------------------------------------------------------------------
# Approach 2: patch the network library. Useful when refactoring is not
# practical and the code calls requests directly.
# ---------------------------------------------------------------------------


@patch("weather_service.requests.get")
def test_weather_client_parses_api_response(mock_get):
    mock_get.return_value.json.return_value = {
        "rain_chance": 0.75,
        "temperature_c": 22.5,
    }
    mock_get.return_value.raise_for_status.return_value = None

    forecast = WeatherClient().get_forecast("Pune")

    assert forecast == Forecast(city="Pune", rain_chance=0.75, temperature_c=22.5)
    mock_get.assert_called_once()
    called_url = mock_get.call_args.args[0]
    assert called_url.endswith("/v1/forecast")


@patch("weather_service.requests.get")
def test_weather_client_propagates_http_errors(mock_get):
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("503")

    with pytest.raises(requests.HTTPError):
        WeatherClient().get_forecast("Pune")


# ---------------------------------------------------------------------------
# Approach 3: pytest-mock (the `mocker` fixture). Same idea, less boilerplate.
# ---------------------------------------------------------------------------


def test_service_calls_notifier_with_pytest_mock(mocker):
    client = mocker.Mock(spec=WeatherClient)
    client.get_forecast.return_value = Forecast("Chennai", 0.9, 30.0)
    notifier = mocker.Mock()

    WeatherService(client, notifier).notify_if_rain_expected("Chennai", "ravi@x.com")

    notifier.send.assert_called_once()
