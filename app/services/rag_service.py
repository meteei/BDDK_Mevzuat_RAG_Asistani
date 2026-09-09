import os
import re  # Regex ile metin içinden madde numarası bulmak için eklendi
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. Model ve Veritabanı Ayarları
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

vector_store = Milvus(
    embedding_function=embeddings,
    collection_name="bddk_regulations",
    connection_args={"host": "localhost", "port": "19530"},
)
retriever = vector_store.as_retriever(search_kwargs={"k": 6})

# 2. Geçmişi Hatırlayan Arama Motoru Promptu (KRİTİK DÜZELTME)
contextualize_q_system_prompt = (
    "Sohbet geçmişine ve kullanıcının son sorusuna bak. "
    "Eğer son soru, önceki konuşmalarla bağlantılıysa (örneğin 'bu komite', 'onlar', 'oran nedir' gibi eksik ifadeler içeriyorsa), "
    "geçmişteki bağlamı kullanarak bu soruyu tek başına anlaşılabilecek bağımsız bir soruya dönüştür. "
    "Örneğin, geçmişte 'Bilgi Güvenliği Komitesi' konuşulduysa ve yeni soru 'kaç kez toplanır?' ise, "
    "bunu 'Bilgi Güvenliği Komitesi yılda kaç kez toplanır?' olarak düzelt. "
    "DİKKAT: SADECE YENİDEN YAZILMIŞ SORUYU DÖNDÜR! Asla soruyu cevaplama, açıklama yapma veya başka bir kelime ekleme."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])
history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

# 3. Asıl Cevaplama Promptu
system_prompt = (
    "Sen uzman bir BDDK mevzuat asistanısın. "
    "Aşağıdaki bağlam metinlerini kullanarak soruyu cevapla. "
    "Eğer cevap bağlamda yoksa, kesinlikle kendi bilgini kullanma ve 'Bu bilgi mevzuatta bulunmamaktadır.' de.\n\n"
    "Bağlam:\n{context}"
)
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# 4. Zincirleri Birleştirme
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# 5. Hafıza (Memory) Yönetimi
store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)


# 6. Servisi Dışarıya Açan Fonksiyonlar
def get_rag_response(user_query: str, session_id: str):
    # Hafızalı zinciri çalıştır
    response = conversational_rag_chain.invoke(
        {"input": user_query},
        config={"configurable": {"session_id": session_id}}
    )

    # Langchain formatındaki dokümanların sadece metinlerini al
    source_texts = [doc.page_content for doc in response["context"]]

    return {
        "answer": response["answer"],
        "sources": source_texts
    }


def process_and_ingest_pdf(file_path: str):
    """Sisteme yeni yüklenen PDF dosyasını okur, parçalar ve vektör DB'ye ekler."""
    try:
        # 1. PDF'i Yükle
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        # 2. Metni Parçalara Böl
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        # 3. ŞEMA DÜZELTMESİ (Kaynak ve Madde No)
        filename = os.path.basename(file_path)
        if filename.startswith("temp_"):
            filename = filename[5:]

        for split in splits:
            # Zorunlu 'kaynak' alanını ekliyoruz
            split.metadata["kaynak"] = filename

            # Metnin içinden "MADDE 1", "MADDE 5" gibi sadece rakamları yakalıyoruz
            match = re.search(r'MADDE\s+(\d+)', split.page_content, re.IGNORECASE)
            if match:
                # Bulunan string (metin) değeri 'int' ile tam sayıya dönüştürüyoruz
                split.metadata["madde_no"] = int(match.group(1))
            else:
                # Milvus int64 beklediği için "Genel" metni yerine 0 (sıfır) tam sayısını gönderiyoruz
                split.metadata["madde_no"] = 0

        # 4. Vektörleştir ve Milvus'a Ekle
        # (DİKKAT: Bu satır for döngüsünün dışında olmalıydı, girintisi düzeltildi)
        vector_store.add_documents(splits)

        return len(splits)
    except Exception as e:
        raise Exception(f"Belge işlenirken bir hata oluştu: {str(e)}")