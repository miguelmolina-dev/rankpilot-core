import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_llm(temperature: float = 0.2):
    """
    Returns an instance of ChatOpenAI configured for either OpenRouter (local development)
    or a server-deployed OpenAI model (production/server environment), based on environment variables.
    """
    # Determine the environment
    environment = os.getenv("ENVIRONMENT", "production").lower() 
    
    print(f"\n=== DEBUG [llm.py] ===")
    print(f"-> Environment detected: '{environment}'")

    if environment == "local":
        api_key = os.getenv("OPENROUTER_API_KEY", "missing-key")
        # Enmascarar la llave por seguridad (muestra solo los primeros 6 y últimos 4 caracteres)
        safe_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "INVALID_OR_MISSING"
        
        print(f"-> Loading LOCAL config via OpenRouter")
        print(f"-> Model: google/gemini-2.0-flash-001")
        print(f"-> API Key used: {safe_key}")
        print(f"======================\n")

        return ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            timeout=300,
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost:8000"),
                "X-Title": os.getenv("OPENROUTER_TITLE", "RankPilot"),
            }
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY", "missing-key")
        safe_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "INVALID_OR_MISSING"
        
        print(f"-> Loading PRODUCTION config via direct OpenAI")
        print(f"-> Model: gpt-5.4-mini")
        print(f"-> API Key used: {safe_key}")
        print(f"======================\n")

        kwargs = {
            "model": "gpt-5.4-mini",
            "api_key": api_key,
            "temperature": temperature
        }

        return ChatOpenAI(**kwargs)