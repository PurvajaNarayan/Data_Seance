# Efficient multi-point Ceteris Paribus (ICE) implementation
# - Handles multiple datapoints at once
# - Predicts in batches per feature (vectorized) for efficiency
# - Returns {feature: (figure, dataframe_used)}
#
# Minimal demonstration included at the bottom.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO


def ceteris_paribus_bytes_multi(model, X: pd.DataFrame, num_datapoints: int = 1, grid_points: int = 50):
    """
    Build Ceteris Paribus (ICE) plots for 'num_datapoints' rows from X and return
    images as PNG bytes.

    Args:
        model: fitted estimator with predict() and optionally predict_proba()
        X (pd.DataFrame): data defining grids and base rows
        num_datapoints (int): number of rows (taken from the top of X)
        grid_points (int): grid resolution per feature

    Returns:
        dict[str, tuple[bytes, pd.DataFrame]]:
            feature -> (png_bytes, data)
            where data columns: ['row_id','feature_value','prediction']
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
            print(f"using predict_proba")
        else:
            preds = model.predict(base_df)
        
        row_ids = np.repeat(np.arange(num_datapoints), grid_points)
        df_plot = pd.DataFrame(
            {"row_id": row_ids, "feature_value": base_df[feature].to_numpy(), "prediction": preds.astype(float)}
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
