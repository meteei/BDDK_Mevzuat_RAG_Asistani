import re
from typing import List, Optional
from langchain_core.documents import Document


class TextProcessor:
    """
    BDDK Regülasyon metinlerini işlemek için kurumsal yardımcı sınıf.
    Metni rastgele değil, tüm sayfaları birleştirip tam olarak
    'MADDE' başlıklarından böler (Semantic/Legal Chunking).

    document_service ve ingest scriptleri tarafından kullanılır.
    """

    # --- 1. Metin Temizleme ---

    @staticmethod
    def clean_and_normalize_text(text: str) -> str:
        """Metindeki fazla boş satırları temizler ve normalleştirir."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    # --- 2. Başlık Algılama ---

    @staticmethod
    def extract_madde_number(text: str) -> Optional[str]:
        """
        Metnin bir 'MADDE X' başlığı olup olmadığını kontrol eder.
        Eşleşme varsa madde numarasını (örn: '11') döner, yoksa None döner.
        """
        match = re.match(r'MADDE\s+(\d+)', text.strip(), re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    # --- 3. Hiyerarşik Bölümleme (Semantic Chunking) ---

    @classmethod
    def split_by_madde(cls, full_text: str, filename: str) -> List[Document]:
        """
        Tüm metni 'MADDE' başlıklarına göre hiyerarşik olarak böler.
        Her parçaya 'Kaynak - Madde X' breadcrumb'ı ve metadata ekler.
        """
        processed_splits = []

        # Metni "MADDE X" başlıklarından ayırıyoruz
        parts = re.split(r'(MADDE\s+\d+)', full_text, flags=re.IGNORECASE)

        current_madde_no = "Genel_Hukum"

        for i in range(len(parts)):
            chunk_text = parts[i].strip()
            if not chunk_text:
                continue

            # Eğer parça "MADDE X" ise, numarayı hafızaya al ve içeriğe geç
            madde_no = cls.extract_madde_number(chunk_text)
            if madde_no:
                current_madde_no = madde_no
                continue

            # İçerik kısmındayız. Etiketi (Breadcrumb) en başa basıyoruz.
            breadcrumb = f"[Kaynak: {filename} - Madde {current_madde_no}]\n"
            final_content = breadcrumb + chunk_text

            new_doc = Document(
                page_content=final_content,
                metadata={
                    "kaynak": filename,
                    "madde_no": str(current_madde_no)
                }
            )
            processed_splits.append(new_doc)

        return processed_splits

    # --- 4. Ana İşlem (Entry Point) ---

    @classmethod
    def process_documents(cls, docs: List[Document], filename: str) -> List[Document]:
        """
        Tüm belge sayfalarını tek bir dev metinde birleştirir ve işler.
        (Sayfa sonlarına denk gelen maddelerin bölünmesini önler).
        """
        # 1. Aşama: Sayfaları birleştir ve temizle
        full_text = "\n\n".join([doc.page_content for doc in docs])
        full_text = cls.clean_and_normalize_text(full_text)

        # 2. Aşama: Madde bazlı hiyerarşik bölümlere ayır
        return cls.split_by_madde(full_text, filename)


# Proje genelinde kullanılacak tekil (singleton) nesne
text_processor = TextProcessor()