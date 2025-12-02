
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
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import LanguageModelLike
from pprint import pprint

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


async def run_model(
    llm: LanguageModelLike,
    system_prompt: SystemMessage,
    user_prompt: HumanMessage
) -> dict:
    """
    Review and refine
    """
    messages = [system_prompt, user_prompt]

    #printing input messages\
    
    print("getting answer ...\n")

    # --- 1) Bind extra options for max introspection ---

    llm_debug = llm.bind(
        extra_body={
            # Ask OpenRouter to include visible reasoning, if the model supports it.
            "include_reasoning": True,
            # Optional: some models use a reasoning block configuration:
            # "reasoning": {"effort": "medium", "exclude": False},
        },
        logprobs=True,     # request logprobs if supported
        top_logprobs=3,
    )

    # --- 2) Async streaming: smallest observable units as they arrive ---

    # astream(...) yields ChatMessage-like chunks as they come in.
    stream = llm_debug.astream(messages, stream_usage=True)

    first_chunk = True
    full_msg = None
    final_usage = {}
    all_chunks = []

    async for chunk in stream:
        # Keep them all to reconstruct full message later
        all_chunks.append(chunk)

        if first_chunk:
            # First chunk seeds the accumulated AIMessage
            full_msg = chunk
            first_chunk = False

        else:
            # LangChain ChatMessageChunks support + to accumulate
            full_msg += chunk

        # --- Atomic-level output as it’s produced ---

        # chunk.content is often the "delta" text; print it as soon as we see it
        if getattr(chunk, "content", None):
            print(chunk.content, end="", flush=True)

        # Usage metadata can appear in special final chunk(s)
        if getattr(chunk, "usage_metadata", None):
            final_usage = chunk.usage_metadata

    # Safety: if nothing came back
    if full_msg is None:
        print("\n[No chunks received from model]")
        return

    # print("\n\n======= FINAL MESSAGE CONTENT =======\n")
    # print(full_msg.content)

    # --- 3) Token usage summary ---

    print("\n======= TOKEN USAGE (usage_metadata) =======")
    if final_usage:
        pprint(final_usage)
    else:
        print("No usage_metadata reported by this provider/model.")

    # --- 4) Reasoning / thinking tokens (if exposed) ---

    # OpenRouter / some backends store reasoning in additional_kwargs
    reasoning = (full_msg.additional_kwargs or {}).get("reasoning")
    if reasoning:
        print("\n======= REASONING / THINKING CONTENT =======\n")
        print(reasoning)

    # Some backends tuck extra info into response_metadata
    reasoning_meta = (full_msg.response_metadata or {}).get("reasoning_details")
    if reasoning_meta:
        print("\n======= RAW REASONING METADATA =======")
        pprint(reasoning_meta)

    # --- 5) Logprobs per token (if available) ---

    logprobs = (full_msg.response_metadata or {}).get("logprobs")
    if logprobs:
        print("\n======= LOGPROBS =======")
        pprint(logprobs)

    # --- 6) Human-friendly LangChain view ---
    return {
        'full_message_content' : full_msg.content,
        'usage' : final_usage,
        'reasoning' : reasoning,
        'reasoning' : reasoning_meta,
        'logprobs' : logprobs
    }