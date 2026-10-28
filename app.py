import os
import streamlit as st
from groq import Groq
from ddgs import DDGS

# Configuração da página
st.set_page_config(page_title="Minha IA", page_icon="🤖")
st.title("🤖 Minha IA Pessoal")

# Inicializa o histórico de chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Você é um assistente útil, direto e fala português brasileiro. Use o contexto da web quando fornecido."}
    ]

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

# Mostra o histórico na tela
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Campo de digitação
if prompt := st.chat_input("Digite sua mensagem..."):
    # Mostra a mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Verifica se precisa buscar na web
    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado"]
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
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages[:-1] + [{"role": "user", "content": mensagem_para_ia}],
                temperature=0.7,
                max_tokens=1024
            )
            resposta = response.choices[0].message.content
            st.markdown(resposta)
            
    st.session_state.messages.append({"role": "assistant", "content": resposta})