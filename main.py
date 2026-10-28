import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS  # <-- MUDANÇA AQUI (era duckduckgo_search)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def pesquisar_na_web(consulta):
    """Busca informações atualizadas na internet"""
    try:
        with DDGS() as ddgs:
            # Pega os 3 melhores resultados
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados:
                contexto = "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
                return contexto
            return "Nenhuma informação recente encontrada na web."
    except Exception as e:
        return f"Erro ao buscar na web: {e}"

def conversar(mensagem, historico):
    palavras_chave_busca = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado"]
    precisa_buscar = any(palavra in mensagem.lower() for palavra in palavras_chave_busca)
    
    mensagem_final = mensagem
    if precisa_buscar:
        print("🔍 Buscando informações atualizadas na web...")
        contexto_web = pesquisar_na_web(mensagem)
        mensagem_final = f"""
        Use as seguintes informações recentes da internet para responder à pergunta do usuário. 
        Se a informação não estiver no contexto, diga que não encontrou dados confiáveis.
        
        CONTEXTO DA WEB:
        {contexto_web}
        
        PERGUNTA DO USUÁRIO: {mensagem}
        """

    historico.append({"role": "user", "content": mensagem_final})

    resposta = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=historico,
        temperature=0.7,
        max_tokens=1024
    )

    texto = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": texto})
    return texto

if __name__ == "__main__":
    data_atual = datetime.now().strftime("%d/%m/%Y")
    print(f"🤖 IA pronta! (Data de referência: {data_atual})")
    print("Digite 'sair' para encerrar.\n")
    
    historico = [
        {"role": "system", "content": f"Você é um assistente útil, direto e fala português brasileiro. A data atual é {data_atual}. Baseie suas respostas em fatos e, quando fornecido, use o contexto da web."}
    ]

    while True:
        msg = input("Você: ").strip()
        if msg.lower() == "sair":
            break
        if not msg:
            continue
            
        print(f"\nIA: {conversar(msg, historico)}\n")