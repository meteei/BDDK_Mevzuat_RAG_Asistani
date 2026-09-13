# backend/app/helpers/text_processor.py
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


class BDDKTextProcessor:
    """
    BDDK Regülasyon metinlerini işlemek için yardımcı sınıf.
    Metin temizleme, parçalama (chunking) ve madde numarası (MADDE X) algılama işlemlerini sağlar.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        # LangChain'in standart parçalayıcısını kullanıyoruz
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    @staticmethod
    def clean_and_normalize_text(text: str) -> str:
        """Metindeki fazla boş satırları temizler ve normalleştirir."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def extract_article_number(text: str) -> int:
        """
        Metin içindeki 'MADDE 5', 'Madde 12' gibi ifadeleri yakalar.
        Eğer madde numarası bulamazsa 0 döner.
        """
        match = re.search(r'MADDE\s+(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def process_documents(self, docs, filename: str) -> list:
        """
        LangChain'den gelen ham PDF dokümanlarını parçalar, temizler
        ve metadata (kaynak, madde_no) bilgilerini ekleyerek geri döner.
        """
        splits = self.text_splitter.split_documents(docs)

        for split in splits:
            # Metni temizle
            split.page_content = self.clean_and_normalize_text(split.page_content)

            # Metadata'ları zenginleştir
            split.metadata["kaynak"] = filename
            split.metadata["madde_no"] = self.extract_article_number(split.page_content)

        return splits


# Proje genelinde kullanılacak tekil (singleton) nesne
text_processor = BDDKTextProcessor()