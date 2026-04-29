import streamlit as st
import os
import base64
import uuid
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from fpdf import FPDF
from openai import OpenAI

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
    /* Arredondar a caixa de texto do chat */
    div[data-testid="stChatInput"] > div {
        border-radius: 30px !important;
        border: 1px solid #555555 !important;
        overflow: hidden !important;
    }
    
    /* TOPO TRANSPARENTE (Mantém a setinha da sidebar visível) */
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }

    /* Esconde o menu de opções (três pontos) */
    #MainMenu {visibility: hidden;}
    
    /* Ajuste de margem superior e alinhamento à esquerda */
    .block-container {
        padding-top: 2rem;
        max-width: 1000px;
        margin-left: 0;
    }
    
    /* Estilo para a sidebar e botões de histórico */
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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

instrucao_sistema = """
Você é a Yuna, uma IA especialista em sustentabilidade e meio ambiente criada por Yago.
Sua missão é ajudar com estudos, curiosidades e atividades ecológicas.
"""

def criar_pdf(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    texto_limpo = texto.replace("##", "").replace("**", "").replace("*", "-")
    pdf.multi_cell(0, 10, txt=texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output()

def codificar_imagem(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- BARRA LATERAL (Lado Esquerdo) ---
with st.sidebar:
    st.image(icone_yuna, use_container_width=True)
    
    if st.button("+ Nova Conversa"):
        novo_id = str(uuid.uuid4())
        st.session_state.chat_history[novo_id] = {"title": "Nova Conversa", "messages": []}
        st.session_state.current_chat_id = novo_id
        st.rerun()
    
    st.markdown("---")
    st.subheader("📜 Histórico")
    
    # Listagem das conversas salvas
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
    arquivo_upload = st.file_uploader("Anexar arquivos:", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    st.markdown('<p class="sidebar-footer">Yuna é uma IA e pode cometer erros.</p>', unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
# Alteração aqui: Usando Markdown para colorir apenas o nome Yuna
st.markdown("# :green[Yuna]: Inteligência Ambiental🌱")
st.caption("Desenvolvida por Yago | Tecnologia a serviço do Planeta")

# Carrega a conversa selecionada
chat_atual = st.session_state.chat_history[st.session_state.current_chat_id]

for message in chat_atual["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Lógica de Entrada do Chat
if prompt := st.chat_input("Pergunte algo sobre o meio ambiente..."):
    # Atualiza o título no histórico com a primeira mensagem
    if not chat_atual["messages"]:
        chat_atual["title"] = prompt[:20] + "..."

    chat_atual["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        mensagens_api = [{"role": "system", "content": instrucao_sistema}]
        
        # Inclui o contexto da conversa atual
        for m in chat_atual["messages"]:
            mensagens_api.append({"role": m["role"], "content": m["content"]})
        
        # Tratamento de imagens
        if arquivo_upload and arquivo_upload.type != "application/pdf":
            img = Image.open(arquivo_upload)
            img_base64 = codificar_imagem(img)
            # Ajuste para formato multimodal
            mensagens_api[-1]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
            ]

        try:
            with st.spinner("Yuna analisando..."):
                resposta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=mensagens_api,
                    temperature=0.7
                )
                
                resposta_final = resposta.choices[0].message.content
                st.markdown(resposta_final)
                
                pdf_bytes = criar_pdf(resposta_final)
                st.download_button(label="📥 Baixar em PDF", data=pdf_bytes, file_name="estudo_yuna.pdf")
                
                chat_atual["messages"].append({"role": "assistant", "content": resposta_final})
        
        except Exception as e:
            st.error(f"Erro técnico: {e}")