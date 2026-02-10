"""
Unit tests for chart generation module (services/chart_builder.py).

Tests the core natal chart generation functionality including:
- Chart generation from date/time/location
- Text export formatting
- JSON structure generation
"""

import pytest
from datetime import datetime
from services.chart_builder import (
    build_natal_chart_text_and_json,
    deg_to_dms,
    house_suffix,
    get_timezone_from_coordinates
)


@pytest.mark.unit
class TestChartBuilder:
    """Tests for chart generation functions."""

    def test_deg_to_dms_conversion(self):
        """Test decimal degrees to degrees/minutes/seconds conversion."""
        assert deg_to_dms(15.5) == "15°30'"
        assert deg_to_dms(0.0) == "0°00'"
        assert deg_to_dms(359.99) == "359°59'"
        assert deg_to_dms(10.25) == "10°15'"

    def test_house_suffix(self):
        """Test ordinal suffix generation for house numbers."""
        assert house_suffix(1) == "1st"
        assert house_suffix(2) == "2nd"
        assert house_suffix(3) == "3rd"
        assert house_suffix(4) == "4th"
        assert house_suffix(11) == "11th"
        assert house_suffix(12) == "12th"

    def test_get_timezone_from_coordinates(self):
        """Test timezone detection from latitude/longitude."""
        # New York coordinates
        tz = get_timezone_from_coordinates(40.7128, -74.0060)
        assert tz == "America/New_York"
        
        # London coordinates
        tz = get_timezone_from_coordinates(51.5074, -0.1278)
        assert tz == "Europe/London"
        
        # Invalid coordinates should raise error or return None
        with pytest.raises(Exception):
            get_timezone_from_coordinates(999, 999)

    def test_build_natal_chart_basic(self):
        """Test basic natal chart generation."""
        # Test with known birth data
        dob = "1990-01-15"
        time_str = "14:30"
        lat = 40.7128
        lng = -74.0060
        original_input = f"DOB: {dob}\nTime: {time_str}\nLat: {lat}\nLng: {lng}"
        
        chart_text, chart_json = build_natal_chart_text_and_json(
            dob=dob,
            time=time_str,
            lat=lat,
            lng=lng,
            original_input=original_input
        )
        
        # Verify chart text is generated
        assert isinstance(chart_text, str)
        assert len(chart_text) > 0
        assert "Sun" in chart_text
        assert "Moon" in chart_text
        
        # Verify JSON structure
        assert isinstance(chart_json, dict)
        assert "planets" in chart_json
        assert "houses" in chart_json
        assert "metadata" in chart_json
        
        # Check metadata
        assert chart_json["metadata"]["date_of_birth"] == dob
        assert chart_json["metadata"]["time_of_birth"] == time_str
        
        # Check planets structure
        assert "Sun" in chart_json["planets"]
        assert "Moon" in chart_json["planets"]
        assert "degree" in chart_json["planets"]["Sun"]
        assert "sign" in chart_json["planets"]["Sun"]

    def test_build_natal_chart_with_different_locations(self):
        """Test chart generation with different geographic locations."""
        dob = "1985-06-21"
        time_str = "08:00"
        
        # Test multiple locations
        locations = [
            (51.5074, -0.1278, "Europe/London"),  # London
            (35.6762, 139.6503, "Asia/Tokyo"),     # Tokyo
            (-33.8688, 151.2093, "Australia/Sydney")  # Sydney
        ]
        
        for lat, lng, expected_tz in locations:
            original_input = f"DOB: {dob}\nTime: {time_str}\nLat: {lat}\nLng: {lng}"
            chart_text, chart_json = build_natal_chart_text_and_json(
                dob=dob,
                time=time_str,
                lat=lat,
                lng=lng,
                original_input=original_input
            )
            
            assert isinstance(chart_text, str)
            assert len(chart_text) > 0
            assert isinstance(chart_json, dict)
            # Verify timezone is detected
            assert chart_json["metadata"]["timezone"] == expected_tz

    def test_build_natal_chart_invalid_date(self):
        """Test chart generation with invalid date format."""
        with pytest.raises(Exception):
            build_natal_chart_text_and_json(
                dob="invalid-date",
                time="14:30",
                lat=40.7128,
                lng=-74.0060,
                original_input="invalid"
            )

    def test_build_natal_chart_invalid_coordinates(self):
        """Test chart generation with invalid coordinates."""
        with pytest.raises(Exception):
            build_natal_chart_text_and_json(
                dob="1990-01-15",
                time="14:30",
                lat=999,  # Invalid latitude
                lng=-74.0060,
                original_input="invalid coords"
            )
