import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .upload_zip_modal import upload_zip_modal
from captcha.captcha_solver import *
from .click_save_chek import *
from .log_utils import log


def _set_input(driver, selectors, value, log_panel, wait_seconds=5):
    for sel in selectors:
        try:
            el = WebDriverWait(driver, wait_seconds).until(
                EC.element_to_be_clickable((By.XPATH, sel))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.clear()
            driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                el, str(value)
            )
            log(log_panel, f"🟢 {sel} uchun qiymat yozildi: {value}")
            return True
        except Exception:
            continue
    return False


def select_mxik_code(driver, mxik_value, log_panel, timeout=12):
    """
    MXIK (ant-select) ni bosadi, input paydo bo'lgach yozadi va pastdagi ro'yxatdan
    mos variantni tanlaydi. Agar id yoki strukturalar dinamik bo'lsa, fallback qilinadi.
    """
    try:
        log(log_panel, "🔄 MXIK kodi tanlash jarayoni boshlandi...")

        # 1) Ant-select konteynerini topish (productCode bo'lgan element)
        select_xpath = "//div[contains(@class,'ant-select') and (contains(@name,'productCode') or contains(@name,'productCode'))]"
        mxik_select = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, select_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", mxik_select)
        driver.execute_script("arguments[0].click();", mxik_select)   # js click barqaror
        log(log_panel, "📂 MXIK tanlash oynasi ochildi.")
        time.sleep(0.3)

        # 2) Avval shu select ichidagi inputni tekshirish (ba'zan shu yerdadir)
        input_box = None
        try:
            # element ichida .find_element qaytaradi yoki xato tushadi
            candidate = mxik_select.find_element(By.CSS_SELECTOR, "input.ant-select-selection-search-input")
            if candidate.is_displayed():
                input_box = candidate
        except Exception:
            input_box = None

        # 3) Agar shu yerda topilmasa — global ravishda ko'rinadigan inputni topamiz
        if input_box is None:
            input_box = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input.ant-select-selection-search-input"))
            )

        # 4) inputga yozish (foydalanuvchi kabi, bir martalik click yetarli)
        try:
            input_box.click()
        except Exception:
            pass
        # NOTE: sen "tozalash kerak emas" deding — shuning uchun clear qilmaymiz
        input_box.send_keys(str(mxik_value))
        log(log_panel, f"⌨️ MXIK kodi yozildi: {mxik_value}")
        time.sleep(0.6)  # server/JS ro'yxatni chiqarishi uchun kichik kutish

        # 5) Faol dropdownni kutamiz (ant-select-dropdown va hidden bo'lmagan)
        dropdown_xpath = "//div[contains(@class,'ant-select-dropdown') and not(contains(@class,'ant-select-dropdown-hidden'))]"
        dropdown = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, dropdown_xpath))
        )

        # 6) variantlarni olamiz (ant-select-item-option-content ichidagi matnlar)
        option_xpath = f"{dropdown_xpath}//div[contains(@class,'ant-select-item-option-content')]"
        options = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, option_xpath))
        )

        if not options:
            raise Exception("MXIK variantlari topilmadi (options bo'sh).")

        # 7) Matnga mos keladigan variantni qidiramiz (birinchi to'liq teng yoki contains)
        matched = None
        for opt in options:
            t = opt.text.strip()
            # birinchi to'liq mos yoki qiymat matn ichida bo'lsa tanlash
            if str(mxik_value) == t or str(mxik_value) in t:
                matched = opt
                break

        # agar topilmasa, active item yoki birinchi elementga fallback
        if matched is None:
            try:
                matched = dropdown.find_element(By.CSS_SELECTOR, ".ant-select-item-option-active .ant-select-item-option-content")
            except Exception:
                matched = options[0] if options else None
                log(log_panel, "⚠️ Mos MXIK topilmadi — birinchi variantga fallback qilinmoqda.")

        if matched is None:
            raise Exception("Hech qanday MXIK varianti tanlanmadi.")

        # 8) Tanlash (scroll + js click)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", matched)
        driver.execute_script("arguments[0].click();", matched)
        log(log_panel, f"✅ MXIK kodi tanlandi: {matched.text.strip()}")
        return True

    except Exception as e:
        # debug: saqlaymiz screenshot va page source
        os.makedirs("screenshots", exist_ok=True)
        fname = f"screenshots/mxik_error_{int(time.time())}.png"
        try:
            driver.save_screenshot(fname)
            log(log_panel, f"⚠️ MXIK tanlashda xatolik: {e}. Screenshot: {fname}")
        except Exception:
            log(log_panel, f"⚠️ MXIK tanlashda xatolik: {e}. Screenshot saqlanmadi.")
        try:
            src = driver.page_source
            with open("debug_mxik_page.html", "w", encoding="utf-8") as f:
                f.write(src)
            log(log_panel, "🧾 debug_mxik_page.html saqlandi (page_source).")
        except Exception:
            pass
        return False



def select_unit_name(
    driver,
    unit_value,
    log_panel,
    timeout=12,
    per_item_scroll=300,
    per_item_sleep=0.45,
    max_no_change_rounds=20
):
    from selenium.common.exceptions import (
        StaleElementReferenceException,
        ElementClickInterceptedException,
        TimeoutException
    )
    import os, time

    try:
        log(log_panel, "🔄 Ulchov birligi tanlash jarayoni boshlandi...")

        select_xpath = "//div[contains(@class,'ant-select') and contains(@name,'unitName')]"
        unit_select = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, select_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", unit_select)
        try:
            unit_select.click()
        except Exception:
            driver.execute_script("arguments[0].click();", unit_select)

        log(log_panel, "📂 Ulchov tanlash oynasi ochildi.")
        time.sleep(0.5)

        dropdown_xpath = "//div[contains(@class,'ant-select-dropdown') and not(contains(@class,'ant-select-dropdown-hidden'))]"
        dropdown = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, dropdown_xpath))
        )

        try:
            scroll_area = dropdown.find_element(By.CLASS_NAME, "rc-virtual-list-holder")
        except Exception:
            try:
                scroll_area = dropdown.find_element(By.CLASS_NAME, "rc-virtual-list")
            except Exception:
                scroll_area = dropdown

        option_xpath = f"{dropdown_xpath}//div[contains(@class,'ant-select-item-option-content')]"
        target = str(unit_value).lower().strip()

        unique_seen, unique_set = [], set()
        total_checked = 0
        no_change_rounds = 0

        try:
            last_scroll = driver.execute_script("return arguments[0].scrollTop;", scroll_area)
        except Exception:
            last_scroll = None

        while True:
            log(log_panel, "🔍 Izlayapti...")
            try:
                options = driver.find_elements(By.XPATH, option_xpath)
            except StaleElementReferenceException:
                time.sleep(0.12)
                options = driver.find_elements(By.XPATH, option_xpath)

            for opt in options:
                try:
                    text = opt.get_attribute("textContent") or opt.text or ""
                    text = text.strip()
                except StaleElementReferenceException:
                    continue
                if not text:
                    continue

                if text not in unique_set:
                    unique_set.add(text)
                    unique_seen.append(text)
                    total_checked += 1

                if text.lower().strip() == target:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
                        time.sleep(0.18)
                        try:
                            opt.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", opt)
                        log(log_panel, f"✅ Topildi va tanlandi: {text}")
                        return True
                    except StaleElementReferenceException:
                        candidates = driver.find_elements(By.XPATH, option_xpath)
                        for c in candidates:
                            try:
                                t2 = (c.get_attribute("textContent") or c.text or "").strip()
                            except StaleElementReferenceException:
                                continue
                            if t2.lower().strip() == target:
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", c)
                                time.sleep(0.18)
                                try:
                                    c.click()
                                except Exception:
                                    driver.execute_script("arguments[0].click();", c)
                                log(log_panel, f"✅ Topildi va tanlandi (retry): {t2}")
                                return True
                        continue

            try:
                before_scroll = driver.execute_script("return arguments[0].scrollTop;", scroll_area)
            except Exception:
                before_scroll = None

            driver.execute_script("arguments[0].scrollTop += arguments[1];", scroll_area, per_item_scroll)
            time.sleep(per_item_sleep)

            try:
                after_scroll = driver.execute_script("return arguments[0].scrollTop;", scroll_area)
            except Exception:
                after_scroll = None

            if before_scroll is not None and after_scroll is not None:
                if after_scroll == before_scroll:
                    no_change_rounds += 1
                else:
                    no_change_rounds = 0
            else:
                no_change_rounds += 1

            if no_change_rounds >= max_no_change_rounds or len(unique_seen) > 5000:
                break

        log(log_panel, f"⚠️ '{unit_value}' ulchov birligi topilmadi.")
        return False

    except Exception as e:
        os.makedirs("screenshots", exist_ok=True)
        fname = f"screenshots/unit_error_{int(time.time())}.png"
        try:
            driver.save_screenshot(fname)
            log(log_panel, f"❌ Xatolik: {e}. Screenshot: {fname}")
        except Exception:
            log(log_panel, f"❌ Xatolik: {e}. Screenshot saqlanmadi.")

        with open("debug_unit_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log(log_panel, "🧾 debug_unit_page.html saqlandi (page_source).")
        raise



def fill_edit_check_fields(driver, data, log_panel):
    """
    Chek tahrirlash oynasidagi maydonlarni to'ldiradi,
    ZIP faylni yuklaydi, CAPTCHA'ni yechadi va saqlash jarayonini bajaradi.
    """
    fields = {
        "price": ["Сумма", "Summa", "summa", "price"],
        "amount": ["Миқдори", "Miqdor", "miqdor", "amount"],
        "mxik": ["МХИК коди", "MXIK", "MHHK", "mxik"],
        "unit": ["Ўлчов бирлиги", "ulchov", "unit"]
    }

    try:
        fields_filled = []
        zip_uploaded = False
        captcha_solved = False
        
        log(log_panel, "\n" + "="*60)
        log(log_panel, "📝 MAYDONLARNI TO'LDIRISH BOSHLANDI")
        log(log_panel, "="*60 + "\n")
        
        for name, variants in fields.items():
            # Exceldan qiymatni olish
            value = next((data[v] for v in variants if data.get(v)), None)
            if not value:
                log(log_panel, f"ℹ️ {name} Excelda yo'q, o'tkazib yuborildi.")
                continue

            ok = False
            
            # MXIK tanlash
            if name == "mxik":
                ok = select_mxik_code(driver, value, log_panel)
                if ok:
                    fields_filled.append("mxik")
                    log(log_panel, f"✅ MXIK tanlandi: {value}")

            # Ulchov birligi tanlash
            elif name == "unit":
                ok = select_unit_name(driver, value, log_panel)
                if ok:
                    fields_filled.append("unit")
                    log(log_panel, f"✅ Ulchov birligi tanlandi: {value}")
                    
                    # ZIP fayl yuklash
                    log(log_panel, "\n📦 ZIP fayl yuklanmoqda...")
                    time.sleep(1)
                    zip_ok = upload_zip_modal(driver, log_panel, zip_folder=r"C:\lll_ha")
                    if zip_ok:
                        zip_uploaded = True
                        log(log_panel, "✅ ZIP fayl yuklandi!")
                    
                    # Captcha yechish
                    log(log_panel, "\n🤖 Captcha yechish boshlandi...")
                    time.sleep(1)
                    captcha_ok = solve_captcha(driver, log_panel)
                    if captcha_ok:
                        captcha_solved = True
                        log(log_panel, "✅ Captcha muvaffaqiyatli yechildi!")
                    else:
                        log(log_panel, "❌ Captcha yechishda xato!")
                else:
                    log(log_panel, "⚠️ Ulchov birligi tanlanmadi!")

            # Oddiy maydonlar (Summa, Miqdor)
            else:
                selectors = [
                    f"//input[contains(@name, 'restore') and contains(@name, '{name}')]",
                    f"//input[contains(@name, '{name}')]"
                ]
                ok = _set_input(driver, selectors, value, log_panel)
                if ok:
                    fields_filled.append(name)
                    log(log_panel, f"✅ {name} = {value}")

            # Agar maydon topilmasa
            if not ok:
                os.makedirs("screenshots", exist_ok=True)
                fname = f"screenshots/missing_{name}_{int(time.time())}.png"
                driver.save_screenshot(fname)
                log(log_panel, f"⚠️ {name} topilmadi! Screenshot: {fname}")

        # Natijalarni ko'rsatish
        log(log_panel, "\n" + "="*60)
        log(log_panel, "📊 TO'LDIRILGAN MAYDONLAR HISOBOTI")
        log(log_panel, "="*60)
        log(log_panel, f"✅ To'ldirilgan maydonlar: {', '.join(fields_filled) if fields_filled else 'Yo\'q'}")
        log(log_panel, f"📦 ZIP yuklandi: {'Ha' if zip_uploaded else 'Yo\'q'}")
        log(log_panel, f"🤖 Captcha yechildi: {'Ha' if captcha_solved else 'Yo\'q'}")
        log(log_panel, "="*60 + "\n")
        
        # Saqlash shartlarini tekshirish
        if not captcha_solved:
            log(log_panel, "❌ XATO: Captcha yechilmagan - saqlash amalga oshmaydi!")
            return False
        
        if len(fields_filled) == 0:
            log(log_panel, "❌ XATO: Hech qanday maydon to'ldirilmagan!")
            return False
        
        # SAQLASH JARAYONI
        log(log_panel, "\n" + "="*60)
        log(log_panel, "🚀 SAQLASH JARAYONI BOSHLANDI")
        log(log_panel, "="*60 + "\n")
        time.sleep(1)
        
        save_ok = click_save_button_in_modal(driver, log_panel, timeout=15, max_retries=3)
        
        if save_ok:
            log(log_panel, "\n" + "="*60)
            log(log_panel, "✅✅✅ CHEK MUVAFFAQIYATLI SAQLANDI! ✅✅✅")
            log(log_panel, "="*60 + "\n")
            time.sleep(2)
            return True
        else:
            log(log_panel, "\n" + "="*60)
            log(log_panel, "❌❌❌ SAQLASHDA MUAMMO! ❌❌❌")
            log(log_panel, "="*60 + "\n")
            return False

    except Exception as e:
        log(log_panel, f"\n❌ KRITIK XATO: {e}")
        import traceback
        log(log_panel, traceback.format_exc())
        return False