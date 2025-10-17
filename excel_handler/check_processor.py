import psycopg2
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def process_checks(connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT chek_raqam, summa, miqdor, mxik, ulchov, faktura_summa, faktura_miqdor 
                FROM checks
                WHERE faktura_summa IS NOT NULL AND faktura_miqdor IS NOT NULL
            """)
            rows = cursor.fetchall()

        if not rows:
            logger.warning("❌ Hech qanday ma'lumot topilmadi")
            return

        grouped = defaultdict(list)
        for row in rows:
            grouped[row[3]].append({
                "chek_raqam": row[0],
                "summa": float(row[1] or 0),
                "miqdor": row[2],
                "mxik": row[3],
                "ulchov": row[4],
                "faktura_summa": float(row[5] or 0),
                "faktura_miqdor": float(row[6] or 0),
            })

        with connection.cursor() as cursor:
            for mxik, items in grouped.items():
                faktura_summa = items[0]["faktura_summa"]
                faktura_miqdor = items[0]["faktura_miqdor"]

                total = 0
                valid_checks = []
                for item in items:
                    total += item["summa"]
                    valid_checks.append(item)
                    if total >= faktura_summa * 1.1:  # 10% oshish chegarasi
                        break

                bir_birik = round(total / faktura_miqdor, 2)
                logger.info(f"MXIK {mxik}: jami={total}, bir_birik={bir_birik}")

                for item in valid_checks:
                    miqdor = round(item["summa"] / bir_birik, 2)
                    cursor.execute("""
                        INSERT INTO select_checks (chek_raqam, summa, miqdor, mxik, ulchov, bir_birik)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        item["chek_raqam"],
                        item["summa"],
                        miqdor,
                        item["mxik"],
                        item["ulchov"],
                        bir_birik
                    ))

            connection.commit()
            logger.info("✅ Barcha ma'lumotlar select_checks jadvaliga yozildi")

    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        connection.rollback()
