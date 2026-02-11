"""
Unit tests for chart generation module (services/chart_builder.py).

Tests the core natal chart generation functionality including:
- Chart generation from date/time/location
- Text export formatting
- JSON structure generation
"""

import pytest
from src.services.chart_builder import (
    build_natal_chart_text_and_json,
    deg_to_dms,
    house_suffix
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
        assert house_suffix(1) == "st"
        assert house_suffix(2) == "nd"
        assert house_suffix(3) == "rd"
        assert house_suffix(4) == "th"
        assert house_suffix(11) == "th"
        assert house_suffix(12) == "th"

    def test_build_natal_chart_basic(self):
        """Test basic natal chart generation."""
        # Test with known birth data
        result = build_natal_chart_text_and_json(
            name="Test User",
            year=1990,
            month=1,
            day=15,
            hour=14,
            minute=30,
            lat=40.7128,
            lng=-74.0060,
            city="New York",
            nation="USA"
        )
        
        # Verify chart text is generated
        assert isinstance(result, dict)
        assert "text_export" in result
        assert "chart_json" in result
        
        text_export = result["text_export"]
        chart_json = result["chart_json"]
        
        assert isinstance(text_export, str)
        assert len(text_export) > 0
        assert "Sun" in text_export
        assert "Moon" in text_export
        
        # Verify JSON structure
        assert isinstance(chart_json, dict)
        assert "planets" in chart_json
        assert "houses" in chart_json
        assert "meta" in chart_json
        
        # Check metadata
        assert chart_json["meta"]["city"] == "New York"
        assert chart_json["meta"]["nation"] == "USA"
        
        # Check planets structure
        planets = chart_json["planets"]
        planet_names = [p["name"] for p in planets]
        assert "Sun" in planet_names
        assert "Moon" in planet_names

    def test_build_natal_chart_with_different_locations(self):
        """Test chart generation with different geographic locations."""
        locations = [
            (51.5074, -0.1278, "London", "UK"),  # London
            (35.6762, 139.6503, "Tokyo", "Japan"),  # Tokyo
            (-33.8688, 151.2093, "Sydney", "Australia")  # Sydney
        ]
        
        for lat, lng, city, nation in locations:
            result = build_natal_chart_text_and_json(
                name="Test User",
                year=1985,
                month=6,
                day=21,
                hour=8,
                minute=0,
                lat=lat,
                lng=lng,
                city=city,
                nation=nation
            )
            
            assert isinstance(result, dict)
            assert "text_export" in result
            assert "chart_json" in result
            assert len(result["text_export"]) > 0

    def test_build_natal_chart_invalid_date(self):
        """Test chart generation with invalid date."""
        with pytest.raises(Exception, match="Failed to generate natal chart"):
            build_natal_chart_text_and_json(
                name="Test User",
                year=1990,
                month=13,  # Invalid month
                day=32,  # Invalid day
                hour=14,
                minute=30,
                lat=40.7128,
                lng=-74.0060
            )

    def test_build_natal_chart_timezone_handling(self):
        """Test chart generation with explicit timezone."""
        result = build_natal_chart_text_and_json(
            name="Test User",
            year=1990,
            month=1,
            day=15,
            hour=14,
            minute=30,
            lat=40.7128,
            lng=-74.0060,
            city="New York",
            nation="USA",
            tz_str="America/New_York"
        )
        
        assert isinstance(result, dict)
        assert result["chart_json"]["meta"]["timezone"] == "America/New_York"
