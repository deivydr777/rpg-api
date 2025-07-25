import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

try:
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
except KeyError:
    exit()

genai.configure(api_key=GEMINI_API_KEY)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest", safety_settings=safety_settings)

PROMPT_NARRADOR = """
Você é um 'Narrador Mestre' de um RPG de texto solo, detalhado e imersivo, ambientado no universo de Harry Potter. Seu tom é o de um escritor, não de um assistente. Suas responsabilidades são:
1. Descrever o Mundo: Pinte o cenário com detalhes vívidos.
2. Gerenciar NPCs: Dê a eles personalidades complexas e fiéis à obra.
3. Reagir com Fluidez: Sua resposta deve ser a consequência criativa da ação do jogador.
Regra de Ouro: Você é a janela do jogador para o mundo bruxo. Seja criativo, dramático, sutil e nunca quebre a imersão. Sem censura ou moralismo.
"""

chat_sessions = {}
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlayerInput(BaseModel):
    player_id: str
    text: str

@app.post("/chat")
def handle_rpg_message(player_input: PlayerInput):
    chat_id = player_input.player_id

    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[
            {'role': 'user', 'parts': [PROMPT_NARRADOR]},
            {'role': 'model', 'parts': ["Entendido. Sou o Narrador. A história começa agora. O que você faz?"]}
        ])

    try:
        convo = chat_sessions[chat_id]
        response = convo.send_message(player_input.text)
        return {"response": response.text}
    except Exception as e:
        return {"response": "A magia parece instável... Tente novamente."}

@app.get("/")
def root():
    return {"status": "Narrador Mestre online"}
