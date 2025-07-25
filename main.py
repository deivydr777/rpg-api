import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# --- CONFIGURAÇÃO INICIAL ---

# Tenta carregar a chave da API a partir das variáveis de ambiente do Render.
# Se a chave não estiver configurada no Render, a aplicação não iniciará.
try:
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
except KeyError:
    # Esta mensagem aparecerá nos logs do Render se a variável não for encontrada.
    print("ERRO CRÍTICO: Variável de ambiente GEMINI_API_KEY não configurada.")
    exit()

# Configura a API do Google
genai.configure(api_key=GEMINI_API_KEY)

# Configurações de segurança para permitir uma narrativa de RPG mais livre.
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Inicializa o modelo generativo
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings=safety_settings
)

# O "cérebro" da nossa API: um dicionário para guardar cada sessão de chat individual.
# A chave será o player_id e o valor será o objeto de chat do Gemini.
chat_sessions = {}

# --- PROMPT DO MESTRE ---

# A personalidade e as regras para o nosso Narrador AI.
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
    allow_origins=["*"],  # Permite acesso de qualquer origem
    allow_methods=["*"],  # Permite todos os métodos (POST, GET, etc)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# Define o formato esperado para os dados que o App Inventor enviará
class PlayerInput(BaseModel):
    player_id: str
    text: str

# O coração da nossa API: a rota que recebe a ação do jogador
@app.post("/chat")
def handle_rpg_message(player_input: PlayerInput):
    chat_id = player_input.player_id

    # Verifica se é um jogador novo. Se for, cria uma nova sessão de chat para ele.
    if chat_id not in chat_sessions:
        print(f"Nova sessão iniciada para o jogador: {chat_id}")
        chat_sessions[chat_id] = model.start_chat(history=[
            {'role': 'user', 'parts': [PROMPT_NARRADOR]},
            {'role': 'model', 'parts': ["Entendido. Sou o Narrador Mestre. A aventura no mundo de Harry Potter se inicia agora. Descreva sua primeira ação."]}
        ])

    try:
        # Recupera a sessão de chat específica deste jogador
        convo = chat_sessions[chat_id]
        # Envia a ação do jogador para o Gemini e aguarda a resposta do narrador
        response = convo.send_message(player_input.text)
        # Retorna a resposta do narrador para o aplicativo
        return {"response": response.text}
    except Exception as e:
        # Em caso de erro com a API do Gemini, envia uma mensagem de erro
        print(f"Erro na API do Gemini para o jogador {chat_id}: {e}")
        return {"response": "A magia parece instável no momento... Por favor, tente sua ação novamente."}

# Uma rota simples para verificar se a API está online
@app.get("/")
def root():
    return {"status": "Narrador Mestre online e aguardando aventureiros."}
