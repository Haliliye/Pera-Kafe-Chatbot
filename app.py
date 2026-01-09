import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import re
import speech_recognition as sr
from gtts import gTTS
import io
import base64 
import os
from streamlit_mic_recorder import mic_recorder 

# ---  API ANAHTARI ---
# Anahtarı Streamlit Secrets'tan çekiyoruz
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit ayarlarından ekleyin.")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pera Kafe", page_icon="☕", layout="wide")


#  CSS ENTEGRASYONU 

@st.cache_resource
def load_css():
    st.markdown("""
    <style>
    /* 1. ANA ARKA PLAN */
    .stApp {
        background-color: #F5F1E8; 
        color: #4A3B2A; 
    }

    /* 2. HEADER VE BOTTOM GİZLEME */
    header[data-testid="stHeader"] {
        background-color: #F5F1E8 !important;
    }
    div[data-testid="stBottom"] {
        background-color: #F5F1E8 !important;
        padding-bottom: 20px;
    }

    /* 3. YAN MENÜ (SIDEBAR) */
    section[data-testid="stSidebar"] {
        background-color: #E8D5B5; 
        color: #4A3B2A;
    }
      
    /* 4. MENÜ VE LİSTE DÜZELTMESİ */
    div[data-testid="stSelectbox"] label p {
        color: #4A3B2A !important;
        font-weight: bold;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #4E342E !important; 
        border: 2px solid #3E2723;
        color: white !important;
    }
    /* İçerideki tüm metinleri ve ikonları zorla beyaz yap */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    div[data-testid="stSelectbox"] svg {
        fill: #FFFFFF !important;
    }

    /* Popover (Açılır Menü) Renkleri */
    div[data-baseweb="popover"] {
        background-color: #3E2723 !important;
    }
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] div {
        background-color: #3E2723 !important;
    }
    div[data-baseweb="popover"] * {
        color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li:hover *, 
    div[data-baseweb="popover"] li:hover div {
        background-color: #5D4037 !important;
    }
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #8D6E63 !important;
    }

    /* 5. KUTULAR (ADİSYON VE SOHBET) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; 
        border: 4px solid #5D4037 !important; 
        border-radius: 15px !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.15) !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] h3 {
        color: #5D4037 !important;
        border-bottom: 2px solid #D7CCC8;
        padding-bottom: 10px;
        margin-bottom: 15px !important;
    }

    /* 6. GENEL METİNLER */
    h1, h2, h3, span, p, div {
        color: #4A3B2A !important;
    }

    /* 7. BUTONLAR */
    .stButton > button {
        background-color: #4E342E !important; 
        color: #FFFFFF !important; 
        border: none !important;
        border-radius: 10px;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 0.8rem 1rem;
        transition: all 0.2s ease;
    }
    .stButton > button p, .stButton > button div {
        color: #FFFFFF !important;
    }
    .stButton > button:hover {
        background-color: #6D4C41 !important; 
        color: #FFFFFF !important; 
        transform: scale(1.02);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* 8. CHAT BALONLARI */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F5F5F5 !important; 
        border: 1px solid #D7CCC8;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #EFEBE0 !important; 
        border: 1px solid #A1887F;
    }

    /* 9. METİN GİRİŞ KUTUSU */
    div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #3E2723 !important;
        border: 3px solid #5D4037 !important;
        border-radius: 10px;
        padding: 10px;
    }
    div[data-testid="stTextInput"] label p {
        color: #4A3B2A !important;
        font-weight: bold;
    }
      
    /* 10. AVATAR ÇERÇEVESİ */
    .avatar-frame {
        width: 100%;  
        max-width: 650px; 
        height: 55vh;      
        border-radius: 20px;
        overflow: hidden;
        border: 6px solid #4E342E; 
        box-shadow: 0 12px 30px rgba(0,0,0,0.3); 
        background-color: #D7CCC8; 
    }
    .avatar-frame img, .avatar-frame video {
        width: 100%;
        height: 100%;
        object-fit: cover;    
        object-position: top center; 
    }
    .avatar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 10px;
    }
      
    .block-container {
        padding-top: 3rem !important; 
        padding-bottom: 5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_css() 


#  AVATAR / GÖRSEL YÖNETİMİ

def get_base64_content(file_path):
    """Dosyayı base64 formatına çevirir."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_avatar(durum="idle"):
    """
    durum="idle" -> Sabit Resim (idle_cafe.png)
    durum="talking" -> Konuşan Video (Talking_cafe.mp4)
    """
    IDLE_IMG = "idle_cafe.png"
    

    
    st.markdown("""
        <style>
        .avatar-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 10px;
        }
        .block-container {
            padding-top: 5rem;
            padding-bottom: 0rem;
        }
        .avatar-frame {
            width: 800px;  
            height: 450px; 
            border-radius: 10%;
            overflow: hidden;
            border: 5px solid #6F4E37;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            background-color: #1E1E1E;
        }
        .avatar-frame img, .avatar-frame video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        </style>
    """, unsafe_allow_html=True)

    content_html = ""
    
    
    b64 = get_base64_content(IDLE_IMG)
    if b64:
            content_html = f"""
                <div class="avatar-container">
                    <div class="avatar-frame">
                        <img src="data:image/jpeg;base64,{b64}">
                    </div>
                </div>
            """
    else:
            st.warning(f"{IDLE_IMG} bulunamadı!")

    st.markdown(content_html, unsafe_allow_html=True)



# --- SEPET BAŞLANGIÇ ---
if "sepet" not in st.session_state:
    st.session_state.sepet = []

def sepeti_bosalt():
    st.session_state.sepet = []

# --- SES FONKSİYONLARI ---
def bytes_to_text(audio_bytes):
    """mic_recorder'dan gelen bayt verisini metne çevirir."""
    r = sr.Recognizer()
    try:
        # Bayt verisini ses dosyası gibi okuyoruz
        audio_io = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_io) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="tr-TR")
            return text
    except sr.UnknownValueError:
        return None
    except Exception as e:
        st.error(f"Ses işleme hatası: {e}")
        return None

def metni_oku(text):
    try:
        tts = gTTS(text=text, lang='tr')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        audio_b64 = base64.b64encode(audio_bytes.read()).decode()
        md = f"""
            <audio autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Ses hatası: {e}")

# --- VERİTABANI ---
def get_menu_data():
    try:
        conn = sqlite3.connect("kafe.db")
        cursor = conn.cursor()
        cursor.execute("SELECT kategori, urun_adi, taban_fiyat, boyut_var FROM menu")
        rows = cursor.fetchall()
        conn.close()
    except:
        return {}, "Veritabanı hatası."

    menu_dict = {}
    ai_text = "GÜNCEL FİYAT LİSTESİ:\n"

    for row in rows:
        kategori, urun, fiyat, boyut_var = row
        if kategori not in menu_dict: menu_dict[kategori] = []

        if boyut_var:
            fiyat_str = f"Küçük: {fiyat}₺ | Orta: {fiyat+15}₺ | Büyük: {fiyat+25}₺"
            ai_fiyat = f"- {urun} (Küçük): {fiyat} TL\n- {urun} (Orta): {fiyat+15} TL\n- {urun} (Büyük): {fiyat+25} TL"
        else:
            fiyat_str = f"Tek Boy: {fiyat}₺"
            ai_fiyat = f"- {urun}: {fiyat} TL"

        menu_dict[kategori].append({"urun": urun, "fiyat_gorunum": fiyat_str, "taban_fiyat": fiyat})
        ai_text += ai_fiyat + "\n"

    return menu_dict, ai_text

menu_db, menu_text_for_ai = get_menu_data()

# SOL PANEL 

with st.sidebar:
    st.title("☕ Pera Kafe")
    st.markdown("---")
    
    st.header("📜 Menü")
    
    if menu_db:
        # Varsayılan kategori (Session state yoksa ilkini al)
        if "secili_kat" not in st.session_state:
            st.session_state.secili_kat = list(menu_db.keys())[0]

        # Dropdown görünümü veren Expander
        with st.expander(f"{st.session_state.secili_kat}", expanded=False):
            # İçine radio buton koyuyoruz ama sadece seçim için
            yeni_secim = st.radio(
                "Gizli Başlık",
                list(menu_db.keys()),
                label_visibility="collapsed",
                index=list(menu_db.keys()).index(st.session_state.secili_kat)
            )
            
            # Seçim değişirse state'i güncelle (ve sayfa yenilensin diye)
            if yeni_secim != st.session_state.secili_kat:
                st.session_state.secili_kat = yeni_secim
                st.rerun()

        # Listeleme
        secilen_kategori = st.session_state.secili_kat
        if secilen_kategori in menu_db:
            for item in menu_db[secilen_kategori]:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1: st.markdown(f"**{item['urun']}**")
                    with c2: st.markdown(f"*{item['taban_fiyat']}₺*")
                    st.caption(item['fiyat_gorunum'])

# ANA EKRAN DÜZENİ

# 1. Mesaj Geçmişini Başlat 
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hoş geldiniz! Size ne ikram edelim?"})

col_center, col_receipt = st.columns([2, 1])

# --- ORTA KOLON: SADECE AVATAR VE GİRİŞ BUTONLARI ---
with col_center:
    
    # 1. BÖLÜM: AVATAR
    render_avatar("idle")

    st.write("") # Görsel boşluk

   

    # 2. BÖLÜM: BUTONLAR 
    c_btn, c_input = st.columns([1, 4])
    
    # --- SES KAYIT BİLEŞENİ ---
    with c_btn:
        audio = mic_recorder(
            start_prompt="🎙️ Konuş",
            stop_prompt="⏹️ Durdur",
            just_once=True,
            use_container_width=True,
            format="wav",
            key="recorder"
        )
        
        if audio:
            transcribed_text = bytes_to_text(audio['bytes'])
            if transcribed_text:
                st.session_state.ses_input = transcribed_text

    # --- YAZILI GİRİŞ ---
    with c_input:
        user_input = st.chat_input("Veya buraya yazın...")

# --- SAĞ KOLON: SOHBET GEÇMİŞİ + ADİSYON ---
with col_receipt:
    
    
    # A) SOHBET GEÇMİŞİ (SABİT BOYUT + SON 3 MESAJ)
    st.markdown("##### 💬 Son Konuşmalar")
    
    
    chat_container = st.container(height=250, border=True) 
    
    with chat_container:
        
        son_mesajlar = st.session_state.messages[-3:] 
        
        if not son_mesajlar:
            st.info("Henüz mesaj yok.")
            
        for message in son_mesajlar:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    st.write("") 

    
    # B) ADİSYON (SABİT BOYUT)
    receipt_container = st.container(height=350, border=True)

    with receipt_container:
        st.subheader("🧾 Canlı Adisyon")
        st.divider()
        
        toplam = 0
        if st.session_state.sepet:
            for i, urun in enumerate(st.session_state.sepet):
                c_ad, c_fiyat = st.columns([3, 1])
                c_ad.write(f"{i+1}. {urun['ad']}")
                c_fiyat.write(f"**{urun['fiyat']}₺**")
                toplam += urun['fiyat']
            
            st.divider()
            st.markdown(f"### Toplam: {toplam} TL")
            
            # Butonu en alta koyuyoruz
            st.write("") 
            if st.button("Ödeme Yap / Sıfırla", use_container_width=True):
                sepeti_bosalt()
                st.rerun()
        else:
            st.info("Sepetiniz şu an boş.")


#  AI ve SES İŞLEME MANTIĞI


# Girdi Kontrolü (Ses veya Yazı)
final_input = None

# Eğer ses input gelmişse onu al, yoksa yazıyı al
if "ses_input" in st.session_state and st.session_state.ses_input:
    final_input = st.session_state.ses_input
    del st.session_state.ses_input 
elif user_input:
    final_input = user_input

if final_input:
    # 1. Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": final_input})
    
    # 2. AI Hazırlığı
    system_instruction = f"""
    Sen "Pera Kafe"nin garsonusun.
    Menü: {menu_text_for_ai}
    
    GÖREVİN:
    1. Müşteriyle samimi konuş.
    2. Eğer siparişte bir DEĞİŞİKLİK olursa, sepetin SON HALİNİ JSON olarak ver.
    
    MİKTAR KURALI:
    - "3 tane Çay" denirse, JSON listesine **3 TANE AYRI** çay objesi ekle.
    
    FORMAT:
    JSON kodunu cümlenin en sonuna gizlice ekle:
    SIPARIS_JSON:[{{"ad": "Ürün Adı", "fiyat": 00}}]
    """

    try:
        genai.configure(api_key=MY_API_KEY)
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = next((m for m in available_models if "flash" in m), "models/gemini-1.5-flash-latest")
        except:
            model_name = "gemini-1.5-flash"

        model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)

        chat_history = []
        for msg in st.session_state.messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=chat_history)
        
        with st.spinner("Garson düşünüyor..."):
            response = chat.send_message(final_input)
            bot_text = response.text

        # 3. JSON Ayrıştırma
        siparis_match = re.search(r"SIPARIS_JSON:(.*)", bot_text, re.DOTALL)
        json_data = None

        if siparis_match:
            clean_text = bot_text.replace(siparis_match.group(0), "")
            try:
                json_data = json.loads(siparis_match.group(1).strip())
            except:
                pass
        else:
            clean_text = bot_text

        # 4. Cevabı Ekle ve Sesi Kuyruğa Al
        st.session_state.messages.append({"role": "assistant", "content": clean_text})
        st.session_state.ses_kuyrugu = clean_text 

        # 5. Sepeti Güncelle
        if json_data is not None:
            st.session_state.sepet = json_data
        
        st.rerun()

    except Exception as e:
        st.error(f"Hata: {e}")


# SES OYNATMA (Sayfa Sonu)
if "ses_kuyrugu" in st.session_state and st.session_state.ses_kuyrugu:
    metni_oku(st.session_state.ses_kuyrugu)

    del st.session_state.ses_kuyrugu
