import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from .log_utils import log


def perform_search_and_open_detail(driver, chek_raqam, log_panel,
                                   timeout_search=20, timeout_detail=30, timeout_modal=30):
    # ========================================
    # INPUT TOPISH
    # ========================================
    check_selectors = [
        "input[name='check']",
        "input.ant-select-selection-search-input",
        "input.ant-input[name='check']",
        "input[placeholder='Chek raqami']"
    ]
    chek_input = None
    for sel in check_selectors:
        try:
            chek_input = WebDriverWait(driver, timeout_search).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            break
        except Exception:
            continue
    
    if not chek_input:
        log(log_panel, f"❌ Chek {chek_raqam}: 'check' input topilmadi.", "error")
        return False

    # ========================================
    # YANGI CHEK RAQAMINI TO'G'RIDAN-TO'G'RI YOZISH (React uchun)
    # ========================================
    try:
        old_value = chek_input.get_attribute('value')
        if old_value:
            log(log_panel, f"🧹 Avvalgi qiymat: '{old_value}'")

        # JavaScript orqali to'g'ridan-to'g'ri value o'zgartirish va eventlarni trigger qilish
        driver.execute_script("""
            const input = arguments[0];
            const newValue = arguments[1];
            
            // React uchun native input event yaratish
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(input, newValue);
            
            // Barcha kerakli eventlarni trigger qilish
            const inputEvent = new Event('input', { bubbles: true });
            const changeEvent = new Event('change', { bubbles: true });
            
            input.dispatchEvent(inputEvent);
            input.dispatchEvent(changeEvent);
        """, chek_input, str(chek_raqam))
        
        time.sleep(0.5)
        
        # Tekshirish
        current_value = chek_input.get_attribute('value')
        if current_value == str(chek_raqam):
            log(log_panel, f"✅ Chek raqami muvaffaqiyatli o'zgartirildi: {chek_raqam}")
        else:
            log(log_panel, f"⚠️ Qiymat kutilganidek emas: '{current_value}' (kutilgan: {chek_raqam})")
            
    except Exception as e:
        log(log_panel, f"❌ Chek raqamini kiritishda xato: {e}")
        return False


    # ========================================
    # QIDIRISH TUGMASINI BOSISH
    # ========================================
    search_xpaths = [
        "//button[contains(.,'Қидириш') or contains(.,'Qidirish') or contains(.,'Қидирув')]",
        "//input[@name='check']/ancestor::form//button"
    ]
    search_btn = None
    for xp in search_xpaths:
        try:
            search_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            break
        except Exception:
            continue

    if not search_btn:
        log(log_panel, f"❌ Chek {chek_raqam}: Qidirish tugmasi topilmadi.", "error")
        return False

    try:
        search_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", search_btn)
    log(log_panel, f"🔍 Chek {chek_raqam}: Qidirish bosildi.")
    
    time.sleep(2)  # Natijalar yuklanishini kutish

    # ========================================
    # BATAFSIL TUGMASINI BOSISH
    # ========================================
    try:
        batafsil_btn = WebDriverWait(driver, timeout_detail).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Batafsil') or contains(.,'Батафсил')]"))
        )
        batafsil_btn.click()
        log(log_panel, f"🟢 Chek {chek_raqam}: Batafsil ochildi.")
        time.sleep(2)

        # ========================================
        # TAHRIRLASH TUGMASINI BOSISH
        # ========================================
        try:
            edit_btn = WebDriverWait(driver, timeout_modal).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(.,'Таҳрирлаш') or contains(.,'Taxrirlash') or contains(.,'Тахрирлаш') or contains(.,'Tahrirlash') or contains(.,'Edit') or contains(.,'Редактировать')]"
                ))
            )
            driver.execute_script("arguments[0].click();", edit_btn)
            log(log_panel, f"✏️ Chek {chek_raqam}: Таҳрирлаш tugmasi bosildi.")
            time.sleep(1)
            return True
        except TimeoutException:
            log(log_panel, f"⚠️ Chek {chek_raqam}: Таҳрирлаш tugmasi topilmadi yoki sahifada chiqmadi.", "warn")
            return False

    except TimeoutException:
        log(log_panel, f"❌ Chek {chek_raqam}: Batafsil topilmadi.", "error")
        return False
