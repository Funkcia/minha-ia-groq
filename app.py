import os
import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- SIDEBAR (Configurações e Histórico) ---
with st.sidebar:
    st.title("⚙️ Configurações")

    # Seleção de Persona
    persona = st.selectbox(
        "🎭 Personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    st.markdown("---")
    st.subheader(" Conversas")

    # Inicializar lista de conversas
    if "conversations" not in st.session_state:
        st.session_state.conversations = []

    if "current_conv_id" not in st.session_state:
        st.session_state.current_conv_id = None

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

    # Listar conversas existentes
    if st.session_state.conversations:
        st.markdown("**Histórico:**")
        for conv in st.session_state.conversations:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                    st.session_state.current_conv_id = conv["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()

    st.markdown("---")
    st.caption("Feito com Streamlit + Groq")

# --- DEFINIÇÃO DOS PROMPTS ---
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

# --- EXIBIR CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- FUNÇÃO DE BUSCA ---
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
    # Se não há conversa ativa, criar uma nova
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

    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Atualizar título da conversa se for a primeira mensagem
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 0:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

    # Mostrar mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # Verificar se precisa buscar na web
    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado", "últimas"]
    precisa_buscar = any(palavra in prompt.lower() for palavra in palavras_chave)

    mensagem_para_ia = prompt
    if precisa_buscar:
        with st.status("🔍 Buscando informações atualizadas na web...", expanded=True) as status:
            contexto = pesquisar_na_web(prompt)
            st.write("Dados encontrados!")
            status.update(label="Busca concluída!", state="complete", expanded=False)

            mensagem_para_ia = f"""
            Use este contexto da web para responder:
            {contexto}
            Pergunta: {prompt}
            """

    # Gerar resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
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

            # Auto-scroll via JavaScript
            st.markdown("""
            <script>
            setTimeout(function() {
                window.scrollTo(0, document.body.scrollHeight);
            }, 100);
            </script>
            """, unsafe_allow_html=True)

    # Salvar resposta no histórico
    st.session_state.messages.append({"role": "assistant", "content": resposta})

    # Atualizar conversa no session_state
    if current_conv:
        current_conv["messages"] = st.session_state.messages.copy()
