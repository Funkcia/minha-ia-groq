import os
import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import html

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS COMPLETO PARA TEMAS ---
CSS_TEMA = """
<style>
/* TEMA CLARO */
body.claro .stApp {
    background-color: #ffffff;
    color: #262730;
}
body.claro .stSidebar {
    background-color: #f0f2f6;
}
body.claro .stChatMessage {
    background-color: #f8f9fa;
}
body.claro .stTextInput > div > div > input {
    background-color: #ffffff;
    color: #262730;
}

/* TEMA ESCURO */
body.escuro .stApp {
    background-color: #0e1117 !important;
    color: #fafafa !important;
}
body.escuro .stSidebar {
    background-color: #161b22 !important;
}
body.escuro .stSidebar .stMarkdown {
    color: #fafafa !important;
}
body.escuro .stSidebar h1, 
body.escuro .stSidebar h2, 
body.escuro .stSidebar h3,
body.escuro .stSidebar p,
body.escuro .stSidebar label,
body.escuro .stSidebar span {
    color: #fafafa !important;
}
body.escuro .stChatMessage {
    background-color: #1c2128 !important;
    border: 1px solid #30363d !important;
}
body.escuro .stChatMessage .stMarkdown {
    color: #fafafa !important;
}
body.escuro .stChatMessage .stMarkdown p {
    color: #fafafa !important;
}
body.escuro .stTextInput > div > div > input {
    background-color: #21262d !important;
    color: #fafafa !important;
    border: 1px solid #30363d !important;
}
body.escuro .stSelectbox > div > div > div {
    background-color: #21262d !important;
    color: #fafafa !important;
}
body.escuro .stButton > button {
    color: #fafafa !important;
}
body.escuro .stButton > button[kind="secondary"] {
    background-color: #21262d !important;
    border: 1px solid #30363d !important;
}
body.escuro .stButton > button[kind="primary"] {
    background-color: #ff4b4b !important;
}
body.escuro hr {
    border-color: #30363d !important;
}
body.escuro .stCaption {
    color: #8b949e !important;
}
body.escuro .stAlert {
    background-color: #1c2128 !important;
    color: #fafafa !important;
}
body.escuro .stStatusWidget {
    background-color: #1c2128 !important;
}
body.escuro .stStatusWidget .stMarkdown {
    color: #fafafa !important;
}

/* Botões de ação */
.btn-acao {
    background: transparent;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.btn-acao:hover {
    background-color: #f3f4f6;
    transform: translateY(-1px);
}
body.escuro .btn-acao {
    border-color: #30363d;
    color: #fafafa;
}
body.escuro .btn-acao:hover {
    background-color: #21262d;
}
</style>
"""

# Aplicar tema
st.markdown(f'<body class="{st.session_state.tema}"></body>', unsafe_allow_html=True)
st.markdown(CSS_TEMA, unsafe_allow_html=True)

# --- JAVASCRIPT PARA TTS E COPIAR ---
JS_FUNCIONALIDADES = """
<script>
// Carregar vozes
let vozesCarregadas = false;
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = function() {
        vozesCarregadas = true;
    };
}

function ouvirTexto(texto) {
    // Decodificar HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = texto;
    const textoLimpo = textarea.value;
    
    // Parar qualquer fala anterior
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(textoLimpo);
    utterance.lang = 'pt-BR';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    // Aguardar vozes carregarem
    const tentarFalar = () => {
        const vozes = window.speechSynthesis.getVoices();
        const vozPt = vozes.find(v => v.lang.startsWith('pt'));
        if (vozPt) {
            utterance.voice = vozPt;
            window.speechSynthesis.speak(utterance);
        } else {
            // Fallback: tentar qualquer voz
            window.speechSynthesis.speak(utterance);
        }
    };
    
    if (vozesCarregadas || window.speechSynthesis.getVoices().length > 0) {
        tentarFalar();
    } else {
        // Aguardar carregamento
        setTimeout(tentarFalar, 500);
    }
}

function copiarTexto(texto, btnId) {
    // Decodificar HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = texto;
    const textoLimpo = textarea.value;
    
    navigator.clipboard.writeText(textoLimpo).then(() => {
        const btn = document.getElementById(btnId);
        if (btn) {
            const original = btn.innerHTML;
            btn.innerHTML = '✓ Copiado!';
            setTimeout(() => { btn.innerHTML = original; }, 1500);
        }
    }).catch(err => {
        console.error('Erro ao copiar:', err);
    });
}
</script>
"""
st.markdown(JS_FUNCIONALIDADES, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Toggle de Tema
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Claro", use_container_width=True, 
                     type="primary" if st.session_state.tema == "claro" else "secondary"):
            if st.session_state.tema != "claro":
                st.session_state.tema = "claro"
                st.rerun()
    with col2:
        if st.button(" Escuro", use_container_width=True,
                     type="primary" if st.session_state.tema == "escuro" else "secondary"):
            if st.session_state.tema != "escuro":
                st.session_state.tema = "escuro"
                st.rerun()

    st.markdown("---")

    # Seleção de Persona
    persona = st.selectbox(
        "🎭 Personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    st.markdown("---")
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
                if st.button(f"{ativo}{conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                    st.session_state.current_conv_id = conv["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

    st.markdown("---")
    st.caption("Feito com Streamlit + Groq 🚀")

# --- PROMPTS DAS PERSONAS ---
prompts = {
    "Assistente Padrão": "Você é um assistente útil, direto e fala português brasileiro. Use o contexto da web quando fornecido.",
    "Professor Didático": "Você é um professor paciente e didático. Explica conceitos complexos de forma simples, usa analogias e exemplos do dia a dia. Fala português brasileiro.",
    "Programador Sênior": "Você é um engenheiro de software sênior. Foca em código limpo, boas práticas e explica a lógica por trás das soluções. Fala português brasileiro.",
    "Amigo Informal": "Você é um amigo próximo e descontraído. Usa gírias leves, é empático e animado. Fala português brasileiro."
}

# --- CARREGAR CONVERSA ATUAL ---
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

# --- TÍTULO DO CHAT ---
if st.session_state.current_conv_id and current_conv:
    st.title(f"💬 {current_conv['title']}")
    st.caption(f" {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title("🤖 Minha IA Pessoal")
    st.info("👈 Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Botões apenas nas respostas da IA
        if message["role"] == "assistant":
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            
            # Preparar texto para JavaScript (escape HTML)
            texto_html = html.escape(message["content"])
            
            # Botão Ouvir
            with col_btn1:
                st.markdown(
                    f'<button class="btn-acao" onclick="ouvirTexto(\'{texto_html}\')">🔊 Ouvir</button>',
                    unsafe_allow_html=True
                )
            
            # Botão Copiar
            with col_btn2:
                btn_id = f"copiar_{idx}"
                st.markdown(
                    f'<button class="btn-acao" id="{btn_id}" onclick="copiarTexto(\'{texto_html}\', \'{btn_id}\')">📋 Copiar</button>',
                    unsafe_allow_html=True
                )

# --- FUNÇÃO DE BUSCA NA WEB ---
def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception:
        return "Erro ao buscar na web."

# --- INPUT DO USUÁRIO ---
if prompt := st.chat_input("Digite sua mensagem..."):
    # Criar conversa se não existir
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

    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Atualizar título se for primeira mensagem
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 0:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

    # Mostrar mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # Verificar busca na web
    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado", "últimas", "quanto está", "cotação"]
    precisa_buscar = any(palavra in prompt.lower() for palavra in palavras_chave)

    mensagem_para_ia = prompt
    if precisa_buscar:
        with st.status("🔍 Buscando informações atualizadas na web...", expanded=True) as status:
            contexto = pesquisar_na_web(prompt)
            st.write("Dados encontrados!")
            status.update(label="✅ Busca concluída!", state="complete", expanded=False)
            mensagem_para_ia = f"Use este contexto da web para responder:\n{contexto}\n\nPergunta: {prompt}"

    # Gerar resposta
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

            # Auto-scroll
            st.markdown("<script>setTimeout(() => window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'}), 300);</script>", unsafe_allow_html=True)

    # Salvar resposta
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    if current_conv:
        current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
