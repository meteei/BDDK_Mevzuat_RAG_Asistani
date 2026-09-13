import logging
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory

# Kelime bazlı arama için BM25
from langchain_community.retrievers import BM25Retriever

from app.clients.openai_client import get_embeddings, get_llm
from app.clients.milvus_client import get_vector_store
from app.services.memory import get_session_history

logger = logging.getLogger("Chat_Service")

# Altyapı Bağlantıları
embeddings = get_embeddings()
llm = get_llm()
vector_store = get_vector_store(embeddings)

# 1. Vektör Tabanlı Retriever (Anlamsal arama için)
vector_retriever = vector_store.as_retriever(search_kwargs={"k": 4})

# 2. Kelime Bazlı (Keyword / BM25) Retriever Kurulumu
try:
    all_docs = vector_store.similarity_search("", k=100)  # Tüm 47 maddeyi çek
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = 4


    # Kendi hatasız, özel Hibrit Arama (Ensemble) sınıfımız
    class SimpleEnsembleRetriever:
        def __init__(self, retrievers):
            self.retrievers = retrievers

        def invoke(self, query):
            combined_docs = []
            seen_contents = set()
            for retriever in self.retrievers:
                docs = retriever.invoke(query)
                for doc in docs:
                    if doc.page_content not in seen_contents:
                        seen_contents.add(doc.page_content)
                        combined_docs.append(doc)
            return combined_docs


    ensemble_retriever = SimpleEnsembleRetriever(retrievers=[bm25_retriever, vector_retriever])
    logger.info("Özel Hibrit Arama (BM25 + Milvus Vektör) başarıyla kuruldu.")
except Exception as e:
    logger.warning(f"BM25 kurulamadı, sadece vektör arama ile devam ediliyor: {e}")
    ensemble_retriever = vector_retriever

# Soru Ayrıştırma (Decomposition) Promptu
decomposition_system_prompt = (
    "Sen uzman bir BDDK mevzuat analistisin. Sohbet geçmişine ve kullanıcının son sorusuna bak. "
    "Eğer kullanıcı sorusu birden fazla farklı konu, kural veya niyeti (multi-intent) içeriyorsa, "
    "geçmişteki sohbet bağlamını da göz önüne alarak bu soruyu bağımsız ve net alt sorulara böl. "
    "Eğer soru tek bir konuyu içeriyorsa, sohbet geçmişine göre bağımsızlaştırılmış tek bir soru olarak listele. "
    "Çıktıyı SADECE JSON formatında bir string liste olarak ver, başka hiçbir açıklama ekleme. "
    "Örnek format: [\"Alt soru 1\", \"Alt soru 2\"]"
)

decomposition_prompt = ChatPromptTemplate.from_messages([
    ("system", decomposition_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

decomposition_chain = decomposition_prompt | llm | StrOutputParser()

# Çok Katı ve Tavizsiz Denetçi Promptu (Yorum yapmaya kapalı)
system_prompt = (
    "Sen çok katı, tavizsiz ve resmi bir BDDK mevzuat denetçisi ve yapay zeka asistanısın. "
    "Sana sağlanan bağlam metinlerini ve mevzuat maddelerini kesinlikle esas alarak soruları yanıtla.\n\n"
    "ÇOK ÖNEMLİ UYUM KURALLARI:\n"
    "1. Asla kendi genel internet bilgini, dışarıdan edindiğin KVKK ezberlerini, bulut esnekliklerini veya varsayımlarını kullanma.\n"
    "2. Mevzuatta 'zorunludur' denilen bir kuralı asla esnetme; 'edilemez' veya 'kullanılamaz' denilen yasakları asla ihtimalli ('olabilir', 'uygun olabilir', 'risk taşıyabilir' vb.) yorumlama. Bunlar mutlak ve istisnasız kurallardır.\n"
    "3. Yanıtında mutlaka ilgili madde numaralarını (Örn: Madde 25, Madde 29, Madde 34) açıkça referans göstererek hükmü net bir şekilde açıkla.\n"
    "4. Eğer sorunun cevabı sağlanan bağlamda kesin olarak geçmiyorsa, asla yorum yapma ve sadece 'Bu bilgi mevzuatta bulunmamaktadır.' de.\n\n"
    "Bağlam:\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)


def process_rag_pipeline(inputs):
    """Soru ayrıştırma, Hibrit Arama ve yanıt verme boru hattı."""
    chat_history = inputs.get("chat_history", [])
    user_input = inputs.get("input", "")

    # 1. Karmaşık soruyu alt sorulara böl
    try:
        raw_response = decomposition_chain.invoke({
            "chat_history": chat_history,
            "input": user_input
        })
        content = raw_response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        sub_queries = json.loads(content)
        if not isinstance(sub_queries, list):
            sub_queries = [user_input]
    except Exception as e:
        logger.warning(f"Soru ayrıştırma sırasında hata oluştu, orijinal soru ile devam ediliyor: {e}")
        sub_queries = [user_input]

    logger.info(f"Oluşturulan alt sorgular: {sub_queries}")

    # 2. Her alt soru için HİBRİT ARAMA yap (BM25 + Vektör) ve benzersiz dokümanları topla
    all_docs = []
    seen_contents = set()

    for q in sub_queries:
        docs = ensemble_retriever.invoke(q)
        for doc in docs:
            if doc.page_content not in seen_contents:
                seen_contents.add(doc.page_content)
                all_docs.append(doc)

    source_texts = [doc.page_content for doc in all_docs]
    logger.info(f"Hibrit arama sonucunda toplanan benzersiz kaynak parça sayısı: {len(source_texts)}")

    # 3. Toplanan dokümanlar ile LLM'den yanıt üret
    qa_chain_input = {
        "context": all_docs,
        "input": user_input,
        "chat_history": chat_history
    }
    answer = question_answer_chain.invoke(qa_chain_input)

    return {
        "answer": answer,
        "sources": source_texts
    }


conversational_rag_chain = RunnableWithMessageHistory(
    RunnableLambda(process_rag_pipeline),
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)


def get_rag_response(user_query: str, session_id: str):
    logger.info(f"Hibrit RAG yanıtı üretiliyor [Session: {session_id}] Soru: '{user_query}'")
    try:
        response = conversational_rag_chain.invoke(
            {"input": user_query},
            config={"configurable": {"session_id": session_id}}
        )
        return {"answer": response["answer"], "sources": response["sources"]}
    except Exception as e:
        logger.error(f"RAG yanıtı üretilirken hata oluştu: {str(e)}")
        raise e