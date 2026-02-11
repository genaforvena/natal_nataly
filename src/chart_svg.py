"""
SVG Chart Visualization Module
Generates basic SVG natal chart visualizations
"""
import logging
import math
import os
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Zodiac sign symbols
ZODIAC_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
    "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "Ascendant": "AC"
}


def generate_chart_svg(natal_chart: Dict[str, Any], width: int = 600, height: int = 600) -> str:
    """
    Generate a basic SVG natal chart visualization.
    
    Args:
        natal_chart: Natal chart data with planetary positions
        width: SVG width in pixels
        height: SVG height in pixels
        
    Returns:
        SVG string
    """
    logger.info("Generating SVG natal chart")
    
    try:
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 60
        
        svg_parts = []
        svg_parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
        
        # Background
        svg_parts.append(f'<rect width="{width}" height="{height}" fill="#1a1a2e"/>')
        
        # Outer circle
        svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" stroke="#4a4a6a" stroke-width="2"/>')
        
        # Inner circle
        inner_radius = radius * 0.7
        svg_parts.append(
            f'<circle cx="{center_x}" cy="{center_y}" r="{inner_radius}" '
            f'fill="none" stroke="#4a4a6a" stroke-width="1"/>'
        )
        
        # Zodiac wheel (12 segments)
        for i in range(12):
            angle_start = (i * 30 - 90) * math.pi / 180
            angle_end = ((i + 1) * 30 - 90) * math.pi / 180
            
            # Draw segment line
            x = center_x + radius * math.cos(angle_start)
            y = center_y + radius * math.sin(angle_start)
            svg_parts.append(f'<line x1="{center_x}" y1="{center_y}" x2="{x}" y2="{y}" stroke="#4a4a6a" stroke-width="1"/>')
            
            # Add zodiac sign label
            angle_mid = (angle_start + angle_end) / 2
            label_radius = radius + 25
            label_x = center_x + label_radius * math.cos(angle_mid)
            label_y = center_y + label_radius * math.sin(angle_mid)
            
            sign_name = list(ZODIAC_SYMBOLS.keys())[i]
            sign_symbol = ZODIAC_SYMBOLS[sign_name]
            svg_parts.append(
                f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
                f'dominant-baseline="middle" fill="#8a8aaa" font-size="18" font-family="Arial">'
                f'{sign_symbol}</text>'
            )
        
        # Plot planets
        for planet_name, data in natal_chart.items():
            if not isinstance(data, dict) or 'degree' not in data:
                continue
            
            degree = data['degree']
            # Convert degree to angle (0° Aries = 0°, going counter-clockwise)
            angle = (degree - 90) * math.pi / 180
            
            # Position on chart
            planet_radius = inner_radius + (radius - inner_radius) / 2
            planet_x = center_x + planet_radius * math.cos(angle)
            planet_y = center_y + planet_radius * math.sin(angle)
            
            # Get planet symbol
            symbol = PLANET_SYMBOLS.get(planet_name, planet_name[:2])
            
            # Draw planet
            color = get_planet_color(planet_name)
            svg_parts.append(f'<circle cx="{planet_x}" cy="{planet_y}" r="8" fill="{color}"/>')
            svg_parts.append(
                f'<text x="{planet_x}" y="{planet_y}" text-anchor="middle" '
                f'dominant-baseline="middle" fill="white" font-size="12" font-family="Arial" '
                f'font-weight="bold">{symbol}</text>'
            )
        
        # Title
        svg_parts.append(
            f'<text x="{center_x}" y="30" text-anchor="middle" '
            f'fill="#ffffff" font-size="24" font-family="Arial" font-weight="bold">'
            f'Natal Chart</text>'
        )
        
        svg_parts.append('</svg>')
        
        svg_content = '\n'.join(svg_parts)
        logger.info("SVG chart generated successfully")
        return svg_content
        
    except Exception as e:
        logger.exception(f"Error generating SVG chart: {e}")
        raise


def get_planet_color(planet_name: str) -> str:
    """Get color for a planet"""
    colors = {
        "Sun": "#FFD700",
        "Moon": "#C0C0C0",
        "Mercury": "#FFA500",
        "Venus": "#FF69B4",
        "Mars": "#FF4500",
        "Jupiter": "#4169E1",
        "Saturn": "#8B4513",
        "Uranus": "#00CED1",
        "Neptune": "#9370DB",
        "Pluto": "#800080",
        "Ascendant": "#00FF00"
    }
    return colors.get(planet_name, "#FFFFFF")


def save_chart_svg(telegram_id: str, natal_chart: Dict[str, Any], charts_dir: str = "./charts") -> str:
    """
    Generate and save SVG chart to file.
    
    Args:
        telegram_id: User's Telegram ID
        natal_chart: Natal chart data
        charts_dir: Directory to save charts
        
    Returns:
        Path to saved SVG file
    """
    logger.info(f"Saving SVG chart for user {telegram_id}")
    
    # Create charts directory if it doesn't exist
    os.makedirs(charts_dir, exist_ok=True)
    
    # Generate SVG
    svg_content = generate_chart_svg(natal_chart)
    
    # Save to file
    file_path = os.path.join(charts_dir, f"{telegram_id}.svg")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    logger.info(f"SVG chart saved to: {file_path}")
    return file_path
