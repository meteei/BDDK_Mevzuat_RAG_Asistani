# 🏦 BDDK Mevzuat Asistanı & Kurumsal RAG Sistemi

PDF formatındaki bankacılık mevzuatlarını, yönetmeliklerini ve tebliğlerini işlemek, vektörleştirmek ve sorgulamak için tasarlanmış akıllı, anlamsal bir kurumsal Soru-Cevap RAG (Retrieval-Augmented Generation) sistemidir. FastAPI, OpenAI, Milvus, RustFS, PostgreSQL ve Streamlit kullanılarak **Clean Architecture** ve **Mikroservis** prensiplerine uygun olarak geliştirilmiştir.

Kullanıcıların karmaşık bankacılık regülasyonları üzerinden sorular sormasına olanak tanır ve belgelerden bağlama duyarlı, kaynak atıflı ve tavizsiz denetçi tonunda doğru yanıtlar sağlar.

---

## Belge Kaynağı
Sistem, arayüz üzerinden dinamik olarak yüklenen PDF belgeleriyle çalışır. Varsayılan senaryoda aşağıdaki belge türleri hedeflenmiştir:
* **Dosya Tipi:** BDDK Yönetmelikleri (Örn: `Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik` veya `GeneratePdf.pdf`)
* Yüklenen belgeler otomatik olarak parçalanır, meta verileri temizlenir ve Milvus vektör veritabanına indekslenir.

---

## Genel Bakış

Bu proje, basit bir Python betiği olmaktan çıkarılarak uçtan uca kurumsal bir RAG platformuna dönüştürülmüştür. Ön yüz (Frontend) ve arka plan (Backend) tamamen izole çalışır. 

Tüm soru-cevap trafiği, API performans metrikleri (istek süresi, kaynaklar) ve kullanıcı geri bildirimleri (`is_helpful`) ilişkisel veritabanında saklanır. Sistem; katı şema uyumlu Milvus entegrasyonu, dinamik PDF yükleme, Docker tabanlı yönetim panelleri (**Attu** ve **RustFS**) ve oturum bazlı hafıza yetenekleriyle kesintisiz bir yapay zeka deneyimi sunar.

### Temel Teknolojiler ve Mimari

1. **FastAPI**: API istekleri için asenkron, yüksek performanslı ve tip güvenli backend katmanı.
2. **OpenAI (GPT-4o & text-embedding-3-small)**: Metinlerin anlamsal vektörlerini (embedding) üretmek ve kaynak atıflı, mevzuata dayalı doğal dil yanıtları oluşturmak için kullanılır.
3. **Milvus**: Mevzuat maddeleri arasında milisaniyeler düzeyinde benzerlik araması yapmak için kullanılan HNSW indeksli vektör veri tabanı. Veri bütünlüğü için katı şema (`strict schema`) uygulanır.
4. **RustFS**: Milvus veri depolama katmanı için kullanılan yüksek performanslı, S3 uyumlu nesne depolama motoru. Web tabanlı yönetim konsolu ile bucket ve nesne yönetimi yapılabilir.
5. **Attu**: Milvus veritabanı koleksiyonlarını, varlıklarını (entities) ve sağlık durumunu görsel olarak izlemek ve yönetmek için kullanılan resmi web arayüzü.
6. **SQLAlchemy & Alembic**: PostgreSQL veritabanı ORM modellerini yönetir ve veritabanı şema geçişlerini (migrations) takip eder.
7. **PostgreSQL (Docker)**: Kullanıcı sorgularını, asistan yanıtlarını, işlem sürelerini ve geri bildirim loglarını kaydeder.
8. **Streamlit**: Canlı chat özelliklerine, dinamik dosya yükleme, kaynak gösterimi ve admin paneline sahip modern web arayüzü.

---

## Özellikler

1. **Clean Architecture & Mikroservis Mimarisi**:
   - **Backend / Frontend Ayrımı:** Streamlit ön yüzü ile FastAPI arka yüzü tamamen bağımsız çalışır.
   - **Router ↔ Service İzolasyonu:** Her API ucu kendi router dosyasında HTTP katmanını yönetirken, iş mantığı (business logic) service katmanlarında yürütülür.
2. **Katı Metadata Filtreleme & Ayıklama**: `PyPDFLoader` veya diğer işleyicilerden gelen fazla meta veriler, `text_processor.py` ve `document_service.py` içerisinde katı bir filtreleme katmanından geçirilerek temizlenir. Yalnızca Milvus şemasının zorunlu kıldığı `kaynak` ve `madde_no` alanları bırakılarak schema hataları tamamen engellenir.
3. **Sıfır Halüsinasyon (Zero-Hallucination)**: Katı prompt mühendisliği (Strict Prompting) sayesinde LLM yalnızca Milvus'tan dönen mevzuat bağlamını kullanmaya zorlanır. Bilgi mevzuatta yoksa sistem internetten uydurmak yerine *"Bu bilgi mevzuatta bulunmamaktadır"* yanıtını verir.
4. **Ölçeklenebilir Vektör Altyapısı**: Milvus ve Cosine metriği ile yüksek performanslı anlamsal aramalar gerçekleştirilir.
5. **Kaynak Gösterimli (Atıflı) Yanıt Üretimi**: OpenAI, Milvus'tan gelen en ilgili metin parçalarını alıp, hangi belgeden (`kaynak`) ve hangi maddeden (`madde_no`) alındığını belirterek cevap üretir.
6. **Kullanıcı Geri Bildirim Döngüsü (Feedback Loop)**: Sohbet arayüzünde her cevabın altında 👍 (Faydalı) ve 👎 (Geliştirilmeli) butonları yer alır. Verilen tepkiler anlık olarak PostgreSQL'e işlenir.
7. **Konuşma Hafızası (Short-Term Memory)**: `RunnableWithMessageHistory` ve `session_id` entegrasyonu sayesinde asistan ardışık sorulardaki bağlamı unutmaz.

---

## Mimarisi ve İstek Akışı

1. **Belge Yükleme (Upload/Ingestion)**: Kullanıcı Streamlit arayüzünden PDF yükler. Belge Backend API ucuna iletilir.
2. **Metin İşleme ve Filtreleme**: `document_service.py` ve `text_processor.py` devreye girer; PDF'i okur, parçalar (chunks) ve Milvus şemasına uymayan tüm ham meta verileri temizler.
3. **Vektörleştirme (Embedding)**: `openai_client.py` üzerinden embeddings modeli çağrılarak her parça vektörleştirilir.
4. **Vektör Kaydı**: Parçalar `kaynak` ve `madde_no` verileriyle birlikte `milvus_client.py` aracılığıyla veritabanına yazılır.
5. **RAG Arama**: Kullanıcı Streamlit'ten sorusunu yazar. History-Aware Retriever önceki mesajlara bakarak soruyu bağımsızlaştırır ve Milvus'ta arar.
6. **Yanıt Üretimi**: Alınan mevzuat maddeleri LLM'e iletilir. Atıflı yanıt üretilir, `db_logger.py` ile yanıt süresi (ms) hesaplanıp PostgreSQL'e kaydedilir.

---

## Proje Klasör Yapısı

```text
BDDK_RAG_Project/
├── .venv/                               # Python sanal ortamı
├── alembic/                             # Alembic veritabanı migrasyon (göç) dosyaları
│   ├── versions/
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── backend/                             # Backend mikroservis kök dizini
│   ├── app/
│   │   ├── clients/                     # Harici servis istemcileri
│   │   │   ├── __init__.py
│   │   │   ├── milvus_client.py         # Milvus bağlantı yapılandırması
│   │   │   ├── openai_client.py         # OpenAI (LLM & Embeddings) yapılandırması
│   │   │   └── rustfs_client.py         # RustFS nesne depolama bağlantısı
│   │   ├── configs/                     # Uygulama ve veritabanı ayarları
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Çevre değişkenleri ve Pydantic ayar sınıfı
│   │   │   └── database.py              # SQLAlchemy DB bağlantı motoru
│   │   ├── helpers/                     # Yardımcı araçlar ve işleyiciler
│   │   │   ├── __init__.py
│   │   │   └── text_processor.py        # Metin parçalama (chunking) ve metadata temizleme
│   │   ├── models/                      # Veritabanı modelleri
│   │   │   ├── __init__.py
│   │   │   └── models.py                # API Logları ve diğer ORM tabloları
│   │   ├── postman/                     # API Test Koleksiyonları
│   │   │   └── bddk_rag_collection.json
│   │   ├── prompts/                     # LLM yönlendirme şablonları (Prompts)
│   │   │   ├── __init__.py
│   │   │   └── rag_prompts.py           # BDDK denetçi tonunda sistem promptları
│   │   ├── routers/                     # API Yönlendiricileri (Endpoints)
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat_router.py       # Soru-cevap (Ask), loglama ve geri bildirim uç noktaları
│   │   │   │   └── document_router.py   # PDF yükleme ve belge yönetim API uç noktaları
│   │   │   └── __init__.py
│   │   ├── schemas/                     # Veri doğrulama şemaları (Pydantic)
│   │   │   ├── __init__.py
│   │   │   └── schemas.py               # Girdi/Çıktı (Request/Response) şemaları
│   │   ├── services/                    # Çekirdek İş Mantığı (Business Logic)
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py          # RAG zinciri, arama ve yanıt üretimi
│   │   │   ├── db_logger.py             # Asenkron veritabanı performans loglama
│   │   │   ├── document_service.py      # PDF okuma ve Milvus ingestion yönetimi
│   │   │   └── memory.py                # Session bazlı konuşma hafızası (Short-Term Memory)
│   │   ├── templates/                   # HTML/Jinja arayüz şablonları
│   │   │   └── index.html               
│   │   ├── __init__.py
│   │   └── main.py                      # FastAPI ana sunucu başlatıcı (App Factory)
│   ├── .env                             # Backend çevre değişkenleri
│   ├── __init__.py
│   └── wsgi.py                          # Geleneksel sunucu başlatıcı
├── frontend/                            # Streamlit arayüz kök dizini
│   ├── frontend.py                      # Streamlit ana UI kodları (Sohbet, Yükleme, Panel)
│   └── run_ui.py                        # Streamlit uygulamasını başlatan betik
├── scripts/                             # Bağımsız CLI test ve yükleme betikleri
│   ├── __init__.py
│   └── ingest_pdf.py                    # CLI üzerinden Milvus'a PDF indeksleme betiği
├── static/                              # Statik dosyalar ve kaynaklar
│   └── imports/                         
│       └── GeneratePdf.pdf              # Örnek test regülasyon dosyası
├── .gitignore                           # Git tarafından yoksayılacak dosyalar
├── alembic.ini                          # Alembic yapılandırma dosyası
├── check_logs.py                        # Log tablolarını test etmek için CLI betiği
├── docker-compose.yml                   # PostgreSQL, Milvus, RustFS ve Attu konteyner tanımları
├── README.md                            # Proje ana dokümantasyonu
└── requirements.txt                     # Proje genel Python bağımlılıkları listesi
```
## Kurulum ve Başlatma

### Ön Koşullar

- **Python 3.9+** (Önerilen: 3.14)
- **Docker ve Docker Compose** (PostgreSQL, Milvus, RustFS ve Attu için)

### Adım Adım Kurulum

**1. Bağımlılıkları Yükleyin**
Sanal ortamınızı (`.venv`) oluşturup etkinleştirdikten sonra gerekli kütüphaneleri yükleyin:
```bash
pip install -r backend/requirements.txt
```

**2. Docker Servislerini Başlatın**
PostgreSQL veritabanını, Milvus'u, RustFS depolama katmanını ve Attu arayüzünü ayağa kaldırın:
```bash
docker compose up -d
```

**3. Çevre Değişkenlerini Düzenleyin**
Kök dizindeki `.env` dosyasını kendi ortamınıza göre tanımlayın:
```env
DATABASE_URL=postgresql://admin:adminpassword@localhost:5432/rag_logs
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**4. Veritabanı Migration İşlemini Uygulayın**
PostgreSQL üzerinde log tablolarını oluşturmak için Alembic'i çalıştırın:
```bash
alembic upgrade head
```

**5. Servisleri Çalıştırın**
Proje mikroservis mimarisinde olduğu için Backend ve Frontend iki ayrı terminalde çalıştırılmalıdır:

*Terminal 1: FastAPI Sunucusu (Backend)*
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

*Terminal 2: Streamlit Arayüzü (Frontend)*
```bash
cd frontend
streamlit run frontend.py
```

---

## API Uç Noktaları (Endpoints) ve Örnekler

| Yöntem | Rota | Açıklama | Router / Service |
|---|---|---|---|
| `POST` | `/api/ask` | Kullanıcı sorgusunu ve `session_id` alır, RAG ile yanıt üretir. | `rag_router.py` / `rag_service.py` |
| `POST` | `/api/documents/upload` | Yüklenen PDF'in meta verilerini temizler ve Milvus'a yazar. | `document_router.py` / `document_service.py` |
| `GET` | `/api/logs` | Geçmiş sorguları, yanıt sürelerini ve değerlendirmeleri listeler. | `rag_router.py` |
| `PUT` | `/api/logs/{log_id}` | Belirli bir log kaydının `is_helpful` durumunu günceller. | `rag_router.py` |
| `DELETE`| `/api/logs/{log_id}` | Belirtilen log kaydını veritabanından siler. | `rag_router.py` |

### Örnek İstek ve Yanıtlar

#### 1. Sohbet API Ucu (`POST /api/ask`)

**İstek Gövdesi:**
```json
{
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?",
  "session_id": "denetci_test_01"
}
```

**Yanıt Gövdesi:**
```json
{
  "log_id": 42,
  "query": "Bankaların asgari sermaye yeterlilik oranı nedir?",
  "answer": "BDDK mevzuatına göre bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az %8'dir.",
  "time_taken_ms": 845,
  "sources": [
    "Bankaların Sermaye Yeterliliğinin Ölçülmesine İlişkin Yönetmelik - Madde 4"
  ],
  "session_id": "denetci_test_01"
}
```

---

## Görsel İnceleme ve Yönetim Araçları

| Araç | URL / Erişim | Açıklama |
|---|---|---|
| **Web Sohbet & Admin Paneli (Streamlit)** | `http://localhost:8501` | RAG sohbet, dinamik PDF yükleme ve log admin paneli |
| **Milvus Yönetim Arayüzü (Attu)** | `http://localhost:3000` | Koleksiyonlar, entity sayıları ve vektör veritabanı paneli |
| **Nesne Depolama Konsolu (RustFS)** | `http://localhost:9001` | S3 uyumlu depolama alanı ve kova (bucket) yönetimi (`minioadmin` / `minioadmin`) |
| **FastAPI Swagger Docs** | `http://localhost:8000/docs` | İnteraktif API dokümantasyonu ve uç nokta test arayüzü |

---
*Geliştirici:* Ahmet Mete Işık