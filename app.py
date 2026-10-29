import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import streamlit.components.v1 as components
import base64
import io
from pypdf import PdfReader
import google.generativeai as genai

st.set_page_config(page_title="Minha IA Pessoal", page_icon="🤖", layout="wide")

for chave, valor in [("conversations", []), ("current_conv_id", None), ("documento", None),
                     ("imagem", None), ("erro_gemini", None), ("status_visao", None)]:
    if chave not in st.session_state:
        st.session_state[chave] = valor

# --- VISÃO AO VIVO (SEM CACHE: reflete a chave na hora) ---
def visao_config():
    if st.secrets.get("GEMINI_API_KEY"):
        return "gemini", None
    try:
        c = Groq(api_key=st.secrets["GROQ_API_KEY"])
        ids = [m.id for m in c.models.list()]
        for p in ["vision", "scout", "maverick"]:
            for mid in ids:
                if p in mid:
                    return mid, None
    except Exception as e:
        return None, f"Groq indisponível: {e}"
    return None, "Sem chave Gemini e sem modelo de visão no Groq"

def chamar_gemini(imagem_bytes, prompt_final):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    from PIL import Image
    # 1) Normaliza a imagem: remove alpha e limita o tamanho -> menos tokens, mais rápido
    img_pil = Image.open(io.BytesIO(imagem_bytes))
    if img_pil.mode in ("RGBA", "LA", "P"):
        img_pil = img_pil.convert("RGB")
    if max(img_pil.size) > 1024:
        img_pil.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    img_final = Image.open(buf)

    cfg = genai.types.GenerationConfig(max_output_tokens=400, temperature=0.4)
    ultimo = None
    # 2) Timeout CURTO (25s): se um modelo travar, pula pro próximo sem esperar o século
    # 3) Ordem: os mais estáveis primeiro, o "latest" (que deu 504) por último
    for nome in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
        try:
            mg = genai.GenerativeModel(nome, generation_config=cfg)
            r = mg.generate_content([prompt_final, img_final], request_options={"timeout": 25})
            try:
                txt = r.text
            except Exception:
                txt = ""
            if txt and txt.strip():
                return txt, None
            ultimo = f"[{nome}] vazio/bloqueado"
        except Exception as e:
            ultimo = f"[{nome}] {e}"
    return None, ultimo

st.markdown("""
<style>
.btn-neutro { background: transparent; border: 1px solid #8b949e; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 14px; width: 100%; color: #8b949e; }
.btn-neutro:hover { border-color: #b1bac4; color: #b1bac4; }
.stChatMessage { border-radius: 12px; }
.stApp:has(input[type="checkbox"]:checked) { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) * { color: #262730 !important; }
body:has(input[type="checkbox"]:checked) { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) .stSidebar, .stApp:has(input[type="checkbox"]:checked) .stSidebar > div { background-color: #f6f8fa !important; }
.stApp:has(input[type="checkbox"]:checked) .stChatMessage { background-color: #f6f8fa !important; border: 1px solid #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) .stChatInput textarea, .stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] textarea { background-color: #ffffff !important; caret-color: #262730 !important; }
.stApp:has(input[type="checkbox"]:checked) .stChatInput textarea::placeholder, .stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] textarea::placeholder { color: #808495 !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInputContainer"], .stApp:has(input[type="checkbox"]:checked) .stChatInputContainer, .stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"], .stApp:has(input[type="checkbox"]:checked) .stChatInput, .stApp:has(input[type="checkbox"]:checked) [data-testid="stChatInput"] div, .stApp:has(input[type="checkbox"]:checked) .stChatInput div, .stApp:has(input[type="checkbox"]:checked) [data-testid="stBottom"], .stApp:has(input[type="checkbox"]:checked) [data-testid="stBottomBlockContainer"] { background-color: #ffffff !important; border-color: #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) .stButton > button { background-color: #ffffff !important; border: 1px solid #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) .stButton > button:hover { background-color: #f0f2f6 !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stSelectbox"] div, .stApp:has(input[type="checkbox"]:checked) [data-testid="stSelectbox"] div div { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) hr { border-color: #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) .stCaption { color: #57606a !important; }
.stApp:has(input[type="checkbox"]:checked) .stTextInput > div > div > input { background-color: #ffffff !important; border: 1px solid #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stExpander"] details, .stApp:has(input[type="checkbox"]:checked) .streamlit-expanderHeader { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stAlert"], .stApp:has(input[type="checkbox"]:checked) .stAlert { background-color: #f6f8fa !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stStatusWidget"], .stApp:has(input[type="checkbox"]:checked) .stStatusWidget { background-color: #f6f8fa !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"], .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploadDropzone"], .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploadDropzone"] div, .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"] section, .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"] section div { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploadDropzone"] { border-color: #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"] button, .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploadDropzone"] button { background-color: #ffffff !important; border: 1px solid #d0d7de !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"] button, .stApp:has(input[type="checkbox"]:checked) [data-testid="stFileUploader"] button * { color: #262730 !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"], .stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"], .stApp:has(input[type="checkbox"]:checked) header { background-color: #ffffff !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"] button, .stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"] button { background-color: #0e1117 !important; border-radius: 8px !important; }
.stApp:has(input[type="checkbox"]:checked) [data-testid="stHeader"] button *, .stApp:has(input[type="checkbox"]:checked) [data-testid="stToolbar"] button * { color: #fafafa !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Configurações")
    st.checkbox("☀️ Modo claro", help="Desmarcado = tema escuro")
    st.divider()
    persona = st.selectbox("🎭 Personalidade da IA:", ["Assistente Padrão", "Professor Didático", "Programador Sênior", "Amigo Informal"])
    st.divider()
    st.subheader("💬 Conversas")
    if st.button("➕ Nova Conversa", use_container_width=True):
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": f"Conversa {len(st.session_state.conversations) + 1}", "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.rerun()
    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            ativo = "✅ " if conv["id"] == st.session_state.current_conv_id else ""
            if st.button(f"{ativo}{conv['title']}", key=f"load_{conv['id']}", use_container_width=True):
                st.session_state.current_conv_id = conv["id"]
                st.rerun()
            col_rename, col_delete = st.columns([1, 1])
            with col_rename:
                if st.button("✏️ Renomear", key=f"rename_{conv['id']}", use_container_width=True):
                    st.session_state[f"renaming_{conv['id']}"] = True
            with col_delete:
                if st.button("🗑️ Deletar", key=f"del_{conv['id']}", use_container_width=True):
                    st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != conv["id"]]
                    if st.session_state.current_conv_id == conv["id"]:
                        st.session_state.current_conv_id = None
                    st.rerun()
            if st.session_state.get(f"renaming_{conv['id']}", False):
                with st.expander("Renomear conversa", expanded=True):
                    new_name = st.text_input("Novo nome:", value=conv["title"], key=f"input_{conv['id']}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Salvar", key=f"save_{conv['id']}", use_container_width=True):
                            conv["title"] = new_name
                            st.session_state[f"renaming_{conv['id']}"] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_{conv['id']}", use_container_width=True):
                            st.session_state[f"renaming_{conv['id']}"] = False
                            st.rerun()
    st.divider()
    st.subheader("📎 Arquivos")
    tipo_v, mot_v = visao_config()
    if tipo_v == "gemini":
        st.caption("👁️ Visão: ✅ Gemini (chave ok)")
    elif tipo_v:
        st.caption(f"👁️ Visão: ✅ Groq ({tipo_v})")
    else:
        st.caption(f"👁️ Visão: ❌ {mot_v}")
    upload = st.file_uploader("PDF, TXT ou imagem", type=["pdf", "txt", "png", "jpg", "jpeg"], label_visibility="collapsed")
    if upload is not None:
        ext = upload.name.split(".")[-1].lower()
        if ext == "txt":
            st.session_state.documento = {"nome": upload.name, "texto": upload.getvalue().decode("utf-8", errors="ignore")}
            st.session_state.imagem = None
        elif ext == "pdf":
            try:
                reader = PdfReader(io.BytesIO(upload.getvalue()))
                texto_pdf = "\n".join([(p.extract_text() or "") for p in reader.pages])
                st.session_state.documento = {"nome": upload.name, "texto": texto_pdf}
                st.session_state.imagem = None
                st.success(f"📄 {len(reader.pages)} página(s) carregadas!")
            except Exception:
                st.error("Não consegui ler este PDF.")
        else:
            st.session_state.imagem = {"nome": upload.name, "base64": base64.b64encode(upload.getvalue()).decode(), "mime": upload.type, "bytes": upload.getvalue()}
            st.session_state.documento = None
    if st.session_state.documento:
        st.success(f"📄 Documento ativo: {st.session_state.documento['nome']}")
    if st.session_state.imagem:
        st.image(st.session_state.imagem["bytes"], width=180)
    if (st.session_state.documento or st.session_state.imagem) and st.button("🗑️ Remover arquivo", use_container_width=True):
        st.session_state.documento = None
        st.session_state.imagem = None
        st.session_state["erro_gemini"] = None
        st.session_state["status_visao"] = None
        st.rerun()
    st.divider()
    conv_atual = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if conv_atual and conv_atual.get("messages"):
        linhas = []
        for m in conv_atual["messages"]:
            quem = "👤 Você" if m["role"] == "user" else "🤖 IA"
            linhas.append(f"{quem}: {m['content']}")
        st.download_button("📥 Exportar conversa (TXT)", data="\n\n".join(linhas), file_name=f"conversa-{conv_atual['id']}.txt", mime="text/plain", use_container_width=True)
    st.divider()
    st.caption("Feito com Streamlit + Groq 🚀")

prompts = {
    "Assistente Padrão": "Você é um assistente útil, direto e fala português brasileiro.",
    "Professor Didático": "Você é um professor paciente e didático. Explica conceitos complexos de forma simples. Fala português brasileiro.",
    "Programador Sênior": "Você é um engenheiro de software sênior. Foca em código limpo e boas práticas. Fala português brasileiro.",
    "Amigo Informal": "Você é um amigo próximo e descontraído. Usa gírias leves, é empático. Fala português brasileiro."
}

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
system_prompt += " Detecte o idioma da mensagem do usuário e responda exatamente no mesmo idioma, a menos que ele peça outro idioma."

if st.session_state.get("erro_gemini"):
    st.error(f"❌ {st.session_state['erro_gemini']}")

if st.session_state.current_conv_id and current_conv:
    st.title(f"💬 {current_conv['title']}")
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title("🤖 Minha IA Pessoal")
    st.info("👈 Clique em **Nova Conversa** ou digite sua primeira mensagem abaixo!")

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.divider()
            col_btn1, col_btn2 = st.columns(2)
            texto_escape = message["content"].replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
            with col_btn1:
                components.html(f"""
                <style>body {{ margin: 0; padding: 0; background: transparent; }}</style>
                <button class="btn-neutro" onclick="falar()">🔊 Ouvir</button>
                <script>
                function falar() {{
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance('{texto_escape}');
                    u.lang = 'pt-BR';
                    const vozes = window.speechSynthesis.getVoices();
                    const vozPt = vozes.find(v => v.lang.includes('pt'));
                    if (vozPt) u.voice = vozPt;
                    window.speechSynthesis.speak(u);
                }}
                </script>
                """, height=50, width=130, scrolling=False)
            with col_btn2:
                components.html(f"""
                <style>body {{ margin: 0; padding: 0; background: transparent; }}</style>
                <button id="btn" class="btn-neutro" onclick="copiar()">📋 Copiar</button>
                <script>
                function copiar() {{
                    navigator.clipboard.writeText('{texto_escape}').then(() => {{
                        const btn = document.getElementById('btn');
                        btn.innerText = '✅ Copiado!';
                        setTimeout(() => {{ btn.innerText = '📋 Copiar'; }}, 1500);
                    }});
                }}
                </script>
                """, height=50, width=130, scrolling=False)

def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados: return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception: return "Erro ao buscar na web."

if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state["erro_gemini"] = None
    st.session_state["status_visao"] = None
    if not st.session_state.current_conv_id:
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": prompt[:30] + "..." if len(prompt) > 30 else prompt, "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.session_state.messages = []
        st.rerun()
    texto_exibido = prompt
    if st.session_state.imagem:
        texto_exibido += f"\n\n📷 *[imagem anexada: {st.session_state.imagem['nome']}]*"
    st.session_state.messages.append({"role": "user", "content": texto_exibido})
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 0:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
    with st.chat_message("user"): st.markdown(texto_exibido)

    palavras_chave = ["quem ganhou", "eleições", "hoje", "atual", "preço", "notícia", "2026", "2025", "resultado", "últimas", "quanto está", "cotação"]
    precisa_buscar = any(palavra in prompt.lower() for palavra in palavras_chave)
    mensagem_para_ia = prompt
    if precisa_buscar:
        with st.status("🔍 Buscando informações atualizadas na web...", expanded=True) as status:
            contexto = pesquisar_na_web(prompt)
            st.write("Dados encontrados!")
            status.update(label="✅ Busca concluída!", state="complete", expanded=False)
            mensagem_para_ia = f"Use este contexto da web para responder:\n{contexto}\n\nPergunta: {prompt}"
    if st.session_state.documento:
        doc = st.session_state.documento
        texto_doc = doc["texto"][:15000]
        mensagem_para_ia = f"Use o conteúdo do documento '{doc['nome']}' abaixo para responder:\n\n---INÍCIO DO DOCUMENTO---\n{texto_doc}\n---FIM DO DOCUMENTO---\n\nPergunta: {mensagem_para_ia}"

    modelo = "openai/gpt-oss-120b"
    conteudo_usuario = mensagem_para_ia
    resposta_especial = None
    pular_groq = False
    if st.session_state.imagem:
        tipo_v, _ = visao_config()
        if tipo_v == "gemini":
            st.session_state["status_visao"] = "👁️ Analisando imagem com Gemini..."
            txt, err = chamar_gemini(st.session_state.imagem["bytes"], f"{system_prompt}\n\nPergunta do usuário: {mensagem_para_ia}")
            if txt:
                resposta_especial = txt
            else:
                st.session_state["erro_gemini"] = f"Falha na Gemini → {err}"
                pular_groq = True
        elif tipo_v:
            modelo = tipo_v
            img = st.session_state.imagem
            conteudo_usuario = [{"type": "text", "text": mensagem_para_ia}, {"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['base64']}"}}]
        else:
            st.session_state["erro_gemini"] = "Sem visão disponível (veja o 👁️ na sidebar)."
            pular_groq = True

    resposta = None
    with st.chat_message("assistant"):
        if st.session_state.imagem and st.session_state.get("status_visao"):
            st.caption(st.session_state["status_visao"])
        with st.spinner("🤔 Pensando..."):
            if resposta_especial is not None and resposta_especial.strip():
                resposta = resposta_especial
                st.markdown(resposta)
            elif pular_groq:
                msg = st.session_state.get("erro_gemini") or "Nenhum modelo de visão disponível para esta imagem."
                st.session_state["erro_gemini"] = msg
                st.error(f"❌ {msg}")
            else:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                mensagens_envio = [{"role": "system", "content": system_prompt}] + st.session_state.messages[:-1] + [{"role": "user", "content": conteudo_usuario}]
                response = client.chat.completions.create(model=modelo, messages=mensagens_envio, temperature=0.7, max_tokens=1024)
                resposta = response.choices[0].message.content
                st.markdown(resposta)
    if resposta is not None:
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        if current_conv: current_conv["messages"] = st.session_state.messages.copy()
    st.rerun()
