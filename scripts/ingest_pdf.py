import os
import pymupdf
import re
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus

# Projenin ana kök dizinini buluyoruz (scripts/ klasöründen bir üst dizine çıkıyoruz)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env dosyan backend klasörünün içinde olduğu için yolu buna göre güncelliyoruz: backend/.env
dotenv_path = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(dotenv_path)

# OpenAI API anahtarının okunup okunmadığını kontrol ediyoruz
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ UYARI: OPENAI_API_KEY bulunamadı! Lütfen 'backend/.env' dosyanızı ve içerisindeki anahtarı kontrol edin.")

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def run_ingestion():
    # PDF'in gerçek konumu: static/imports/GeneratePdf.pdf
    pdf_path = os.path.join(BASE_DIR, "static", "imports", "GeneratePdf.pdf")

    if not os.path.exists(pdf_path):
        print(f"Hata: PDF bulunamadı. Lütfen dosyanın tam olarak şu konumda olduğundan emin olun:\n{pdf_path}")
        return

    print("1. PDF okunuyor ve madde sınırlarına göre akıllı parçalanıyor...")
    pdf_text = extract_text_from_pdf(pdf_path)

    # MADDE başlıklarına göre metni bütünüyle yakalayan hassas regex deseni
    pattern = r"(MADDE\s+\d+[\s\S]*?)(?=(?:MADDE\s+\d+|\Z))"
    matches = re.findall(pattern, pdf_text)

    if not matches:
        maddeler_ham = re.split(r'\n(?=MADDE\s+\d+)', pdf_text)
        chunks = [m.strip() for m in maddeler_ham if len(m.strip()) > 20]
    else:
        chunks = [m.strip() for m in matches if len(m.strip()) > 20]

    print("2. Dokümanlar LangChain formatına ve gerçek madde numaralarıyla metadata'ya dönüştürülüyor...")
    docs = []
    for chunk in chunks:
        # Metin içerisinden gerçek Madde numarasını yakalıyoruz (Örn: "MADDE 25")
        madde_match = re.search(r"MADDE\s+(\d+)", chunk)
        if madde_match:
            madde_no = int(madde_match.group(1))
            madde_str = f"Madde {madde_no}"
        else:
            madde_str = "Genel_Hukum_Veya_Tanim"

        doc = Document(
            page_content=chunk,
            metadata={
                "kaynak": "BDDK_Yonetmelik",
                "madde_no": madde_str
            }
        )
        docs.append(doc)

    print(f"3. OpenAI ada-002 ile Embedding yapılıyor ve Milvus'a yazılıyor ({len(docs)} parça)...")
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # drop_old=True ile eski verileri temizleyip tertemiz madde bazlı yükleme yapıyoruz
    vector_db = Milvus.from_documents(
        documents=docs,
        embedding=embeddings,
        connection_args={"host": "127.0.0.1", "port": "19530"},
        collection_name="bddk_regulations",
        drop_old=True
    )

    print(f"✅ İŞLEM TAMAM! {len(docs)} adet BDDK maddesi başarıyla Milvus'a kaydedildi.")

if __name__ == "__main__":
    run_ingestion()