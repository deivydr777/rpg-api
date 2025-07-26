import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from typing import List, Optional

# --- CONFIGURAÇÃO ---

# É CRUCIAL que você configure sua chave de API como uma variável de ambiente
# no Render. Não coloque a chave diretamente no código.
# Nome da variável: GOOGLE_API_KEY
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# Configuração do CORS para permitir que seu site (frontend) se comunique com esta API
origins = ["*"]  # Em produção, seria melhor restringir ao domínio do seu site

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INSTRUÇÃO PARA A IA (O "CÉREBRO" DO NARRADOR) ---

# Esta é a instrução que define o comportamento do nosso narrador.
# A parte mais importante é a instrução sobre como formatar as ações.
INSTRUCAO_SISTEMA = """
Você é um Mestre de Jogo especialista e o narrador de um RPG de texto imersivo baseado no universo de Harry Potter.
Sua tarefa é descrever o mundo, os personagens e os eventos de forma vívida e envolvente.
O jogador está no quinto ano em Hogwarts.
Sempre responda em português do Brasil.

IMPORTANTE: Quando a história chegar a um ponto onde o jogador precisa fazer uma escolha clara, ofereça a ele de 3 a 4 opções.
Formate essas opções como uma lista Python no final da sua resposta, exatamente assim: ["Ação 1", "Ação 2", "Ação 3"]
Exemplo de resposta com ações:
"Você vê o Trasgo no banheiro feminino. Hermione está encurralada e apavorada. O que você faz? ["Atacar o Trasgo com um feitiço", "Criar uma distração para que Hermione possa fugir", "Correr para buscar ajuda de um professor"]"

Se for um momento de narração contínua e não houver uma escolha específica a ser feita, simplesmente continue a história sem adicionar a lista de ações.
"""

# --- MODELOS DE DADOS (PYDANTIC) ---

class UserInput(BaseModel):
    message: str

# Este é o novo modelo de resposta!
# Ele pode conter uma lista opcional de strings (actions).
class ChatResponse(BaseModel):
    text: str
    actions: Optional[List[str]] = None

# --- ENDPOINT DA API ---

@app.post("/chat", response_model=ChatResponse)
async def chat(user_input: UserInput):
    """
    Recebe a mensagem do usuário, gera a resposta do narrador e a retorna
    junto com possíveis ações.
    """
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            system_instruction=INSTRUCAO_SISTEMA
        )
        
        # Gera a resposta da IA com base na mensagem do usuário
        response = model.generate_content(user_input.message)
        
        full_response_text = response.text
        narrative_text = full_response_text
        parsed_actions = None

        # --- LÓGICA PARA ANALISAR A RESPOSTA E EXTRAIR AÇÕES ---
        # Verifica se a resposta da IA contém uma lista de ações no formato esperado
        actions_start_index = full_response_text.rfind('[')
        actions_end_index = full_response_text.rfind(']')

        if actions_start_index != -1 and actions_end_index > actions_start_index:
            actions_str = full_response_text[actions_start_index : actions_end_index + 1]
            try:
                # Tenta converter a string da lista em uma lista Python real
                parsed_actions = json.loads(actions_str)
                # Se for bem-sucedido, remove a lista da parte narrativa
                narrative_text = full_response_text[:actions_start_index].strip()
            except json.JSONDecodeError:
                # Se a IA cometer um erro e o formato não for um JSON válido,
                # ignoramos e tratamos tudo como texto narrativo.
                pass

        return ChatResponse(text=narrative_text, actions=parsed_actions)

    except Exception as e:
        # Em caso de erro com a API do Gemini ou outra falha
        print(f"Erro no servidor: {e}")
        return ChatResponse(text="Houve um erro mágico no Ministério... O narrador parece confuso. Tente novamente em alguns instantes.")
