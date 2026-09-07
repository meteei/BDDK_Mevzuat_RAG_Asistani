from app.prompts.rag_prompts import QA_SYSTEM_PROMPT, CONTEXTUALIZE_Q_SYSTEM_PROMPT
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

# 2. Geçmişi Hatırlayan Arama Motoru Promptu (Soruyu Yeniden Formüle Eder)
contextualize_q_system_prompt = (
    "Sohbet geçmişine ve kullanıcının son sorusuna bak. "
    "Eğer kullanıcı önceki konuşmalara atıfta bulunuyorsa, bu soruyu tek başına anlaşılabilecek "
    "bağımsız bir soruya dönüştür. Soruyu cevaplama, sadece gerekiyorsa yeniden formüle et."
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


# Servisi Dışarıya Açan Fonksiyon
def get_rag_response(user_query: str, session_id: str = "default_session"):
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