#!/usr/bin/env python3
"""
Aviation Visualization Launcher
=============================

Launch the advanced Streamlit aviation visualization application.
"""

import subprocess
import sys
from pathlib import Path
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pydeck', 
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Not installed")
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print("Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✅ All dependencies satisfied!")
    return True

def launch_streamlit_app():
    """Launch the Streamlit application"""
    
    app_path = Path(__file__).parent / "aviation_visualization" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ Application not found at {app_path}")
        return False
    
    print(f"🚀 Launching Streamlit application...")
    print(f"📁 App location: {app_path}")
    print(f"🌐 Opening in browser...")
    
    try:
        # Change to the project directory
        os.chdir(Path(__file__).parent)
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(app_path),
            '--browser.gatherUsageStats', 'false'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    
    print("🛩️ Advanced Aviation Visualization Launcher")
    print("=" * 48)
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\nPlease install missing packages and try again.")
        return
    
    print("\n🎯 Features of the Advanced Aviation App:")
    print("   • 🗺️ 2D/3D map visualization with multiple styles")
    print("   • 📡 Real-time weather station data from database")
    print("   • ✈️ Interactive route planning with validation")
    print("   • 🌤️ Weather tooltips on hover")
    print("   • 📊 Flight statistics and weather summaries")
    print("   • 🎛️ Full control panel with toggles and settings")
    
    input("\n👆 Press Enter to launch the application...")
    
    if launch_streamlit_app():
        print("\n✅ Application launched successfully!")
    else:
        print("\n❌ Failed to launch application")

if __name__ == "__main__":
    main()