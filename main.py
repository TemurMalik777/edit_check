from selenium_scripts.actions.process_excel import process_excel
from config import DEFAULT_EXCEL_PATH, DEFAULT_ZIP_PATH
from database.chek_importer import ChekImporter

class LogToTerminal:
    def append(self, text):
        print(text)

if __name__ == "__main__":
    print("🚀 Jarayon boshlandi...")
    try:
        log_panel = LogToTerminal()
        process_excel(DEFAULT_EXCEL_PATH, DEFAULT_ZIP_PATH, log_panel)
        print("✅ Excel jarayoni tugadi, endi ma’lumotlar bazaga yoziladi...")

        importer = ChekImporter()
        importer.import_from_excel(DEFAULT_EXCEL_PATH)
        print("✅ Jarayon tugadi, ma’lumotlar bazaga yozildi.")
    except Exception as e:
        print("❌ Xato:", e)
