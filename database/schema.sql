-- Database yaratish (psql da bajaring)
-- CREATE DATABASE cheak_db WITH ENCODING 'UTF8';

-- Extension yaratish (UUID uchun)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Birinchi jadval: Asosiy cheklar jadvali
CREATE TABLE IF NOT EXISTS checks (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    chek_raqam VARCHAR(100) NOT NULL,
    summa DECIMAL(15, 2),
    miqdor DECIMAL(15, 8),
    mxik VARCHAR(100),
    ulchov VARCHAR(500),
    faktura_summa DECIMAL(15, 2),
    faktura_miqdor DECIMAL(15, 8),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ikkinchi jadval: Tanlangan cheklar
CREATE TABLE IF NOT EXISTS select_checks (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    chek_raqam VARCHAR(100) NOT NULL,
    summa DECIMAL(15, 2),
    miqdor DECIMAL(15, 8),
    mxik VARCHAR(100),
    ulchov VARCHAR(500),
    faktura_summa DECIMAL(15, 2),
    faktura_miqdor DECIMAL(15, 8),
    bir_birlik_narxi DECIMAL(15, 2),
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    selected_from_checks_id INTEGER REFERENCES checks(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indekslar
CREATE INDEX IF NOT EXISTS idx_checks_chek_raqam ON checks(chek_raqam);
CREATE INDEX IF NOT EXISTS idx_checks_mxik ON checks(mxik);
CREATE INDEX IF NOT EXISTS idx_checks_summa ON checks(summa);
CREATE INDEX IF NOT EXISTS idx_checks_created ON checks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_select_checks_chek_raqam ON select_checks(chek_raqam);
CREATE INDEX IF NOT EXISTS idx_select_checks_selected_at ON select_checks(selected_at DESC);

-- Trigger: updated_at yangilash
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger yaratish
DROP TRIGGER IF EXISTS trg_update_checks_updated_at ON checks;
CREATE TRIGGER trg_update_checks_updated_at
BEFORE UPDATE ON checks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- View yaratish: Statistika uchun
CREATE OR REPLACE VIEW checks_statistics AS
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT chek_raqam) as unique_cheks,
    SUM(summa) as total_summa,
    AVG(summa) as average_summa,
    MAX(summa) as max_summa,
    MIN(summa) as min_summa,
    SUM(faktura_summa) as total_faktura_summa,
    AVG(faktura_summa) as average_faktura_summa,
    COUNT(DISTINCT mxik) as unique_mxik_codes,
    MAX(created_at) as last_record_date,
    MIN(created_at) as first_record_date
FROM checks
WHERE is_active = true;

-- Function: Dublikat cheklar
CREATE OR REPLACE FUNCTION get_duplicate_checks()
RETURNS TABLE(
    chek_raqam VARCHAR,
    duplicate_count BIGINT,
    total_summa DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chek_raqam,
        COUNT(*) as duplicate_count,
        SUM(c.summa) as total_summa
    FROM checks c
    WHERE c.is_active = true
    GROUP BY c.chek_raqam
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: MXIK bo'yicha statistika
CREATE OR REPLACE FUNCTION get_mxik_statistics(mxik_code VARCHAR DEFAULT NULL)
RETURNS TABLE(
    mxik VARCHAR,
    record_count BIGINT,
    total_summa DECIMAL,
    average_summa DECIMAL,
    total_miqdor DECIMAL
) AS $$
BEGIN
    IF mxik_code IS NULL THEN
        RETURN QUERY
        SELECT 
            c.mxik,
            COUNT(*) as record_count,
            SUM(c.summa) as total_summa,
            AVG(c.summa) as average_summa,
            SUM(c.miqdor) as total_miqdor
        FROM checks c
        WHERE c.is_active = true AND c.mxik IS NOT NULL
        GROUP BY c.mxik
        ORDER BY COUNT(*) DESC
        LIMIT 50;
    ELSE
        RETURN QUERY
        SELECT 
            c.mxik,
            COUNT(*) as record_count,
            SUM(c.summa) as total_summa,
            AVG(c.summa) as average_summa,
            SUM(c.miqdor) as total_miqdor
        FROM checks c
        WHERE c.is_active = true AND c.mxik LIKE '%' || mxik_code || '%'
        GROUP BY c.mxik
        ORDER BY COUNT(*) DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Umumiy statistika view
CREATE OR REPLACE VIEW overall_statistics AS
SELECT 
    (SELECT COUNT(*) FROM checks WHERE is_active = true) as total_checks,
    (SELECT COUNT(*) FROM select_checks) as total_selected,
    (SELECT COUNT(DISTINCT chek_raqam) FROM checks WHERE is_active = true) as unique_checks,
    (SELECT SUM(summa) FROM checks WHERE is_active = true) as total_amount,
    (SELECT COUNT(DISTINCT mxik) FROM checks WHERE is_active = true) as unique_products;