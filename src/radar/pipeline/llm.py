"""LLM Factory and OpenRouter / OpenAI Provider Integration for Allen + Clarke Radar.

Supports OpenRouter, OpenAI, Anthropic, and local/custom OpenAI-compatible endpoints,
with automatic environment variable detection and fallback to heuristic reasoning.
"""

import logging
import os
from typing import Any, Dict, Optional
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

# Try loading .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.1,
    max_retries: int = 2,
    timeout: float = 60.0,
) -> Optional[BaseChatModel]:
    """Instantiates a LangChain ChatModel configured for OpenRouter, OpenAI, or compatible endpoints.

    Resolution Priority:
    1. Explicit arguments (`provider`, `model`, `api_key`, `base_url`).
    2. Environment variables (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`).
    3. OpenAI environment variables (`OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`).
    4. Returns None (signals agents to use deterministic heuristics engine).

    Args:
        provider: 'openrouter', 'openai', 'anthropic', 'heuristics', or 'custom'.
        model: Model identifier (e.g. 'anthropic/claude-3.5-sonnet', 'openai/gpt-4o-mini', 'google/gemini-2.5-flash').
        api_key: API key string.
        base_url: Custom API base URL.
        temperature: Sampling temperature (0.0 to 1.0).
        max_retries: Number of retries on transient errors.
        timeout: Request timeout in seconds.

    Returns:
        Configured BaseChatModel instance, or None if no API key is available or heuristics requested.
    """
    selected_provider = (provider or "").strip().lower()

    if selected_provider == "heuristics" or selected_provider == "none":
        logger.info("Heuristic evaluation explicitly selected; skipping LLM initialization.")
        return None

    # Check for OpenRouter configuration
    openrouter_key = api_key if (selected_provider == "openrouter" and api_key) else (
        api_key or os.environ.get("OPENROUTER_API_KEY")
    )
    openrouter_model = model or os.environ.get("OPENROUTER_MODEL") or "anthropic/claude-3.5-sonnet"
    openrouter_base_url = base_url or os.environ.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"

    # Check for standard OpenAI configuration
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    openai_model = model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
    openai_base_url = base_url or os.environ.get("OPENAI_BASE_URL")

    # 1. OpenRouter Provider (Priority when OPENROUTER_API_KEY is present or provider == 'openrouter')
    if selected_provider == "openrouter" or (openrouter_key and not selected_provider):
        if not openrouter_key:
            logger.warning("OpenRouter provider requested but OPENROUTER_API_KEY is not set.")
            return None

        try:
            from langchain_openai import ChatOpenAI

            headers = {
                "HTTP-Referer": "https://github.com/beastob/allen-clarke-bd-opportunity-radar",
                "X-Title": "Allen + Clarke BD Opportunity Radar",
            }

            llm = ChatOpenAI(
                model=openrouter_model,
                api_key=openrouter_key,
                base_url=openrouter_base_url,
                temperature=temperature,
                max_retries=max_retries,
                timeout=timeout,
                default_headers=headers,
            )
            logger.info(f"Initialized OpenRouter LLM: model='{openrouter_model}', base_url='{openrouter_base_url}'")
            return llm

        except ImportError:
            logger.error("langchain-openai is required for OpenRouter integration. Run `pip install langchain-openai`.")
            return None
        except Exception as e:
            logger.exception(f"Failed to initialize OpenRouter LLM: {e}")
            return None

    # 2. Standard OpenAI Provider
    if selected_provider == "openai" or (openai_key and not selected_provider):
        if not openai_key:
            logger.warning("OpenAI provider requested but OPENAI_API_KEY is not set.")
            return None

        try:
            from langchain_openai import ChatOpenAI

            kwargs: Dict[str, Any] = {
                "model": openai_model,
                "api_key": openai_key,
                "temperature": temperature,
                "max_retries=max_retries": max_retries,
                "timeout": timeout,
            }
            if openai_base_url:
                kwargs["base_url"] = openai_base_url

            llm = ChatOpenAI(
                model=openai_model,
                api_key=openai_key,
                base_url=openai_base_url,
                temperature=temperature,
                max_retries=max_retries,
                timeout=timeout,
            )
            logger.info(f"Initialized OpenAI LLM: model='{openai_model}'")
            return llm

        except ImportError:
            logger.error("langchain-openai is required for OpenAI integration. Run `pip install langchain-openai`.")
            return None
        except Exception as e:
            logger.exception(f"Failed to initialize OpenAI LLM: {e}")
            return None

    # No LLM API key detected
    logger.debug("No LLM API keys found (OPENROUTER_API_KEY or OPENAI_API_KEY). Using deterministic heuristics engine.")
    return None


def get_llm_status() -> Dict[str, Any]:
    """Returns diagnostic status of configured LLM providers and environment variables."""
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    def mask_key(k: Optional[str]) -> Optional[str]:
        if not k:
            return None
        if len(k) <= 8:
            return "***"
        return f"{k[:6]}...{k[-4:]}"

    detected_provider = "none"
    if openrouter_key:
        detected_provider = "openrouter"
    elif openai_key:
        detected_provider = "openai"

    return {
        "detected_provider": detected_provider,
        "is_llm_available": bool(openrouter_key or openai_key),
        "openrouter": {
            "is_configured": bool(openrouter_key),
            "masked_key": mask_key(openrouter_key),
            "model": os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
            "base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        },
        "openai": {
            "is_configured": bool(openai_key),
            "masked_key": mask_key(openai_key),
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        },
    }
