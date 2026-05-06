from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


def _log(message: str) -> None:
    print(f"[05_hyperbolic_smoothing] {message}", flush=True)


def _experiment_suffix(experiment_tag: str | None) -> str:
    tag = (experiment_tag or "").strip().lower()
    return "_experimentb" if tag in {"b", "experimentb"} else ""


def _fit_hyperbolic(offset: np.ndarray, t_ms: np.ndarray) -> np.ndarray:
    valid = np.isfinite(offset) & np.isfinite(t_ms) & (t_ms > 0)
    if valid.sum() < 3:
        return t_ms.copy()

    x2 = np.square(offset[valid])
    t2 = np.square(t_ms[valid])
    design = np.column_stack([np.ones_like(x2), x2])
    coeff, *_ = np.linalg.lstsq(design, t2, rcond=None)

    fitted_t2 = coeff[0] + coeff[1] * np.square(offset)
    fitted_t2 = np.maximum(fitted_t2, 0.0)
    return np.sqrt(fitted_t2)


def smooth_prediction_file(
    pred_path: Path,
    out_path: Path,
    z_threshold: float = 2.0,
    log_every_gathers: int = 50,
) -> pd.DataFrame:
    _log(f"Reading {pred_path.name}")
    pred_df = pd.read_csv(pred_path)
    if "prediction_status" not in pred_df.columns:
        pred_df["prediction_status"] = "predicted_labeled"
    _log(f"Input rows: {len(pred_df):,}")

    if "shot_id" not in pred_df.columns:
        out = pred_df.copy()
        out["predicted_ms_smoothed"] = out["predicted_ms"]
        out["replaced_by_hyperbola"] = 0
        assert "prediction_status" in out.columns, "prediction_status column lost during smoothing"
        out.to_csv(out_path, index=False)
        _log(f"No shot_id column; wrote passthrough file {out_path.name}")
        return out

    feature_cache: Dict[str, pd.DataFrame] = {}

    rows: List[pd.DataFrame] = []
    grouped = pred_df.groupby(["asset", "shot_id"], sort=False)
    total_gathers = grouped.ngroups
    _log(f"Total gathers to smooth: {total_gathers:,}")

    for i, ((asset_key, shot_id), group) in enumerate(grouped, start=1):
        g = group.copy()
        offset_col = "offset" if "offset" in g.columns else None
        if offset_col is None:
            if asset_key not in feature_cache:
                feat_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
                _log(f"Loading offset lookup for asset={asset_key} from {feat_path.name}")
                feature_cache[asset_key] = pd.read_csv(feat_path, usecols=["shot_id", "trace_index", "offset"])
            feat = feature_cache[asset_key]
            g = g.merge(feat, on=["shot_id", "trace_index"], how="left")
            offset_col = "offset"

        x = g[offset_col].to_numpy(dtype=np.float64)
        y = g["predicted_ms"].to_numpy(dtype=np.float64)

        fitted = _fit_hyperbolic(x, y)
        residual = y - fitted
        std = float(np.nanstd(residual, ddof=1)) if len(residual) > 1 else 0.0
        if std <= 0:
            replace_mask = np.zeros(len(g), dtype=bool)
        else:
            replace_mask = np.abs(residual) > (z_threshold * std)

        is_dead = (
            g["prediction_status"].to_numpy() == "dead_trace"
            if "prediction_status" in g.columns
            else np.zeros(len(g), dtype=bool)
        )
        replace_mask = replace_mask & ~is_dead
        g["predicted_ms_smoothed"] = np.where(replace_mask, fitted, y)
        g.loc[is_dead, "predicted_ms_smoothed"] = np.nan
        g["replaced_by_hyperbola"] = replace_mask.astype(np.int64)
        rows.append(g)

        if i == 1 or i % log_every_gathers == 0 or i == total_gathers:
            _log(f"Processed gathers: {i:,}/{total_gathers:,}")

    out_df = pd.concat(rows, ignore_index=True)
    assert "prediction_status" in out_df.columns, "prediction_status column lost during smoothing"
    out_df.to_csv(out_path, index=False)
    replaced = int(out_df["replaced_by_hyperbola"].sum())
    _log(f"Wrote {out_path.name} rows={len(out_df):,} replaced={replaced:,}")
    return out_df


def run_hyperbolic_smoothing(
    splits: List[str],
    z_threshold: float,
    log_every_gathers: int,
    experiment_tag: str | None = None,
) -> None:
    config.ensure_output_dirs()
    artifact_suffix = _experiment_suffix(experiment_tag)
    _log(f"Using z_threshold={z_threshold}")
    if artifact_suffix:
        _log(f"Using artifact suffix: {artifact_suffix}")

    for split in splits:
        in_path = config.EVALUATION_DIR / f"predictions_{split}{artifact_suffix}.csv"
        if not in_path.exists():
            _log(f"Skip split={split}: file not found ({in_path.name})")
            continue
        out_path = config.EVALUATION_DIR / f"predictions_{split}{artifact_suffix}_smoothed.csv"
        smooth_prediction_file(
            pred_path=in_path,
            out_path=out_path,
            z_threshold=z_threshold,
            log_every_gathers=log_every_gathers,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply gather-level hyperbolic smoothing with live logs")
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        help="Prediction splits to smooth",
    )
    parser.add_argument("--z-threshold", type=float, default=2.0)
    parser.add_argument("--log-every-gathers", type=int, default=50)
    parser.add_argument(
        "--experiment-tag",
        type=str,
        default="",
        help="Use 'experimentb' (or 'b') to smooth predictions_*_experimentb.csv files.",
    )
    args = parser.parse_args()

    run_hyperbolic_smoothing(
        splits=args.splits,
        z_threshold=args.z_threshold,
        log_every_gathers=args.log_every_gathers,
        experiment_tag=args.experiment_tag,
    )
