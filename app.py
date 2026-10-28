import os
import streamlit as st
from groq import Groq
from ddgs import DDGS

# Configuração da página
st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

# --- SIDEBAR (Configurações) ---
with st.sidebar:
    st.title("️ Configurações")

    # Seleção de Persona
    persona = st.selectbox(
        "Escolha a personalidade da IA:",
        ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"]
    )

    # Botão de limpar histórico
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
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

system_prompt = prompts[persona]

# Inicializa o histórico de chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra o histórico na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Função de busca na web
def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception:
        return "Erro ao buscar na web."

# Campo de digitação
if prompt := st.chat_input("Digite sua mensagem..."):
    # Mostra a mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Verifica se precisa buscar na web
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

    # Gera a resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Usando st.secrets (a forma nativa e segura do Streamlit)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Monta a lista de mensagens enviando o system prompt correto da persona
            mensagens_envio = [{"role": "system", "content": system_prompt}] + st.session_state.messages[:-1] + [{"role": "user", "content": mensagem_para_ia}]

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=mensagens_envio,
                temperature=0.7,
                max_tokens=1024
            )
            resposta = response.choices[0].message.content
            st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
