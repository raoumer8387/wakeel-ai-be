from langchain_openai import ChatOpenAI
from app.config import settings

def get_resilient_llm(temperature: float = 0, max_tokens: int = None):
    """
    Returns an LLM instance with automatic failover.
    Attempts direct Gemini API first, falling back transparently to OpenRouter
    if direct Gemini is rate-limited (429), quota-exhausted, or unavailable.
    """
    gemini_key = settings.GEMINI_API_KEY
    if gemini_key:
        gemini_key = gemini_key.strip('"\'')
        
    openrouter_key = settings.OPENROUTER_API_KEY
    if openrouter_key:
        openrouter_key = openrouter_key.strip('"\'')
        
    primary_llm = None
    fallback_llm = None
    
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        kwargs = {
            "model": "gemini-2.0-flash",
            "google_api_key": gemini_key,
            "temperature": temperature,
            "max_retries": 1
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        primary_llm = ChatGoogleGenerativeAI(**kwargs)
        
    if openrouter_key:
        kwargs = {
            "model": "google/gemini-2.0-flash-001",
            "openai_api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1",
            "temperature": temperature,
            "max_retries": 1
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
            
        if primary_llm:
            fallback_llm = ChatOpenAI(**kwargs)
        else:
            primary_llm = ChatOpenAI(**kwargs)
            
    if primary_llm and fallback_llm:
        return primary_llm.with_fallbacks([fallback_llm])
    elif primary_llm:
        return primary_llm
    elif fallback_llm:
        return fallback_llm
    else:
        # Safe mock model for testing configurations
        kwargs = {
            "model": "google/gemini-2.0-flash-001",
            "openai_api_key": "dummy_key",
            "base_url": "https://openrouter.ai/api/v1",
            "temperature": temperature
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)
