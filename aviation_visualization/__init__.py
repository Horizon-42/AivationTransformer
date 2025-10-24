"""
Aviation Weather Visualization Package
====================================

Modern interactive map visualization for aviation weather data using Streamlit + PyDeck.

This package provides a comprehensive real-time visualization system featuring:
- 3D interactive maps with 2D/3D switching
- Real-time weather station data with METAR parsing
- Interactive flight route planning
- Multiple map styles and themes
- Weather information on hover
- Smart caching and performance optimization

Main Classes:
- AdvancedAviationApp: Complete Streamlit application with all features

Example Usage:
    from aviation_visualization import AdvancedAviationApp
    
    # Launch the interactive Streamlit app
    app = AdvancedAviationApp()
    app.run()
    
    # Or use the launcher script
    # python3 launch_aviation_app.py
"""

__version__ = "2.0.0"
__author__ = "Aviation Transformer Project"

# Import main classes for easy access
from .streamlit_app import AdvancedAviationApp

__all__ = [
    "AdvancedAviationApp"
]