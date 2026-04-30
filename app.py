import streamlit as st
import os
import uuid
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Carregar o Ícone Personalizado
try:
    icone_yuna = Image.open("icone_yuna.png")
except:
    icone_yuna = Image.open("icone_yuna.jpg")

# --- INTERFACE VISUAL E CONFIGURAÇÕES ---
st.set_page_config(page_title="Yuna AI", page_icon=icone_yuna, layout="wide")

# 2. Injeção de CSS para um visual Minimalista e Limpo
st.markdown("""
    <style>
    div[data-testid="stChatInput"] > div {
        border-radius: 30px !important;
        border: 1px solid #555555 !important;
        overflow: hidden !important;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    #MainMenu {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        max-width: 1000px;
        margin-left: 0;
    }
    .sidebar-footer {
        color: #888888;
        font-size: 0.8rem;
        padding-top: 20px;
    }
    .stButton > button {
        width: 100%;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Inicialização do Registro de Conversas
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {} 
if "current_chat_id" not in st.session_state:
    id_inicial = str(uuid.uuid4())
    st.session_state.chat_history[id_inicial] = {"title": "Nova Conversa", "messages": []}
    st.session_state.current_chat_id = id_inicial

# 4. Conexão e Segurança
load_dotenv()
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

instrucao_sistema = """
Você é a Yuna, uma IA especialista em sustentabilidade e meio ambiente criada por Yago.
Sua missão é ajudar com estudos, curiosidades e atividades ecológicas.
Use sempre um tom amigável e encorajador.
"""

# --- BARRA LATERAL ---
with st.sidebar:
    st.image(icone_yuna, use_container_width=True)
    
    if st.button("+ Nova Conversa"):
        novo_id = str(uuid.uuid4())
        st.session_state.chat_history[novo_id] = {"title": "Nova Conversa", "messages": []}
        st.session_state.current_chat_id = novo_id
        st.rerun()
    
    st.markdown("---")
    st.subheader("📜 Histórico")
    
    for chat_id in list(st.session_state.chat_history.keys()):
        col_chat, col_del = st.columns([4, 1])
        with col_chat:
            titulo = st.session_state.chat_history[chat_id]["title"]
            if st.button(titulo, key=f"btn_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                if chat_id == st.session_state.current_chat_id:
                    if st.session_state.chat_history:
                        st.session_state.current_chat_id = list(st.session_state.chat_history.keys())[0]
                    else:
                        novo_id = str(uuid.uuid4())
                        st.session_state.chat_history[novo_id] = {"title": "Nova Conversa", "messages": []}
                        st.session_state.current_chat_id = novo_id
                st.rerun()

    st.markdown("---")
    st.markdown('<p class="sidebar-footer">Yuna é uma IA e pode cometer erros.</p>', unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
st.markdown("# :green[Yuna]: Inteligência Ambiental🌱")
st.caption("Desenvolvida por Yago | Tecnologia a serviço do Planeta")

chat_atual = st.session_state.chat_history[st.session_state.current_chat_id]

for message in chat_atual["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pergunte algo sobre o meio ambiente..."):
    if not chat_atual["messages"]:
        chat_atual["title"] = prompt[:20] + "..."

    chat_atual["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history_contents = []
        for m in chat_atual["messages"][:-1]:
            role = "model" if m["role"] == "assistant" else "user"
            history_contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
            )
            
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
                
                st.markdown(resposta_final)
                chat_atual["messages"].append({"role": "assistant", "content": resposta_final})
        
        except Exception as e:
            st.error(f"Erro técnico: {e}")