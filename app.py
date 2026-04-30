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
    icone_yuna = Image.open("icone_yuna.jpg")

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
    
    # ATENÇÃO: Troque a URL abaixo pela URL exata do seu projeto Streamlit Cloud
    # Exemplo: "https://projeto-yuna.streamlit.app/"
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
    # --- ÁREA DO CHAT (Usuário Logado) ---
    usuario_logado = st.session_state["user_email"]
    
    with st.sidebar:
        st.write(f"Logado como: **{usuario_logado}**")
        if st.button("Sair da conta"):
            del st.session_state["user_email"]
            st.rerun()

    # 1. Puxar o histórico do banco de dados usando o E-MAIL
    resposta_db = supabase.table("historico_yuna").select("*").eq("usuario", usuario_logado).order("created_at").execute()
    mensagens_db = resposta_db.data

    # Exibir as mensagens na tela
    for msg in mensagens_db:
        role_visual = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role_visual):
            st.markdown(msg["content"])

    # 2. Lógica de nova mensagem
    if prompt := st.chat_input("Pergunte algo sobre o meio ambiente..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Salva a pergunta vinculada ao E-MAIL
        supabase.table("historico_yuna").insert({"usuario": usuario_logado, "role": "user", "content": prompt}).execute()

        history_contents = []
        for m in mensagens_db:
            history_contents.append(types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])]))
            
        chat_gemini = st.session_state.gemini_client.chats.create(
            model="gemini-2.5-flash",
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
                
                # Salva a resposta da Yuna vinculada ao E-MAIL
                supabase.table("historico_yuna").insert({"usuario": usuario_logado, "role": "model", "content": resposta_final}).execute()
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Erro técnico: {e}")
