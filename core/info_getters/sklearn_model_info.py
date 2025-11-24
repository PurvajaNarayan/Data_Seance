from __future__ import annotations

from typing import Any, Dict
import inspect

import numpy as np

try:
    import sklearn
except ImportError:
    sklearn = None


def _safe_truncate(text: str, max_length: int) -> str:
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

    This function only inspects the estimator object itself and does not require
    any training data or external metadata. It is intended for use as context
    in LLM prompts.
    """
    lines = []

    # --- High-level info ---------------------------------------------------
    # lines.append("Scikit-learn model summary")
    # lines.append("=" * 29)
    # lines.append("")

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
                # Keep columns summary short and structural
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
