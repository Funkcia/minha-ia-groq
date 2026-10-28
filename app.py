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
                ativo = "✅ " if conv["id"] == st.session_state.current_conv_id else ""
                if st.button(f"{ativo}{conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                    st.session_state.current_conv_id = conv["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]: st.session_state.current_conv_id = None
                    st.rerun()
    st.markdown("---")
    st.caption("Feito com Streamlit + Groq ")

# --- PROMPTS ---
prompts = {
    "Assistente Padrão": "Você é um assistente útil, direto e fala português brasileiro.",
    "Professor Didático": "Você é um professor paciente e didático. Explica conceitos complexos de forma simples. Fala português brasileiro.",
    "Programador Sênior": "Você é um engenheiro de software sênior. Foca em código limpo e boas práticas. Fala português brasileiro.",
    "Amigo Informal": "Você é um amigo próximo e descontraído. Usa gírias leves, é empático. Fala português brasileiro."
}

# --- CARREGAR CONVERSA ---
if st.session_state.current_conv_id:
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv:
        st.session_state.messages = current_conv["messages"]
        system_prompt = prompts[current_conv.get("persona", persona)]
    else:
        st.session_state.messages = []
        system_prompt = prompts[persona]
else:
    st.session_state.messages = []
    system_prompt = prompts[persona]

# --- TÍTULO ---
if st.session_state.current_conv_id and current_conv:
    st.title(f"💬 {current_conv['title']}")
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title("🤖 Minha IA Pessoal")
    st.info("👈 Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant":
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                criar_botao_ouvir(message["content"])
            with col_btn2:
                criar_botao_copiar(message["content"], idx)

# --- BUSCA WEB ---
def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados: return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception: return "Erro ao buscar na web."

# --- INPUT ---
if prompt := st.chat_input("Digite sua mensagem..."):
    if not st.session_state.current_conv_id:
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": prompt[:30] + "..." if len(prompt) > 30 else prompt, "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.session_state.messages = []
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 0:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

    with st.chat_message("user"): st.markdown(prompt)

    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado", "últimas", "quanto está", "cotação"]
    precisa_buscar = any(palavra in prompt.lower() for palavra in palavras_chave)

    mensagem_para_ia = prompt
    if precisa_buscar:
        with st.status("🔍 Buscando informações atualizadas na web...", expanded=True) as status:
            contexto = pesquisar_na_web(prompt)
            st.write("Dados encontrados!")
            status.update(label="✅ Busca concluída!", state="complete", expanded=False)
            mensagem_para_ia = f"Use este contexto da web para responder:\n{contexto}\n\nPergunta: {prompt}"

    with st.chat_message("assistant"):
        with st.spinner(" Pensando..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            mensagens_envio = [{"role": "system", "content": system_prompt}] + st.session_state.messages[:-1] + [{"role": "user", "content": mensagem_para_ia}]
            response = client.chat.completions.create(model="openai/gpt-oss-120b", messages=mensagens_envio, temperature=0.7, max_tokens=1024)
            resposta = response.choices[0].message.content
            st.markdown(resposta)
            st.markdown("<script>setTimeout(() => window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'}), 300);</script>", unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
    if current_conv: current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
