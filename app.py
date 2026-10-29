import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- ESTADO INICIAL ---
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS: TEMA CLARO INSTANTÂNEO (ativa quando o checkbox está marcado) ---
st.markdown("""
<style>
/* ===== Botões isolados (Ouvir/Copiar): cinza neutro, visível nos 2 temas ===== */
.btn-neutro {
    background: transparent;
    border: 1px solid #8b949e;
    border-radius: 6px;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
    width: 100%;
    color: #8b949e;
}
.btn-neutro:hover { border-color: #b1bac4; color: #b1bac4; }

/* ===== Bolhas do chat arredondadas ===== */
.stChatMessage { border-radius: 12px; }

/* =====================================================
   MODO CLARO (ativa com a caixinha "Modo claro" marcada)
   ===================================================== */
.stApp:has(input[type="checkbox"]:checked) {
    background-color: #ffffff !important;
}
.stApp:has(input[type="checkbox"]:checked) * {
    color: #262730 !important;
}
body:has(input[type="checkbox"]:checked) {
    background-color: #ffffff !important;
}
.stApp:has(input[type="checkbox"]:checked) .stSidebar,
.stApp:has(input[type="checkbox"]:checked) .stSidebar > div {
    background-color: #f6f8fa !important;
}
.stApp:has(input[type="checkbox"]:checked) .stChatMessage {
    background-color: #f6f8fa !important;
    border: 1px solid #d0d7de !important;
}
.stApp:has(input[type="checkbox"]:checked) .stChatInput textarea,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] textarea {
    background-color: #ffffff !important;
    caret-color: #262730 !important;
}
.stApp:has(input[type="checkbox"]:checked) .stChatInput textarea::placeholder,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] textarea::placeholder {
    color: #808495 !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInputContainer"],
.stApp:has(input[type="checkbox"]:checked) .stChatInputContainer,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"],
.stApp:has(input[type="checkbox"]:checked) .stChatInput,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] div,
.stApp:has(input[type="checkbox"]:checked) .stChatInput div,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stBottom"],
.stApp:has(input[type="checkbox"]:checked) [data-testid="stBottomBlockContainer"] {
    background-color: #ffffff !important;
    border-color: #d0d7de !important;
}
.stApp:has(input[type="checkbox"]:checked) .stButton > button {
    background-color: #ffffff !important;
    border: 1px solid #d0d7de !important;
}
.stApp:has(input[type="checkbox"]:checked) .stButton > button:hover {
    background-color: #f0f2f6 !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stSelectbox"] div,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stSelectbox"] div div {
    background-color: #ffffff !important;
}
.stApp:has(input[type="checkbox"]:checked) hr {
    border-color: #d0d7de !important;
}
.stApp:has(input[type="checkbox"]:checked) .stCaption {
    color: #57606a !important;
}
.stApp:has(input[type="checkbox"]:checked) .stTextInput > div > div > input {
    background-color: #ffffff !important;
    border: 1px solid #d0d7de !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stExpander"] details,
.stApp:has(input[type="checkbox"]:checked) .streamlit-expanderHeader {
    background-color: #ffffff !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stAlert"],
.stApp:has(input[type="checkbox"]:checked) .stAlert {
    background-color: #f6f8fa !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stStatusWidget"],
.stApp:has(input[type="checkbox"]:checked) .stStatusWidget {
    background-color: #f6f8fa !important;
}

/* ===== Topo branco com botões em "chips" escuros (ícones visíveis) ===== */
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"],
.stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"],
.stApp:has(input[type="checkbox"]:checked) header {
    background-color: #ffffff !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"] button,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"] button {
    background-color: #0e1117 !important;
    border-radius: 8px !important;
}
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"] button *,
.stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"] button * {
    color: #fafafa !important;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Interruptor de tema (instantâneo, mesma aba)
    st.checkbox("☀️ Modo claro", help="Desmarcado = tema escuro")

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
            ativo = "✅ " if conv["id"] == st.session_state.current_conv_id else ""
            if st.button(f"{ativo}{conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                st.session_state.current_conv_id = conv["id"]
                st.rerun()

            col_rename, col_delete = st.columns([1, 1])
            with col_rename:
                if st.button("✏️ Renomear", key=f"rename_{conv['id']}", use_container_width=True):
                    st.session_state[f"renaming_{conv['id']}"] = True
            with col_delete:
                if st.button("🗑️ Deletar", key=f"del_{conv['id']}", use_container_width=True):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

            if st.session_state.get(f"renaming_{conv['id']}", False):
                with st.expander("Renomear conversa", expanded=True):
                    new_name = st.text_input("Novo nome:", value=conv["title"], key=f"input_{conv['id']}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Salvar", key=f"save_{conv['id']}", use_container_width=True):
                            conv["title"] = new_name
                            st.session_state[f"renaming_{conv['id']}"] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_{conv['id']}", use_container_width=True):
                            st.session_state[f"renaming_{conv['id']}"] = False
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
                <style>body {{ margin: 0; padding: 0; background: transparent; }}</style>
                <button class="btn-neutro" onclick="falar()">🔊 Ouvir</button>
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
                components.html(html_ouvir, height=50, width=130, scrolling=False)

            # === BOTÃO COPIAR ===
            with col_btn2:
                texto_escape = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                html_copiar = f"""
                <style>body {{ margin: 0; padding: 0; background: transparent; }}</style>
                <button id="btn" class="btn-neutro" onclick="copiar()">📋 Copiar</button>
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
                components.html(html_copiar, height=50, width=130, scrolling=False)

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
        with st.spinner("🤔 Pensando..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            mensagens_envio = [{"role": "system", "content": system_prompt}] + st.session_state.messages[:-1] + [{"role": "user", "content": mensagem_para_ia}]
            response = client.chat.completions.create(model="openai/gpt-oss-120b", messages=mensagens_envio, temperature=0.7, max_tokens=1024)
            resposta = response.choices[0].message.content
            st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
    if current_conv: current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
