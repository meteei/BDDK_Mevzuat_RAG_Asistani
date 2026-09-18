# 🏦 BDDK Mevzuat Asistanı & Kurumsal RAG Sistemi

PDF formatındaki bankacılık mevzuatlarını, yönetmeliklerini ve tebliğlerini işlemek, vektörleştirmek ve sorgulamak için tasarlanmış akıllı, anlamsal bir kurumsal Soru-Cevap RAG (Retrieval-Augmented Generation) sistemidir. FastAPI, OpenAI, Milvus, RustFS ve PostgreSQL kullanılarak **Clean Architecture** ve **App Factory** prensiplerine uygun olarak geliştirilmiştir.

Kullanıcıların karmaşık bankacılık regülasyonları üzerinden sorular sormasına olanak tanır ve belgelerden bağlama duyarlı, kaynak atıflı ve tavizsiz denetçi tonunda doğru yanıtlar sağlar.

---

## Belge Kaynağı
Sistem, arayüz üzerinden dinamik olarak yüklenen PDF belgeleriyle çalışır. Varsayılan senaryoda aşağıdaki belge türleri hedeflenmiştir:
* **Dosya Tipi:** BDDK Yönetmelikleri (Örn: `Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik` veya `GeneratePdf.pdf`)
* Yüklenen belgeler otomatik olarak parçalanır, meta verileri temizlenir ve Milvus vektör veritabanına indekslenir.

---

## Genel Bakış

Bu proje, uçtan uca entegre kurumsal bir RAG platformudur. Tüm soru-cevap trafiği, API performans metrikleri (istek süresi, kaynaklar) ve sistem logları asenkron olarak ilişkisel veritabanında saklanır. Sistem; katı şema uyumlu Milvus entegrasyonu, dinamik PDF yükleme, Docker tabanlı yönetim panelleri (**Attu** ve **RustFS**) ve modern, duyarlı (responsive) Tailwind CSS web arayüzü ile kesintisiz bir yapay zeka deneyimi sunar.

### Temel Teknolojiler ve Mimari

1. **FastAPI**: API istekleri ve arayüz sunumu (Jinja2 Templates) için asenkron, yüksek performanslı backend katmanı.
2. **OpenAI (GPT-4o & text-embedding-3-small)**: Metinlerin anlamsal vektörlerini (embedding) üretmek ve kaynak atıflı, mevzuata dayalı doğal dil yanıtları oluşturmak için kullanılır.
3. **Milvus (v2.4.0)**: Mevzuat maddeleri arasında milisaniyeler düzeyinde benzerlik araması yapmak için kullanılan HNSW indeksli vektör veri tabanı. Veri bütünlüğü için katı şema (`strict schema`) uygulanır.
4. **RustFS (MinIO Altyapısı)**: Milvus vektör depolaması ve harici sistem yedekleri için kullanılan yüksek performanslı, S3 uyumlu nesne depolama motoru. 
5. **Attu**: Milvus veritabanı koleksiyonlarını, varlıklarını (entities) ve sağlık durumunu görsel olarak izlemek ve yönetmek için kullanılan resmi web arayüzü.
6. **SQLAlchemy & Alembic**: PostgreSQL veritabanı ORM modellerini yönetir ve veritabanı şema geçişlerini (migrations) takip eder.
7. **PostgreSQL (Docker)**: Kullanıcı sorgularını, asistan yanıtlarını, işlem sürelerini ve geri bildirim loglarını kaydeder.
8. **Tailwind CSS & HTML5**: Enterprise düzeyinde, modern ve asenkron çalışan web paneli (FastAPI üzerinden doğrudan sunulur).

---

## Özellikler

1. **Clean Architecture & App Factory Mimarisi**:
   - Proje bağımlılıkları ve uygulama başlatma mantığı tamamen izole edilmiştir.
   - **Router ↔ Service İzolasyonu:** Her API ucu kendi router dosyasında (`chat_router.py`, `document_router.py`) HTTP katmanını yönetirken, iş mantığı service katmanlarında yürütülür.
2. **Katı Metadata Filtreleme & Ayıklama**: İşleyicilerden gelen fazla meta veriler, `text_processor.py` içerisinde katı bir filtreleme katmanından geçirilerek temizlenir. Yalnızca Milvus şemasının zorunlu kıldığı `kaynak` ve `madde_no` alanları bırakılarak schema hataları tamamen engellenir.
3. **Sıfır Halüsinasyon (Zero-Hallucination)**: Katı prompt mühendisliği ve `Top-K` optimizasyonları sayesinde LLM yalnızca Milvus'tan dönen mevzuat bağlamını kullanmaya zorlanır. Bilgi mevzuatta yoksa sistem internetten uydurmak yerine *"Bu bilgi mevzuatta bulunmamaktadır"* yanıtını verir.
4. **Ölçeklenebilir Vektör Altyapısı**: Milvus ve Cosine metriği ile yüksek performanslı anlamsal aramalar gerçekleştirilir.
5. **Kaynak Gösterimli (Atıflı) Yanıt Üretimi**: OpenAI, Milvus'tan gelen en ilgili metin parçalarını alıp, hangi belgeden ve maddeden alındığını belirterek profesyonel denetçi formatında cevap üretir.
6. **Asenkron Arka Plan Görevleri (Background Tasks)**: Veritabanı loglama ve metrik kayıt işlemleri, kullanıcıya yanıt dönüldükten sonra asenkron olarak arka planda yürütülür, API yanıt süresi sıfır gecikmeyle çalışır.

---

## Mimarisi ve İstek Akışı

1. **Belge Yükleme (Upload/Ingestion)**: Kullanıcı web arayüzünden PDF yükler.
2. **Metin İşleme ve Filtreleme**: `document_service.py` ve `text_processor.py` devreye girer; PDF'i okur, parçalar (chunks) ve Milvus şemasına uymayan tüm ham meta verileri temizler.
3. **Vektörleştirme (Embedding)**: `openai_client.py` üzerinden embeddings modeli çağrılarak her parça vektörleştirilir.
4. **Vektör Kaydı**: Parçalar `kaynak` ve `madde_no` verileriyle birlikte `milvus_client.py` aracılığıyla veritabanına yazılır.
5. **RAG Arama**: Kullanıcı sorusunu yazar. Milvus üzerinde Semantic Search yapılarak en benzer mevzuat maddeleri çekilir.
6. **Yanıt Üretimi**: Alınan mevzuat maddeleri LLM'e iletilir. Atıflı yanıt üretilir, `db_logger.py` ile yanıt süresi ve metrikler PostgreSQL'e kaydedilir.

---
## Proje Klasör Yapısı

```text
PythonProjectRegulasyon_RAG/
├── .venv/                               # Python sanal ortamı
├── alembic/                             # Alembic veritabanı migrasyon (göç) dosyaları
│   ├── versions/
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── backend/                             # Backend mikroservis kök dizini
│   └── app/
│       ├── clients/                     # Harici servis istemcileri
│       │   ├── __init__.py
│       │   ├── milvus_client.py         # Milvus bağlantısı
│       │   ├── openai_client.py         # OpenAI entegrasyonu
│       │   └── rustfs_client.py         # MinIO/RustFS depolama
│       ├── configs/                     # Uygulama ve veritabanı ayarları
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── database.py
│       ├── helpers/                     # Yardımcı betikler (Metin işleme vb.)
│       │   ├── __init__.py
│       │   └── text_processor.py
│       ├── models/                      # SQLAlchemy ORM Modelleri
│       │   ├── __init__.py
│       │   └── models.py
│       ├── postman/                     # API Test koleksiyonu
│       │   └── bddk_rag_collection.json
│       ├── prompts/                     # LLM Prompt şablonları
│       │   ├── __init__.py
│       │   └── rag_prompts.py
│       ├── routers/                     # FastAPI uç noktaları (Endpoints)
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   ├── chat_router.py
│       │   │   └── document_router.py
│       │   └── __init__.py
│       ├── schemas/                     # Pydantic veri doğrulama şemaları
│       │   ├── __init__.py
│       │   └── schemas.py
│       ├── services/                    # İş mantığı ve RAG servisleri
│       │   ├── __init__.py
│       │   ├── chat_service.py
│       │   ├── db_logger.py
│       │   ├── document_service.py
│       │   └── memory.py
│       ├── templates/                   # Frontend HTML/Tailwind şablonları
│       │   └── index.html
│       ├── .env                         # Backend ortam değişkenleri
│       ├── __init__.py
│       ├── main.py                      # FastAPI ana sunucu başlatıcı (App Factory)
│       └── wsgi.py                      # Geleneksel sunucu başlatıcı betiği
├── scripts/                             # Bağımsız test ve yükleme betikleri
│   ├── __init__.py
│   ├── ingest.py                        # Milvus'a manuel PDF indeksleme aracı
│   └── test_search.py                   # Vektör arama testi
├── static/                              # Statik dosyalar ve örnekler
│   └── imports/
│       └── GeneratePdf.pdf              # Örnek mevzuat test dosyası
├── .gitignore                           # Git tarafından yoksayılacak dosyalar
├── alembic.ini                          # Alembic yapılandırma dosyası
├── docker-compose.yml                   # PostgreSQL, Milvus ve RustFS konteynerleri
├── README.md                            # Proje ana dokümantasyonu
└── requirements.txt                     # Python kütüphane bağımlılıkları
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
FastAPI sunucusunu başlatın (Web arayüzü de bu sunucu üzerinden servis edilecektir):

cd backend
python wsgi.py
# veya uvicorn app.main:app --reload

---

## API Uç Noktaları (Endpoints) ve Örnekler

| Yöntem | Rota | Açıklama | Router / Service |
|---|---|---|---|
| `POST` | `/api/v1/chat` *(veya `/api/ask`)* | Kullanıcı sorgusunu alır, Milvus ve LLM üzerinden RAG ile yanıt üretir. | `chat_router.py` / `chat_service.py` |
| `POST` | `/api/v1/documents/upload` | Yüklenen PDF'in meta verilerini temizler ve Milvus'a yazar. | `document_router.py` / `document_service.py` |
| `GET` | `/api/v1/logs` | Geçmiş sorguları, yanıt sürelerini ve logları listeler. | `chat_router.py` / `db_logger.py` |
| `PUT` | `/api/v1/logs/{log_id}` | Belirli bir log kaydının durumunu günceller. | `chat_router.py` / `db_logger.py` |
| `DELETE`| `/api/v1/logs/{log_id}` | Belirtilen log kaydını veritabanından siler. | `chat_router.py` / `db_logger.py` |

### Örnek İstek ve Yanıtlar

#### 1. Sohbet API Ucu (`POST /api/v1/chat`)

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
| **Web Denetim Paneli & UI** | `http://localhost:8000` | Tailwind CSS tabanlı RAG denetim ve mevzuat sorgulama arayüzü |
| **FastAPI Swagger Docs** | `http://localhost:8000/docs` | İnteraktif API dokümantasyonu ve uç nokta test arayüzü |
| **Milvus Yönetim Arayüzü (Attu)** | `http://localhost:3000` | Vektör koleksiyonları, entity sayıları ve arama analiz paneli |
| **Nesne Depolama Konsolu (RustFS)** | `http://localhost:9001` | S3 uyumlu depolama ve kova (bucket) yönetimi (`rustfsadmin` / `rustfsadmin`) |

---
*Geliştirici:* Ahmet Mete Işık