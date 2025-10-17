import time
import threading
from selenium.webdriver.support import expected_conditions as EC
from excel_handler.excel_reader import read_excel
from selenium_scripts.browser import create_driver
from .log_utils import log
from .login_checker import is_logged_in
from .fiskal_module import wait_for_fiskal_module
from .search_detail import perform_search_and_open_detail
from .field_filler import fill_edit_check_fields
from .edit_button import click_edit_button
from database.chek_importer import ChekImporter


def process_excel(excel_path, zip_path, log_panel):
    data = read_excel(excel_path)
    driver = create_driver()
    log(log_panel, f"📊 Excel fayldan {len(data)} ta qator o‘qildi.")

    # ✅ Parallel database yozish funksiyasi
    def save_to_database():
        importer = ChekImporter()
        importer.import_from_excel(excel_path)
        log(log_panel, "💾 Ma’lumotlar bazaga yozildi (parallel).")

    # 🔄 Parallel oqimni ishga tushirish
    db_thread = threading.Thread(target=save_to_database)
    db_thread.start()

    timeout = 300
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_logged_in(driver, log_panel):
            log(log_panel, "✅ Foydalanuvchi tizimga kirdi.")
            break
        time.sleep(2)
    else:
        log(log_panel, "❌ Tizimga kirish amalga oshmadi.", "error")
        driver.quit()
        return

    wait_for_fiskal_module(driver, log_panel)

    for idx, row in enumerate(data):
        chek_raqam = str(row.get("Chek_raqam", "")).strip()
        if not chek_raqam:
            log(log_panel, f"⚠️ {idx+1}-chekda 'Chek_raqam' yo‘q.")
            continue

        log(log_panel, f"🔹 {idx+1}-chek jarayoni boshlandi...")

        ok = perform_search_and_open_detail(driver, chek_raqam, log_panel)
        if not ok:
            log(log_panel, f"❌ Chek {chek_raqam} topilmadi yoki batafsil ochilmadi.")
            continue

        edit_ok = click_edit_button(driver, log_panel)
        if not edit_ok:
            log(log_panel, f"⚠️ Chek {chek_raqam}: Tahrirlash oynasi ochilmadi.")
            continue

        fill_edit_check_fields(driver, row, log_panel)
        log(log_panel, f"✅ Chek {chek_raqam} uchun maydonlar to‘ldirildi.")

    log(log_panel, "🎯 Barcha cheklar bo‘yicha jarayon tugadi.")
    driver.quit()

    # ✅ Dastur tugashidan oldin database yozish oqimi ham yakunlansin
    db_thread.join()
    log(log_panel, "✅ Parallel database yozish yakunlandi.")
