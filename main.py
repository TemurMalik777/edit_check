from database.chek_importer import ChekImporter

if __name__ == "__main__":
    excel_path = "test_data.xlsx"  # Excel fayl nomi (aniq yo‘l bo‘lsin)
    importer = ChekImporter()
    importer.import_from_excel(excel_path)
