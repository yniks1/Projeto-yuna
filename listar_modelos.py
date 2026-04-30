import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega a sua chave do arquivo .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Modelos disponíveis para a Yuna:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        # Já limpa o "models/" do nome para facilitar
        print("-", m.name.replace('models/', ''))