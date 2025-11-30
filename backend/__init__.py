"""
ANEW - AI Ethics Compliance Analysis System

A refactored, modular system for analyzing ML models and datasets for ethics
compliance violations using LLM-based evaluation with explainability methods.

Main modules:
- main: Primary entry point for ethics compliance analysis
- llm_call: LLM configuration and calling utilities
- llm_helpers: XAI methods and info getters (ICE, LIME, model/data descriptions)
- prompts: Ethics compliance system prompts

Author: User
Date: November 28, 2025
"""

from .main import (
    analyze_ethics,  # NEW: Unified function for all cases
    analyze_ethics_compliance,
    analyze_ethics_compliance_simple,
    save_analysis_report
)

from .llm_call import (
    call_llm,
    get_llm,
    load_env_vars,
    make_text_generation_model_open_router,
    DEFAULT_MODEL_ID,
    ALTERNATIVE_MODELS
)

from .llm_helpers import (
    # XAI methods
    ceteris_paribus_bytes_multi,
    lime_explain_instances,
    lime_explain_text_summary,
    
    # Info getters
    describe_pandas_dataset,
    describe_sklearn_model,
    
    # Convenience
    prepare_ethics_context
)

from .prompts import (
    get_prompt,
    ETHICS_COMPLIANCE_DETAILED,
    ETHICS_COMPLIANCE_CONCISE,
    DETAILED_PROMPT,
    CONCISE_PROMPT,
    DEFAULT_PROMPT
)

__version__ = "1.0.0"

__all__ = [
    # Main functions
    "analyze_ethics",  # NEW: Unified smart function
    "analyze_ethics_compliance",
    "analyze_ethics_compliance_simple",
    "save_analysis_report",
    
    # LLM functions
    "call_llm",
    "get_llm",
    "load_env_vars",
    "make_text_generation_model_open_router",
    "DEFAULT_MODEL_ID",
    "ALTERNATIVE_MODELS",
    
    # XAI & helpers
    "ceteris_paribus_bytes_multi",
    "lime_explain_instances",
    "lime_explain_text_summary",
    "describe_pandas_dataset",
    "describe_sklearn_model",
    "prepare_ethics_context",
    
    # Prompts
    "get_prompt",
    "ETHICS_COMPLIANCE_DETAILED",
    "ETHICS_COMPLIANCE_CONCISE",
    "DETAILED_PROMPT",
    "CONCISE_PROMPT",
    "DEFAULT_PROMPT",
]

