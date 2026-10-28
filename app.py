import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import json

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS CORRIGIDO (Foco no Input e Contraste) ---
CSS_ESTILO = """
<style>
/* TEMA ESCURO */
body.escuro .stApp { background-color: #0e1117 !important; }
body.escuro .stSidebar { background-color: #161b22 !important; }
body.escuro .stSidebar * { color: #fafafa !important; }

/* CORREÇÃO DO TEXTO DIGITADO (O que estava invisível) */
body.escuro .stChatInput textarea,
body.escuro div[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    caret-color: #ffffff !important; /* Cursor branco */
    background-color: #21262d !important;
}

/* Mensagens do Chat */
body.escuro .stChatMessage {
    background-color: #1c2128 !important;
    border: 1px solid #30363d !important;
}
body.escuro .stChatMessage .stMarkdown,
body.escuro .stChatMessage .stMarkdown p,
body.escuro .stChatMessage .stMarkdown li {
    color: #fafafa !important;
}

/* Botões e Inputs Gerais */
body.escuro .stSelectbox > div > div > div { background-color: #21262d !important; color: #fafafa !important; }
body.escuro .stButton > button { color: #fafafa !important; border: 1px solid #30363d !important; }
body.escuro hr { border-color: #30363d !important; }

/* Botões de Ação (Ouvir/Copiar) */
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
    color: #24292f;
}
body.escuro .btn-acao {
    border-color: #30363d;
    color: #fafafa;
}
.btn-acao:hover { background-color: #f3f4f6; }
body.escuro .btn-acao:hover { background-color: #30363d; }
</style>
"""

# Aplica o tema
st.markdown(f'<body class="{st.session_state.tema}"></body>', unsafe_allow_html=True)
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# --- JAVASCRIPT (Corrigido para não travar) ---
JS_FUNCIONALIDADES = """
<script>
// Carregar vozes do navegador
window.speechSynthesis.getVoices();

function falarTexto(texto) {
    window.speechSynthesis.cancel();
    
    // Limpa formatação markdown básica para a fala ficar natural
    const textoLimpo = texto.replace(/\\*\\*/g, '').replace(/\\*/g, '').replace(/`/g, '').replace(/#/g, '');
    
    const utterance = new SpeechSynthesisUtterance(textoLimpo);
    utterance.lang = 'pt-BR';
    utterance.rate = 1.0;
    
    const vozes = window.speechSynthesis.getVoices();
    const vozPt = vozes.find(v => v.lang.includes('pt-BR') || v.lang.includes('pt'));
    if (vozPt) utterance.voice = vozPt;
    
    window.speechSynthesis.speak(utterance);
}

function copiarTexto(texto, btnId) {
    const textoLimpo = texto.replace(/\\*\\*/g, '').replace(/\\*/g, '').replace(/`/g, '').replace(/#/g, '');
    
    navigator.clipboard.writeText(textoLimpo).then(() => {
        const btn = document.getElementById(btnId);
        if (btn) {
            const original = btn.innerHTML;
            btn.innerHTML = '✓ Copiado!';
            setTimeout(() => { btn.innerHTML = original; }, 1500);
        }
    });
}
</script>
"""
st.markdown(JS_FUNCIONALIDADES, unsafe_allow_html=True)

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
    st.title(f" {current_conv['title']}")
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title(" Minha IA Pessoal")
    st.info("👈 Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant":
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            
            # A MÁGICA: json.dumps transforma o texto em uma string JavaScript segura
            # Isso impede que aspas ou quebras de linha quebrem o botão
            texto_seguro_js = json.dumps(message["content"])
            
            with col_btn1:
                st.markdown(f'<button class="btn-acao" onclick="falarTexto({texto_seguro_js})">🔊 Ouvir</button>', unsafe_allow_html=True)
            with col_btn2:
                btn_id = f"copiar_{idx}"
                st.markdown(f'<button class="btn-acao" id="{btn_id}" onclick="copiarTexto({texto_seguro_js}, \'{btn_id}\')">📋 Copiar</button>', unsafe_allow_html=True)

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
