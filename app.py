import streamlit as st
import os
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from fpdf import FPDF
from openai import OpenAI

# 1. Carregar o Ícone Personalizado
# Certifique-se de que a imagem icone_yuna.png está na mesma pasta!
icone_yuna = Image.open("icone_yuna.png")
# --- INTERFACE VISUAL E CONFIGURAÇÕES ---
st.set_page_config(page_title="Yuna AI", page_icon=icone_yuna, layout="wide")

# 2. Injeção de CSS para um visual Minimalista e Chat Arredondado
st.markdown("""
    <style>
    /* Arredondar completamente todas as camadas da caixa de texto do chat */
    div[data-testid="stChatInput"] > div {
        border-radius: 30px !important;
        border: 1px solid #555555 !important;
        overflow: hidden !important;
    }
    
    /* Esconder botão de deploy/menu padrão do Streamlit para manter o visual limpo */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Conexão e Segurança
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

instrucao_sistema = """
Você é a Yuna, uma IA especialista em sustentabilidade e meio ambiente criada por Yago.
Sua missão é ajudar com estudos, curiosidades e atividades ecológicas.
Regras:
1. Recuse pedidos obscenos ou ilícitos.
2. Use títulos (##), negrito e listas para organizar a resposta.
3. Se houver uma imagem, analise-a sob a ótica ambiental.
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

# 4. Cabeçalho Personalizado Limpo
st.title("Yuna: Inteligência Ambiental")
    
st.caption("Desenvolvida por Yago | Tecnologia a serviço do Planeta")

# Barra Lateral
with st.sidebar:
    st.image(icone_yuna, use_container_width=True) 
    arquivo_upload = st.file_uploader("Envie uma imagem ambiental:", type=['jpg', 'jpeg', 'png'])
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Histórico de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de Usuário
if prompt := st.chat_input("Pergunte algo sobre o meio ambiente..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        mensagens_api = [{"role": "system", "content": instrucao_sistema}]
        conteudo_usuario = [{"type": "text", "text": prompt}]
        
        if arquivo_upload:
            img = Image.open(arquivo_upload)
            st.image(img, width=300, caption="Imagem enviada.")
            img_base64 = codificar_imagem(img)
            conteudo_usuario.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            })
            
        mensagens_api.append({"role": "user", "content": conteudo_usuario})

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
                st.download_button(
                    label="📥 Baixar Estudo em PDF",
                    data=pdf_bytes,
                    file_name="estudo_yuna.pdf",
                    mime="application/pdf"
                )
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_final})
        
        except Exception as e:
            st.error(f"Erro técnico detalhado: {e}")
