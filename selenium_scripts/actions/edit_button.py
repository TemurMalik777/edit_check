from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .log_utils import log

def click_edit_button(driver, log_panel):
    try:
        edit_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Таҳрирлаш') or contains(.,'Taxrirlash')]"))
        )
        driver.execute_script("arguments[0].click();", edit_btn)
        log(log_panel, "✏️ Taxrirlash tugmasi bosildi.")
        return True
    except Exception:
        log(log_panel, "⚠️ Taxrirlash tugmasi topilmadi.")
        return False
