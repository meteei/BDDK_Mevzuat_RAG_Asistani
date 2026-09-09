import streamlit as st
import requests
import uuid

# Sayfa yapılandırması
st.set_page_config(page_title="BDDK Asistanı", page_icon="🏦", layout="centered")

# Benzersiz oturum kimliği (session_id) oluşturma
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Mesaj geçmişini tutan liste
if "messages" not in st.session_state:
    st.session_state.messages = []

# API Adresimiz
API_BASE_URL = "http://127.0.0.1:8002/api"

# --- SOL MENÜ (SIDEBAR) ---
with st.sidebar:
    st.header("🔄 Sohbet Yönetimi")
    # Hafızayı sıfırlayan ve yeni bir session_id üreten buton
    if st.button("Yeni Sohbet Başlat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()

    # --- YENİ: DİNAMİK BELGE YÜKLEME ALANI ---
    st.header("📄 Dinamik Belge Yükleme")
    st.caption("Sisteme yeni bir mevzuat veya tebliğ PDF'i ekleyin")

    uploaded_file = st.file_uploader("PDF Dosyası Seçin", type=["pdf"])

    if st.button("Belgeyi Veritabanına İndeksle", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("Belge yapay zeka tarafından okunuyor ve vektörleştiriliyor... ⏳"):
                try:
                    # Dosyayı FastAPI'nin anlayacağı formata (multipart/form-data) çeviriyoruz
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    res = requests.post(f"{API_BASE_URL}/upload", files=files)

                    if res.status_code == 200:
                        st.success(res.json().get("message"))
                    else:
                        error_detail = res.json().get("detail", "Bilinmeyen bir hata oluştu.")
                        st.error(f"Yükleme başarısız: {error_detail}")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")
        else:
            st.warning("Lütfen sisteme eklemek için önce bir PDF dosyası seçin.")

    st.divider()
    # ----------------------------------------

    st.header("📊 Yönetici Paneli")
    st.caption("Sistem Performansı ve Loglar (API)")

    if st.button("Son İstekleri Göster", use_container_width=True):
        try:
            response = requests.get(f"{API_BASE_URL}/logs?limit=10")
            if response.status_code == 200:
                logs_data = response.json()
                if logs_data:
                    logs = [
                        {
                            "ID": row["id"],
                            "Süre (ms)": row["time_taken_ms"],
                            "Soru": row["prompt"],
                            "Faydalı?": "👍" if row.get("is_helpful") is True else (
                                "👎" if row.get("is_helpful") is False else "➖")
                        }
                        for row in logs_data
                    ]
                    st.dataframe(logs)
                else:
                    st.info("Henüz log kaydı bulunmuyor.")
            else:
                st.error("Loglar çekilemedi. API yanıt vermiyor.")
        except Exception as e:
            st.error(f"API bağlantı hatası: {e}")

    st.divider()
    st.write("Bu panel sadece yöneticiler içindir. Veriler FastAPI üzerinden anlık çekilir.")
# ----------------------------------------------

# --- ANA EKRAN (SOHBET ARAYÜZÜ) ---
st.title("🏦 BDDK Mevzuat Asistanı")
st.caption("Softtech Regülasyon RAG Sistemi")

# Önceki mesajları ekranda göster
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("🔍 Dayanılan Orijinal BDDK Mevzuat Maddeleri"):
                for i, source_text in enumerate(msg["sources"], 1):
                    st.markdown(f"**Kaynak {i}:**\n{source_text}")
                    st.divider()
        if msg.get("feedback_given"):
            st.caption(f"Sizin Değerlendirmeniz: {'👍 Faydalı' if msg['feedback_is_helpful'] else '👎 Geliştirilmeli'}")

# Kullanıcıdan Soru Alma
if prompt := st.chat_input("BDDK yönetmeliği hakkında bir soru sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Asistan belgeleri inceliyor... ⏳")

        try:
            # POST İsteği Atıyoruz
            payload = {
                "query": prompt,
                "session_id": st.session_state.session_id
            }
            response = requests.post(f"{API_BASE_URL}/ask", json=payload)
            response.raise_for_status()

            data = response.json()
            answer = data.get("answer", "Cevap alınamadı.")
            time_taken = data.get("time_taken_ms", 0)
            sources = data.get("sources", [])
            log_id = data.get("log_id")

            full_response = f"{answer}\n\n*(Yanıt süresi: {time_taken} ms)*"
            message_placeholder.markdown(full_response)

            if sources:
                with st.expander("🔍 Dayanılan Orijinal BDDK Mevzuat Maddeleri"):
                    for i, source_text in enumerate(sources, 1):
                        st.markdown(f"**Kaynak {i}:**\n{source_text}")
                        st.divider()

            # Yeni mesajı hafızaya ekliyoruz
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "log_id": log_id,
                "feedback_given": False,
                "feedback_is_helpful": None
            })

            st.rerun()

        except Exception as e:
            message_placeholder.markdown(
                f"**Bağlantı Hatası:** Arka plan API'si kapalı olabilir. Lütfen Uvicorn sunucusunun çalıştığından emin olun. Hata: {e}")

# --- GERİ BİLDİRİM (FEEDBACK) KONTROLÜ ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]

    if not last_msg.get("feedback_given") and last_msg.get("log_id"):
        st.write("---")
        st.markdown("**Bu cevap size yardımcı oldu mu?**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("👍 Evet, faydalıydı", key=f"up_{last_msg['log_id']}"):
                requests.put(f"{API_BASE_URL}/logs/{last_msg['log_id']}?is_helpful=true")
                st.session_state.messages[-1]["feedback_given"] = True
                st.session_state.messages[-1]["feedback_is_helpful"] = True
                st.rerun()

        with col2:
            if st.button("👎 Hayır, geliştirmeli", key=f"down_{last_msg['log_id']}"):
                requests.put(f"{API_BASE_URL}/logs/{last_msg['log_id']}?is_helpful=false")
                st.session_state.messages[-1]["feedback_given"] = True
                st.session_state.messages[-1]["feedback_is_helpful"] = False
                st.rerun()