# 🏦 BDDK Mevzuat Asistanı & Kurumsal RAG Sistemi

PDF formatındaki bankacılık mevzuatlarını, yönetmeliklerini ve tebliğlerini işlemek, vektörleştirmek ve sorgulamak için tasarlanmış akıllı, anlamsal bir kurumsal Soru-Cevap RAG (Retrieval-Augmented Generation) sistemidir. FastAPI, OpenAI, Milvus, RustFS, PostgreSQL ve Streamlit kullanılarak **Clean Architecture** ve **Mikroservis** prensiplerine uygun olarak geliştirilmiştir.

Kullanıcıların karmaşık bankacılık regülasyonları üzerinden sorular sormasına olanak tanır ve belgelerden bağlama duyarlı, kaynak atıflı ve tavizsiz denetçi tonunda doğru yanıtlar sağlar.

---

## Belge Kaynağı
Sistem, arayüz üzerinden dinamik olarak yüklenen PDF belgeleriyle çalışır. Varsayılan senaryoda aşağıdaki belge türleri hedeflenmiştir:
* **Dosya Tipi:** BDDK Yönetmelikleri (Örn: `Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik`)
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
2. **Katı Metadata Filtreleme & Ayıklama**: `PyPDFLoader` tarafından üretilen fazla ve uyumsuz dosya meta verileri (`producer`, `creator`, `page` vb.), `document_service.py` içerisinde katı bir filtreleme katmanından geçirilerek temizlenir. Yalnızca Milvus şemasının zorunlu kıldığı `kaynak` ve `madde_no` alanları bırakılarak `MilvusException (code=1100)` hataları tamamen engellenir.
3. **Sıfır Halüsinasyon (Zero-Hallucination)**: Katı prompt mühendisliği (Strict Prompting) sayesinde LLM yalnızca Milvus'tan dönen mevzuat bağlamını kullanmaya zorlanır. Bilgi mevzuatta yoksa sistem internetten uydurmak yerine *"Bu bilgi mevzuatta bulunmamaktadır"* yanıtını verir.
4. **Ölçeklenebilir Vektör Altyapısı**: Milvus ve Cosine metriği ile yüksek performanslı anlamsal aramalar gerçekleştirilir.
5. **Kaynak Gösterimli (Atıflı) Yanıt Üretimi**: OpenAI, Milvus'tan gelen en ilgili metin parçalarını alıp, hangi belgeden (`kaynak`) ve hangi maddeden (`madde_no`) alındığını belirterek cevap üretir.
6. **Kullanıcı Geri Bildirim Döngüsü (Feedback Loop)**: Sohbet arayüzünde her cevabın altında 👍 (Faydalı) ve 👎 (Geliştirilmeli) butonları yer alır. Verilen tepkiler anlık olarak PostgreSQL'e işlenir.
7. **Konuşma Hafızası (Short-Term Memory)**: `RunnableWithMessageHistory` ve `session_id` entegrasyonu sayesinde asistan ardışık sorulardaki bağlamı unutmaz (Örn: *"Peki bu komite ne zaman toplanır?"*).

---

## Kullanım Senaryoları

**BDDK Regülasyon ve Denetim Sorguları**

* **Bağlam Korumalı Sorgular:** 
  - *"Bilgi Güvenliği Komitesi kimlerden oluşur?"*
  - *"Peki bu komite yılda kaç kez toplanmalıdır?"* (Sistem 'bu komite' ifadesini hafızadan çözer).
* **Sayısal ve Risk Sorguları:** 
  - *"Bankaların sermaye yeterliliği standart oranı yasal sınır olarak en az yüzde kaçtır ve bu oran hesaplanırken hangi risk türleri dikkate alınır?"*
* **Vaka ve İhlal Analizi:** 
  - *"Banka, ikincil sistemlerini yurt dışında bulunan bir veri merkezine taşımıştır. Bu durum yönetmeliğe uygun mudur? İlgili maddelerle açıklayın."*

---

## Mimarisi ve İstek Akışı

1. **Belge Yükleme (Upload/Ingestion)**: Kullanıcı Streamlit arayüzünden PDF yükler. Belge `POST /api/documents/upload` ucuna iletilir.
2. **Metin İşleme ve Filtreleme**: `document_service.py` PDF'i okur, parçalar (chunks) ve Milvus şemasına uymayan tüm ham meta verileri temizler.
3. **Vektörleştirme (Embedding)**: LangChain üzerinden OpenAI embeddings modeli çağrılarak her parça vektörleştirilir.
4. **Vektör Kaydı**: Parçalar `kaynak` ve `madde_no` verileriyle birlikte Milvus koleksiyonuna yazılır.
5. **RAG Arama**: Kullanıcı Streamlit'ten sorusunu yazar. `POST /api/ask` tetiklenir, History-Aware Retriever önceki mesajlara bakarak soruyu bağımsızlaştırır ve Milvus'ta arar.
6. **Yanıt Üretimi**: Alınan mevzuat maddeleri LLM'e iletilir. Atıflı yanıt üretilir, yanıt süresi (ms) hesaplanır ve PostgreSQL veritabanına kaydedilir.
7. **Geri Bildirim ve Loglama**: Kullanıcı yanıta 👍/👎 verdiğinde `PUT /api/logs/{log_id}` tetiklenir. Yöneticiler tüm bu akışı admin paneli üzerinden izler.

---

## Proje Klasör Yapısı

```text
BDDK_RAG_Project/
├── alembic/                             # Alembic veritabanı şema versiyonları ve migrasyonlar
├── backend/                             # Backend mikroservis kök dizini
│   ├── app/
│   │   ├── main.py                      # FastAPI ana sunucu başlatıcı, CORS ve router kayıtları
│   │   ├── database.py                  # SQLAlchemy veritabanı oturum (session) yönetimi
│   │   ├── clients/                     
│   │   │   ├── openai_client.py         # OpenAI embeddings ve LLM istemci konfigürasyonu
│   │   │   └── milvus_client.py         # Milvus vektör veritabanı istemci bağlantısı
│   │   ├── helpers/                     
│   │   │   └── text_processor.py        # Metin parçalama (chunking) ve madde no ayıklama asistanı
│   │   ├── models/                      
│   │   │   └── models.py                # SQLAlchemy ORM modelleri (API Logs tablosu)
│   │   ├── schemas/                     
│   │   │   └── schemas.py               # Pydantic veri doğrulama ve girdi/çıktı şemaları
│   │   ├── services/
│   │   │   ├── document_service.py      # PDF okuma, katı metadata temizleme ve Milvus ingestion
│   │   │   ├── rag_service.py           # LangChain RAG zincirleri, History-Aware Retriever
│   │   │   └── memory.py                # Session bazlı in-memory konuşma hafızası
│   │   └── routers/                     
│   │       ├── document_router.py       # PDF yükleme ve belge yönetim API uç noktaları
│   │       └── rag_router.py            # Soru-cevap (Ask), loglama ve geri bildirim uç noktaları
│   └── requirements.txt                 # Backend Python bağımlılıkları listesi
├── frontend/                            
│   └── frontend.py                      # Streamlit RAG sohbet, dinamik PDF yükleme, kaynaklar ve admin panel
├── docker-compose.yml                   # PostgreSQL, Milvus, RustFS ve Attu konteyner yapılandırması
├── alembic.ini                          # Alembic göç yapılandırma dosyası
└── .env                                 # Çevre değişkenleri (API anahtarları ve veritabanı URL'i)
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