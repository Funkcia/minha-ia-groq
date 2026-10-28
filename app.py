import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS TEMA ESCURO (Agressivo) ---
CSS_TEMA = ""
if st.session_state.tema == "escuro":
    CSS_TEMA = """
    <style>
    /* Fundo geral */
    .stApp { background-color: #0e1117 !important; }
    .stApp * { color: #fafafa !important; }
    
    /* Sidebar */
    .stSidebar { background-color: #161b22 !important; }
    .stSidebar * { color: #fafafa !important; }
    
    /* Chat Messages */
    .stChatMessage { background-color: #1c2128 !important; border: 1px solid #30363d !important; }
    .stChatMessage .stMarkdown, .stChatMessage .stMarkdown p { color: #fafafa !important; }
    
    /* CAIXA DE DIGITAÇÃO (Correção crucial) */
    .stChatInput textarea, div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        caret-color: #ffffff !important;
        background-color: #21262d !important;
    }
    .stChatInput textarea::placeholder { color: #8b949e !important; }
    
    /* Botões e Selects */
    .stSelectbox > div > div > div { background-color: #21262d !important; color: #fafafa !important; }
    .stButton > button { color: #fafafa !important; border: 1px solid #30363d !important; background-color: #21262d !important; }
    .stButton > button:hover { background-color: #30363d !important; }
    .stButton > button[kind="primary"] { background-color: #ff4b4b !important; color: white !important; }
    
    /* Outros elementos */
    hr { border-color: #30363d !important; }
    .stCaption { color: #8b949e !important; }
    .stAlert { background-color: #1c2128 !important; color: #fafafa !important; }
    .stStatusWidget { background-color: #1c2128 !important; }
    .stStatusWidget * { color: #fafafa !important; }
    
    /* Esconder barra de rolagem feia */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
    </style>
    """
else:
    CSS_TEMA = """
    <style>
    /* Tema Claro - Texto preto na caixa de digitação */
    .stChatInput textarea, div[data-testid="stChatInput"] textarea {
        color: #000000 !important;
        caret-color: #000000 !important;
    }
    </style>
    """

st.markdown(CSS_TEMA, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES PARA BOTÕES (HTML Isolado) ---
def criar_botao_ouvir(texto):
    # Escape simples para JavaScript
    texto_js = texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    html = f"""
    <button onclick="falarTexto('{texto_js}')" style="background:transparent; border:1px solid #ccc; border-radius:4px; padding:4px 12px; cursor:pointer; font-size:13px;">🔊 Ouvir</button>
    <script>
    function falarTexto(t) {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(t);
        u.lang = 'pt-BR';
        const vozes = window.speechSynthesis.getVoices();
        const vozPt = vozes.find(v => v.lang.includes('pt'));
        if (vozPt) u.voice = vozPt;
        window.speechSynthesis.speak(u);
    }}
    </script>
    """
    components.html(html, height=35, width=100)

def criar_botao_copiar(texto, idx):
    texto_js = texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    html = f"""
    <button id="btn_{idx}" onclick="copiarTexto('{texto_js}', 'btn_{idx}')" style="background:transparent; border:1px solid #ccc; border-radius:4px; padding:4px 12px; cursor:pointer; font-size:13px;">📋 Copiar</button>
    <script>
    function copiarTexto(t, id) {{
        navigator.clipboard.writeText(t).then(() => {{
            const btn = document.getElementById(id);
            if (btn) {{ btn.innerText = '✓ Copiado!'; setTimeout(() => {{ btn.innerText = '📋 Copiar'; }}, 1500); }}
        }});
    }}
    </script>
    """
    components.html(html, height=35, width=100)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Claro", use_container_width=True, type="primary" if st.session_state.tema == "claro" else "secondary"):
            if st.session_state.tema != "claro":
                st.session_state.tema = "claro"
                st.rerun()
    with col2:
        if st.button("🌙 Escuro", use_container_width=True, type="primary" if st.session_state.tema == "escuro" else "secondary"):
            if st.session_state.tema != "escuro":
                st.session_state.tema = "escuro"
                st.rerun()
    
    st.markdown("---")
    persona = st.selectbox("🎭 Personalidade da IA:", ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"])
    st.markdown("---")
    st.subheader("💬 Conversas")
    
    if st.button("➕ Nova Conversa", use_container_width=True):
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": f"Conversa {len(st.session_state.conversations) + 1}", "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.rerun()
    
    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            col1, col2 = st.columns([4, 1])
            with col1:
                ativo = "✅ " if conv
