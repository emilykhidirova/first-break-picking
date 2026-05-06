from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


def _log(message: str) -> None:
    print(f"[08_visualize_predictions] {message}", flush=True)


def _experiment_suffix(experiment_tag: str) -> str:
    tag = experiment_tag.strip().lower()
    return "_experimentb" if tag in {"b", "experimentb"} else ""


def _normalized_experiment_tag(experiment_tag: str) -> str:
    tag = experiment_tag.strip().lower()
    if tag in {"b", "experimentb"}:
        return "experimentb"
    return tag


def _candidate_prediction_files(experiment_tag: str) -> List[Path]:
    out = config.EVALUATION_DIR
    suffix = _experiment_suffix(experiment_tag)
    names = [
        f"predictions_test{suffix}_smoothed.csv",
        f"predictions_test{suffix}.csv",
        f"predictions_val{suffix}_smoothed.csv",
        f"predictions_val{suffix}.csv",
        f"predictions_train{suffix}_smoothed.csv",
        f"predictions_train{suffix}.csv",
    ]
    if suffix:
        names.extend(
            [
                "predictions_test_smoothed.csv",
                "predictions_test.csv",
                "predictions_val_smoothed.csv",
                "predictions_val.csv",
                "predictions_train_smoothed.csv",
                "predictions_train.csv",
            ]
        )
    return [out / n for n in names if (out / n).exists()]


def _load_predictions_for_asset(asset_key: str, experiment_tag: str) -> pd.DataFrame:
    for path in _candidate_prediction_files(experiment_tag):
        df = pd.read_csv(path)
        if "prediction_status" not in df.columns:
            df["prediction_status"] = "predicted_labeled"
        pred_col = "predicted_ms_smoothed" if "predicted_ms_smoothed" in df.columns else "predicted_ms"
        if pred_col != "predicted_ms":
            df["predicted_ms"] = df[pred_col]
        df = df[df["asset"] == asset_key].copy()
        if not df.empty:
            out = df[df["prediction_status"] == "predicted_labeled"].copy()
            out = out[np.isfinite(out["predicted_ms"]) & np.isfinite(out["label_ms"]) & (out["label_ms"] > 0)].copy()
            return out
    return pd.DataFrame()


def _pick_representative_shot(asset_key: str, pred_df: pd.DataFrame) -> int:
    counts = pred_df.groupby("shot_id").size().sort_values(ascending=False)
    if counts.empty:
        raise ValueError(f"No predicted labeled rows found for asset={asset_key}")
    return int(counts.index[0])


def _load_gather_metadata(asset_key: str, shot_id: int) -> pd.DataFrame:
    path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    head = pd.read_csv(path, nrows=1)
    offset_col = "offset" if "offset" in head.columns else "stored_offset"
    usecols = ["trace_index", "shot_id", "trace_index_within_gather", offset_col, "samp_rate_us", "label_ms"]
    df = pd.read_csv(path, usecols=usecols)
    if offset_col != "offset":
        df = df.rename(columns={offset_col: "offset"})
    df = df[df["shot_id"] == shot_id].copy()
    if df.empty:
        raise ValueError(f"No valid metadata rows for asset={asset_key}, shot_id={shot_id}")
    return df


def _load_traces(asset_key: str, trace_indices: np.ndarray) -> np.ndarray:
    order = np.argsort(trace_indices, kind="stable")
    sorted_idx = trace_indices[order]
    unique_sorted_idx, inverse_unique = np.unique(sorted_idx, return_inverse=True)
    with h5py.File(config.get_asset_path(asset_key), "r") as h5f:
        data_array = h5f["TRACE_DATA"]["DEFAULT"]["data_array"]
        traces_unique = np.asarray(data_array[unique_sorted_idx, :], dtype=np.float32)
        traces_sorted = traces_unique[inverse_unique]
    inverse = np.empty_like(order)
    inverse[order] = np.arange(order.size)
    return traces_sorted[inverse]


def _build_overlay_for_asset(asset_key: str, experiment_tag: str) -> Tuple[Path, float]:
    pred_df = _load_predictions_for_asset(asset_key, experiment_tag=experiment_tag)
    if pred_df.empty:
        raise ValueError(f"No prediction rows available for asset={asset_key}")
    shot_id = _pick_representative_shot(asset_key, pred_df)
    shot_pred = pred_df[pred_df["shot_id"] == shot_id].copy()
    meta = _load_gather_metadata(asset_key, shot_id)
    merged = meta.merge(
        shot_pred[["trace_index", "predicted_ms", "label_ms"]],
        on="trace_index",
        how="inner",
        suffixes=("_meta", "_pred"),
    )
    if merged.empty:
        raise ValueError(f"No merged prediction rows for asset={asset_key}, shot_id={shot_id}")

    merged = merged.sort_values("trace_index_within_gather").reset_index(drop=True)
    trace_indices = merged["trace_index"].to_numpy(dtype=np.int64)
    traces = _load_traces(asset_key, trace_indices)  # [n_trace, n_time]
    image = traces.T  # [n_time, n_trace]

    gt_ms = merged["label_ms_meta"].to_numpy(dtype=np.float64)
    pred_ms = merged["predicted_ms"].to_numpy(dtype=np.float64)
    mae = float(np.mean(np.abs(pred_ms - gt_ms)))
    samp_rate_us = float(merged["samp_rate_us"].median())
    ms_per_sample = samp_rate_us / 1000.0
    x = np.arange(len(merged), dtype=np.float64)
    y_gt = gt_ms / ms_per_sample
    y_pred = pred_ms / ms_per_sample

    fig, ax = plt.subplots(figsize=(10, 6))
    vmax = np.percentile(np.abs(image), 99)
    ax.imshow(image, cmap="gray", aspect="auto", vmin=-vmax, vmax=vmax, origin="upper")
    ax.plot(x, y_gt, color="red", linewidth=1.5, label="Ground Truth")
    ax.plot(x, y_pred, color="deepskyblue", linewidth=1.5, label="Predicted")
    ax.set_title(f"{asset_key} | shot {shot_id} | MAE={mae:.2f} ms")
    ax.set_xlabel("Trace Index Within Gather")
    ax.set_ylabel("Time Sample")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.2)
    suffix = _experiment_suffix(experiment_tag)
    out_path = config.EVALUATION_DIR / f"gather_overlay_{asset_key}{suffix}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    _log(f"Saved overlay: {out_path.name}")
    return out_path, mae


def run_visualization(experiment_tag: str) -> None:
    config.ensure_output_dirs()
    suffix = _experiment_suffix(experiment_tag)
    norm_tag = _normalized_experiment_tag(experiment_tag)
    if suffix:
        _log(f"Using artifact suffix: {suffix}")
    asset_keys = list(config.DATASET_ASSETS.keys())
    overlay_paths: Dict[str, Path] = {}
    asset_mae: Dict[str, float] = {}

    for asset_key in asset_keys:
        try:
            path, mae = _build_overlay_for_asset(asset_key, experiment_tag=experiment_tag)
            overlay_paths[asset_key] = path
            asset_mae[asset_key] = mae
        except (ValueError, FileNotFoundError) as exc:
            _log(f"Warning: skipping {asset_key}: {exc}")
            asset_mae[asset_key] = float("nan")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    for ax, asset_key in zip(axes, asset_keys):
        overlay_path = overlay_paths.get(asset_key)
        if overlay_path is None or not overlay_path.exists():
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                f"{asset_key}\nNo predictions available\nMAE=NaN",
                ha="center",
                va="center",
                fontsize=11,
            )
            continue
        img = plt.imread(overlay_path)
        ax.imshow(img)
        mae = asset_mae.get(asset_key, float("nan"))
        ax.set_title(f"{asset_key} | MAE={mae:.2f} ms")
        ax.axis("off")

    out = config.EVALUATION_DIR / f"presentation_gather_comparison_all_assets_{norm_tag}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    _log(f"Saved presentation panel: {out.name}")
    if not suffix:
        default_out = config.EVALUATION_DIR / "presentation_gather_comparison_all_assets.png"
        # Keep legacy file path for default/non-experimentb mode.
        default_out.write_bytes(out.read_bytes())
        _log(f"Saved presentation panel: {default_out.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualize gather overlays from prediction files")
    parser.add_argument(
        "--experiment-tag",
        type=str,
        default="latest",
        help="Use 'experimentb' (or 'b') to read predictions_*_experimentb*.csv artifacts.",
    )
    args = parser.parse_args()
    run_visualization(experiment_tag=args.experiment_tag)
