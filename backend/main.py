"""
Main Ethics Compliance Analysis Entry Point

This module provides the primary function for running ethics compliance analysis
on ML models and datasets using LLM-based evaluation.

Author: User
Date: November 28, 2025
"""

from pathlib import Path
from typing import Any, Optional, Mapping
import base64

import pandas as pd

from .prompts import get_prompt
from .llm_call import call_llm, get_llm, load_env_vars
from .llm_helpers import (
    describe_sklearn_model,
    describe_pandas_dataset,
    ceteris_paribus_bytes_multi,
    lime_explain_instances,
    lime_explain_text_summary,
    prepare_ethics_context
)


# Default guidelines path
DEFAULT_GUIDELINES_PATH = Path(__file__).parent.parent / 'assets' / 'guidelines' / 'guidelines_shorter.txt'


def analyze_ethics(
    data: Optional[Any] = None,
    model: Optional[Any] = None,
    *,
    data_train: Optional[pd.DataFrame] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    project_description: str = "ML project",
    guidelines_path: Optional[Path] = None,
    guidelines_text: Optional[str] = None,
    prompt_style: str = "detailed",
    include_ice: bool = True,
    include_lime: bool = False,
    num_ice_datapoints: int = 3,
    ice_grid_points: int = 50,
    num_lime_instances: int = 3,
    num_lime_features: int = 10,
    model_id: Optional[str] = None,
    temperature: float = 0.7,
    return_context: bool = False
) -> dict[str, Any]:
    """
    Unified ethics compliance analysis - handles datasets (CSV/DataFrame) with or without models.
    
    This intelligent function automatically determines what type of analysis to perform:
    
    1. **Dataset Only** (no model):
       - Analyzes data for ethical issues (PII, bias, protected attributes)
       - Fast, no model training required
    
    2. **Dataset + Model**:
       - Full analysis with XAI methods (ICE plots, LIME)
       - Analyzes both data and model behavior
    
    3. **Model Only** (data required for analysis):
       - Analyzes model with provided test data
    
    Args:
        data: Input data - accepts:
            - Path to CSV file (str or Path)
            - Pandas DataFrame
            - None (if only analyzing pre-trained model with data_train)
        model: Optional trained sklearn model. If None, performs dataset-only analysis
        data_train: Optional training data (required if include_lime=True)
        metadata: Optional dict mapping column names to descriptions
        project_description: Brief description of the project
        guidelines_path: Path to guidelines file. If None, uses default
        guidelines_text: Direct guidelines text (overrides guidelines_path)
        prompt_style: 'detailed' or 'concise' prompt style
        include_ice: Whether to generate ICE plots (requires model). Default: True
        include_lime: Whether to generate LIME explanations (requires model). Default: False
        num_ice_datapoints: Number of instances for ICE plots. Default: 3
        ice_grid_points: Grid resolution for ICE plots. Default: 50
        num_lime_instances: Number of instances for LIME. Default: 3
        num_lime_features: Number of features per LIME explanation. Default: 10
        model_id: LLM model ID (uses default if None)
        temperature: LLM sampling temperature. Default: 0.7
        return_context: If True, returns full context dict. Default: False
    
    Returns:
        dict containing analysis results appropriate to the input type
    
    Examples:
        >>> # Case 1: Analyze CSV dataset only (no model)
        >>> result = analyze_ethics(data='data.csv')
        
        >>> # Case 2: Analyze DataFrame only
        >>> result = analyze_ethics(data=my_dataframe)
        
        >>> # Case 3: Analyze dataset + model
        >>> result = analyze_ethics(
        ...     data=X_test,
        ...     model=trained_model,
        ...     data_train=X_train,
        ...     include_lime=True
        ... )
        
        >>> # Case 4: Analyze model with data
        >>> result = analyze_ethics(
        ...     data=X_test,
        ...     model=trained_model
        ... )
    
    Raises:
        ValueError: If neither data nor model is provided
        FileNotFoundError: If CSV path doesn't exist
    """
    # Load environment variables
    load_env_vars()
    
    # === 1. Validate and load data ===
    if data is None and model is None:
        raise ValueError(
            "Must provide at least 'data' or 'model'. "
            "Recommended: provide both for comprehensive analysis."
        )
    
    # Handle different data input types
    if data is not None:
        if isinstance(data, (str, Path)):
            # Load CSV file
            data_path = Path(data)
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            print(f"📂 Loading data from: {data_path}")
            if str(data_path).endswith('.csv'):
                df = pd.read_csv(data_path)
            elif str(data_path).endswith('.pkl'):
                import pickle
                with open(data_path, 'rb') as f:
                    loaded = pickle.load(f)
                    # Handle dict format like boston_housing_dataset.pkl
                    if isinstance(loaded, dict) and 'data' in loaded:
                        df = loaded['data']
                        if metadata is None and 'metadata' in loaded:
                            metadata = loaded['metadata']
                    else:
                        df = loaded
            else:
                raise ValueError(f"Unsupported file format: {data_path}. Use .csv or .pkl")
            
            print(f"   ✓ Loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise TypeError(
                f"'data' must be a file path (str/Path) or pandas DataFrame, "
                f"got {type(data)}"
            )
    else:
        df = None
    
    # === 2. Determine analysis type ===
    if model is None:
        # Dataset-only analysis
        print("\n🔍 Analysis mode: DATASET ONLY (no model)")
        print("   Checking for data ethics issues...")
        
        if df is None:
            raise ValueError("Cannot perform dataset-only analysis without data")
        
        return _analyze_dataset_only(
            df,
            metadata=metadata,
            project_description=project_description,
            guidelines_path=guidelines_path,
            guidelines_text=guidelines_text,
            prompt_style=prompt_style,
            model_id=model_id,
            temperature=temperature
        )
    
    else:
        # Model + Dataset analysis (full XAI)
        print("\n🔍 Analysis mode: MODEL + DATASET")
        print("   Performing comprehensive analysis with XAI methods...")
        
        if df is None:
            raise ValueError(
                "Model analysis requires test data. "
                "Provide 'data' parameter with test dataset."
            )
        
        return analyze_ethics_compliance(
            model=model,
            data=df,
            data_train=data_train,
            metadata=metadata,
            project_description=project_description,
            guidelines_path=guidelines_path,
            guidelines_text=guidelines_text,
            prompt_style=prompt_style,
            include_ice=include_ice,
            include_lime=include_lime,
            num_ice_datapoints=num_ice_datapoints,
            ice_grid_points=ice_grid_points,
            num_lime_instances=num_lime_instances,
            num_lime_features=num_lime_features,
            model_id=model_id,
            temperature=temperature,
            return_context=return_context
        )


def _analyze_dataset_only(
    data: pd.DataFrame,
    metadata: Optional[Mapping[str, Any]],
    project_description: str,
    guidelines_path: Optional[Path],
    guidelines_text: Optional[str],
    prompt_style: str,
    model_id: Optional[str],
    temperature: float
) -> dict[str, Any]:
    """
    Internal function for dataset-only analysis.
    """
    # Load guidelines
    if guidelines_text is None:
        if guidelines_path is None:
            guidelines_path = DEFAULT_GUIDELINES_PATH
        
        if not Path(guidelines_path).exists():
            raise FileNotFoundError(f"Guidelines file not found: {guidelines_path}")
        
        with open(guidelines_path, 'r') as f:
            guidelines = f.read()
    else:
        guidelines = guidelines_text
    
    # Generate data description
    data_desc = describe_pandas_dataset(data, metadata=metadata)
    
    # Build system and user prompts
    system_prompt = get_prompt(style=prompt_style, guidelines=guidelines)
    
    user_prompt_parts = [
        "# Dataset Ethics Analysis (No Model)",
        "",
        f"**Project Description:** {project_description}",
        "",
        "# Dataset Information",
        data_desc,
        "",
        "# Analysis Task",
        "",
        "Analyze this dataset for potential ethical compliance issues:",
        "",
        "1. **Protected Attributes**: Identify features representing or proxying protected characteristics",
        "2. **Data Fairness**: Assess for bias or potential unfair outcomes",
        "3. **Privacy & Data Governance**: Identify privacy concerns (PII, sensitive data)",
        "4. **Transparency**: Evaluate documentation sufficiency",
        "5. **Missing Information**: Note what's needed for complete assessment",
        "",
        "**Note**: This is DATASET-ONLY analysis (no trained model). Focus on data quality and ethical issues.",
        "",
        "Provide specific evidence and clear recommendations."
    ]
    
    if metadata:
        user_prompt_parts.extend([
            "",
            "# Column Metadata",
            *[f"- {col}: {desc}" for col, desc in metadata.items()]
        ])
    
    user_prompt = "\n".join(user_prompt_parts)
    
    # Call LLM
    llm_kwargs = {'temperature': temperature}
    if model_id:
        llm_kwargs['model_id'] = model_id
    
    llm_response = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        **llm_kwargs
    )
    
    return {
        'llm_response': llm_response,
        'data_description': data_desc,
        'guidelines': guidelines,
        'project_description': project_description,
        'analysis_type': 'dataset_only'
    }


def analyze_ethics_compliance(
    model: Any,
    data: pd.DataFrame,
    *,
    data_train: Optional[pd.DataFrame] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    project_description: str = "ML model project",
    guidelines_path: Optional[Path] = None,
    guidelines_text: Optional[str] = None,
    prompt_style: str = "detailed",
    include_ice: bool = True,
    include_lime: bool = False,
    num_ice_datapoints: int = 3,
    ice_grid_points: int = 50,
    num_lime_instances: int = 3,
    num_lime_features: int = 10,
    model_id: Optional[str] = None,
    temperature: float = 0.7,
    return_context: bool = False
) -> dict[str, Any]:
    """
    Run complete ethics compliance analysis on a model and dataset.
    
    This is the main entry point for the ethics compliance system. It:
    1. Prepares model and data descriptions
    2. Generates explainability visualizations (ICE plots, LIME)
    3. Loads ethics guidelines
    4. Calls LLM with detailed prompt
    5. Returns comprehensive analysis results
    
    Args:
        model: Fitted sklearn model to analyze
        data: Pandas DataFrame (typically test/validation data)
        data_train: Optional training data (required if include_lime=True)
        metadata: Optional dict mapping column names to descriptions
        project_description: Brief description of the project/model purpose
        guidelines_path: Path to guidelines file. If None, uses default
        guidelines_text: Direct guidelines text (overrides guidelines_path)
        prompt_style: 'detailed' or 'concise' prompt style
        include_ice: Whether to generate ICE plots. Default: True
        include_lime: Whether to generate LIME explanations. Default: False
        num_ice_datapoints: Number of instances for ICE plots. Default: 3
        ice_grid_points: Grid resolution for ICE plots. Default: 50
        num_lime_instances: Number of instances for LIME. Default: 3
        num_lime_features: Number of features per LIME explanation. Default: 10
        model_id: LLM model ID (uses default if None)
        temperature: LLM sampling temperature. Default: 0.7
        return_context: If True, returns full context dict. Default: False
    
    Returns:
        dict containing:
            - 'llm_response': The LLM's ethics compliance analysis
            - 'model_description': Text description of the model
            - 'data_description': Text description of the dataset
            - 'guidelines': The guidelines used for evaluation
            - 'ice_plots': (if include_ice) Dict of ICE plot bytes
            - 'lime_explanations': (if include_lime) LIME explanation data
            - 'context': (if return_context) Full context sent to LLM
    
    Example:
        >>> from sklearn.ensemble import RandomForestRegressor
        >>> from sklearn.model_selection import train_test_split
        >>> 
        >>> # Load and prepare data
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y)
        >>> model = RandomForestRegressor().fit(X_train, y_train)
        >>> 
        >>> # Run analysis
        >>> result = analyze_ethics_compliance(
        ...     model, 
        ...     X_test,
        ...     data_train=X_train,
        ...     metadata={'feature1': 'Description of feature1'},
        ...     project_description="Housing price prediction model",
        ...     include_lime=True
        ... )
        >>> 
        >>> print(result['llm_response'])
    
    Raises:
        ValueError: If include_lime=True but data_train not provided
        FileNotFoundError: If guidelines file not found
    """
    # Load environment variables
    load_env_vars()
    
    # === 1. Load or use guidelines ===
    if guidelines_text is None:
        if guidelines_path is None:
            guidelines_path = DEFAULT_GUIDELINES_PATH
        
        if not Path(guidelines_path).exists():
            raise FileNotFoundError(
                f"Guidelines file not found: {guidelines_path}\n"
                f"Please provide guidelines_text or valid guidelines_path"
            )
        
        with open(guidelines_path, 'r') as f:
            guidelines = f.read()
    else:
        guidelines = guidelines_text
    
    # === 2. Generate model and data descriptions ===
    model_desc = describe_sklearn_model(model)
    data_desc = describe_pandas_dataset(data, metadata=metadata)
    
    # === 3. Generate explainability results ===
    ice_plots = None
    lime_explanations = None
    lime_text = None
    
    if include_ice:
        ice_plots = ceteris_paribus_bytes_multi(
            model, 
            data, 
            num_datapoints=num_ice_datapoints,
            grid_points=ice_grid_points
        )
    
    if include_lime:
        if data_train is None:
            raise ValueError(
                "data_train is required when include_lime=True. "
                "Provide training data for LIME explainer."
            )
        
        try:
            lime_explanations = lime_explain_instances(
                model,
                data,
                data_train,
                num_instances=num_lime_instances,
                num_features=num_lime_features
            )
            lime_text = lime_explain_text_summary(
                model,
                data,
                data_train,
                num_instances=num_lime_instances,
                num_features=num_lime_features
            )
        except ImportError:
            lime_text = "[LIME not available - install with: pip install lime]"
    
    # === 4. Build LLM prompt ===
    system_prompt = get_prompt(style=prompt_style, guidelines=guidelines)
    
    # Build user prompt content
    user_prompt_parts = [
        "# Project Context",
        f"**Project Description:** {project_description}",
        "",
        "# Data Information",
        data_desc,
        "",
        "# Model Information",
        model_desc,
        ""
    ]
    
    if lime_text:
        user_prompt_parts.extend([
            "# LIME Explanations (Instance-level)",
            lime_text,
            ""
        ])
    
    if ice_plots:
        user_prompt_parts.extend([
            f"# ICE/Ceteris Paribus Plots",
            f"Generated ICE plots for {len(ice_plots)} features showing how predictions change as features vary.",
            f"Features analyzed: {', '.join(ice_plots.keys())}",
            "",
            "**Note:** Visual ICE plots are attached as images (see below).",
            ""
        ])
    
    user_prompt_parts.extend([
        "# Your Task",
        "Based on the project context, data information, model details, and explainability results provided above, ",
        "analyze this project for ethics compliance violations according to the guidelines.",
        "",
        "Identify any violations or concerns, provide specific evidence, and explain your reasoning clearly."
    ])
    
    user_prompt = "\n".join(user_prompt_parts)
    
    # === 5. Call LLM ===
    llm_kwargs = {'temperature': temperature}
    if model_id:
        llm_kwargs['model_id'] = model_id
    
    llm_response = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        **llm_kwargs
    )
    
    # === 6. Prepare result ===
    result = {
        'llm_response': llm_response,
        'model_description': model_desc,
        'data_description': data_desc,
        'guidelines': guidelines,
        'project_description': project_description,
    }
    
    if ice_plots:
        result['ice_plots'] = ice_plots
    
    if lime_explanations:
        result['lime_explanations'] = lime_explanations
    
    if return_context:
        result['context'] = {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
        }
    
    return result


def analyze_ethics_compliance_simple(
    model: Any,
    data: pd.DataFrame,
    data_train: Optional[pd.DataFrame] = None,
    project_description: str = "ML model project"
) -> str:
    """
    Simplified version that returns just the LLM's text response.
    
    Args:
        model: Fitted sklearn model
        data: Test/validation DataFrame
        data_train: Optional training data for LIME
        project_description: Brief project description
    
    Returns:
        str: The LLM's ethics compliance analysis
    
    Example:
        >>> analysis = analyze_ethics_compliance_simple(model, X_test)
        >>> print(analysis)
    """
    result = analyze_ethics_compliance(
        model,
        data,
        data_train=data_train,
        project_description=project_description,
        include_lime=(data_train is not None)
    )
    return result['llm_response']


def save_analysis_report(
    result: dict[str, Any],
    output_dir: Path,
    save_ice_plots: bool = True
) -> None:
    """
    Save analysis results to files.
    
    Args:
        result: Result dict from analyze_ethics_compliance()
        output_dir: Directory to save files
        save_ice_plots: Whether to save ICE plot images
    
    Example:
        >>> result = analyze_ethics_compliance(model, data)
        >>> save_analysis_report(result, Path('./reports'))
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main report
    report_path = output_dir / 'ethics_compliance_report.txt'
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("ETHICS COMPLIANCE ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Project: {result.get('project_description', 'N/A')}\n\n")
        f.write("=" * 80 + "\n")
        f.write("LLM ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['llm_response'])
        f.write("\n\n")
        f.write("=" * 80 + "\n")
        f.write("MODEL DESCRIPTION\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['model_description'])
        f.write("\n\n")
        f.write("=" * 80 + "\n")
        f.write("DATA DESCRIPTION\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['data_description'])
    
    print(f"✓ Report saved to: {report_path}")
    
    # Save ICE plots
    if save_ice_plots and 'ice_plots' in result:
        ice_dir = output_dir / 'ice_plots'
        ice_dir.mkdir(exist_ok=True)
        
        for feature, (plot_bytes, _) in result['ice_plots'].items():
            plot_path = ice_dir / f'ice_{feature}.png'
            with open(plot_path, 'wb') as f:
                f.write(plot_bytes)
        
        print(f"✓ ICE plots saved to: {ice_dir}")
    
    # Save LIME explanations
    if 'lime_explanations' in result:
        lime_dir = output_dir / 'lime_explanations'
        lime_dir.mkdir(exist_ok=True)
        
        for idx, exp_data in result['lime_explanations'].items():
            # Save text
            text_path = lime_dir / f'lime_instance_{idx}.txt'
            with open(text_path, 'w') as f:
                f.write(exp_data['explanation_text'])
            
            # Save plot
            plot_path = lime_dir / f'lime_instance_{idx}.png'
            with open(plot_path, 'wb') as f:
                f.write(exp_data['plot_bytes'])
        
        print(f"✓ LIME explanations saved to: {lime_dir}")


# Example usage
if __name__ == "__main__":
    """
    Example usage of the ethics compliance analysis system.
    """
    print("Ethics Compliance Analysis System")
    print("=" * 50)
    print("\nThis is the main module. Import and use the functions:")
    print("\nExample:")
    print("""
    from anew.main import analyze_ethics_compliance
    from sklearn.ensemble import RandomForestRegressor
    import pandas as pd
    
    # Train your model
    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    
    # Run ethics analysis
    result = analyze_ethics_compliance(
        model=model,
        data=X_test,
        data_train=X_train,
        metadata={'col1': 'description'},
        project_description="Housing price prediction",
        include_lime=True
    )
    
    # View results
    print(result['llm_response'])
    
    # Or use the simple version
    from anew.main import analyze_ethics_compliance_simple
    analysis = analyze_ethics_compliance_simple(model, X_test)
    print(analysis)
    """)

