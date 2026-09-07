import os
import pymupdf  # fitz yerine güncel ve uyarısız kütüphane
import re
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus

load_dotenv()

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def run_ingestion():
    # Kodu nereden çalıştırırsan çalıştır, projenin ana klasörünü otomatik bulur
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(BASE_DIR, "GeneratePdf.pdf")

    if not os.path.exists(pdf_path):
        print(f"Hata: PDF bulunamadı. Lütfen dosyanın tam olarak şu konumda olduğundan emin olun:\n{pdf_path}")
        return

    print("1. PDF okunuyor ve yapısal olarak parçalanıyor...")
    pdf_text = extract_text_from_pdf(pdf_path)

    maddeler_ham = re.split(r'\n(?=MADDE\s+\d+)', pdf_text)
    chunks = [madde.strip() for madde in maddeler_ham if len(madde.strip()) > 50]

    print("2. Dokümanlar LangChain formatına dönüştürülüyor...")
    docs = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={"kaynak": "BDDK_Yonetmelik", "madde_no": i + 1}
        )
        docs.append(doc)

    print("3. OpenAI ada-002 ile Embedding yapılıyor ve Milvus'a yazılıyor...")
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    vector_db = Milvus.from_documents(
        documents=docs,
        embedding=embeddings,
        connection_args={"host": "127.0.0.1", "port": "19530"},
        collection_name="bddk_regulations"
    )

    print(f"✅ İŞLEM TAMAM! {len(docs)} adet BDDK maddesi başarıyla Milvus'a kaydedildi.")

if __name__ == "__main__":
    run_ingestion()