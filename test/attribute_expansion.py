

import sys
from pathlib import Path
import pickle
import base64

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Add the parent directory to the path so we can import backend
project_dir = Path(__file__).parent.parent

# Add the parent directory to the path so we can import backend
sys.path.insert(0, str(project_dir))

from backend.main import analyze_ethics, elaborate_attribute, plot_interp_attr
from backend.api import parse_llm_to_structured_issues

# Default guidelines path
DEFAULT_GUIDELINES_PATH = project_dir / 'assets' / 'guidelines' / 'guidelines_shorter.txt'

def main():
    
    guidelines_path = DEFAULT_GUIDELINES_PATH

    if not Path(guidelines_path).exists():
        raise FileNotFoundError(
            f"Guidelines file not found: {guidelines_path}\n"
            f"Please provide guidelines_text or valid guidelines_path"
        )

    with open(guidelines_path, 'r') as f:
        guidelines = f.read()
                

    print("=" * 80)
    print("ETHICS COMPLIANCE ANALYSIS - Boston Housing")
    print("=" * 80)
    print()

    with open(project_dir / 'test' / 'boston_housing_dataset.pkl', 'rb') as rf:
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

    print("🔍 Starting first analysis...")
    print("-" * 80)
    print()

    # Run the analysis (dataset only, no model)
    result = analyze_ethics(
        data=X,
        data_train=X_train,
        metadata=metadata,
        project_description='The project is to do housing price prediction',
        prompt_style="structured",  # Use detailed analysis
        model=model,
        temperature=0.7
    )

    # Extract the LLM response
    llm_response = result['llm_response']

    print("\n###\tRESPONSE\t###\n")
    
    print(llm_response)
    print()
    
    # Parse into structured format
    structured_response = parse_llm_to_structured_issues(
        llm_response,
        "temp.py",
        'The project is to do housing price prediction'
    )

    print(f"✅ Analysis complete. Found {len(structured_response['issues'])} issues.\n")

    attributes = structured_response['full_analysis'].split('---')
    
    print("\n🔍 Starting attribute specific analysis for the below attribute...\n")
    
    attr = attributes[0]
    print(attr)
    print("-" * 80)
    print()
    
    attr_desc = elaborate_attribute(
        proj_desc=result['project_description'],
        model_desc=result['model_description'],
        data_desc=result['model_description'],
        attr_response=attributes[0],
        guidelines=guidelines,
        temperature=0.7,
        model_id=None
    )
    
    print("\n###\tATTRIBUTE SPECIFIC EXPLANATION\t###\n")
    print(attr_desc)
    print("-" * 80)
    print()
    
    print("\n🔍 Starting attribute specific Explainability plot anaylsis for the attribute...\n")
    print("-" * 80)
    print()
    
    ice_context = dict()
    for feature_name, (bytes_image, ice_df) in result['ice_plots'].items():
        image_data = image_data = base64.b64encode(bytes_image).decode("utf-8")
        ice_context[feature_name]={
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_data}"},
            "image description": f"Ceteris Paribus (ICE) explainability plots using multiple datapoints for the '{feature_name}' feature"
        }

    plot_desc = plot_interp_attr(
        proj_desc=result['project_description'],
        model_desc=result['model_description'],
        data_desc=result['model_description'],
        attr_response=attributes[0],
        guidelines=guidelines,
        temperature=0.7,
        model_id="google/gemini-2.0-flash-exp:free",
        attr_ice_context=ice_context['B']
    )

    print("\n###\tPLOT EXPLANATION\t###\n")
    print(plot_desc)
    
if __name__=='__main__':
    main()