
from core.backend.xai import ceteris_paribus_bytes_multi
from core.utils import load_and_show_png_bytes
import pandas as pd
from core.config import PROJECT_DIR
from core.backend.llms import make_text_generation_model_open_router
import base64
import pprint
from langchain_core.messages import HumanMessage, SystemMessage
from IPython.display import Image as im
from IPython.display import display as dis
from core.utils import describe_sklearn_model, describe_pandas_dataset, pretty_messages_pretty
from core.backend.llms import run_model
import asyncio
import pprint
from core.frontend.nb_maker import create_nb_w_context_wo_code
from core.config import load_env_vars

async def v1(
    project_desc: str,
    model,
    data: pd.DataFrame,
    metadata
):
    load_env_vars()
    # model_info = describe_sklearn_model(model)
    # data_info = describe_pandas_dataset(data, metadata=metadata)
    
    X = data.drop(columns=['MEDV'])
    x_sample = X.sample(20)      
    
    cp_bytes = ceteris_paribus_bytes_multi(model, x_sample, num_datapoints=5, grid_points=100)
    
    system_prompt_path = PROJECT_DIR / 'assets'/ 'SP_ethics_compliance.txt'
    guidelines_path =  PROJECT_DIR / 'assets'/ 'guidelines' / 'guidelines_shorter.txt'
    with open(system_prompt_path) as rf:
        system_prompt_template = rf.read()
    with open(guidelines_path) as rf:
        guidelines = rf.read()

    # Initialize the language model with a specific model ID
    llm = make_text_generation_model_open_router( # get vision language models here : https://openrouter.ai/models?fmt=cards&input_modalities=image&max_price=0
        # model_id='z-ai/glm-4.5-air:free'
        # model_id='google/gemini-2.0-flash-exp:free'
        model_id='nvidia/nemotron-nano-12b-v2-vl:free'
        # model_id='google/gemma-3-27b-it:free'
        # model_id='mistralai/mistral-small-3.1-24b-instruct:free'
    )
    
    image_bytes = cp_bytes['B'][0]
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    
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
        
    response = await run_model(llm=llm, system_prompt=system_prompt, user_prompt=user_prompt)
    response_markdown = f"# AI generated Response\n\n{response['full_message_content']}\n___"
    create_nb_w_context_wo_code(markdown=response_markdown)
