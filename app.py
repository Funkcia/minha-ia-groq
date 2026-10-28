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
if "ultimo_copiado" not in st.session_state:
    st.session_state.ultimo_copiado = None

# --- CSS MÍNIMO E CIRÚRGICO (sem quebrar nada) ---
CSS_TEMA = """
<style>
/* Apenas ajustes pontuais - não sobrescrever tudo */

/* Tema Escuro */
body.escuro .stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}
body.escuro .stSidebar {
    background-color: #1A1D21;
}
body.escuro .stSidebar .stMarkdown h1,
body.escuro .stSidebar .stMarkdown h2,
body.escuro .stSidebar .stMarkdown h3,
body.escuro .stSidebar .stMarkdown p,
body.escuro .stSidebar .stMarkdown label,
body.escuro .stSidebar .stMarkdown span,
body.escuro .stSidebar .stMarkdown div {
    color: #FAFAFA !important;
}
body.escuro .stSelectbox label,
body.escuro .stSelectbox [data-baseweb="select"] {
    color: #FAFAFA !important;
}
body.escuro .stChatMessage {
    background-color: #1C2128;
    border: 1px solid #30363D;
}
body.escuro .stChatMessage .stMarkdown,
body.escuro .stChatMessage .stMarkdown p,
body.escuro .stChatMessage .stMarkdown li,
body.escuro .stChatMessage .stMarkdown strong {
    color: #FAFAFA !important;
}
body.escuro .stChatInput textarea {
    color: #FAFAFA !important;
    caret-color: #FAFAFA !important;
}
body.escuro .stChatInput textarea::placeholder {
    color: #8B949E !important;
}
body.escuro hr {
    border-color: #30363D !important;
}
body.escuro .stCaption {
    color: #8B949E !important;
}
body.escuro .stAlert {
    background-color: #1C2128;
    color: #FAFAFA;
    border: 1px solid #30363D;
}
body.escuro .stStatusWidget {
    background-color: #1C2128;
    color: #FAFAFA;
}
body.escuro .stStatusWidget .stMarkdown {
    color: #FAFAFA !important;
}

/* Tema Claro */
body.claro .stApp {
    background-color: #FFFFFF;
    color: #262730;
}
body.claro .stChatInput textarea {
    color: #262730 !important;
    caret-color: #262730 !important;
}
body.claro .stChatInput textarea::placeholder {
    color: #808495 !important;
}

/* Botões de ação (Ouvir/Copiar) */
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
}
.btn-acao:hover {
    background-color: #F3F4F6;
    border-color: #AFB1B8;
}
body.escuro .btn-acao {
    border-color: #30363D;
    color: #C9D1D9;
}
body.escuro .btn-acao:hover {
    background-color: #21262D;
    border-color: #8B949E;
}
</style>
"""

st.markdown(f'<body class="{st.session_state.tema}"></body>', unsafe_allow_html=True)
st.markdown(CSS_TEMA, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Toggle de Tema (botões nativos)
    col1, col2 = st.columns(2)
    with col1:
        tema_claro = st.session_state.tema == "claro"
        if st.button("☀️ Claro", use_container_width=True, type="primary" if tema_claro else "secondary"):
            if not tema_claro:
                st.session_state.tema = "claro"
                st.rerun()
    with col2:
        tema_escuro = st.session_state.tema == "escuro"
        if st.button("🌙 Escuro", use_container_width=True, type="primary" if tema_escuro else "secondary"):
            if not tema_escuro:
                st.session_state.tema = "escuro"
                st.rerun()

    st.divider()

    # Seleção de Persona
    persona = st.selectbox(
        " Personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    st.divider()
    st.subheader("💬 Conversas")

    # Botão Nova Conversa
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

    # Listar conversas
    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            col1, col2 = st.columns([4, 1])
            with col1:
                ativo = "✅ " if conv["id"] == st.session_state.current_conv_id else ""
                label = f"{ativo}{conv['title']}"
                if st.button(label, key=f"load_{conv['id']}", use_container_width=True):
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
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title(" Minha IA Pessoal")
    st.info(" Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Botões apenas nas respostas da IA
        if message["role"] == "assistant":
            st.divider()
            col_btn1, col_btn2 = st.columns(2)

            # Botão Ouvir (HTML isolado, altura correta)
            with col_btn1:
                texto_limpo = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                html_ouvir = f"""
                <button class="btn-acao" onclick="falarTexto('{texto_limpo}')">🔊 Ouvir</button>
                <script>
                function falarTexto(t) {{
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance(t);
                    u.lang = 'pt-BR';
                    u.rate = 1.0;
                    const vozes = window.speechSynthesis.getVoices();
                    const vozPt = vozes.find(v => v.lang.includes('pt'));
                    if (vozPt) u.voice = vozPt;
                    window.speechSynthesis.speak(u);
                }}
                if (!window._vozesCarregadas) {{
                    speechSynthesis.onvoiceschanged = () => {{ window._vozesCarregadas = true; }};
                }}
                </script>
                """
                components.html(html_ouvir, height=40, width=120, scrolling=False)

            # Botão Copiar (NATIVO do Streamlit - sem HTML quebrado)
            with col_btn2:
                btn_id = f"copiar_{idx}"
                copiado = st.session_state.ultimo_copiado == btn_id
                label = "✅ Copiado!" if copiado else "📋 Copiar"
                tipo = "primary" if copiado else "secondary"
                if st.button(label, key=btn_id, use_container_width=True, type=tipo):
                    st.session_state.ultimo_copiado = btn_id
                    # Guarda o texto para copiar via JS
                    st.session_state[f"_texto_{btn_id}"] = message["content"]
                    st.rerun()

# --- JavaScript global para copiar (quando o botão nativo for clicado) ---
if st.session_state.ultimo_copiado:
    btn_id = st.session_state.ultimo_copiado
    texto = st.session_state.get(f"_texto_{btn_id}", "")
    texto_js = texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    js_copiar = f"""
    <script>
    navigator.clipboard.writeText('{texto_js}').then(() => {{
        console.log('Copiado com sucesso');
    }}).catch(err => {{
        console.error('Erro ao copiar:', err);
    }});
    </script>
    """
    components.html(js_copiar, height=0, width=0, scrolling=False)

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
        with st.status("🔍 Buscando informações atualizadas na web...", expanded=True) as status:
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
