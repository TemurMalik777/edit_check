import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal, ROUND_HALF_UP

class FakturaProcessor:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS checks (
                chek_raqami BIGINT PRIMARY KEY,
                summa NUMERIC NOT NULL,
                miqdor NUMERIC,
                mxik VARCHAR(50) NOT NULL,
                ulchov VARCHAR(50) NOT NULL,
                faktura_summa NUMERIC,
                faktura_miqdor NUMERIC,
                processed BOOLEAN DEFAULT FALSE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS select_checks (
                id SERIAL PRIMARY KEY,
                chek_raqami BIGINT,
                summa NUMERIC,
                miqdor NUMERIC,
                mxik VARCHAR(50),
                ulchov VARCHAR(50),
                bir_birlik NUMERIC
            )
        ''')
        self.conn.commit()

    def add_check(self, chek_raqami, summa, mxik, ulchov, faktura_summa=None, faktura_miqdor=None):
        self.cursor.execute('''
            INSERT INTO checks (chek_raqami, summa, mxik, ulchov, faktura_summa, faktura_miqdor)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (chek_raqami) DO NOTHING
        ''', (chek_raqami, summa, mxik, ulchov, faktura_summa, faktura_miqdor))
        self.conn.commit()

    def get_unique_faktura_items(self):
        self.cursor.execute('''
            SELECT DISTINCT mxik, ulchov, faktura_summa, faktura_miqdor
            FROM checks
            WHERE faktura_summa IS NOT NULL
              AND faktura_miqdor IS NOT NULL
              AND processed = FALSE
            ORDER BY mxik
        ''')
        return self.cursor.fetchall()

    def get_checks_for_mxik(self, mxik, ulchov):
        self.cursor.execute('''
            SELECT chek_raqami, summa, mxik, ulchov
            FROM checks
            WHERE mxik = %s AND ulchov = %s AND processed = FALSE
            ORDER BY chek_raqami
        ''', (mxik, ulchov))
        return self.cursor.fetchall()

    def process_faktura_item(self, faktura_item):
        mxik = faktura_item['mxik']
        ulchov = faktura_item['ulchov']
        faktura_summa = Decimal(str(faktura_item['faktura_summa']))
        faktura_miqdor = Decimal(str(faktura_item['faktura_miqdor']))
        max_summa = faktura_summa * Decimal('1.10')

        checks = self.get_checks_for_mxik(mxik, ulchov)
        if not checks:
            return []

        selected_checks = []
        total_summa = Decimal('0')

        for check in checks:
            check_summa = Decimal(str(check['summa']))
            if total_summa + check_summa <= max_summa:
                selected_checks.append(check)
                total_summa += check_summa
                if total_summa >= faktura_summa:
                    break

        if not selected_checks:
            return []

        bir_birlik = total_summa / faktura_miqdor
        results, total_miqdor = [], Decimal('0')

        for i, check in enumerate(selected_checks):
            check_summa = Decimal(str(check['summa']))
            if i == len(selected_checks) - 1:
                miqdor = faktura_miqdor - total_miqdor
            else:
                miqdor = check_summa / bir_birlik
                miqdor = miqdor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_miqdor += miqdor

            result = {
                'chek_raqami': check['chek_raqami'],
                'summa': float(check_summa),
                'miqdor': float(miqdor),
                'mxik': mxik,
                'ulchov': ulchov,
                'bir_birlik': float(bir_birlik.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            }
            results.append(result)

            self.cursor.execute('''
                INSERT INTO select_checks (chek_raqami, summa, miqdor, mxik, ulchov, bir_birlik)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (result['chek_raqami'], result['summa'], result['miqdor'],
                  result['mxik'], result['ulchov'], result['bir_birlik']))

            self.cursor.execute('UPDATE checks SET processed = TRUE WHERE chek_raqami = %s', (check['chek_raqami'],))

        self.conn.commit()
        return results

    def process_all_fakturas(self):
        faktura_items = self.get_unique_faktura_items()
        all_results = {}
        for item in faktura_items:
            key = f"{item['mxik']}_{item['ulchov']}"
            results = self.process_faktura_item(item)
            if results:
                all_results[key] = results
        return all_results

    def get_select_checks_results(self):
        self.cursor.execute('SELECT * FROM select_checks ORDER BY id')
        return self.cursor.fetchall()

    def print_results(self):
        rows = self.get_select_checks_results()
        print("="*100)
        print(f"{'Chek №':<12} {'Summa':<12} {'Miqdor':<12} {'MXIK':<15} {'Ulchov':<12} {'Bir birlik':<12}")
        print("="*100)
        for r in rows:
            print(f"{r['chek_raqami']:<12} {r['summa']:<12.2f} {r['miqdor']:<12.2f} {r['mxik']:<15} {r['ulchov']:<12} {r['bir_birlik']:<12.2f}")

    def close(self):
        self.cursor.close()
        self.conn.close()
