"""Browser configuration for web automation."""

from browser_use import BrowserUse

def get_browser_config():
    """Get browser configuration with optimized settings."""
    return {
        "headless": True,
        "defaultViewport": {
            "width": 1920,
            "height": 1080
        },
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080"
        ],
        "ignoreHTTPSErrors": True,
        "timeout": 60000  # Increase default timeout to 60 seconds
    }

def create_browser():
    """Create a browser instance with optimized settings."""
    browser = BrowserUse()
    browser.set_config(get_browser_config())
    return browser
