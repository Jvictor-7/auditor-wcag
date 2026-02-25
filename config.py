import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

llm = ChatOpenAI(
    model=MODEL,
    api_key=OPENAI_API_KEY,
)

print(f"SDK detectado. LLM: {MODEL} via OpenAI")
print("✅ Ambiente configurado com sucesso!")
