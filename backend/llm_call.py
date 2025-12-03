"""
LLM Configuration and Calling Functions

This module provides LLM configuration and calling utilities extracted from core/llms.py.
It handles OpenRouter API integration and provides functions to create and call language models.

"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.utils.utils import secret_from_env
from pydantic import SecretStr, Field
from langchain_core.messages import HumanMessage, SystemMessage


# Default model configuration
DEFAULT_MODEL_ID = "google/gemma-3-27b-it:free"

# Alternative models available (free tier)
ALTERNATIVE_MODELS = {
    "nvidia": "nvidia/nemotron-nano-12b-v2-vl:free",
    "gemini": "google/gemini-2.0-flash-exp:free",
    "glm": "z-ai/glm-4.5-air:free",
    "gemma": "google/gemma-3-27b-it:free",
    "mistral": "mistralai/mistral-small-3.1-24b-instruct:free",
}


class SecretString(SecretStr):
    """
    A wrapper class for SecretStr to handle sensitive information like API keys.
    Inherits from Pydantic's SecretStr for secure string handling.
    """
    pass


class ChatOpenRouter(ChatOpenAI):
    """
    A custom wrapper for language models initialized with OpenRouter API keys.
    
    This class extends ChatOpenAI to work with OpenRouter's API, providing a seamless
    interface for making API calls while maintaining security best practices for
    API key handling.

    Attributes:
        openai_api_key (SecretStr | None): The API key for OpenRouter, stored securely
        base_url (str): The base URL for OpenRouter's API endpoint
    """
    openai_api_key: SecretStr | None = Field(
        alias="api_key",
        default_factory=secret_from_env("OPENROUTER_API_KEY", default=None),
        description="OpenRouter API key, fetched from environment variables"
    )

    @property
    def lc_secrets(self) -> dict[str, str]:
        """
        Defines the mapping of class attributes to environment variables.
        
        Returns:
            dict[str, str]: Mapping of attribute names to environment variable names
        """
        return {"openai_api_key": "OPENROUTER_API_KEY"}

    def __init__(
        self,
        openai_api_key: SecretStr | None = None,
        **kwargs
    ):
        """
        Initialize the ChatOpenRouter instance.

        Args:
            openai_api_key (SecretStr | None): Optional API key override
            **kwargs: Additional arguments passed to ChatOpenAI
        """
        openai_api_key = (
            openai_api_key or SecretString(os.environ["OPENROUTER_API_KEY"])
        )
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=openai_api_key,
            **kwargs
        )


def make_text_generation_model_open_router(
    model_id: str = DEFAULT_MODEL_ID,
    max_retries: int = 12,
    temperature: float = 0.7
) -> ChatOpenRouter:
    """
    Create and configure a text generation model using OpenRouter's inference endpoint.
    
    This factory function initializes a ChatOpenRouter instance with the specified
    model ID and retry settings. It provides a convenient way to create language
    model instances for text generation tasks.

    Args:
        model_id (str, optional): The identifier for the specific model to use.
            Defaults to DEFAULT_MODEL_ID (nvidia/nemotron-nano-12b-v2-vl:free)
        max_retries (int, optional): Maximum number of retry attempts for failed API
            calls. Defaults to 12.
        temperature (float, optional): Sampling temperature (0.0-1.0). Defaults to 0.7

    Returns:
        ChatOpenRouter: Configured instance ready for text generation tasks

    Example:
        >>> llm = make_text_generation_model_open_router()  # Uses default model
        >>> response = llm.invoke('Write a greeting')
    """
    return ChatOpenRouter(
        model_name=model_id,
        max_retries=max_retries,
        temperature=temperature
    )


def call_llm(
    prompt: str,
    model_id: str = DEFAULT_MODEL_ID,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_retries: int = 12
) -> str:
    """
    Call an LLM with a prompt and return the response.
    
    This is a convenience function that creates an LLM instance and calls it with
    the provided prompt and optional system prompt.

    Args:
        prompt (str): The user prompt/query to send to the LLM
        model_id (str, optional): The model identifier. Defaults to DEFAULT_MODEL_ID 
            (nvidia/nemotron-nano-12b-v2-vl:free)
        system_prompt (str | None, optional): Optional system prompt to set context/behavior
        temperature (float, optional): Sampling temperature (0.0-1.0). Defaults to 0.7
        max_retries (int, optional): Maximum retry attempts. Defaults to 12

    Returns:
        str: The LLM's response text

    Example:
        >>> response = call_llm(
        ...     prompt="What is machine learning?",
        ...     system_prompt="You are a helpful AI assistant."
        ... )
        >>> print(response)
    """
    llm = ChatOpenRouter(
        model_name=model_id,
        max_retries=max_retries,
        temperature=temperature
    )
    
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))
    
    response = llm.invoke(messages)
    return response.content


def call_llm_with_model(
    llm: ChatOpenRouter,
    prompt: str,
    system_prompt: str | None = None
) -> str:
    """
    Call an already-configured LLM instance with a prompt.
    
    This function is useful when you want to reuse the same LLM configuration
    for multiple calls.

    Args:
        llm (ChatOpenRouter): Pre-configured LLM instance
        prompt (str): The user prompt/query to send to the LLM
        system_prompt (str | None, optional): Optional system prompt

    Returns:
        str: The LLM's response text

    Example:
        >>> llm = make_text_generation_model_open_router('anthropic/claude-3.5-sonnet')
        >>> response1 = call_llm_with_model(llm, "Hello!")
        >>> response2 = call_llm_with_model(llm, "How are you?")
    """
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))
    
    response = llm.invoke(messages)
    return response.content


def get_llm(model_id: str = DEFAULT_MODEL_ID, temperature: float = 0.7, max_retries: int = 12) -> ChatOpenRouter:
    """
    Get a pre-configured LLM instance ready to use.
    
    This is the simplest way to get an LLM instance with the default model.
    
    Args:
        model_id (str, optional): Model ID to use. Defaults to DEFAULT_MODEL_ID 
            (nvidia/nemotron-nano-12b-v2-vl:free)
        temperature (float, optional): Sampling temperature. Defaults to 0.7
        max_retries (int, optional): Maximum retries. Defaults to 12
    
    Returns:
        ChatOpenRouter: Ready-to-use LLM instance
    
    Example:
        >>> llm = get_llm()  # Uses default model
        >>> response = llm.invoke("Hello!")
    """
    return make_text_generation_model_open_router(model_id, max_retries, temperature)


# Environment variable loading utility
def load_env_vars():
    """
    Load environment variables from .env file in the project root.
    
    This function should be called before using any LLM functions if you're
    using a .env file to store your OPENROUTER_API_KEY.
    
    Example:
        >>> load_env_vars()
        >>> llm = make_text_generation_model_open_router('anthropic/claude-3.5-sonnet')
    """
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Go up two levels from anew/ to get to project root
    project_root = Path(__file__).parent.parent.resolve()
    dotenv_path = project_root / '.env'
    
    if dotenv_path.exists():
        load_dotenv(dotenv_path=str(dotenv_path))
    else:
        # Try looking in parent of project root (workspace level)
        dotenv_path = project_root.parent / '.env'
        if dotenv_path.exists():
            load_dotenv(dotenv_path=str(dotenv_path))

