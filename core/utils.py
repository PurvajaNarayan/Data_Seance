from __future__ import annotations

from typing import Any, Mapping, Optional, Dict, Sequence
import pandas as pd
import numpy as np
import inspect
import sklearn 
from langchain_core.messages import BaseMessage
from pprint import pformat
import matplotlib.pyplot as plt

def load_and_show_png_bytes(img_bytes: bytes, title: str | None = None):
    """
    Loader function: read PNG bytes and plot them with matplotlib.
    """
    from io import BytesIO
    import matplotlib.image as mpimg

    arr = mpimg.imread(BytesIO(img_bytes), format="png")
    plt.figure()
    plt.imshow(arr)
    plt.axis("off")
    if title:
        plt.title(title)
    plt.show()


def _is_probably_binary_string(s: str) -> bool:
    """Heuristic to avoid dumping base64/data URLs and other non-human strings."""
    if not isinstance(s, str):
        return False

    if s.startswith("data:image") or "base64," in s[:80]:
        return True

    if len(s) > 256:
        base64_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r "
        )
        if set(s[:1024]) <= base64_chars:
            return True

    non_printable = sum((ord(c) < 32 or ord(c) > 126) for c in s)
    if len(s) == 0:
        return False
    return (non_printable / len(s)) > 0.30


def _indent_preserve(text: str, indent: int) -> str:
    """Indent every line of `text` by `indent` spaces, preserving internal formatting."""
    prefix = " " * indent
    return "".join(prefix + line for line in text.splitlines(keepends=True))


def _sanitize_for_print(obj: Any, max_list_items: int = 8) -> Any:
    """
    Prepare an object for pretty-printing inside dicts:

    - binary-ish strings / bytes -> "[binary data omitted]"
    - long lists -> truncated list + note element
    """
    if isinstance(obj, (bytes, bytearray)):
        return "[binary data omitted]"

    if isinstance(obj, str):
        if _is_probably_binary_string(obj):
            return "[binary data omitted]"
        return obj

    if isinstance(obj, dict):
        return {k: _sanitize_for_print(v, max_list_items) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        total = len(obj)
        show_n = min(total, max_list_items)
        items = [_sanitize_for_print(x, max_list_items) for x in obj[:show_n]]
        if total > show_n:
            items.append(
                f"... (list truncated, has {total} elements; showing first {show_n})"
            )
        return items if isinstance(obj, list) else tuple(items)

    return obj


# ---------- object → human string ----------

def _humanize_obj(
    obj: Any,
    indent: int = 0,
    max_list_items: int = 8,
) -> str:
    """
    Convert arbitrary object to a human-readable multi-line string.

    IMPORTANT: strings are *never* re-wrapped or reformatted;
    their internal newlines/spacing are preserved.
    """
    lines: list[str] = []
    prefix = " " * indent

    # None
    if obj is None:
        lines.append(prefix + "null")

    # Strings (preserve formatting)
    elif isinstance(obj, str):
        if _is_probably_binary_string(obj):
            lines.append(prefix + "[binary data omitted]")
        else:
            lines.append(_indent_preserve(obj, indent))

    # Simple scalars
    elif isinstance(obj, (int, float, bool)):
        lines.append(prefix + repr(obj))

    # Dicts: recursively pretty-print as a dict literal
    elif isinstance(obj, dict):
        sanitized = _sanitize_for_print(obj, max_list_items=max_list_items)
        pretty = pformat(sanitized, width=80, compact=False)
        lines.append(_indent_preserve(pretty, indent))

    # Lists / tuples: each element as its own block, with truncation
    elif isinstance(obj, (list, tuple)):
        total = len(obj)
        if total == 0:
            lines.append(prefix + "[]")
        else:
            show_n = min(total, max_list_items)
            for i, item in enumerate(obj[:show_n], 1):
                lines.append(
                    _humanize_obj(
                        item,
                        indent=indent,
                        max_list_items=max_list_items,
                    )
                )
                if i != show_n:
                    lines.append("")  # blank line between elements

            if total > show_n:
                lines.append(
                    f"{prefix}(list truncated, has {total} elements; "
                    f"showing first {show_n})"
                )

    # Fallback: pretty repr
    else:
        pretty = pformat(obj, width=80, compact=True)
        lines.append(_indent_preserve(pretty, indent))

    return "\n".join(lines)


def _render_content(content: Any) -> str:
    """
    Render the .content attribute of a message.
    - Plain string: returned exactly as-is.
    - List: each element pretty-printed as its own block.
    - Dict / other: pretty-printed generically.
    """
    if content is None:
        return "content: null"

    # Plain text: show exactly as stored
    if isinstance(content, str):
        return _indent_preserve(content, 2)

    # List-of-blocks content
    if isinstance(content, list):
        blocks: list[str] = []
        for idx, block in enumerate(content, 1):
            blocks.append(f"- item {idx}:")
            blocks.append(_humanize_obj(block, indent=4))
            blocks.append("")
        return "\n".join("  " + line if line else "" for line in blocks)

    # Anything else
    return  _humanize_obj(content, indent=2)


# ---------- public API ----------

def pretty_messages_pretty(
    messages: Sequence[BaseMessage],
    max_list_items: int = 8,
) -> str:
    """
    Pretty-print LangChain Messages.

    - **Preserves** the original first line from `pretty_repr()` (the
      `==================== Human Message ====================` header).
    - Replaces the rest with a more readable view of `.content`:
        * strings unchanged,
        * dicts recursively pretty-printed,
        * lists printed element-by-element with truncation note,
        * binary-ish data omitted.
    """
    out: list[str] = []

    for msg in messages:
        # Grab original pretty_repr and keep the header line AS-IS
        if hasattr(msg, "pretty_repr") and callable(getattr(msg, "pretty_repr")):
            try:
                base = msg.pretty_repr()
            except TypeError:
                base = msg.pretty_repr(html=False)
        else:
            base = repr(msg)

        lines = base.splitlines() or [repr(msg)]
        header_line = lines[0]  # e.g. "====================  Human Message  ===================="

        out.append(header_line)      # keep exactly
        out.append("")               # blank line after header
        out.append(_render_content(getattr(msg, "content", None)))
        out.append("")               # blank line between messages

    return "\n".join(out)

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

    This is meant to be copy-pasted into an LLM prompt. It focuses on structural
    information (shape, column types, missingness, cardinality) and optional
    user-provided metadata. It does NOT include actual data values.
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

    # 🔧 FIXED: use general datetime / datetimetz selectors
    datetime_cols = df.select_dtypes(
        include=[np.datetime64, "datetime", "datetimetz"]
    ).columns

    object_cols = df.select_dtypes(include=["object"]).columns  # often string / categorical-like

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
