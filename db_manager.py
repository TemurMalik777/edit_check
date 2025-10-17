# db_manager.py deb saqlab, import qiling
from db_manager import DatabaseConnection

# Sozlamalarni o'rnating
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'sizning_database',
    'user': 'sizning_user',
    'password': 'sizning_parol'
}

# Ishlating
db = DatabaseConnection(db_config)