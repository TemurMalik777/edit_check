import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .log_utils import log

def wait_for_fiskal_module(driver, log_panel):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select-selection-item"))
        )
        log(log_panel, "🟢 Fiskal modul render bo‘ldi, 10 sekund kutiladi...")
        time.sleep(10)
        log(log_panel, "⏳ 10 sekund kutildi, jarayon davom etadi")
    except TimeoutException:
        log(log_panel, "⚠️ Fiskal modul element topilmadi, 10 sekund kutiladi baribir...")
        time.sleep(10)

def get_selected_module_text(driver):
    try:
        elems = driver.find_elements(By.CSS_SELECTOR, ".ant-select-selection-item, .ant-select-selection-placeholder")
        for e in elems:
            txt = e.text.strip()
            if txt:
                return txt
        sel = driver.find_element(By.CSS_SELECTOR, "div.ant-select.ant-select-single")
        return sel.text.strip()
    except Exception:
        return ""
