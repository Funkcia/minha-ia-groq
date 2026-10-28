import os
import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- CSS PARA TEMA ESCURO ---
if st.session_state.tema == "escuro":
    st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stSidebar {
        background-color: #161B22;
    }
    .stTextInput > div > div > input {
        background-color: #21262D;
        color: #FAFAFA;
    }
    .stChatMessage {
        background-color: #161B22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- JAVASCRIPT PARA TTS E COPIAR ---
st.markdown("""
<script>
function ouvirTexto(texto) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = 'pt-BR';
    utterance.rate = 1.0;
    const vozes = window.speechSynthesis.getVoices();
    const vozPt = vozes.find(v => v.lang.startsWith('pt'));
    if (vozPt) utterance.voice = vozPt;
    window.speechSynthesis.speak(utterance);
}

function copiarTexto(texto, btnId) {
    navigator.clipboard.writeText(texto).then(() => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.innerText = '✓ Copiado!';
            setTimeout(() => { btn.innerText = '📋 Copiar'; }, 1500);
        }
    });
}
</script>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Toggle de Tema
    tema_atual = st.session_state.tema
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Claro", use_container_width=True, type="primary" if tema_atual == "claro" else "secondary"):
            if tema_atual != "claro":
                st.session_state.tema = "claro"
                st.rerun()
    with col2:
        if st.button("🌙 Escuro", use_container_width=True, type="primary" if tema_atual == "escuro" else "secondary"):
            if tema_atual != "escuro":
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
    st.info(" Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Botões apenas nas respostas da IA
        if message["role"] == "assistant":
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            
            # Botão Ouvir
            with col_btn1:
                texto_limpo = message["content"].replace("'", "\\'").replace('"', '\\"')
                st.markdown(
                    f'<button onclick="ouvirTexto(\'{texto_limpo}\')" style="background:none;border:1px solid #ccc;border-radius:4px;padding:4px 12px;cursor:pointer;">🔊 Ouvir</button>',
                    unsafe_allow_html=True
                )
            
            # Botão Copiar
            with col_btn2:
                btn_id = f"copiar_{idx}"
                texto_escape = message["content"].replace('"', '\\"').replace('\n', '\\n').replace("'", "\\'")
                st.markdown(
                    f'<button id="{btn_id}" onclick="copiarTexto(\'{texto_escape}\', \'{btn_id}\')" style="background:none;border:1px solid #ccc;border-radius:4px;padding:4px 12px;cursor:pointer;">📋 Copiar</button>',
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
