import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "anthropic/claude-sonnet-4.5"

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY não encontrada. "
        "Defina no arquivo .env"
    )

llm = ChatOpenAI(
    model=MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

print(f"SDK detectado. LLM: {MODEL} via OpenRouter")
print("✅ Ambiente configurado com sucesso!")
