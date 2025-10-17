import openpyxl

def read_excel(path):
    wb = openpyxl.load_workbook(path)
    sheet = wb.active
    data = []

    # 1-qator: faqat qiymati bor ustunlarni olish
    headers = []
    for cell in sheet[1]:
        if cell.value is not None:
            headers.append(str(cell.value).strip().replace(" ", "_"))

    expected = ["Chek_raqam", "Summa", "Miqdor", "MXIK", "ulchov", "Faktura_summa", "Faktura_miqdor"]

    if headers != expected:
        print("⚠️ Ustun nomlari to‘g‘ri emas. Quyidagi tartibda bo‘lishi kerak:")
        print(expected)
        print("Sizda esa:", headers)

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue
        row_values = list(row)[:len(expected)]  # Keraksiz ustunlarni e'tiborga olmaslik

        data.append({
            "Chek_raqam": row_values[0],
            "Summa": row_values[1],
            "Miqdor": row_values[2],
            "MXIK": row_values[3],
            "ulchov": row_values[4],
            "Faktura_summa": row_values[5],
            "Faktura_miqdor": row_values[6],
        })

    print(f"📊 Excel fayldan {len(data)} ta qator o‘qildi.")
    return data
