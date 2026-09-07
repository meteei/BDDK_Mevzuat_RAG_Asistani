# 🏦 BDDK Mevzuat Asistanı (RAG Sistemi)

Bu proje, Bankacılık Düzenleme ve Denetleme Kurumu (BDDK) mevzuatları ve yönetmelikleri hakkında sorulan sorulara, Retrieval-Augmented Generation (RAG) mimarisi kullanarak doğru, hızlı ve kaynak göstererek yanıt veren tam teşekküllü bir yapay zeka asistanıdır.

Proje, basit bir Python betiği olmaktan çıkarılarak **Mikroservis Mimarisi** standartlarında uçtan uca (Full-Stack) bir uygulama olarak tasarlanmıştır.

## 🚀 Proje Mimarisi ve Kullanılan Teknolojiler

* **Yapay Zeka & RAG:** LangChain, Milvus (Vektör Veritabanı)
* **Backend (API):** FastAPI, Pydantic
* **Frontend (Arayüz):** Streamlit
* **İlişkisel Veritabanı:** PostgreSQL (Docker üzerinden)
* **ORM & Versiyonlama:** SQLAlchemy, Alembic

## ✨ Temel Özellikler

1. **RAG Tabanlı Doğru Yanıt Sistemi:** LLM halüsinasyonlarını engellemek için cevaplar doğrudan BDDK mevzuat maddelerine dayandırılır ve arayüzde "Kaynaklar" sekmesi altında kullanıcıya sunulur.
2. **Kapsamlı API Uç Noktaları:** FastAPI üzerinde `GET`, `POST`, `PUT` ve `DELETE` metodlarıyla asistanın tüm logları dışarıdan yönetilebilir haldedir (Swagger UI entegreli).
3. **Kullanıcı Geri Bildirim Döngüsü:** Arayüz üzerinden verilen 👍 / 👎 tepkileri, asenkron olarak veritabanındaki `is_helpful` sütununa kaydedilir.
4. **Yönetici Paneli:** Streamlit yan menüsünde, API üzerinden beslenen ve sistem loglarını anlık gösteren bir metrik paneli bulunmaktadır.
5. **Veritabanı Versiyon Kontrolü:** Alembic ile veritabanı şemasındaki değişiklikler (migration) veri kaybı yaşanmadan yönetilmektedir.

## 🛠️ Kurulum ve Çalıştırma

Projeyi lokal ortamınızda çalıştırmak için aşağıdaki adımları izleyin:

### 1. Gereksinimlerin Yüklenmesi
Sanal ortamınızı (virtual environment) aktif ettikten sonra gerekli kütüphaneleri kurun:
`pip install -r requirements.txt`

### 2. Veritabanının Ayağa Kaldırılması
Docker kullanarak PostgreSQL instance'ını başlatın ve Alembic ile tabloları oluşturun:
`alembic upgrade head`

### 3. Servislerin Başlatılması
Proje mikroservis mimarisinde olduğu için Backend ve Frontend iki ayrı terminalde çalıştırılmalıdır.

**Terminal 1: FastAPI Sunucusu (Backend)**
`uvicorn main:app --reload --port 8002`
*API Dokümantasyonuna (Swagger UI) http://127.0.0.1:8002/docs adresinden ulaşabilirsiniz.*

**Terminal 2: Streamlit Arayüzü (Frontend)**
`python run_ui.py`
*Web arayüzü otomatik olarak tarayıcınızda açılacaktır.*

## 📂 Proje Yapısı

* **alembic/** : Veritabanı migration dosyaları
* **app/main.py** : FastAPI ana uygulaması
* **app/models/** : SQLAlchemy veritabanı modelleri
* **app/routers/** : API uç noktaları (rag_router.py)
* **app/schemas/** : Pydantic veri doğrulama şemaları
* **frontend.py** : Streamlit kullanıcı arayüzü
* **run_ui.py** : Streamlit başlatıcı script
* **alembic.ini** : Alembic yapılandırma dosyası
* **requirements.txt** : Python bağımlılıkları

---
*Geliştirici:* Ahmet Mete Işık