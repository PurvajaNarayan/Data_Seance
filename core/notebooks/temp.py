import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))

print(str(Path(__file__).parent.parent.parent.resolve()))

from core.config import load_env_vars

load_env_vars()

from core.config import PROJECT_DIR

from core.backend.llms import make_text_generation_model_open_router
import base64
import pprint
from langchain_core.messages import HumanMessage, SystemMessage
from IPython.display import Image as im
from IPython.display import display as dis
from core.backend.sklearn_model_info import describe_sklearn_model
from core.backend.pd_df_info import describe_pandas_dataset
from core.utils import pretty_messages_pretty
import asyncio
from pprint import pprint
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from core.backend.xai import ceteris_paribus_bytes_multi
from core.utils import load_and_show_png_bytes

import sys
from pathlib import Path
from core.config import DATA_DIR
import pickle

async def run_model():
    with open(DATA_DIR / 'boston_housing_dataset.pkl', 'rb') as rf:
        data_dict = pickle.load(rf)


    data = data_dict['data']
    metadata = data_dict['metadata']

    # === Separate features and target ===
    X = data.drop(columns=['MEDV'])
    y = data['MEDV']

    # === Train/test split ===
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # === Fit a baseline model ===
    model = RandomForestRegressor(random_state=42, n_estimators=200)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"R²: {r2_score(y_test, y_pred):.3f}")
    print(f"MAE: {mean_absolute_error(y_test, y_pred):.3f}")

    cp_bytes = ceteris_paribus_bytes_multi(model, X_test, num_datapoints=3, grid_points=100)

    # Initialize the language model with a specific model ID
    llm = make_text_generation_model_open_router( # get vision language models here : https://openrouter.ai/models?fmt=cards&input_modalities=image&max_price=0
        # model_id='z-ai/glm-4.5-air:free'
        # model_id='google/gemini-2.0-flash-exp:free'
        # model_id='nvidia/nemotron-nano-12b-v2-vl:free'
        model_id='qwen/qwen2.5-vl-32b-instruct:free'
        # model_id='mistralai/mistral-small-3.1-24b-instruct:free'
    )
    
    image_bytes = cp_bytes['B'][0]
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    
    model_info = describe_sklearn_model(model)
    data_info = describe_pandas_dataset(data, metadata=metadata)
    
    system_prompt_path = PROJECT_DIR / 'assets'/ 'SP_ethics_compliance.txt'
    guidelines_path =  PROJECT_DIR / 'assets'/ 'guidelines' / 'guidelines_shorter.txt'
    with open(system_prompt_path) as rf:
        system_prompt_template = rf.read()
    with open(guidelines_path) as rf:
        guidelines = rf.read()
        
        
    system_prompt_str = system_prompt_template.format(guidelines=guidelines)
    
    system_prompt = SystemMessage(content=system_prompt_str)
    
    user_prompt = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "project details :The project is to do housing price prediction"
            },
            {
                "type": "text",
                "text": f'Data info : {pprint.pformat(metadata)}'
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"},
                "image description": "explainability plot for a feature of the dataset"
            },
            {
                "type": "text",
                "text": "Given the project context, and the explainability results, Are any company guidelines violated?"
            },
        ]
    )
    
    messages = [system_prompt, user_prompt]
    
    print(pretty_messages_pretty(messages))

    messages = [system_prompt, user_prompt]

    print(pretty_messages_pretty(messages))
    print("getting answer with full transparency (async)...\n")

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

    print("=== Streaming chunks (atomic units) ===\n")

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

    print("\n\n======= FINAL MESSAGE CONTENT =======\n")
    print(full_msg.content)

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

    print("\n======= pretty_print() (LangChain view) =======")
    full_msg.pretty_print()

# Actually run the async function (in a script)
if __name__ == "__main__":
    asyncio.run(run_model())

