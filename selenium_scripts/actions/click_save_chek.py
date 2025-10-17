import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from captcha.captcha_solver import *
from .log_utils import log


def wait_for_notification(driver, log_panel, timeout=15):
    """
    Ant Design notifikatsiyasini kutish va turini aniqlash
    Returns: "success", "error", "captcha_error", None
    """
    
    try:
        log(log_panel, "⏳ Xabar kutilmoqda...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Variant 1: Ant Design notification
            try:
                notifications = driver.find_elements(By.CSS_SELECTOR, "div.ant-notification-notice")
                
                for notification in notifications:
                    if notification.is_displayed():
                        classes = notification.get_attribute("class")
                        
                        # Success xabari
                        if "ant-notification-notice-success" in classes:
                            log(log_panel, "✅ MUVAFFAQIYAT xabari topildi!")
                            
                            try:
                                desc = notification.find_element(By.CSS_SELECTOR, 
                                    ".ant-notification-notice-description div").text
                                log(log_panel, f"📝 Xabar: {desc}")
                            except:
                                pass
                            
                            return "success"
                        
                        # Error xabari
                        elif "ant-notification-notice-error" in classes:
                            log(log_panel, "❌ XATO xabari topildi!")
                            
                            try:
                                title = notification.find_element(By.CSS_SELECTOR, 
                                    ".ant-notification-notice-message").text
                                desc = notification.find_element(By.CSS_SELECTOR, 
                                    ".ant-notification-notice-description div").text
                                
                                log(log_panel, f"📝 {title}")
                                log(log_panel, f"📝 {desc}")
                                
                                # Captcha xatosi
                                if "рақамлар нотўғри" in desc or "captcha" in desc.lower() or "расмдаги" in desc.lower():
                                    log(log_panel, "🔴 CAPTCHA XATO!")
                                    return "captcha_error"
                                
                                return "error"
                                
                            except:
                                pass
                            
                            return "error"
            except:
                pass
            
            # Variant 2: Oddiy div matni ("Амалиёт муваффақиятли бажарилди!")
            try:
                success_divs = driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Амалиёт муваффақиятли') or contains(text(), 'муваффақиятли бажарилди') or contains(text(), 'муваффақиятли')]")
                
                for div in success_divs:
                    if div.is_displayed():
                        text = div.text
                        log(log_panel, f"✅ SUCCESS DIV topildi: {text}")
                        return "success"
            except:
                pass
            
            # Variant 3: Ant message (qisqa xabar)
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, "div.ant-message-notice")
                
                for msg in messages:
                    if msg.is_displayed():
                        text = msg.text
                        
                        if "муваффақиятли" in text.lower() or "успешно" in text.lower():
                            log(log_panel, f"✅ MESSAGE: {text}")
                            return "success"
                        elif "хато" in text.lower() or "ошибка" in text.lower():
                            log(log_panel, f"❌ ERROR MESSAGE: {text}")
                            return "error"
            except:
                pass
            
            time.sleep(0.5)  # Har 500ms tekshirish
        
        log(log_panel, "⏱️ Xabar topilmadi (timeout)")
        return None
    
    except Exception as e:
        log(log_panel, f"⚠️ Xabar tekshirishda xato: {e}")
        return None


def click_save_button_in_modal(driver, log_panel, timeout=15, max_retries=3):
    """Saqlash tugmasini bosish va natijani tekshirish (retry bilan)"""
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                log(log_panel, f"\n{'='*50}")
                log(log_panel, f"🔄 QAYTA URINISH #{attempt}/{max_retries}")
                log(log_panel, f"{'='*50}\n")
                time.sleep(2)
            
            # Tugmani topish
            log(log_panel, "🔍 Saqlash tugmasini qidirish...")
            
            save_button = None
            selectors = [
                "//button[@type='submit' and contains(text(), 'Сақлаш')]",
                "//button[@type='submit' and contains(text(), 'Saqlash')]",
                "(//div[@class='ant-modal-body']//button[@type='submit'])[last()]",
            ]
            
            for selector in selectors:
                try:
                    btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if btn.is_displayed():
                        save_button = btn
                        log(log_panel, f"✅ Tugma topildi")
                        break
                except:
                    continue
            
            if not save_button:
                log(log_panel, "❌ Saqlash tugmasi topilmadi!")
                return False
            
            # Tugmani bosish
            log(log_panel, "🚀 Saqlash tugmasi bosilmoqda...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
            time.sleep(0.5)
            
            try:
                save_button.click()
            except:
                driver.execute_script("arguments[0].click();", save_button)
            
            log(log_panel, "✅ Tugma bosildi!")
            
            # Xabarni kutish
            time.sleep(2)  # Biroz ko'proq kutish
            result = wait_for_notification(driver, log_panel, timeout=15)
            
            # SUCCESS
            if result == "success":
                log(log_panel, "\n" + "🎉"*20)
                log(log_panel, "🎊 MA'LUMOT MUVAFFAQIYATLI SAQLANDI! 🎊")
                log(log_panel, "🎉"*20 + "\n")
                
                time.sleep(2)
                
                # Modalni yopish
                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, ".ant-modal-close")
                    close_btn.click()
                    log(log_panel, "✅ Modal yopildi (X tugmasi)")
                    time.sleep(1)
                except:
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        log(log_panel, "✅ Modal yopildi (ESC)")
                        time.sleep(1)
                    except:
                        log(log_panel, "⚠️ Modal avtomatik yopilmadi")
                
                return True
            
            # CAPTCHA XATO
            elif result == "captcha_error":
                log(log_panel, "\n❌ CAPTCHA XATO!")
                
                if attempt < max_retries:
                    log(log_panel, "🔄 Captcha qayta yechiladi...")
                    time.sleep(2)
                    
                    # Captcha rasmini yangilash (agar kerak bo'lsa)
                    try:
                        refresh_btns = driver.find_elements(By.CSS_SELECTOR, 
                            "button[aria-label*='efresh'], button[class*='refresh'], .captcha-refresh")
                        for btn in refresh_btns:
                            if btn.is_displayed():
                                btn.click()
                                log(log_panel, "🔄 Captcha rasmi yangilandi")
                                time.sleep(1)
                                break
                    except:
                        pass
                    
                    # Captcha inputni tozalash
                    try:
                        captcha_input = driver.find_element(By.NAME, "captchaValue")
                        captcha_input.clear()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Captcha qayta yechish
                    captcha_ok = solve_captcha(driver, log_panel)
                    
                    if captcha_ok:
                        log(log_panel, "✅ Captcha qayta yechildi, yana uriniladi...")
                        time.sleep(1)
                        continue  # Keyingi urinishga o'tish
                    else:
                        log(log_panel, "❌ Captcha qayta yechilmadi!")
                        return False
                else:
                    log(log_panel, "❌ Maksimal urinishlar soni tugadi!")
                    return False
            
            # BOSHQA XATO
            elif result == "error":
                log(log_panel, f"\n❌ XATO (urinish {attempt}/{max_retries})")
                
                if attempt < max_retries:
                    log(log_panel, "⏳ 3 sekund kutib, qayta uriniladi...")
                    time.sleep(3)
                    continue
                else:
                    log(log_panel, "❌ Maksimal urinishlar soni tugadi!")
                    return False
            
            # XABAR TOPILMADI
            else:
                log(log_panel, "⚠️ Xabar topilmadi, modal holatini tekshirish...")
                time.sleep(3)  # Ko'proq kutish
                
                # Modal yopilganini tekshirish
                try:
                    modals = driver.find_elements(By.CSS_SELECTOR, ".ant-modal-mask")
                    visible_modals = [m for m in modals if m.is_displayed()]
                    
                    if len(visible_modals) == 0:
                        log(log_panel, "✅ Modal yopilgan - saqlangan deb hisoblanadi")
                        return True
                    else:
                        log(log_panel, "⚠️ Modal hali ochiq")
                        
                        if attempt < max_retries:
                            log(log_panel, "🔄 Qayta urinish...")
                            time.sleep(2)
                            continue
                        else:
                            log(log_panel, "⚠️ Modal ochiq qoldi, lekin davom ettiriladi")
                            return True
                except:
                    log(log_panel, "✅ Modal yo'q - saqlangan deb hisoblanadi")
                    return True
        
        except Exception as e:
            log(log_panel, f"❌ Urinish {attempt} xatosi: {e}")
            
            if attempt < max_retries:
                log(log_panel, "⏳ 2 sekund kutilmoqda...")
                time.sleep(2)
                continue
            else:
                log(log_panel, "❌ Barcha urinishlar muvaffaqiyatsiz tugadi!")
                return False
    
    return False