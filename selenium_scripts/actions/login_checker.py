from selenium.webdriver.common.by import By
from .log_utils import log

def is_logged_in(driver, log_panel=None):
    try:
        driver.find_element(By.CSS_SELECTOR, "div.ant-select.ant-select-single")
        if log_panel:
            log(log_panel, "✅ Fiskal modul maydoni topildi (login muvaffaqiyatli).")
        return True
    except Exception:
        if log_panel:
            log(log_panel, "⏳ Fiskal modul maydoni hali yuklanmadi...")
        return False
