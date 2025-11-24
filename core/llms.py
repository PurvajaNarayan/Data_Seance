
"""
OpenRouter API Integration Module

This module provides a wrapper for the OpenRouter API, allowing seamless integration
with various language models through LangChain. It handles API key management and
provides a clean interface for text generation tasks.

Author: User
Date: October 23, 2025
"""

import sys
import os
from langchain_openai import ChatOpenAI
from langchain_core.utils.utils import secret_from_env
from pydantic import SecretStr, Field
from langchain_core.messages import HumanMessage
import base64
from IPython.display import display as dis
from IPython.display import Image as im

# from dotenv import load_dotenv
# from pathlib import Path

# # Configuration for environment variables
# PROJECT_DIR = Path(__file__).parent.parent.parent.resolve()
# ENV_DIR = PROJECT_DIR / '.env'
# load_dotenv(ENV_DIR)  # Load environment variables from .env file

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
    model_id: str,
    max_retries: int = 12
) -> ChatOpenRouter:
    """
    Create and configure a text generation model using OpenRouter's inference endpoint.
    
    This factory function initializes a ChatOpenRouter instance with the specified
    model ID and retry settings. It provides a convenient way to create language
    model instances for text generation tasks.

    Args:
        model_id (str): The identifier for the specific model to use
            (e.g., 'z-ai/glm-4.5-air:free')
        max_retries (int, optional): Maximum number of retry attempts for failed API
            calls. Defaults to 12.

    Returns:
        ChatOpenRouter: Configured instance ready for text generation tasks

    Example:
        >>> llm = make_text_generation_model_open_router('z-ai/glm-4.5-air:free')
        >>> response = llm.invoke('Write a greeting')
    """
    return ChatOpenRouter(
        model_name=model_id,
        max_retries=max_retries
    )
