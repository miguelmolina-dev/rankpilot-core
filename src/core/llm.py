import os
from langchain_openai import ChatOpenAI

def get_llm(temperature: float = 0.0):
    """
    Returns an instance of ChatOpenAI configured for either OpenRouter (local development)
    or a server-deployed OpenAI model (production/server environment), based on environment variables.
    """
    # Determine the environment
    environment = os.getenv("ENVIRONMENT", "local").lower()

    if environment == "local":
        # Use OpenRouter for local development
        api_key = os.getenv("OPENROUTER_API_KEY", "your-openrouter-key")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost:8000"),
                "X-Title": os.getenv("OPENROUTER_TITLE", "RankPilot"),
            }
        )
    else:
        # Use OpenAI model deployed in a server for other environments
        api_key = os.getenv("OPENAI_API_KEY", "your-openai-key")
        # If it's a custom server, OPENAI_API_BASE might be set
        base_url = os.getenv("OPENAI_API_BASE", None)
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

        kwargs = {
            "model": model,
            "api_key": api_key,
            "temperature": temperature
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)
