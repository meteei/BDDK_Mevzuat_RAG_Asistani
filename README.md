# 🏦 BDDK Mevzuat Asistanı & Kurumsal RAG Sistemi

BDDK (Bankacılık Düzenleme ve Denetleme Kurumu) mevzuatlarını, yönetmeliklerini ve tebliğlerini işlemek, vektörleştirmek ve sorgulamak için tasarlanmış akıllı, anlamsal bir Soru-Cevap RAG (Retrieval-Augmented Generation) sistemidir. FastAPI, Streamlit, LangChain, Milvus ve SQLAlchemy kullanılarak **Mikroservis** prensiplerine uygun olarak geliştirilmiştir.

Kullanıcıların karmaşık bankacılık regülasyonları üzerinden sorular sormasına olanak tanır ve belgelerden bağlama duyarlı, kaynak atıflı ve doğru yanıtlar sağlar.

## 📌 Genel Bakış

Bu proje, basit bir Python betiği olmaktan çıkarılarak uçtan uca kurumsal bir RAG chatbot sistemine dönüştürülmüştür. Ön yüz (Frontend) ve arka plan (Backend) tamamen izole çalışır.
Tüm soru-cevap trafiği, API performans metrikleri (istek süresi, kaynaklar) ve kullanıcı geri bildirimleri (is_helpful) ilişkisel veritabanında asenkron olarak saklanır.

## 🚀 Temel Teknolojiler ve Mimari

* **FastAPI:** API istekleri için asenkron, yüksek performanslı ve tip güvenli backend katmanı.
* **Streamlit:** Canlı chat özelliklerine, kaynak gösterimine ve yönetici paneline sahip modern web arayüzü.
* **LangChain & LLM:** Metinlerin anlamsal vektörlerini üretmek ve LLM (Büyük Dil Modeli) üzerinden kaynak atıflı doğal dil yanıtları oluşturmak için kullanılır.
* **Milvus:** Vektörleştirilmiş mevzuat maddeleri arasında milisaniyeler düzeyinde benzerlik araması yapmak için kullanılan vektör veri tabanı.
* **SQLAlchemy & Alembic:** PostgreSQL veritabanı ORM modellerini yönetir ve veritabanı şema geçişlerini (migrations) veri kaybı olmadan takip eder.
* **PostgreSQL (Docker):** Kullanıcı sorgularını, asistan yanıtlarını, işlem sürelerini ve geri bildirim loglarını kaydeder.

## ✨ Özellikler

* **Mikroservis Mimarisi (Frontend ↔ Backend Ayrımı):** Web arayüzü doğrudan veritabanına bağlanmaz; tüm işlemler güvenli REST API (FastAPI) uç noktaları üzerinden yönetilir.
* **RAG Tabanlı Atıflı Yanıt Üretimi:** LLM halüsinasyonlarını engellemek için cevaplar doğrudan BDDK mevzuat maddelerine dayandırılır. Kullanıcıya verilen cevabın altında orijinal mevzuat kaynağı genişletilebilir bir menüde sunulur.
* **Kullanıcı Geri Bildirim Döngüsü (Feedback Loop):** Sohbet arayüzünde her cevabın altında 👍 (Faydalı) ve 👎 (Geliştirilmeli) butonları çıkar. Verilen tepkiler `PUT` isteği ile anlık olarak veritabanındaki `is_helpful` sütununa işlenir.
* **Yönetici Paneli (Admin Dashboard):** Streamlit yan menüsünde bulunan "Son İstekleri Göster" butonu sayesinde, yöneticiler sistemin performansını, yanıt sürelerini (ms) ve log kayıtlarını canlı bir tablo halinde inceleyebilir.
* **Veritabanı Versiyon Kontrolü:** Alembic entegrasyonu sayesinde veritabanı şemasına sonradan eklenen alanlar (örn. `is_helpful` kolonu) sistem durdurulmadan ve veri kaybı yaşanmadan `upgrade head` komutuyla içeri aktarılır.
* **CRUD API Altyapısı:** Geçmiş logları okumak, yeni log eklemek, güncellemek veya silmek için Swagger UI destekli tam kapsamlı API uç noktaları hazır durumdadır.

## 💡 Kullanım Senaryoları

* **Sayısal ve Risk Sorguları:** *"Bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az yüzde kaçtır ve bu oran hesaplanırken hangi risk türleri dikkate alınır?"*
* **Yönetimsel / Kurumsal Sorgular:** *"BDDK Kurumsal Yönetim İlkeleri Tebliği'ne göre, bir bankanın yönetim kurulunda denetim komitesi üyelerinin taşıması gereken şartlar nelerdir?"*
* **Müşteri İlişkileri ve Kredi Kartları:** *"Bankaların kredi kartı limit artırım taleplerini değerlendirirken müşterinin gelirine göre uygulaması gereken yasal asgari limit kuralları nelerdir?"*

## 🔄 Mimarisi ve İstek Akışı

1. **Soru Sorma:** Kullanıcı Streamlit arayüzünden sorusunu yazar. Soru `POST /api/ask` uç noktasına iletilir.
2. **RAG Arama:** Soru vektörleştirilir ve Milvus'ta benzerlik araması yapılarak en ilgili mevzuat maddeleri (kaynaklar) çekilir.
3. **Yanıt Üretimi:** Alınan kaynaklar ve soru LLM'e iletilir. Atıflı yanıt üretilir, yanıt süresi (ms) hesaplanır ve veritabanına log olarak kaydedilir (ID üretilir).
4. **Kullanıcıya Sunum:** Yanıt ve kaynaklar Streamlit ekranında gösterilir. Yanıtın altına üretilen veritabanı ID'sine bağlı geri bildirim butonları eklenir.
5. **Geri Bildirim Loglama:** Kullanıcı 👍/👎 butonuna bastığında `PUT /api/logs/{log_id}` tetiklenir ve o spesifik kaydın `is_helpful` değeri güncellenir.

## 📂 Proje Klasör Yapısı

├── alembic/                             # Alembic migrations veritabanı şema versiyonları
├── app/
│   ├── main.py                          # FastAPI sunucu başlatıcı ve yapılandırması
│   ├── models/                          
│   │   └── models.py                    # SQLAlchemy ORM modelleri (API Logs tablosu)
│   ├── schemas/                         
│   │   └── schemas.py                   # Pydantic girdi/çıktı şemaları (QueryRequest, QueryResponse)
│   └── routers/                         
│       └── rag_router.py                # FastAPI API Yönlendiricileri (GET, POST, PUT, DELETE uç noktaları)
│
├── frontend.py                          # Streamlit RAG sohbet, geri bildirim ve log yönetim arayüzü
├── run_ui.py                            # Streamlit başlatıcı script
├── docker-compose.yml                   # PostgreSQL veritabanı konteyner yapılandırması
├── alembic.ini                          # Alembic veritabanı göç yapılandırması
├── requirements.txt                     # Python bağımlılıkları listesi
└── .env                                 # Çevre değişkenleri (Lokal yapılandırma ve Veritabanı URL'i)

## 🛠️ Kurulum ve Başlatma

### Ön Koşullar
* Python 3.9+
* Docker ve Docker Compose (PostgreSQL için)

### Adım Adım Kurulum

**1. Bağımlılıkları Yükleyin**
Kök dizinde terminali açıp Python kütüphanelerini yükleyin:
pip install -r requirements.txt

**2. Çevre Değişkenlerini Düzenleyin**
Kök dizinde bir `.env` dosyası oluşturun ve veritabanı bağlantı cümlenizi ekleyin:
DATABASE_URL=postgresql://admin:adminpassword@localhost:5432/rag_logs

**3. Veritabanını Ayağa Kaldırın**
PostgreSQL servisini Docker üzerinden başlatın ve Alembic ile tabloları oluşturun:
alembic upgrade head

**4. Servisleri Başlatın**
Proje mikroservis mimarisinde olduğu için Backend ve Frontend iki ayrı terminalde çalıştırılmalıdır.

*Terminal 1: FastAPI Sunucusu (Backend)*
uvicorn main:app --reload --port 8002

*Terminal 2: Streamlit Arayüzü (Frontend)*
python run_ui.py

## 🔌 API Uç Noktaları (Endpoints) ve Örnekler

| Yöntem | Rota | Açıklama |
| :--- | :--- | :--- |
| **POST** | `/api/ask` | Kullanıcı sorgusunu alır, RAG ile yanıt üretir ve log_id döndürür. |
| **GET** | `/api/logs` | Veritabanındaki geçmiş soruları, yanıt sürelerini ve değerlendirmeleri listeler. |
| **PUT** | `/api/logs/{log_id}` | Belirli bir log kaydının `is_helpful` (Geri Bildirim) durumunu günceller. |
| **DELETE** | `/api/logs/{log_id}` | İstenilen bir log kaydını veritabanından siler. |

### Örnek İstek ve Yanıtlar

**1. Sohbet API Ucu (POST `/api/ask`)**
*İstek Gövdesi:*
{
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?"
}

*Yanıt Gövdesi:*
{
  "log_id": 42,
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?",
  "answer": "BDDK mevzuatına göre bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az %8'dir.",
  "time_taken_ms": 845,
  "sources": [
    "Bankaların Sermaye Yeterliliğinin Ölçülmesine İlişkin Yönetmelik - Madde 4"
  ]
}

**2. Geri Bildirim API Ucu (PUT `/api/logs/{log_id}?is_helpful=true`)**
*Arayüzden "Faydalı" butonuna basıldığında tetiklenir.*

*Yanıt Gövdesi:*
{
  "message": "Log 42 başarıyla güncellendi",
  "is_helpful": true
}

## 📊 Görsel İnceleme ve Yönetim Araçları

| Araç | URL | Açıklama |
| :--- | :--- | :--- |
| **Web Dashboard (Streamlit)** | `http://localhost:8501` | RAG sohbet, kaynak gösterimi ve geri bildirim arayüzü |
| **FastAPI Swagger Docs** | `http://localhost:8002/docs` | API dokümantasyonu, uç nokta listesi ve test arayüzü |
| **DBeaver / pgAdmin** | `localhost:5432` | PostgreSQL veritabanı görsel yönetim arayüzü |

---
*Geliştirici:* Ahmet Mete Işık