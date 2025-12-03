"""
LLM Helper Functions for Ethics Compliance Analysis

This module provides utilities for preparing data science models and datasets
for LLM-based ethics compliance analysis. It includes:
1. XAI (Explainable AI) methods - ICE plots and LIME for model explainability
2. Info Getters - Convert pandas DataFrames and sklearn models to LLM-readable text

"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional
import inspect
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import sklearn
except ImportError:
    sklearn = None

try:
    import lime
    import lime.lime_tabular
except ImportError:
    lime = None


# =============================================================================
# XAI (EXPLAINABLE AI) METHODS
# =============================================================================

def ceteris_paribus_bytes_multi(
    model, 
    X: pd.DataFrame, 
    num_datapoints: int = 1, 
    grid_points: int = 50
) -> dict[str, tuple[bytes, pd.DataFrame]]:
    """
    Build Ceteris Paribus (ICE) plots for multiple datapoints and return images as PNG bytes.
    
    This function generates Individual Conditional Expectation (ICE) plots showing how
    predictions change as a single feature varies while all other features remain constant.
    Useful for understanding model behavior and identifying potential biases.

    Args:
        model: Fitted estimator with predict() and optionally predict_proba()
        X (pd.DataFrame): Data defining grids and base rows
        num_datapoints (int): Number of rows (taken from the top of X). Default: 1
        grid_points (int): Grid resolution per feature. Default: 50

    Returns:
        dict[str, tuple[bytes, pd.DataFrame]]:
            Dictionary mapping feature names to (png_bytes, data_df)
            where data_df has columns: ['row_id', 'feature_value', 'prediction']

    Example:
        >>> from sklearn.ensemble import RandomForestRegressor
        >>> model = RandomForestRegressor().fit(X_train, y_train)
        >>> ice_plots = ceteris_paribus_bytes_multi(model, X_test, num_datapoints=3)
        >>> feature_plot_bytes = ice_plots['age'][0]  # Get PNG bytes for 'age' feature
    """
    num_datapoints = max(1, min(num_datapoints, len(X)))
    X_targets = X.iloc[:num_datapoints].copy()
    out = {}

    # Binary probability if available
    proba_fn = getattr(model, "predict_proba", None)
    is_binary = False
    if proba_fn is not None:
        classes_ = getattr(model, "classes_", None)
        is_binary = classes_ is not None and len(classes_) == 2

    for feature in X.columns:
        if not np.issubdtype(X[feature].dtype, np.number):
            continue

        grid = np.linspace(X[feature].min(), X[feature].max(), grid_points)

        base = np.repeat(X_targets.values, grid_points, axis=0)
        base_df = pd.DataFrame(base, columns=X.columns)
        base_df[feature] = np.tile(grid, num_datapoints)

        if proba_fn is not None and is_binary:
            preds = model.predict_proba(base_df)[:, 1]
        else:
            preds = model.predict(base_df)
        
        row_ids = np.repeat(np.arange(num_datapoints), grid_points)
        df_plot = pd.DataFrame(
            {
                "row_id": row_ids, 
                "feature_value": base_df[feature].to_numpy(), 
                "prediction": preds.astype(float)
            }
        )

        # Plot one line per row_id + dashed mean curve
        fig = plt.figure()
        ax = fig.gca()
        for rid in range(num_datapoints):
            sub = df_plot[df_plot["row_id"] == rid]
            ax.plot(sub["feature_value"], sub["prediction"], alpha=0.9, linewidth=1.6)
        mean_curve = df_plot.groupby("feature_value", as_index=False)["prediction"].mean()
        ax.plot(mean_curve["feature_value"], mean_curve["prediction"], linestyle="--", linewidth=2.0)

        ax.set_xlabel("feature value")
        ax.set_ylabel("predicted probability for target" if is_binary else "target value")
        ax.set_title(f"Ceteris Paribus Plot (n={num_datapoints})- Feature Name : '{feature}'")
        ax.grid(True, alpha=0.3)

        # Serialize figure to PNG bytes
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
        plt.close(fig)
        png_bytes = buf.getvalue()
        buf.close()

        out[feature] = (png_bytes, df_plot)

    return out


def lime_explain_instances(
    model,
    X: pd.DataFrame,
    X_train: pd.DataFrame,
    instance_indices: Optional[list[int]] = None,
    num_instances: int = 3,
    num_features: int = 10,
    mode: str = "auto"
) -> dict[int, dict[str, Any]]:
    """
    Generate LIME explanations for specific instances and return both text and visualizations.
    
    LIME (Local Interpretable Model-agnostic Explanations) explains individual predictions
    by fitting an interpretable model locally around the prediction.

    Args:
        model: Fitted estimator with predict() and optionally predict_proba()
        X (pd.DataFrame): Test data containing instances to explain
        X_train (pd.DataFrame): Training data used to fit the LIME explainer
        instance_indices (Optional[list[int]]): Specific row indices to explain.
            If None, uses first num_instances rows
        num_instances (int): Number of instances to explain if instance_indices not provided. Default: 3
        num_features (int): Number of top features to include in explanation. Default: 10
        mode (str): 'regression', 'classification', or 'auto' (auto-detect). Default: 'auto'

    Returns:
        dict[int, dict[str, Any]]: Dictionary mapping instance index to explanation data:
            - 'explanation_text': Human-readable text explanation
            - 'feature_weights': List of (feature, weight) tuples
            - 'plot_bytes': PNG visualization as bytes
            - 'prediction': Model's prediction for this instance
            - 'intercept': Local model intercept

    Example:
        >>> explanations = lime_explain_instances(model, X_test, X_train, num_instances=3)
        >>> for idx, exp_data in explanations.items():
        ...     print(f"Instance {idx}: {exp_data['explanation_text']}")
        ...     # Use exp_data['plot_bytes'] for visualization

    Raises:
        ImportError: If lime package is not installed
    """
    if lime is None:
        raise ImportError(
            "LIME is not installed. Install it with: pip install lime"
        )
    
    # Determine mode
    if mode == "auto":
        proba_fn = getattr(model, "predict_proba", None)
        if proba_fn is not None:
            mode = "classification"
        else:
            mode = "regression"
    
    # Select instances to explain
    if instance_indices is None:
        instance_indices = list(range(min(num_instances, len(X))))
    
    # Create LIME explainer
    feature_names = list(X.columns)
    
    if mode == "classification":
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train.values,
            feature_names=feature_names,
            mode='classification',
            discretize_continuous=True
        )
        predict_fn = model.predict_proba
    else:
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train.values,
            feature_names=feature_names,
            mode='regression',
            discretize_continuous=True
        )
        predict_fn = model.predict
    
    # Generate explanations
    results = {}
    
    for idx in instance_indices:
        instance = X.iloc[idx].values
        
        # Generate explanation
        exp = explainer.explain_instance(
            instance,
            predict_fn,
            num_features=num_features
        )
        
        # Extract data
        feature_weights = exp.as_list()
        prediction = exp.predict_proba if mode == "classification" else exp.predicted_value
        intercept = exp.intercept[1] if mode == "classification" else exp.intercept
        
        # Create text explanation
        text_lines = [
            f"LIME Explanation for Instance {idx}",
            "=" * 50,
            f"Mode: {mode}",
            f"Prediction: {prediction}",
            f"Local model intercept: {intercept:.4f}",
            "",
            f"Top {len(feature_weights)} feature contributions:",
        ]
        
        for feature, weight in feature_weights:
            direction = "increases" if weight > 0 else "decreases"
            text_lines.append(f"  - {feature}: {weight:+.4f} ({direction} prediction)")
        
        explanation_text = "\n".join(text_lines)
        
        # Create visualization
        fig = exp.as_pyplot_figure()
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
        plt.close(fig)
        plot_bytes = buf.getvalue()
        buf.close()
        
        results[idx] = {
            'explanation_text': explanation_text,
            'feature_weights': feature_weights,
            'plot_bytes': plot_bytes,
            'prediction': prediction,
            'intercept': intercept,
            'lime_explanation_object': exp  # For advanced use
        }
    
    return results


def lime_explain_text_summary(
    model,
    X: pd.DataFrame,
    X_train: pd.DataFrame,
    instance_indices: Optional[list[int]] = None,
    num_instances: int = 3,
    num_features: int = 10
) -> str:
    """
    Generate a concise text summary of LIME explanations for multiple instances.
    
    This is a convenience function that returns just the text explanations
    without plots, suitable for direct inclusion in LLM prompts.

    Args:
        model: Fitted estimator
        X (pd.DataFrame): Test data
        X_train (pd.DataFrame): Training data
        instance_indices (Optional[list[int]]): Specific instances to explain
        num_instances (int): Number of instances if indices not provided. Default: 3
        num_features (int): Number of features per explanation. Default: 10

    Returns:
        str: Formatted text containing all explanations

    Example:
        >>> summary = lime_explain_text_summary(model, X_test, X_train)
        >>> print(summary)
    """
    explanations = lime_explain_instances(
        model, X, X_train, 
        instance_indices=instance_indices,
        num_instances=num_instances,
        num_features=num_features
    )
    
    text_parts = []
    for idx, exp_data in explanations.items():
        text_parts.append(exp_data['explanation_text'])
        text_parts.append("")  # Blank line between instances
    
    return "\n".join(text_parts)


# =============================================================================
# INFO GETTERS - PANDAS DATAFRAME DESCRIPTIONS
# =============================================================================

def _safe_truncate_text(text: str, max_length: int) -> str:
    """Truncate a string to max_length characters with a clear marker."""
    if len(text) <= max_length:
        return text
    marker = f"\n\n... (truncated, original length {len(text)} chars)"
    return text[: max_length - len(marker)] + marker


def describe_pandas_dataset(
    df: pd.DataFrame,
    *,
    metadata: Optional[Mapping[str, Any]] = None,
    max_columns: int = 40,
    max_length: int = 2000,
) -> str:
    """
    Return a concise, schema-focused textual description of a pandas DataFrame.
    
    This function generates LLM-friendly descriptions of datasets that focus on
    structural information (shape, types, missingness, cardinality) without
    including actual data values. Perfect for ethics compliance analysis.

    Args:
        df (pd.DataFrame): The DataFrame to describe
        metadata (Optional[Mapping[str, Any]]): Optional user-provided metadata
            (e.g., column descriptions, data sources)
        max_columns (int): Maximum number of columns to describe individually. Default: 40
        max_length (int): Maximum length of the output text. Default: 2000

    Returns:
        str: A formatted text description suitable for LLM prompts

    Example:
        >>> metadata = {"MEDV": "Median home value in $1000s (target)"}
        >>> description = describe_pandas_dataset(df, metadata=metadata)
        >>> print(description)
    """
    lines = []

    # --- Header ------------------------------------------------------------
    lines.append("Pandas dataset summary")
    lines.append("=" * 24)
    lines.append("")

    # --- User metadata ------------------------------------------------------
    if metadata:
        lines.append("User-provided metadata")
        lines.append("-" * 23)
        for k, v in sorted(metadata.items(), key=lambda kv: kv[0]):
            lines.append(f"- {k}: {v}")
        lines.append("")

    # --- Basic structure ----------------------------------------------------
    n_rows, n_cols = df.shape
    lines.append("Basic structure")
    lines.append("-" * 16)
    lines.append(f"- Shape: {n_rows} rows × {n_cols} columns")
    lines.append(f"- Index type: {type(df.index).__name__}")
    lines.append("")

    # --- Column type overview ----------------------------------------------
    lines.append("Column type overview")
    lines.append("-" * 22)

    dtypes = df.dtypes
    dtype_counts = dtypes.value_counts()

    for dtype, count in dtype_counts.items():
        lines.append(f"- {dtype}: {count} columns")

    # High-level type groups
    num_cols = df.select_dtypes(include=[np.number]).columns
    bool_cols = df.select_dtypes(include=["bool"]).columns
    datetime_cols = df.select_dtypes(
        include=[np.datetime64, "datetime", "datetimetz"]
    ).columns
    object_cols = df.select_dtypes(include=["object"]).columns

    lines.append(f"- numeric columns: {len(num_cols)}")
    lines.append(f"- boolean columns: {len(bool_cols)}")
    lines.append(f"- datetime columns: {len(datetime_cols)}")
    lines.append(f"- object columns: {len(object_cols)}")
    lines.append("")

    # --- Column-level summary ----------------------------------------------
    lines.append("Column-level summary")
    lines.append("-" * 21)
    lines.append(
        "(For each column: dtype, non-null count, % missing, #unique values excluding NaN.)"
    )

    total_rows = float(len(df)) if len(df) > 0 else 1.0

    col_names = list(df.columns)
    show_cols = col_names[:max_columns]
    hidden_count = max(0, len(col_names) - len(show_cols))

    for col in show_cols:
        s = df[col]
        dtype = s.dtype
        non_null = int(s.notna().sum())
        null_count = len(s) - non_null
        null_pct = (null_count / total_rows) * 100.0 if total_rows > 0 else 0.0

        try:
            n_unique = int(s.nunique(dropna=True))
        except Exception:
            n_unique = -1

        parts = [
            f"- {col!r}: dtype={dtype}",
            f"non_null={non_null}",
            f"missing={null_count} ({null_pct:.1f}% of rows)",
        ]
        if n_unique >= 0:
            parts.append(f"n_unique={n_unique}")

        lines.append("; ".join(parts))

    if hidden_count > 0:
        lines.append(
            f"... ({hidden_count} additional columns not listed individually; "
            f"increase max_columns to see more.)"
        )

    lines.append("")

    # --- Numeric high-level note -------------------------------------------
    if len(num_cols) > 0:
        lines.append("Numeric columns (high-level)")
        lines.append("-" * 29)
        lines.append(
            f"- Number of numeric columns: {len(num_cols)} "
            "(standard descriptive statistics can be computed with df[num_cols].describe())"
        )
        lines.append("")

    text = "\n".join(lines)
    return _safe_truncate_text(text, max_length)


# =============================================================================
# INFO GETTERS - SKLEARN MODEL DESCRIPTIONS
# =============================================================================

def _safe_truncate(text: str, max_length: int) -> str:
    """Truncate text with a marker."""
    if len(text) <= max_length:
        return text
    marker = f"\n\n... (truncated, original length {len(text)} chars)"
    return text[: max_length - len(marker)] + marker


def _format_params(d: Dict[str, Any], max_items: int = 30, max_value_len: int = 80) -> str:
    """Format a subset of params into compact 'key=value' lines."""
    items = sorted(d.items(), key=lambda kv: kv[0])[:max_items]
    lines = []
    for k, v in items:
        try:
            v_str = repr(v)
        except Exception:
            v_str = f"<unrepr-able type {type(v).__name__}>"
        if len(v_str) > max_value_len:
            v_str = v_str[: max_value_len - 15] + "... (truncated)"
        lines.append(f"- {k} = {v_str}")
    if len(d) > max_items:
        lines.append(f"- ... ({len(d) - max_items} more parameters not shown)")
    return "\n".join(lines)


def describe_sklearn_model(model: Any, *, max_length: int = 1500) -> str:
    """
    Return a concise, data-agnostic textual description of a scikit-learn model.
    
    This function inspects a fitted sklearn model and generates a text description
    suitable for LLM prompts. It extracts hyperparameters, model structure, and
    internal state without requiring any training data.

    Args:
        model (Any): A fitted scikit-learn estimator
        max_length (int): Maximum length of the output text. Default: 1500

    Returns:
        str: A formatted text description suitable for LLM prompts

    Example:
        >>> from sklearn.ensemble import RandomForestRegressor
        >>> model = RandomForestRegressor(n_estimators=200, random_state=42)
        >>> model.fit(X_train, y_train)
        >>> description = describe_sklearn_model(model)
        >>> print(description)
    """
    lines = []

    # --- High-level info ---------------------------------------------------
    cls = model.__class__
    module = cls.__module__
    name = cls.__name__

    if sklearn is not None:
        lines.append(f"- Library: scikit-learn {getattr(sklearn, '__version__', '?')}")
    else:
        lines.append("- Library: scikit-learn (version unknown)")
    lines.append(f"- Estimator class: {module}.{name}")

    try:
        sig = inspect.signature(cls)
        lines.append(f"- Constructor signature: {name}{sig}")
    except Exception:
        pass

    lines.append("")

    # --- Hyperparameters ---------------------------------------------------
    lines.append("Hyperparameters (get_params(deep=False))")
    lines.append("-" * 41)

    try:
        params = model.get_params(deep=False)
    except Exception:
        params = {}
        lines.append("- <model does not expose get_params(deep=False)>")

    if params:
        simple_params = {}
        complex_params = {}
        for k, v in params.items():
            if isinstance(v, (int, float, str, bool, type(None), tuple)):
                simple_params[k] = v
            else:
                complex_params[k] = f"<{type(v).__module__}.{type(v).__name__}>"

        if simple_params:
            lines.append("Simple parameters:")
            lines.append(_format_params(simple_params))
        if complex_params:
            if simple_params:
                lines.append("")
            lines.append("Complex / nested parameters (summarized):")
            lines.append(_format_params(complex_params))

    lines.append("")

    # --- Composite structures (pipelines, column transformers) ------------
    if hasattr(model, "steps"):
        try:
            steps = getattr(model, "steps")
            lines.append("Pipeline structure")
            lines.append("-" * 18)
            for step_name, est in steps:
                lines.append(
                    f"- '{step_name}': {est.__class__.__module__}.{est.__class__.__name__}"
                )
            lines.append("")
        except Exception:
            pass

    if hasattr(model, "transformers_"):
        try:
            transformers = getattr(model, "transformers_")
            lines.append("ColumnTransformer structure")
            lines.append("-" * 27)
            for name_i, transformer, cols in transformers:
                t_cls = (
                    f"{transformer.__class__.__module__}.{transformer.__class__.__name__}"
                    if transformer is not None
                    else "drop/passthrough"
                )
                lines.append(f"- '{name_i}': {t_cls}, columns spec type = {type(cols).__name__}")
            lines.append("")
        except Exception:
            pass

    # --- SearchCV / tuning results ----------------------------------------
    if any(hasattr(model, a) for a in ("best_params_", "best_score_", "refit_time_")):
        lines.append("Search / tuning summary")
        lines.append("-" * 24)

        if hasattr(model, "best_params_"):
            bp = getattr(model, "best_params_")
            if isinstance(bp, dict):
                lines.append("Best parameters:")
                lines.append(_format_params(bp, max_items=20))
            else:
                lines.append(f"- best_params_: {repr(bp)}")

        if hasattr(model, "best_score_"):
            lines.append(f"- best_score_: {getattr(model, 'best_score_')}")
        if hasattr(model, "refit_time_"):
            lines.append(f"- refit_time_: {getattr(model, 'refit_time_')}")
        lines.append("")

    # --- Model internals (high-level, not raw data) ------------------------
    lines.append("Model internals (high-level)")
    lines.append("-" * 27)

    # Linear models
    if hasattr(model, "coef_"):
        try:
            coef = np.asarray(model.coef_)
            lines.append(f"- coef_ shape: {coef.shape}")
        except Exception:
            lines.append("- coef_: <available but not summarized>")

    if hasattr(model, "intercept_"):
        try:
            intercept = np.asarray(model.intercept_)
            lines.append(f"- intercept_ shape: {intercept.shape}")
        except Exception:
            lines.append("- intercept_: <available but not summarized>")

    # Tree-based / ensemble models
    if hasattr(model, "feature_importances_"):
        try:
            fi = np.asarray(model.feature_importances_)
            lines.append(f"- feature_importances_ length: {fi.size}")
        except Exception:
            lines.append("- feature_importances_: <available but not summarized>")

    if hasattr(model, "n_estimators"):
        try:
            lines.append(f"- n_estimators: {getattr(model, 'n_estimators')}")
        except Exception:
            pass

    # Generic dimension-ish attributes (no direct data)
    for attr in ("n_outputs_", "n_features_in_"):
        if hasattr(model, attr):
            try:
                lines.append(f"- {attr}: {getattr(model, attr)}")
            except Exception:
                pass

    text = "\n".join(lines)
    return _safe_truncate(text, max_length)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def prepare_ethics_context(
    model: Any,
    df: pd.DataFrame,
    metadata: Optional[Mapping[str, Any]] = None,
    num_ice_datapoints: int = 3,
    ice_grid_points: int = 50,
    df_train: Optional[pd.DataFrame] = None,
    include_lime: bool = True,
    num_lime_instances: int = 3,
    num_lime_features: int = 10
) -> dict[str, Any]:
    """
    Prepare a complete context package for ethics compliance analysis.
    
    This convenience function combines model description, dataset description,
    and explainability plots (ICE and optionally LIME) into a single dictionary 
    ready for LLM analysis.

    Args:
        model: Fitted sklearn model
        df: Pandas DataFrame with the dataset (test data)
        metadata: Optional metadata about the dataset columns
        num_ice_datapoints: Number of datapoints for ICE plots. Default: 3
        ice_grid_points: Grid resolution for ICE plots. Default: 50
        df_train: Optional training data for LIME explainer. Required if include_lime=True
        include_lime: Whether to include LIME explanations. Default: True
        num_lime_instances: Number of instances to explain with LIME. Default: 3
        num_lime_features: Number of features per LIME explanation. Default: 10

    Returns:
        dict containing:
            - 'model_description': Text description of the model
            - 'data_description': Text description of the dataset
            - 'ice_plots': Dictionary of {feature: (png_bytes, data_df)}
            - 'lime_explanations': (if include_lime=True) Dictionary of LIME explanations
            - 'lime_text_summary': (if include_lime=True) Text summary of LIME results

    Example:
        >>> # Without LIME
        >>> context = prepare_ethics_context(model, X_test, metadata=metadata, include_lime=False)
        
        >>> # With LIME
        >>> context = prepare_ethics_context(model, X_test, X_train, metadata=metadata)
        >>> print(context['lime_text_summary'])

    Raises:
        ValueError: If include_lime=True but df_train is not provided
    """
    result = {
        'model_description': describe_sklearn_model(model),
        'data_description': describe_pandas_dataset(df, metadata=metadata),
        'ice_plots': ceteris_paribus_bytes_multi(
            model, 
            df, 
            num_datapoints=num_ice_datapoints, 
            grid_points=ice_grid_points
        )
    }
    
    # Add LIME explanations if requested
    if include_lime:
        if df_train is None:
            raise ValueError(
                "df_train is required when include_lime=True. "
                "Provide training data for the LIME explainer."
            )
        
        if lime is not None:
            try:
                lime_explanations = lime_explain_instances(
                    model,
                    df,
                    df_train,
                    num_instances=num_lime_instances,
                    num_features=num_lime_features
                )
                result['lime_explanations'] = lime_explanations
                result['lime_text_summary'] = lime_explain_text_summary(
                    model,
                    df,
                    df_train,
                    num_instances=num_lime_instances,
                    num_features=num_lime_features
                )
            except Exception as e:
                result['lime_error'] = f"LIME generation failed: {str(e)}"
        else:
            result['lime_error'] = "LIME not installed. Install with: pip install lime"
    
    return result

