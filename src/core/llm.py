import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_llm(temperature: float = 0.2, updates: dict = None):
    """
    Returns an instance of ChatOpenAI configured for either OpenRouter or OpenAI.
    If 'updates' dict is provided, it appends diagnostic messages to updates["messages"].
    """
    environment = os.getenv("ENVIRONMENT", "production").lower() 
    
    # 1. Preparar el log inicial
    env_msg = f"LLM Factory: Environment detected -> '{environment}'"
    print(f"\n=== DEBUG [llm.py] ===")
    print(f"-> {env_msg}")
    
    # Si nos pasaron el diccionario de updates, guardamos el log para que viaje a Laravel
    if updates is not None and "messages" in updates:
        updates["messages"].append(env_msg)

    if environment == "local":
        api_key = os.getenv("OPENROUTER_API_KEY", "missing-key")
        safe_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "INVALID_OR_MISSING"
        
        # 2. Preparar el log de OpenRouter
        local_msg = f"LLM Factory: Loading LOCAL config (Gemini) | Key: {safe_key}"
        print(local_msg)
        print(f"======================\n")
        
        if updates is not None and "messages" in updates:
            updates["messages"].append(local_msg)

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
        
        # 3. Preparar el log de Producción
        prod_msg = f"LLM Factory: Loading PRODUCTION config (gpt-5.4-mini) | Key: {safe_key}"
        print(prod_msg)
        print(f"======================\n")
        
        if updates is not None and "messages" in updates:
            updates["messages"].append(prod_msg)

        kwargs = {
            "model": "gpt-5.4-mini",
            "api_key": api_key,
            "temperature": temperature
        }

        return ChatOpenAI(**kwargs)