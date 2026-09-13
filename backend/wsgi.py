import multiprocessing
import os

# Gunicorn (Canlı Sunucu) Yapılandırma Dosyası
# Çalıştırmak için terminal komutu: gunicorn -c wsgi.py app.main:app

bind = "0.0.0.0:8080"
# İşlemci çekirdek sayısına göre dinamik işçi (worker) oluşturur
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
loglevel = "info"
accesslog = "-"
errorlog = "-"

print(f"🚀 Kurumsal ASGI/WSGI Sunucusu Başlatılıyor... İşçi Sayısı: {workers}")