import os
import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- CSS PERSONALIZADO (Temas) ---
CSS_TEMA = """
<style>
/* Tema Claro (padrão) */
body.light {
    background-color: #ffffff;
    color: #31333F;
}

/* Tema Escuro */
body.dark, .stApp.dark {
    background-color: #0E1117;
    color: #FAFAFA;
}

/* Botão de ouvir */
.btn-ouvir {
    background: none;
    border: 1px solid #ccc;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-left: 8px;
    transition: all 0.2s;
}
.btn-ouvir:hover {
    background-color: #f0f0f0;
    transform: scale(1.1);
}

/* Botão copiar */
.btn-copiar {
    background: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 2px 8px;
    cursor: pointer;
    font-size: 12px;
    margin-left: 8px;
}
.btn-copiar:hover {
    background-color: #f0f0f0;
}

/* Ajustes para tema escuro */
.dark .btn-ouvir, .dark .btn-copiar {
    border-color: #555;
    color: #fff;
}
.dark .btn-ouvir:hover, .dark .btn-copiar:hover {
    background-color: #333;
}

/* Esconder barra de rolagem feia */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}
</style>
"""

# --- JAVASCRIPT PARA TTS E COPIAR ---
JS_FUNCIONALIDADES = """
<script>
function ouvirTexto(texto) {
    // Para qualquer fala anterior
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = 'pt-BR';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    // Tenta usar voz em português
    const vozes = window.speechSynthesis.getVoices();
    const vozPt = vozes.find(v => v.lang.startsWith('pt'));
    if (vozPt) utterance.voice = vozPt;
    
    window.speechSynthesis.speak(utterance);
}

function pararFala() {
    window.speechSynthesis.cancel();
}

function copiarTexto(texto, btnId) {
    navigator.clipboard.writeText(texto).then(() => {
        const btn = document.getElementById(btnId);
        if (btn) {
            const original = btn.innerText;
            btn.innerText = '✓ Copiado!';
            setTimeout(() => { btn.innerText = original; }, 1500);
        }
    });
}

function rolarParaBaixo() {
    setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }, 200);
}
</script>
"""

# Injetar CSS e JS
st.markdown(CSS_TEMA, unsafe_allow_html=True)
st.markdown(JS_FUNCIONALIDADES, unsafe_allow_html=True)

# --- ESTADO INICIAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "claro"

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Toggle de Tema
    tema_atual = st.session_state.tema
    novo_tema = st.radio(
        "🎨 Tema:",
        ["️ Claro", "🌙 Escuro"],
        index=0 if tema_atual == "claro" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    if "Escuro" in novo_tema and tema_atual != "escuro":
        st.session_state.tema = "escuro"
        st.rerun()
    elif "Claro" in novo_tema and tema_atual != "claro":
        st.session_state.tema = "claro"
        st.rerun()

    # Aplicar tema via CSS
    if st.session_state.tema == "escuro":
        st.markdown('<body class="dark"></body>', unsafe_allow_html=True)
    else:
        st.markdown('<body class="light"></body>', unsafe_allow_html=True)

    st.markdown("---")

    # Seleção de Persona
    persona = st.selectbox(
        "🎭 Personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    st.markdown("---")
    st.subheader(" Conversas")

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
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title("🤖 Minha IA Pessoal")
    st.info("👈 Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

# --- EXIBIR HISTÓRICO ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Adicionar botões apenas nas respostas da IA
        if message["role"] == "assistant":
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                btn_id_ouvir = f"ouvir_{idx}"
                st.markdown(
                    f'<button class="btn-ouvir" onclick="ouvirTexto(this.parentElement.parentElement.querySelector(\'div[data-testid="stMarkdownContainer"]\').innerText)" id="{btn_id_ouvir}"> Ouvir</button>',
                    unsafe_allow_html=True
                )
            with col_btn2:
                btn_id_copiar = f"copiar_{idx}"
                # Escapa aspas para o JavaScript
                texto_escape = message["content"].replace('"', '\\"').replace('\n', '\\n')
                st.markdown(
                    f'<button class="btn-copiar" onclick="copiarTexto(\\"{texto_escape}\\", \\"{btn_id_copiar}\\")" id="{btn_id_copiar}">📋 Copiar</button>',
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

            # Auto-scroll suave
            st.markdown("<script>setTimeout(() => window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'}), 300);</script>", unsafe_allow_html=True)

    # Salvar resposta
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    if current_conv:
        current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
