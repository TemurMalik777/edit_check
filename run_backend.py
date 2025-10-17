from excel_handler import process_excel
from config import DEFAULT_EXCEL_PATH, DEFAULT_ZIP_PATH

class LogToTerminal:
    def append(self, text):
        print(text)

if __name__ == "__main__":
    print("Jarayon boshlandi...")
    try:
        log_panel = LogToTerminal()
        process_excel(DEFAULT_EXCEL_PATH, DEFAULT_ZIP_PATH, log_panel)
        print("Jarayon tugadi ✅")
    except Exception as e:
        print("Xato:", e)