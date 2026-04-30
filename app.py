import streamlit as st
import os
import jwt
from PIL import Image
from google import genai
from google.genai import types
from supabase import create_client, Client
from streamlit_oauth import OAuth2Component

# --- CONFIGURAÇÕES INICIAIS ---
try:
    icone_yuna = Image.open("icone_yuna.png")
except:
    try:
        icone_yuna = Image.open("icone_yuna.jpg")
    except:
        icone_yuna = None

st.set_page_config(page_title="Yuna AI", page_icon=icone_yuna, layout="wide")

# Estilo para manter a Yuna com visual de App
st.markdown("""
    <style>
    div[data-testid="stChatInput"] > div {
        border-radius: 30px !important;
        border: 1px solid #555555 !important;
        overflow: hidden !important;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Conexão com o Supabase
@st.cache_resource
def iniciar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = iniciar_supabase()

# Conexão com o Gemini
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

instrucao_sistema = """
Você é a Yuna, uma IA especialista em sustentabilidade e meio ambiente criada por Yago.
Sua missão é ajudar com estudos, curiosidades e atividades ecológicas.
Use sempre um tom amigável e encorajador.
"""

st.markdown("# :green[Yuna]: Inteligência Ambiental🌱")

# --- SISTEMA DE LOGIN COM GOOGLE ---
oauth2 = OAuth2Component(
    st.secrets["GOOGLE_CLIENT_ID"],
    st.secrets["GOOGLE_CLIENT_SECRET"],
    "https://accounts.google.com/o/oauth2/v2/auth",
    "https://oauth2.googleapis.com/token",
    "https://oauth2.googleapis.com/token",
    None
)

if "user_email" not in st.session_state:
    st.info("👋 Olá! Faça login com sua conta Google para conversar com a Yuna e salvar seu progresso.")
    
    redirect_uri = "https://projeto-yuna.streamlit.app" 
    
    result = oauth2.authorize_button(
        name="Continuar com o Google",
        icon="https://www.google.com/favicon.ico",
        redirect_uri=redirect_uri,
        scope="openid email profile",
        key="google_login",
        use_container_width=True
    )
    
    if result:
        id_token = result["token"]["id_token"]
        payload = jwt.decode(id_token, options={"verify_signature": False})
        st.session_state["user_email"] = payload["email"]
        st.rerun()

else:
    # --- ÁREA DO USUÁRIO LOGADO ---
    usuario_logado = st.session_state["user_email"]
    
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        if icone_yuna:
            st.image(icone_yuna, width=80)
            
        st.title("Menu da Yuna")
        st.write(f"Logado como: :blue[{usuario_logado}]")
        
        # O botão Nova Conversa agora apaga o histórico do banco para resetar a tela
        if st.button("➕ Nova Conversa", use_container_width=True):
            try:
                supabase.table("historico_yuna").delete().eq("usuario", usuario_logado).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao resetar: {e}")

        if st.button("🗑️ Apagar Todo Histórico", type="secondary", use_container_width=True):
            try:
                supabase.table("historico_yuna").delete().eq("usuario", usuario_logado).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao apagar: {e}")

        st.divider()
        
        if st.button("Sair da conta", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- ÁREA PRINCIPAL DO CHAT ---
    # (Atenção: este código não está recuado, para ficar fora da sidebar)

    # 1. Busca histórico do Supabase
    resposta_db = supabase.table("historico_yuna").select("*").eq("usuario", usuario_logado).order("created_at").execute()
    mensagens_db = resposta_db.data

    # Exibe as mensagens na página principal
    for msg in mensagens_db:
        role_visual = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role_visual):
            st.markdown(msg["content"])

    # 2. Input de nova mensagem
    if prompt := st.chat_input("Pergunte algo sobre o meio ambiente..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Salva pergunta do usuário no banco
        supabase.table("historico_yuna").insert({"usuario": usuario_logado, "role": "user", "content": prompt}).execute()

        # Prepara histórico para o Gemini
        history_contents = []
        for m in mensagens_db:
            role_gemini = "user" if m["role"] == "user" else "model"
            history_contents.append(types.Content(role=role_gemini, parts=[types.Part.from_text(text=m["content"])]))
            
        chat_gemini = st.session_state.gemini_client.chats.create(
            model="gemini-2.0-flash", 
            history=history_contents,
            config=types.GenerateContentConfig(
                system_instruction=instrucao_sistema,
                temperature=0.7
            )
        )
        
        try:
            with st.spinner("Yuna analisando..."):
                resposta = chat_gemini.send_message([types.Part.from_text(text=prompt)])
                resposta_final = resposta.text
                
                with st.chat_message("assistant"):
                    st.markdown(resposta_final)
                
                # Salva resposta da Yuna no banco
                supabase.table("historico_yuna").insert({"usuario": usuario_logado, "role": "model", "content": resposta_final}).execute()
                st.rerun()
                
        except Exception as e:
            st.error(f"Erro técnico: {e}")
