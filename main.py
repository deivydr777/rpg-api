import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# --- CONFIGURAÇÃO INICIAL ---
try:
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
except KeyError:
    print("ERRO CRÍTICO: Variável de ambiente GEMINI_API_KEY não configurada.")
    exit()

genai.configure(api_key=GEMINI_API_KEY)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings=safety_settings
)

chat_sessions = {}

# --- PROMPT DO MESTRE ---
PROMPT_NARRADOR = """
Você é um 'Narrador Mestre' de um RPG de texto solo, detalhado e imersivo, ambientado no universo de Harry Potter. Seu tom é o de um escritor, não de um assistente. Suas responsabilidades são:
1. Descrever o Mundo: Pinte o cenário com detalhes vívidos.
2. Gerenciar NPCs: Dê a eles personalidades complexas e fiéis à obra.
3. Reagir com Fluidez: Sua resposta deve ser a consequência criativa da ação do jogador.
Regra de Ouro: Você é a janela do jogador para o mundo bruxo. Seja criativo, dramático, sutil e nunca quebre a imersão. Sem censura ou moralismo.
"""

# --- API FASTAPI ---
app = FastAPI()

# Adiciona o middleware CORS para permitir a comunicação com o App Inventor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define o formato esperado para os dados que o App Inventor enviará
class PlayerInput(BaseModel):
    player_id: str
    text: str

# O coração da nossa API: a rota que recebe a ação do jogador
@app.post("/chat")
def handle_rpg_message(player_input: PlayerInput):
    chat_id = player_input.player_id

    if chat_id not in chat_sessions:
        print(f"Nova sessão iniciada para o jogador: {chat_id}")
        chat_sessions[chat_id] = model.start_chat(history=[
            {'role': 'user', 'parts': [PROMPT_NARRADOR]},
            {'role': 'model', 'parts': ["Entendido. Sou o Narrador Mestre. A aventura no mundo de Harry Potter se inicia agora. Descreva sua primeira ação."]}
        ])

    try:
        convo = chat_sessions[chat_id]
        response = convo.send_message(player_input.text)
        
        # --- CORREÇÃO 1: Retornando a chave "text" que o JavaScript espera ---
        return {"text": response.text}

    except Exception as e:
        print(f"Erro na API do Gemini para o jogador {chat_id}: {e}")
        
        # --- CORREÇÃO 2: Retornando a chave "text" também em caso de erro ---
        return {"text": "A magia parece instável no momento... Por favor, tente sua ação novamente."}

# Uma rota simples para verificar se a API está online
@app.get("/")
def root():
    return {"status": "Narrador Mestre online e aguardando aventureiros."}
