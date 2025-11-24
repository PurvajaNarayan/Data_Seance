from __future__ import annotations

from typing import Any, Mapping, Optional
import pandas as pd
import numpy as np


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
