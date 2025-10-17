import requests
from config import CAPTCHA_API_KEY
import time, base64, requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium_scripts.actions.log_utils import log
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

POLL_INTERVAL = 5
POLL_RETRIES = 25

def solve_captcha(driver, log_panel):
    """Captcha yechish funksiyasi"""
    try:
        log(log_panel, "🔍 CAPTCHA topilmoqda...")
        try:
            captcha_el = driver.find_element(By.CSS_SELECTOR, ".ant-modal-body img[src^='data:image']")
        except Exception:
            captcha_el = driver.find_element(By.CSS_SELECTOR, ".ant-modal-body img")

        log(log_panel, "📷 Captcha elementi topildi, base64 olinmoqda...")

        # src atributidagi base64 qismni olish
        src_data = captcha_el.get_attribute("src")
        if "base64," in src_data:
            b64_image = src_data.split("base64,")[1]
        else:
            log(log_panel, "⚠️ Captcha base64 topilmadi, screenshot usuliga o'tamiz.")
            captcha_png = captcha_el.screenshot_as_png
            b64_image = base64.b64encode(captcha_png).decode("utf-8")

        # 2Captcha ga yuborish
        send = requests.post(
            "http://2captcha.com/in.php",
            data={"key": os.getenv("API_KEY"), "method": "base64", "body": b64_image, "json": 1},
            timeout=30
        ).json()

        if send.get("status") != 1:
            log(log_panel, f"❌ 2Captcha in.php xato: {send.get('request')}")
            return False

        req_id = send["request"]
        log(log_panel, f"📤 Captcha yuborildi (id={req_id}), yechim kutilmoqda...")

        for i in range(POLL_RETRIES):
            time.sleep(POLL_INTERVAL)
            result = requests.get(
                "http://2captcha.com/res.php",
                params={"key": os.getenv("API_KEY"), "action": "get", "id": req_id, "json": 1},
                timeout=30
            ).json()

            if result.get("status") == 1:
                captcha_text = result["request"]
                log(log_panel, f"✅ Captcha yechildi: {captcha_text}")
                try:
                    input_el = driver.find_element(By.NAME, "captchaValue")
                    input_el.clear()
                    input_el.send_keys(captcha_text)
                    log(log_panel, "✍️ Captcha qiymati yozildi.")
                    return True
                except Exception as e:
                    log(log_panel, f"⚠️ Captcha input topilmadi yoki yozilmadi: {e}")
                    return False

            if "ERROR" in result.get("request", ""):
                log(log_panel, f"❌ 2Captcha xato: {result.get('request')}")
                return False

            log(log_panel, f"⌛ Kutilmoqda... ({i+1}/{POLL_RETRIES})")

        log(log_panel, "⚠️ Captcha yechimiga vaqt tugadi (timeout).")
        return False

    except Exception as e:
        log(log_panel, f"❌ solve_captcha funksiyasida xatolik: {e}")
        return False