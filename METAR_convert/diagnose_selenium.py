"""
Selenium ChromeDriver Diagnostic Script

This script helps diagnose and fix ChromeDriver setup issues.
"""

import sys
import os
from pathlib import Path

print("🔍 Selenium ChromeDriver Diagnostic")
print("=" * 70)

# Check Python version
print(f"\n1. Python Version: {sys.version}")

# Check if selenium is installed
try:
    import selenium
    print(f"2. Selenium Version: {selenium.__version__}")
except ImportError:
    print("❌ Selenium not installed! Run: pip install selenium")
    sys.exit(1)

# Check if webdriver-manager is installed
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("3. Webdriver-manager: ✅ Installed")
except ImportError:
    print("❌ Webdriver-manager not installed! Run: pip install webdriver-manager")
    sys.exit(1)

# Check Chrome browser
print("\n4. Checking Chrome browser...")
try:
    import subprocess
    
    # Try to get Chrome version (macOS)
    try:
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   Chrome: {result.stdout.strip()}")
        else:
            print("   ⚠️ Chrome found but version check failed")
    except Exception as e:
        print(f"   ⚠️ Chrome check failed: {e}")
        print("   Make sure Google Chrome is installed")
except Exception as e:
    print(f"   ❌ Error checking Chrome: {e}")

# Test ChromeDriver download
print("\n5. Testing ChromeDriver download...")
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("   Attempting to download ChromeDriver...")
    
    # Try with different strategies
    try:
        driver_path = ChromeDriverManager().install()
        print(f"   ✅ ChromeDriver installed at: {driver_path}")
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        print("\n   Possible solutions:")
        print("   1. Check internet connection")
        print("   2. Try: pip install --upgrade webdriver-manager")
        print("   3. Use manual ChromeDriver installation (see below)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test basic Selenium
print("\n6. Testing basic Selenium setup...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        print("   ✅ Selenium is working correctly!")
        driver.quit()
    except Exception as e:
        print(f"   ❌ Selenium test failed: {e}")
        print("\n   This is the error preventing Nav Canada queries")
        
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Provide solutions
print("\n" + "=" * 70)
print("📋 SOLUTIONS:")
print("=" * 70)

print("""
If ChromeDriver download failed, try these solutions:

1. UPDATE WEBDRIVER-MANAGER:
   pip install --upgrade webdriver-manager

2. CLEAR CACHE:
   rm -rf ~/.wdm
   
3. MANUAL CHROMEDRIVER INSTALLATION:
   a) Check your Chrome version: chrome://version
   b) Download matching ChromeDriver from:
      https://chromedriver.chromium.org/downloads
   c) Place it in /usr/local/bin/ (macOS)
   d) Make it executable: chmod +x /usr/local/bin/chromedriver
   
4. USE SELENIUM MANAGER (Selenium 4.6+):
   Modify navcanada_simple_client.py to use built-in manager
   
5. CHECK FIREWALL/PROXY:
   If behind a corporate firewall, ChromeDriver download may be blocked
   
6. ALTERNATIVE: Use Firefox instead
   pip install geckodriver-autoinstaller
   
7. VERIFY INTERNET CONNECTION:
   curl -I https://chromedriver.storage.googleapis.com
""")

print("\n" + "=" * 70)
print("🔧 Quick Fix Command:")
print("=" * 70)
print("""
Run these commands:

pip install --upgrade selenium webdriver-manager
rm -rf ~/.wdm
python3 this_diagnostic_script.py
""")
