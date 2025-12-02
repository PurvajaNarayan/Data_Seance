import nbformat as nbf
from nbclient import NotebookClient
import os
from core.config import AIGEN
import nbformat as nbf
from nbclient import NotebookClient
import os

def create_nb_w_context_wo_code(
    markdown: str,
):
    """
    
    todos:
        1. if images are present, you should make copies into the AIGEN, and replace with the AIGEN path to render it.
    """
    nb = nbf.v4.new_notebook()
    
    nb_path = AIGEN / 'ethics_report.ipynb'
    markdown_source = markdown

    # Create the cell objects
    markdown_cell = nbf.v4.new_markdown_cell(markdown_source)
    nb['cells'] = [markdown_cell]

    # Write the initial notebook to a file
    with open(nb_path, 'w') as f:
        nbf.write(nb, f)
        
    print(f"Created initial notebook: {str(nb_path)}")


def create_and_execute_notebook(filename="executed_notebook_with_output.ipynb"):
    # --- 1. Create the notebook structure ---
    nb = nbf.v4.new_notebook()

    markdown_source = """\
# Automatic Jupyter Notebook with Output

This notebook was created and executed programmatically. 
The output below was generated during execution."""

    code_source = """\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

print(f"Python version: {sys.version}")
print(f"Pandas version: {pd.__version__}")

# Generate some sample data and print a message
print("Generating sample data...")
data = {'Category': ['A', 'B', 'C', 'D'], 'Values': [10, 25, 15, 30]}
df = pd.DataFrame(data)

# Print the DataFrame and show a simple plot
print("\\nDataFrame contents:")
print(df)
# In a real notebook, the plot would render automatically in the output cell
# We can simulate this with a print if needed, but the cell will capture output anyway
"""

    # Create the cell objects
    markdown_cell = nbf.v4.new_markdown_cell(markdown_source)
    code_cell = nbf.v4.new_code_cell(code_source)
    nb['cells'] = [markdown_cell, code_cell]

    # Write the initial notebook to a file
    with open(filename, 'w') as f:
        nbf.write(nb, f)
        
    print(f"Created initial notebook: {os.path.abspath(filename)}")
    
    # --- 2. Execute the notebook and capture output ---
    print("Executing notebook...")
    try:
        # Load the notebook file
        with open(filename) as f:
            nb = nbf.read(f, as_version=4)
        
        # Configure the client (e.g., set a timeout for execution)
        # client = NotebookClient(nb, timeout=600, resources={'metadata': {'path': str(PROJECT_DIR)}})
        client = NotebookClient(nb, timeout=600, resources={'metadata': {'path': './'}})
        client.execute() #
        
        # --- 3. Save the executed notebook with output ---
        with open(filename, 'w') as f:
            nbf.write(nb, f)
            
        print(f"Successfully executed and saved notebook with output: {os.path.abspath(filename)}")

    except Exception as e:
        print(f"An error occurred during notebook execution: {e}")
        # Optionally save the notebook with error information
        with open(filename, 'w') as f:
            nbf.write(nb, f)
        print("Notebook saved with partial output/error details.")
        
def add_new_markdown_cell(markdown_text: str):
    """
    Append a new markdown cell with `markdown_text` to the bottom of the notebook and save it.
    If `filename` is None, uses AIGEN / 'ethics_report.ipynb'.
    """
    nb_path = (AIGEN / 'ethics_report.ipynb')
    nb_path_str = str(nb_path)

    if not os.path.exists(nb_path_str):
        # create a new notebook if it doesn't exist
        nb = nbf.v4.new_notebook()
        nb['cells'] = []
    else:
        with open(nb_path_str) as f:
            nb = nbf.read(f, as_version=4)

    md_cell = nbf.v4.new_markdown_cell(markdown_text)
    nb.setdefault('cells', []).append(md_cell)

    with open(nb_path_str, 'w') as f:
        nbf.write(nb, f)

    print(f"Appended markdown cell to {nb_path_str}")
