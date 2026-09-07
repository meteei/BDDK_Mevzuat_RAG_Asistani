from sqlalchemy import create_engine, text

# Veritabanı bağlantımız (app.py ile tamamen aynı)
DATABASE_URL = "postgresql://admin:adminpassword@localhost:5432/rag_logs"
engine = create_engine(DATABASE_URL)

# Veritabanına bağlanıp log tablosunu okuyoruz
with engine.connect() as conn:
    print("--- KAYITLI LOGLAR ---")
    result = conn.execute(text("SELECT id, time_taken_ms, prompt FROM api_logs"))

    for row in result:
        print(f"Kayıt No: {row[0]} | Süre: {row[1]} ms | Soru: {row[2]}")
    print("----------------------")