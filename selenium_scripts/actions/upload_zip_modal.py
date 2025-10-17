from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .log_utils import log



def upload_zip_modal(driver, log_panel, zip_folder=r"C:\lll_ha", timeout=12):
    """
    Modal ichidagi 'Файл танлаш' tugmasi orqali zip faylni tanlaydi va Saqlash tugmasini bosadi.
    - driver: Selenium WebDriver
    - log_panel: log yozish uchun funksiya yoki panel
    - zip_folder: lokal papka nomi, ichidan birinchi .zip fayl tanlanadi
    - timeout: WebDriverWait uchun sekund
    """
    import os, time, glob
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        log(log_panel, "🔄 Fayl yuklash jarayoni boshlandi...")

        # 1️⃣ Papkadan .zip fayl topish
        folder_path = os.path.abspath(zip_folder)
        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Zip papka topilmadi: {folder_path}")

        zip_files = sorted(glob.glob(os.path.join(folder_path, "*.zip")))
        if not zip_files:
            raise FileNotFoundError(f"Papka ichida .zip fayl topilmadi: {folder_path}")

        zip_path = zip_files[0]  # birinchi fayl
        log(log_panel, f"📁 Yuklanadigan fayl: {zip_path}")

        # 2️⃣ Modal ichidagi <input type='file'> elementini topish
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-modal-root"))
        )

        file_input = None
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for inp in inputs:
            try:
                accept = inp.get_attribute("accept") or ""
                if "zip" in accept or accept.strip() == "":
                    file_input = inp
                    break
            except Exception:
                continue

        if file_input is None and inputs:
            file_input = inputs[0]  # fallback

        if file_input is None:
            raise RuntimeError("input[type=file] elementi topilmadi.")

        # 3️⃣ Faylni yuborish
        file_input.send_keys(zip_path)
        log(log_panel, "⬆️ Fayl jo'natildi, yuklanishi kutilyapti...")
        time.sleep(0.6)  # server render uchun kutish

        # 4️⃣ Yuklangan fayl ro'yxatida ko'rinishini kutish
        uploaded = False
        wait_start = time.time()
        while time.time() - wait_start < timeout:
            try:
                uploaded_items = driver.find_elements(By.CSS_SELECTOR, ".ant-upload-list-item, .ant-upload-list .ant-upload-list-item")
                if uploaded_items:
                    for it in uploaded_items:
                        txt = (it.text or "").strip()
                        if os.path.basename(zip_path) in txt or txt != "":
                            uploaded = True
                            break
                if uploaded:
                    break
            except Exception:
                pass
            time.sleep(0.3)

        if not uploaded:
            log(log_panel, "⚠️ Fayl yuklandi deb tasdiqlanmadi — ammo davom etamiz (timeout).")
        else:
            log(log_panel, "✅ Fayl ro'yxatda ko'rindi (yuklandi).")

        # 5️⃣ Saqlash tugmasini bosish
        save_btn = None
        try:
            possible_buttons = driver.find_elements(By.XPATH, "//button[normalize-space(text())='Сақлаш' or normalize-space(text())='Сохранить' or normalize-space(text())='Save']")
            if possible_buttons:
                save_btn = possible_buttons[0]
            else:
                footers = driver.find_elements(By.CSS_SELECTOR, "div.ant-modal-footer, div[role='dialog'] .ant-modal-footer")
                for f in footers:
                    btns = f.find_elements(By.TAG_NAME, "button")
                    if len(btns) >= 2:
                        save_btn = btns[-1]
                        break

            if save_btn is None:
                raise RuntimeError("Saqlash tugmasi topilmadi.")

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
            time.sleep(0.12)
            try:
                save_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", save_btn)

            log(log_panel, "💾 Saqlash tugmasi bosildi — davom etilmoqda.")
            time.sleep(0.8)
            return True

        except Exception as e:
            raise RuntimeError("Saqlash tugmasini bosishda xato: " + str(e))

    except Exception as ex:
        os.makedirs("screenshots", exist_ok=True)
        fname = f"screenshots/upload_error_{int(time.time())}.png"
        try:
            driver.save_screenshot(fname)
            log(log_panel, f"❌ Fayl yuklashda xatolik: {ex}. Screenshot: {fname}")
        except Exception:
            log(log_panel, f"❌ Fayl yuklashda xatolik: {ex}. Screenshot saqlanmadi.")

        try:
            with open("debug_upload_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            log(log_panel, "🧾 debug_upload_page.html saqlandi (page_source).")
        except Exception:
            pass

        raise
