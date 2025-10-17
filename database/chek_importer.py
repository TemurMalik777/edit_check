import openpyxl
import psycopg2
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("import.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChekImporter:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "cheak_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "5432"),
            "port": int(os.getenv("DB_PORT", 5432))
        }
        self.conn = None
        self.cur = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cur = self.conn.cursor()
            logger.info("✅ PostgreSQL bilan ulanish o‘rnatildi")

            self.cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

            # ✅ Jadval tuzilmasini o‘qib bajarish
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                self.cur.execute(sql_script)
                logger.info("📦 schema.sql bajarildi (jadval va funksiyalar yaratildi)")

            self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Ulanishda yoki schema.sql bajarishda xato: {e}")
            raise


    def disconnect(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            logger.info("🔌 Ulanish yopildi")

    def clean_numeric(self, value):
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", ".").replace(" ", "")
            return float(value)
        except:
            return None

    def read_excel(self, path):
        try:
            wb = openpyxl.load_workbook(path)
            sheet = wb.active
            headers = [cell.value for cell in sheet[1]]
            expected = ["Chek_raqam", "Summa", "Miqdor", "MXIK", "ulchov", "Faktura_summa", "Faktura_miqdor"]

            if headers != expected:
                logger.warning("⚠️ Excel ustunlari quyidagicha bo‘lishi kerak:")
                logger.warning(expected)
                logger.warning(f"Sizda: {headers}")

            data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue

                data.append({
                    "chek_raqam": str(row[0]),
                    "summa": self.clean_numeric(row[1]),
                    "miqdor": self.clean_numeric(row[2]),
                    "mxik": str(row[3]) if row[3] else None,
                    "ulchov": str(row[4]) if row[4] else None,
                    "faktura_summa": self.clean_numeric(row[5]),
                    "faktura_miqdor": self.clean_numeric(row[6]),
                })

            logger.info(f"📊 {len(data)} ta qator o‘qildi")
            return data

        except Exception as e:
            logger.error(f"❌ Excelni o‘qishda xato: {e}")
            return []

    def insert_data(self, data):
        if not self.cur:
            logger.error("❌ Ma'lumotlar bazasiga ulanilmagan.")
            return

        query = """
            INSERT INTO checks (
                chek_raqam, summa, miqdor, mxik, ulchov, faktura_summa, faktura_miqdor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        inserted, skipped = 0, 0
        for row in data:
            try:
                self.cur.execute(query, (
                    row["chek_raqam"],
                    row["summa"],
                    row["miqdor"],
                    row["mxik"],
                    row["ulchov"],
                    row["faktura_summa"],
                    row["faktura_miqdor"]
                ))
                inserted += 1
            except psycopg2.Error as e:
                logger.warning(f"⚠️ {row['chek_raqam']} kiritilmadi: {e.pgerror}")
                skipped += 1

        self.conn.commit()
        logger.info(f"✅ {inserted} ta yozuv kiritildi, {skipped} ta o‘tkazib yuborildi")

    def import_from_excel(self, excel_path):
        try:
            self.connect()
            data = self.read_excel(excel_path)
            if data:
                self.insert_data(data)
            else:
                logger.warning("⚠️ Exceldan hech qanday ma’lumot o‘qilmadi.")
        finally:
            self.disconnect()
