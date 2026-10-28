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
if "renaming_id" not in st.session_state:
    st.session_state.renaming_id = None

# --- CSS E TEMA ---
# Injeta a classe 'dark-mode' no body se o tema for escuro
if st.session_state.tema == "escuro":
    st.markdown("""
    <script>document.body.classList.add('dark-mode');</script>
    <style>
    body.dark-mode .stApp { background-color: #0e1117 !important; color: #fafafa !important; }
    body.dark-mode .stSidebar { background-color: #161b22 !important; }
    body.dark-mode .stSidebar .stMarkdown h1,
    body.dark-mode .stSidebar .stMarkdown h2,
    body.dark-mode .stSidebar .stMarkdown h3,
    body.dark-mode .stSidebar .stMarkdown p,
    body.dark-mode .stSidebar .stMarkdown label,
    body.dark-mode .stSidebar .stMarkdown span,
    body.dark-mode .stSidebar .stMarkdown div { color: #fafafa !important; }
    body.dark-mode .stSelectbox [data-baseweb="select"] { background-color: #21262d !important; color: #fafafa !important; }
    body.dark-mode .stChatMessage { background-color: #1c2128 !important; border: 1px solid #30363d !important; }
    body.dark-mode .stChatMessage * { color: #fafafa !important; }
    body.dark-mode .stChatInput textarea { background-color: #21262d !important; color: #fafafa !important; caret-color: #fafafa !important; }
    body.dark-mode .stChatInput textarea::placeholder { color: #8b949e !important; }
    body.dark-mode hr { border-color: #30363d !important; }
    body.dark-mode .stCaption { color: #8b949e !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<script>document.body.classList.remove('dark-mode');</script>", unsafe_allow_html=True)

# CSS Global para botões
st.markdown("""
<style>
.btn-acao {
    background: transparent;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #24292f;
    min-width: 100px;
    justify-content: center;
}
.btn-acao:hover { background-color: #f3f4f6; border-color: #afb1b8; }
body.dark-mode .btn-acao { border-color: #30363d; color: #c9d1d9; }
body.dark-mode .btn-acao:hover { background-color: #21262d; border-color: #8b949e; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("️ Configurações")

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

    st.divider()
    persona = st.selectbox("🎭 Personalidade da IA:", ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"])
    st.divider()
    st.subheader("💬 Conversas")

    if st.button("➕ Nova Conversa", use_container_width=True):
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": f"Conversa {len(st.session_state.conversations) + 1}", "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.rerun()

    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                ativo = "✅ " if conv["id"] == st.session_state.current_conv_id else ""
                if st.button(f"{ativo}{conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                    st.session_state.current_conv_id = conv["id"]
                    st.session_state.renaming_id = None
                    st.rerun()
            
            with col2:
                if st.button("✏️", key=f"rename_{conv['id']}", use_container_width=True):
                    st.session_state.renaming_id = conv["id"]
            
            with col3:
                if st.button("🗑️", key=f"del_{conv['id']}", use_container_width=True):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

            # Interface de Renomear
            if st.session_state.renaming_id == conv["id"]:
                st.markdown("**Renomear:**")
                new_name = st.text_input("Novo nome:", value=conv["title"], key=f"input_{conv['id']}", label_visibility="collapsed")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾", key=f"save_{conv['id']}", use_container_width=True):
                        conv["title"] = new_name
                        st.session_state.renaming_id = None
                        st.rerun()
                with col_cancel:
                    if st.button("❌", key=f"cancel_{conv['id']}", use_container_width=True):
                        st.session_state.renaming_id = None
                        st.rerun()

    st.divider()
    st.caption("Feito com Streamlit + Groq 🚀")

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
            st.divider()
            col_btn1, col_btn2 = st.columns(2)

            # === BOTÃO OUVIR ===
            with col_btn1:
                texto_escape = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                html_ouvir = f"""
                <button class="btn-acao" onclick="falar()">🔊 Ouvir</button>
                <script>
                function falar() {{
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance('{texto_escape}');
                    u.lang = 'pt-BR';
                    const vozes = window.speechSynthesis.getVoices();
                    const vozPt = vozes.find(v => v.lang.includes('pt'));
                    if (vozPt) u.voice = vozPt;
                    window.speechSynthesis.speak(u);
                }}
                </script>
                """
                components.html(html_ouvir, height=40, width=110, scrolling=False)

            # === BOTÃO COPIAR (Com feedback visual) ===
            with col_btn2:
                texto_escape = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                html_copiar = f"""
                <button id="btn" class="btn-acao" onclick="copiar()">📋 Copiar</button>
                <script>
                function copiar() {{
                    navigator.clipboard.writeText('{texto_escape}').then(() => {{
                        const btn = document.getElementById('btn');
                        btn.innerText = '✅ Copiado!';
                        setTimeout(() => {{ btn.innerText = '📋 Copiar'; }}, 1500);
                    }});
                }}
                </script>
                """
                components.html(html_copiar, height=40, width=110, scrolling=False)

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
