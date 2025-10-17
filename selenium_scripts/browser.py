from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

def create_driver(use_profile=False, profile_path=None):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Agar persistent profil ishlatmoqchi bo'lsak:
    if use_profile:
        if not profile_path:
            # default profil papkasi (projekt ichida .chrome_profile)
            profile_path = os.path.abspath("./.chrome_profile")
        options.add_argument(f"--user-data-dir={profile_path}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://my3.soliq.uz/") 
    return driver
