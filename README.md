# 🏦 BDDK Mevzuat Asistanı & Kurumsal RAG Sistemi

BDDK (Bankacılık Düzenleme ve Denetleme Kurumu) mevzuatlarını, yönetmeliklerini ve tebliğlerini işlemek, vektörleştirmek ve sorgulamak için tasarlanmış akıllı, anlamsal bir Soru-Cevap RAG (Retrieval-Augmented Generation) sistemidir. FastAPI, Streamlit, LangChain, Milvus ve SQLAlchemy kullanılarak **Mikroservis** prensiplerine uygun olarak geliştirilmiştir.

Kullanıcıların karmaşık bankacılık regülasyonları üzerinden sorular sormasına olanak tanır ve belgelerden bağlama duyarlı, kaynak atıflı ve doğru yanıtlar sağlar.

## 📌 Genel Bakış

Bu proje, basit bir Python betiği olmaktan çıkarılarak uçtan uca kurumsal bir RAG platformuna dönüştürülmüştür. Ön yüz (Frontend) ve arka plan (Backend) tamamen izole çalışır. Tüm soru-cevap trafiği, API performans metrikleri (istek süresi, kaynaklar) ve kullanıcı geri bildirimleri (is_helpful) ilişkisel veritabanında asenkron olarak saklanır. Sistem, dinamik PDF yükleme ve oturum bazlı hafıza yetenekleriyle kesintisiz bir yapay zeka deneyimi sunar.

## 🚀 Temel Teknolojiler ve Mimari

* **FastAPI:** API istekleri için asenkron, yüksek performanslı ve tip güvenli backend katmanı.
* **Streamlit:** Canlı chat özelliklerine, kaynak gösterimine, dosya yükleme ve yönetici paneline sahip modern web arayüzü.
* **LangChain & LLM:** Metinlerin anlamsal vektörlerini üretmek, geçmişi hatırlayan arama motoru (History-Aware Retriever) kurmak ve LLM üzerinden kaynak atıflı doğal dil yanıtları oluşturmak için kullanılır.
* **Milvus:** Vektörleştirilmiş mevzuat maddeleri arasında milisaniyeler düzeyinde benzerlik araması yapmak için kullanılan vektör veri tabanı. Veri bütünlüğü için katı şema (strict schema) kuralları uygulanır.
* **SQLAlchemy & Alembic:** PostgreSQL veritabanı ORM modellerini yönetir ve veritabanı şema geçişlerini (migrations) veri kaybı olmadan takip eder.
* **PostgreSQL (Docker):** Kullanıcı sorgularını, asistan yanıtlarını, işlem sürelerini ve geri bildirim loglarını kaydeder.

## ✨ Özellikler

* **Oturum Bazlı Hafıza (Short-Term Memory):** `RunnableWithMessageHistory` ve `session_id` entegrasyonu sayesinde asistan, ardışık sorulardaki bağlamı unutmaz (Örn: "Peki bu komite ne zaman toplanır?"). Kullanıcı dilediği an "Yeni Sohbet Başlat" butonuyla hafızayı sıfırlayabilir.
* **Dinamik Belge İndeksleme (Ingestion API):** Sistemi durdurmaya gerek kalmadan arayüz üzerinden yepyeni PDF belgeleri yüklenebilir. Yüklenen belgeler otomatik olarak anlamsal parçalara (chunks) bölünür ve vektörleştirilir.
* **Akıllı Metadata Ayıklama (Regex):** Yüklenen mevzuat metinlerinin içinden Düzenli İfadeler (Regex) kullanılarak Madde Numaraları (`madde_no`) ve kaynak dosya isimleri otomatik olarak ayıklanır. Milvus veritabanının `int64` ve `varchar` şema gereksinimleri kusursuz şekilde karşılanır.
* **Sıfır Halüsinasyon (Zero-Hallucination):** Katı prompt mühendisliği (Strict Prompting) sayesinde, LLM yalnızca Milvus'tan dönen mevzuat bağlamını kullanmaya zorlanır. Bilgi mevzuatta yoksa sistem internetten uydurmak yerine *"Bu bilgi mevzuatta bulunmamaktadır"* yanıtını verir.
* **Kullanıcı Geri Bildirim Döngüsü (Feedback Loop):** Sohbet arayüzünde her cevabın altında 👍 (Faydalı) ve 👎 (Geliştirilmeli) butonları çıkar. Verilen tepkiler `PUT` isteği ile anlık olarak veritabanındaki `is_helpful` sütununa işlenir.
* **Yönetici Paneli (Admin Dashboard):** Yöneticiler sistemin performansını, yanıt sürelerini (ms) ve log kayıtlarını canlı bir tablo halinde Streamlit üzerinden inceleyebilir.

## 💡 Kullanım Senaryoları

* **Bağlam Korumalı Sorgular:** 
  *- Kullanıcı: "Bilgi Güvenliği Komitesi kimlerden oluşur?"*
  *- Kullanıcı: "Peki bu komite yılda kaç kez toplanmalıdır?" (Sistem 'bu komite' ifadesini hafızadan çözer).*
* **Sayısal ve Risk Sorguları:** *"Bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az yüzde kaçtır ve bu oran hesaplanırken hangi risk türleri dikkate alınır?"*
* **Yönetimsel / Kurumsal Sorgular:** *"BDDK Kurumsal Yönetim İlkeleri Tebliği'ne göre, bir bankanın yönetim kurulunda denetim komitesi üyelerinin taşıması gereken şartlar nelerdir?"*

## 🔄 Mimarisi ve İstek Akışı

1. **Soru Sorma:** Kullanıcı Streamlit arayüzünden sorusunu yazar. Soru, özel bir `session_id` ile birlikte `POST /api/ask` uç noktasına iletilir.
2. **Geçmişi Hatırlayan Arama (History-Aware Retrieval):** LangChain, önceki mesajlara bakarak soruyu bağımsızlaştırır ve Milvus'ta benzerlik araması yapar.
3. **Yanıt Üretimi:** Alınan kaynaklar ve soru LLM'e iletilir. Atıflı yanıt üretilir, yanıt süresi (ms) hesaplanır ve PostgreSQL veritabanına kaydedilir (ID üretilir).
4. **Geri Bildirim ve Loglama:** Kullanıcı yanıta 👍/👎 verdiğinde `PUT /api/logs/{log_id}` tetiklenir. Yöneticiler tüm bu akışı `GET /api/logs` üzerinden panele çeker.
5. **Dinamik Yükleme:** Yeni bir PDF yüklendiğinde `POST /api/upload` rotası tetiklenir, `rag_service.py` belgenin metadata'sını (madde_no) çıkarıp Milvus'a anında yazar.

## 📂 Proje Klasör Yapısı

```text
├── alembic/                             # Alembic migrations veritabanı şema versiyonları
├── app/
│   ├── main.py                          # FastAPI sunucu başlatıcı ve yapılandırması
│   ├── models/                          
│   │   └── models.py                    # SQLAlchemy ORM modelleri (API Logs tablosu)
│   ├── schemas/                         
│   │   └── schemas.py                   # Pydantic girdi/çıktı şemaları
│   ├── services/
│   │   └── rag_service.py               # Çekirdek İş Mantığı (LLM Zincirleri, Hafıza, PDF Yükleme ve Regex)
│   └── routers/                         
│       └── rag_router.py                # FastAPI Yönlendiricileri (GET, POST, PUT, DELETE uç noktaları)
│
├── frontend.py                          # Streamlit RAG sohbet, dosya yükleme ve log yönetim arayüzü
├── run_ui.py                            # Streamlit başlatıcı script
├── docker-compose.yml                   # PostgreSQL veritabanı konteyner yapılandırması
├── alembic.ini                          # Alembic veritabanı göç yapılandırması
├── requirements.txt                     # Python bağımlılıkları listesi
└── .env                                 # Çevre değişkenleri (Lokal yapılandırma ve Veritabanı URL'i)
```

## 🛠️ Kurulum ve Başlatma

### Ön Koşullar
* Python 3.9+
* Docker ve Docker Compose (PostgreSQL ve Milvus için)

### Adım Adım Kurulum

**1. Bağımlılıkları Yükleyin**
Kök dizinde terminali açıp Python kütüphanelerini yükleyin:
```bash
pip install -r requirements.txt
```

**2. Çevre Değişkenlerini Düzenleyin**
Kök dizinde bir `.env` dosyası oluşturun ve veritabanı bağlantı cümlenizi ekleyin:
```text
DATABASE_URL=postgresql://admin:adminpassword@localhost:5432/rag_logs
```

**3. Veritabanını Ayağa Kaldırın**
PostgreSQL servisini Docker üzerinden başlatın ve Alembic ile tabloları oluşturun:
```bash
alembic upgrade head
```

**4. Servisleri Başlatın**
Proje mikroservis mimarisinde olduğu için Backend ve Frontend iki ayrı terminalde çalıştırılmalıdır.

*Terminal 1: FastAPI Sunucusu (Backend)*
```bash
uvicorn main:app --reload --port 8002
```

*Terminal 2: Streamlit Arayüzü (Frontend)*
```bash
python run_ui.py
```

## 🔌 API Uç Noktaları (Endpoints) ve Örnekler

| Yöntem | Rota | Açıklama |
| :--- | :--- | :--- |
| **POST** | `/api/ask` | Kullanıcı sorgusunu ve `session_id` alır, RAG ile yanıt üretir ve log_id döndürür. |
| **POST** | `/api/upload` | Form-data olarak gönderilen PDF'i okur, şemalandırır ve canlı olarak vektör DB'ye ekler. |
| **GET** | `/api/logs` | Veritabanındaki geçmiş soruları, yanıt sürelerini ve değerlendirmeleri listeler. |
| **PUT** | `/api/logs/{log_id}` | Belirli bir log kaydının `is_helpful` (Geri Bildirim) durumunu günceller. |
| **DELETE** | `/api/logs/{log_id}` | İstenilen bir log kaydını veritabanından siler. |

### Örnek İstek ve Yanıtlar

**1. Sohbet API Ucu (POST `/api/ask`)**
*İstek Gövdesi:*
```json
{
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?",
  "session_id": "stajyer_test_01"
}
```

*Yanıt Gövdesi:*
```json
{
  "log_id": 42,
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?",
  "answer": "BDDK mevzuatına göre bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az %8'dir.",
  "time_taken_ms": 845,
  "sources": [
    "Bankaların Sermaye Yeterliliğinin Ölçülmesine İlişkin Yönetmelik - Madde 4"
  ],
  "session_id": "stajyer_test_01"
}
```

**2. Geri Bildirim API Ucu (PUT `/api/logs/{log_id}?is_helpful=true`)**
*Yanıt Gövdesi:*
```json
{
  "message": "Geri bildirim başarıyla kaydedildi.",
  "log_id": 42
}
```

## 📊 Görsel İnceleme ve Yönetim Araçları

| Araç | URL | Açıklama |
| :--- | :--- | :--- |
| **Web Dashboard (Streamlit)** | `http://localhost:8501` | RAG sohbet, dinamik belge yükleme, kaynak gösterimi ve admin paneli |
| **FastAPI Swagger Docs** | `http://localhost:8002/docs` | API dokümantasyonu, uç nokta listesi ve interaktif test arayüzü |
| **DBeaver / pgAdmin** | `localhost:5432` | PostgreSQL veritabanı görsel yönetim arayüzü |

---
*Geliştirici:* Ahmet Mete Işık