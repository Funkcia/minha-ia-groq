import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import datetime
import streamlit.components.v1 as components
import base64
import io
import hashlib
from pypdf import PdfReader
import google.generativeai as genai

try:
    from supabase import create_client
except Exception:
    create_client = None

# ================= IDENTIDADE =================
NOME_IA = "Nexa"   # ← troque o nome da sua IA aqui (1 linha só)
ICONE_URL = "https://raw.githubusercontent.com/Funkcia/minha-ia-groq/main/nexa.png"
# Sem o nexa.png no repo? Troque a linha acima por:  ICONE_URL = "🤖"

st.set_page_config(page_title=f"{NOME_IA} · Minha IA Pessoal", page_icon=ICONE_URL, layout="wide")

for chave, valor in [("conversations", []), ("current_conv_id", None), ("documento", None),
                     ("imagem", None), ("erro_gemini", None), ("erro_sb", None), ("msg_memoria", None),
                     ("hash_audio_ultimo", None), ("_sb_carregado", False)]:
    if chave not in st.session_state:
        st.session_state[chave] = valor

# ================= SUPABASE (opt-in) =================
def sb():
    if create_client is None:
        return None
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

def owner_token():
    return st.secrets.get("SUPABASE_OWNER", "eu")

def _serializa(msgs):
    out = []
    for m in msgs or []:
        mm = dict(m)
        if mm.get("imagem") is not None:
            mm["imagem_b64"] = base64.b64encode(mm["imagem"]).decode()
            mm.pop("imagem", None)
        out.append(mm)
    return out

def _desserializa(msgs):
    out = []
    for m in msgs or []:
        mm = dict(m)
        if "imagem_b64" in mm:
            mm["imagem"] = base64.b64decode(mm["imagem_b64"])
            mm.pop("imagem_b64", None)
        out.append(mm)
    return out

def carregar_sb():
    c = sb()
    if not c:
        return
    try:
        r = c.table("conversas").select("*").eq("owner", owner_token()).order("atualizado_em", desc=True).execute()
        convs = []
        for d in r.data:
            convs.append({"id": d["chave"], "title": d.get("titulo") or "Conversa",
                          "persona": d.get("persona") or "Assistente Padrão",
                          "messages": _desserializa(d.get("mensagens"))})
        st.session_state.conversations = convs
        if convs and not st.session_state.current_conv_id:
            st.session_state.current_conv_id = convs[0]["id"]
    except Exception as e:
        st.session_state["erro_sb"] = f"Não consegui carregar do Supabase: {e}"

def salvar_sb(conv):
    c = sb()
    if not c or not conv:
        return
    try:
        c.table("conversas").upsert({
            "owner": owner_token(), "chave": conv["id"], "titulo": conv.get("title"),
            "persona": conv.get("persona"), "mensagens": _serializa(conv.get("messages", [])),
            "atualizado_em": datetime.utcnow().isoformat()
        }, on_conflict="owner,chave").execute()
    except Exception as e:
        st.session_state["erro_sb"] = f"Falha ao salvar no Supabase: {e}"

def deletar_sb(chave):
    c = sb()
    if not c:
        return
    try:
        c.table("conversas").delete().eq("owner", owner_token()).eq("chave", chave).execute()
    except Exception:
        pass

if not st.session_state["_sb_carregado"]:
    st.session_state["_sb_carregado"] = True
    carregar_sb()

# ================= MEMÓRIA DE LONGO PRAZO =================
def ler_memoria():
    c = sb()
    if not c:
        return ""
    try:
        r = c.table("memoria").select("conteudo").eq("owner", owner_token()).execute()
        if r.data and r.data[0].get("conteudo"):
            return r.data[0]["conteudo"]
    except Exception as e:
        st.session_state["erro_sb"] = f"Erro lendo memória: {e}"
    return ""

def salvar_memoria(texto):
    c = sb()
    if not c:
        return False
    try:
        c.table("memoria").upsert({
            "owner": owner_token(), "conteudo": texto,
            "atualizado_em": datetime.utcnow().isoformat()
        }, on_conflict="owner").execute()
        return True
    except Exception as e:
        st.session_state["erro_sb"] = f"Falha salvando memória: {e}"
        return False

_cache_mem = {"val": None}
def memoria_atual():
    if _cache_mem["val"] is None:
        _cache_mem["val"] = ler_memoria()
    return _cache_mem["val"]

def consolidar_memoria(fonte):
    c = sb()
    if not c:
        return None, "Supabase desligado — ligue para usar a memória de longo prazo."
    fonte = (fonte or "").strip()
    if not fonte:
        return None, "Nada para consolidar (conversa vazia)."
    mem_atual = ler_memoria() or "(vazia)"
    prompt_consolida = (
        "Você mantém a MEMÓRIA DE LONGO PRAZO de um usuário.\n\n"
        f"MEMÓRIA ATUAL:\n{mem_atual}\n\n"
        f"NOVA INFORMAÇÃO:\n{fonte}\n\n"
        "Regras: extraia APENAS fatos duráveis e úteis sobre o usuário (quem ele é, preferências, "
        "projetos, contexto pessoal/profissional, como gosta das respostas). Ignore conteúdo efêmero da conversa. "
        "Misture com a memória atual sem duplicar e sem contradizer. Responda SOMENTE com o texto final da memória, "
        "em português, em tópicos curtos, com no máximo 1500 caracteres. Não escreva introduções nem 'Claro'."
    )
    try:
        cl = Groq(api_key=st.secrets["GROQ_API_KEY"])
        resp = cl.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt_consolida}],
            temperature=0.3, max_tokens=600
        )
        novo = (resp.choices[0].message.content or "").strip()
        if not novo:
            return None, "A IA retornou memória vazia."
        if salvar_memoria(novo):
            _cache_mem["val"] = novo
            return novo, None
        return None, st.session_state.get("erro_sb") or "Falha ao gravar memória."
    except Exception as e:
        return None, f"Erro consolidando memória: {e}"

def montar_fonte_conversa():
    conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if not conv or not conv.get("messages"):
        return ""
    partes = []
    for m in conv["messages"][-20:]:
        quem = "Usuário" if m["role"] == "user" else "IA"
        partes.append(f"{quem}: {m['content']}")
    return "\n".join(partes)[:6000]

# ================= VISÃO =================
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
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        from PIL import Image
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
    except Exception as e:
        return None, f"Não consegui preparar a imagem ({type(e).__name__}: {str(e)[:120]})."
    erros = []
    quota = False
    for nome in ["gemini-3.8-flash", "gemini-flash-latest"]:
        try:
            mg = genai.GenerativeModel(nome, generation_config=cfg)
            r = mg.generate_content([prompt_final, img_final], request_options={"timeout": 30})
            try:
                txt = r.text
            except Exception:
                txt = ""
            if txt and txt.strip():
                return txt, None
            erros.append(f"[{nome}] vazio/bloqueado")
        except Exception as e:
            s = str(e)
            if "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower():
                quota = True
            erros.append(f"[{nome}] {s[:140]}")
    if quota:
        return None, "⏳ Limite da camada grátis da Google atingido (429). Espere ~1 min e tente de novo."
    return None, "  •  ".join(erros)

# ================= CSS =================
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

# ================= SIDEBAR =================
with st.sidebar:
    st.title("⚙️ Configurações")
    st.checkbox("☀️ Modo claro", help="Desmarcado = tema escuro")
    modo_entrada = st.radio("🎙️ Forma de falar:", ["⌨️ Digitar", "🎤 Microfone"], horizontal=True)
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
                    deletar_sb(conv["id"])
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
                            salvar_sb(conv)
                            st.session_state[f"renaming_{conv['id']}"] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_{conv['id']}", use_container_width=True):
                            st.session_state[f"renaming_{conv['id']}"] = False
                            st.rerun()

    st.divider()
    st.subheader("🧠 Memória")
    st.caption(f"A {NOME_IA} lembra de você entre as conversas.")
    with st.expander("📖 Ver / editar memória", expanded=False):
        mem_edited = st.text_area("Conteúdo salvo sobre você:", value=memoria_atual(), height=170, key="mem_edit")
        col_ms, col_mc = st.columns(2)
        with col_ms:
            if st.button("💾 Salvar", use_container_width=True, key="mem_save_btn"):
                if salvar_memoria(mem_edited):
                    st.session_state["msg_memoria"] = "💾 Memória salva manualmente."
                    st.rerun()
        with col_mc:
            if st.button("🧹 Limpar", use_container_width=True, key="mem_clear_btn"):
                if salvar_memoria(""):
                    st.session_state["msg_memoria"] = "🧹 Memória apagada."
                    st.rerun()
    if st.button("🧠 Consolidar memória com a conversa atual", use_container_width=True, key="mem_consolidar_btn"):
        if not sb():
            st.session_state["erro_sb"] = "Ligue o Supabase para usar a memória de longo prazo."
            st.rerun()
        fonte = montar_fonte_conversa()
        if not fonte:
            st.session_state["erro_sb"] = "Abra uma conversa com mensagens para consolidar."
            st.rerun()
        with st.spinner("🧠 Consolidando memória..."):
            _, err = consolidar_memoria(fonte)
        if err:
            st.session_state["erro_sb"] = err
        else:
            st.session_state["msg_memoria"] = "🧠 Memória de longo prazo atualizada com esta conversa."
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
    st.caption(f"💾 Persistência: {'✅ Supabase ligado' if sb() else '⚪ só memória (configure Supabase)'}")
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
    st.caption(f"Feito com {NOME_IA} · SysNext Desenvolvimento 🚀")

# ================= PROMPTS / CONVERSA =================
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

_mem = memoria_atual()
if _mem:
    system_prompt += (
        "\n\n=== MEMÓRIA DE LONGO PRAZO SOBRE O USUÁRIO ===\n" + _mem +
        "\n=== FIM ===\nUse esses fatos para personalizar naturalmente. "
        "Não os recite literalmente nem mencione que possui memória, salvo se o usuário perguntar o que você sabe sobre ele."
    )

if st.session_state.get("erro_sb"):
    st.warning(f"⚠️ {st.session_state['erro_sb']}")
if st.session_state.get("erro_gemini"):
    st.error(f"❌ {st.session_state['erro_gemini']}")
if st.session_state.get("msg_memoria"):
    st.info(st.session_state["msg_memoria"])
    st.session_state["msg_memoria"] = None

if st.session_state.current_conv_id and current_conv:
    st.title(f"💬 {current_conv['title']}")
    st.caption(f"🎭 {current_conv.get('persona', persona)} • 📊 {len(st.session_state.messages)} mensagens")
else:
    st.title(f"🤖 {NOME_IA}")
    st.info(f"👈 Eu sou a {NOME_IA}. Clique em **Nova Conversa** ou fale/digite sua primeira mensagem abaixo!")

# ================= HISTÓRICO =================
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("imagem"):
            st.image(message["imagem"], width=240)
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

# ================= BUSCA WEB =================
def pesquisar_na_web(consulta):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=3))
            if resultados: return "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
            return "Nenhuma informação recente encontrada."
    except Exception: return "Erro ao buscar na web."

# ================= ENTRADA (voz OU texto) =================
prompt = None
if modo_entrada.startswith("🎤"):
    audio = st.audio_input("🎤 Grave sua mensagem (clique no microfone, fale, pare)", key="mic")
    if audio is not None:
        h = hashlib.md5(audio.getvalue()).hexdigest()
        if h != st.session_state.get("hash_audio_ultimo"):
            st.session_state["hash_audio_ultimo"] = h
            with st.spinner("🎧 Transcrevendo sua fala..."):
                try:
                    cl = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    f = io.BytesIO(audio.getvalue())
                    f.name = "audio.wav"
                    prompt = cl.audio.transcriptions.create(model="whisper-large-v3-turbo", file=f).text
                except Exception as e:
                    st.error(f"Falha na transcrição (Whisper/Groq): {e}")
else:
    prompt = st.chat_input("Digite sua mensagem...")

# ================= GERAR RESPOSTA =================
if prompt:
    st.session_state["erro_gemini"] = None
    _gatilhos = ["lembre-se", "lembre se", "lembre que", "lembra que", "anote que", "anote:", "memória:", "memoria:", "grave que", "guarde que"]
    if any(g in prompt.lower() for g in _gatilhos):
        if sb():
            _, _err = consolidar_memoria(prompt)
            if _err:
                st.session_state["erro_sb"] = _err
            else:
                st.session_state["msg_memoria"] = "🧠 Anotado na memória de longo prazo."
        else:
            st.session_state["erro_sb"] = "Gatilho de memória detectado, mas o Supabase está desligado."

    if not st.session_state.current_conv_id:
        new_conv = {"id": datetime.now().strftime("%Y%m%d_%H%M%S"), "title": prompt[:30] + "..." if len(prompt) > 30 else prompt, "messages": [], "persona": persona}
        st.session_state.conversations.append(new_conv)
        st.session_state.current_conv_id = new_conv["id"]
        st.session_state.messages = []
        st.rerun()

    nova_msg = {"role": "user", "content": prompt}
    if st.session_state.imagem:
        nova_msg["imagem"] = st.session_state.imagem["bytes"]
    st.session_state.messages.append(nova_msg)
    current_conv = next((c for c in st.session_state.conversations if c["id"] == st.session_state.current_conv_id), None)
    if current_conv and len(current_conv["messages"]) == 1:
        current_conv["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
    with st.chat_message("user"):
        st.markdown(prompt)
        if st.session_state.imagem:
            st.image(st.session_state.imagem["bytes"], width=240)

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
        if current_conv:
            current_conv["messages"] = st.session_state.messages.copy()
            salvar_sb(current_conv)
    st.rerun()
