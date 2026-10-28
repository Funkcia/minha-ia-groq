import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="", layout="wide")

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS GLOBAL (funciona para ambos os temas) ---
CSS_TEMA = """
<style>
/* === TEMA CLARO === */
.stApp {
    background-color: #FFFFFF;
    color: #262730;
}
.stChatInput textarea {
    color: #262730 !important;
    caret-color: #262730 !important;
}
.stChatInput textarea::placeholder {
    color: #808495 !important;
}

/* === TEMA ESCURO (sobrescreve quando ativado) === */
body[data-theme="escuro"] .stApp,
.stApp[data-theme="escuro"] {
    background-color: #0E1117 !important;
    color: #FAFAFA !important;
}
body[data-theme="escuro"] .stSidebar,
.stApp[data-theme="escuro"] .stSidebar {
    background-color: #161B22 !important;
}
body[data-theme="escuro"] .stSidebar *,
.stApp[data-theme="escuro"] .stSidebar * {
    color: #FAFAFA !important;
}
body[data-theme="escuro"] .stSelectbox [data-baseweb="select"],
.stApp[data-theme="escuro"] .stSelectbox [data-baseweb="select"] {
    background-color: #21262D !important;
    color: #FAFAFA !important;
}
body[data-theme="escuro"] .stChatMessage,
.stApp[data-theme="escuro"] .stChatMessage {
    background-color: #1C2128 !important;
    border: 1px solid #30363D !important;
}
body[data-theme="escuro"] .stChatMessage *,
.stApp[data-theme="escuro"] .stChatMessage * {
    color: #FAFAFA !important;
}
body[data-theme="escuro"] .stChatInput textarea,
.stApp[data-theme="escuro"] .stChatInput textarea {
    color: #FAFAFA !important;
    caret-color: #FAFAFA !important;
    background-color: #21262D !important;
}
body[data-theme="escuro"] .stChatInput textarea::placeholder,
.stApp[data-theme="escuro"] .stChatInput textarea::placeholder {
    color: #8B949E !important;
}
body[data-theme="escuro"] hr,
.stApp[data-theme="escuro"] hr {
    border-color: #30363D !important;
}
body[data-theme="escuro"] .stCaption,
.stApp[data-theme="escuro"] .stCaption {
    color: #8B949E !important;
}

/* === BOTÕES DE AÇÃO === */
.btn-acao {
    background: transparent;
    border: 1px solid #D0D7DE;
    border-radius: 6px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #24292F;
    min-width: 100px;
    justify-content: center;
}
.btn-acao:hover {
    background-color: #F3F4F6;
    border-color: #AFB1B8;
}
body[data-theme="escuro"] .btn-acao,
.stApp[data-theme="escuro"] .btn-acao {
    border-color: #30363D;
    color: #C9D1D9;
}
body[data-theme="escuro"] .btn-acao:hover,
.stApp[data-theme="escuro"] .btn-acao:hover {
    background-color: #21262D;
    border-color: #8B949E;
}
</style>
"""

# Aplica o tema via atributo data-theme
st.markdown(f'<div data-theme="{st.session_state.tema}"></div>', unsafe_allow_html=True)
st.markdown(CSS_TEMA, unsafe_allow_html=True)

# --- JavaScript Global para Copiar ---
JS_GLOBAL = """
<script>
window.copiarTextoGlobal = function(texto) {
    // Decodifica HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = texto;
    const textoLimpo = textarea.value;
    
    navigator.clipboard.writeText(textoLimpo).then(() => {
        // Envia mensagem para o Streamlit mostrar toast
        const event = new CustomEvent('textoCopiado', {detail: {sucesso: true}});
        window.dispatchEvent(event);
    }).catch(err => {
        console.error('Erro ao copiar:', err);
    });
};

window.falarTextoGlobal = function(texto) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = texto;
    const textoLimpo = textarea.value;
    
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(textoLimpo);
    u.lang = 'pt-BR';
    u.rate = 1.0;
    const vozes = window.speechSynthesis.getVoices();
    const vozPt = vozes.find(v => v.lang.includes('pt'));
    if (vozPt) u.voice = vozPt;
    window.speechSynthesis.speak(u);
};
</script>
"""
st.markdown(JS_GLOBAL, unsafe_allow_html=True)

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

    st.divider()

    persona = st.selectbox(
        "🎭 Personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    st.divider()
    st.subheader("💬 Conversas")

    if st.button("➕ Nova Conversa", use_container_width=True):
        new_conv = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "title": f"Conversa {len(st.session_state.conversations) + 1}",
            "messages": [],
            "persona": persona
        }
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
                if st.button("️", key=f"del_{conv['id']}", use_container_width=True):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

    st.divider()
    st.caption("Feito com Streamlit + Groq 🚀")

# --- PROMPTS ---
prompts = {
    "Assistente Padrão": "Você é um assistente útil, direto e fala português brasileiro.",
    "Professor Didático": "Você é um professor paciente e didático. Explica conceitos complexos de forma simples, usa analogias. Fala português brasileiro.",
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
    st.caption(f"🎭 {current_conv.get('persona', persona)} •  {len(st.session_state.messages)} mensagens")
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
                <button class="btn-acao" onclick="window.parent.falarTextoGlobal('{texto_escape}')">🔊 Ouvir</button>
                """
                components.html(html_ouvir, height=40, width=110, scrolling=False)

            # === BOTÃO COPIAR ===
            with col_btn2:
                texto_escape = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                html_copiar = f"""
                <button class="btn-acao" onclick="window.parent.copiarTextoGlobal('{texto_escape}')">📋 Copiar</button>
                """
                components.html(html_copiar, height=40, width=110, scrolling=False)

# --- BUSCA WEB ---
def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception:
        return "Erro ao buscar na web."

# --- INPUT ---
if prompt := st.chat_input("Digite sua mensagem..."):
    if not st.session_state.current_conv_id:
        new_conv = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "title": prompt[:30] + "..." if len(prompt) > 30 else prompt,
            "messages": [],
            "persona": persona
        }
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.session_state.messages = []
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": prompt})
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 0:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

    with st.chat_message("user"):
        st.markdown(prompt)

    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado", "últimas", "quanto está", "cotação"]
    precisa_buscar = any(palavra in prompt.lower() for palavra in palavras_chave)

    mensagem_para_ia = prompt
    if precisa_buscar:
        with st.status(" Buscando informações atualizadas na web...", expanded=True) as status:
            contexto = pesquisar_na_web(prompt)
            st.write("Dados encontrados!")
            status.update(label="✅ Busca concluída!", state="complete", expanded=False)
            mensagem_para_ia = f"Use este contexto da web para responder:\n{contexto}\n\nPergunta: {prompt}"

    with st.chat_message("assistant"):
        with st.spinner("🤔 Pensando..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            mensagens_envio = [{"role": "system", "content": system_prompt}] + st.session_state.messages[:-1] + [{"role": "user", "content": mensagem_para_ia}]
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=mensagens_envio,
                temperature=0.7,
                max_tokens=1024
            )
            resposta = response.choices[0].message.content
            st.markdown(resposta)
            st.markdown("<script>setTimeout(() => window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'}), 300);</script>", unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
    if current_conv:
        current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
