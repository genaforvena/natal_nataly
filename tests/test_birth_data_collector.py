"""
Unit tests for birth_data_collector.py.

Validates LLM-free parsing of dates and times, and the geocoding helper.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.birth_data_collector import parse_date, parse_time, geocode_place


@pytest.mark.unit
class TestParseDate:
    """Tests for parse_date() – regex-based, no LLM."""

    def test_iso_format(self):
        assert parse_date("1990-05-15") == "1990-05-15"

    def test_iso_in_sentence(self):
        assert parse_date("I was born on 1990-05-15 in Moscow") == "1990-05-15"

    def test_european_dot_format(self):
        assert parse_date("15.05.1990") == "1990-05-15"

    def test_european_slash_format(self):
        assert parse_date("15/05/1990") == "1990-05-15"

    def test_space_separated(self):
        assert parse_date("15 05 1990") == "1990-05-15"

    def test_text_month_english(self):
        assert parse_date("15 May 1990") == "1990-05-15"

    def test_text_month_english_comma(self):
        assert parse_date("May 15, 1990") == "1990-05-15"

    def test_text_month_russian(self):
        assert parse_date("15 мая 1990") == "1990-05-15"

    def test_text_month_russian_genitive(self):
        assert parse_date("13 ноября 1989 года") == "1989-11-13"

    def test_invalid_text_returns_none(self):
        assert parse_date("just a sentence with no date") is None

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_invalid_month_returns_none(self):
        # Month 13 doesn't exist
        assert parse_date("15.13.1990") is None

    def test_future_year(self):
        assert parse_date("2050-01-01") == "2050-01-01"

    def test_historical_year(self):
        assert parse_date("1850-06-15") == "1850-06-15"

    def test_too_old_year_returns_none(self):
        assert parse_date("1700-01-01") is None

    def test_feb_31_returns_none(self):
        # February 31st does not exist
        assert parse_date("31.02.1990") is None

    def test_feb_29_leap_year_valid(self):
        # 2000 is a leap year
        assert parse_date("29.02.2000") == "2000-02-29"

    def test_feb_29_non_leap_year_returns_none(self):
        # 1991 is not a leap year
        assert parse_date("29.02.1991") is None


@pytest.mark.unit
class TestParseTime:
    """Tests for parse_time() – regex-based, no LLM."""

    def test_24h_colon(self):
        assert parse_time("14:30") == "14:30"

    def test_24h_with_seconds(self):
        assert parse_time("14:30:00") == "14:30"

    def test_short_hour(self):
        assert parse_time("7:45") == "07:45"

    def test_midnight(self):
        assert parse_time("00:00") == "00:00"

    def test_pm_suffix(self):
        assert parse_time("2:30 PM") == "14:30"

    def test_am_suffix_noon(self):
        assert parse_time("12:00 AM") == "00:00"

    def test_pm_noon(self):
        assert parse_time("12:00 PM") == "12:00"

    def test_time_in_sentence(self):
        assert parse_time("I was born at 05:16 in the morning") == "05:16"

    def test_invalid_text_returns_none(self):
        assert parse_time("just text") is None

    def test_empty_string_returns_none(self):
        assert parse_time("") is None

    def test_invalid_minute_returns_none(self):
        assert parse_time("10:99") is None

    def test_ampm_hour_zero_returns_none(self):
        # Hour 0 is not valid in 12-hour notation
        assert parse_time("0:30 PM") is None

    def test_ampm_hour_13_returns_none(self):
        # Hour 13 is not valid in 12-hour notation
        assert parse_time("13:30 PM") is None

    def test_space_separated_not_matched_in_date(self):
        # "15 05 1990" should NOT be parsed as time 15:05 (it's a date)
        assert parse_time("15 05 1990") is None


@pytest.mark.unit
class TestGeocodePlace:
    """Tests for geocode_place() – uses mocked HTTP, no real network calls."""

    @pytest.mark.asyncio
    async def test_successful_geocoding(self):
        mock_response_data = [
            {
                "lat": "55.7558",
                "lon": "37.6173",
                "display_name": "Москва, Центральный федеральный округ, Россия",
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch("src.birth_data_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await geocode_place("Москва")

        assert result is not None
        assert abs(result["lat"] - 55.7558) < 0.001
        assert abs(result["lng"] - 37.6173) < 0.001
        assert result["location"] == "Москва, Центральный федеральный округ"

    @pytest.mark.asyncio
    async def test_no_results_returns_none(self):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("src.birth_data_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await geocode_place("xyznonexistentplace123")

        assert result is None

    @pytest.mark.asyncio
    async def test_network_error_returns_none(self):
        with patch("src.birth_data_collector.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("network error"))
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await geocode_place("Moscow")

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_string_returns_none(self):
        result = await geocode_place("")
        assert result is None
