from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List

import h5py
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config

CHUNK_SIZE = 5_000
EPS = 1e-8


def _samples_from_ms(window_ms: float, samp_rate_us: int) -> int:
    sample_ms = samp_rate_us / 1000.0
    return max(1, int(round(window_ms / sample_ms)))


def _read_traces_by_index(data_array: h5py.Dataset, trace_indices: np.ndarray) -> np.ndarray:
    order = np.argsort(trace_indices, kind="stable")
    sorted_idx = trace_indices[order]
    traces_sorted = np.asarray(data_array[sorted_idx, :], dtype=np.float32)
    inverse = np.empty_like(order)
    inverse[order] = np.arange(order.size)
    return traces_sorted[inverse]


def _compute_stalta_for_chunk(
    traces: np.ndarray,
    sta_samples: int,
    lta_samples: int,
    threshold: float,
    min_search_sample: int,
) -> Dict[str, np.ndarray]:
    """
    Causal STA/LTA using cumulative sum for efficiency.

    At each sample i:
      LTA(i) = mean of |x[i-lta_samples+1 : i+1]|  (looks backward, causal)
      STA(i) = mean of |x[i : i+sta_samples]|       (looks forward from current sample)

    The first break is declared at the first sample where ratio >= threshold,
    searching only from min_search_sample onward.
    """
    n_traces, n_samples = traces.shape
    signal = np.abs(traces).astype(np.float64, copy=False)

    pad = np.zeros((n_traces, 1), dtype=np.float64)
    cumsum = np.cumsum(np.concatenate([pad, signal], axis=1), axis=1)

    lta = np.empty((n_traces, n_samples), dtype=np.float64)
    for i in range(n_samples):
        window = min(i + 1, lta_samples)
        lta[:, i] = (cumsum[:, i + 1] - cumsum[:, i + 1 - window]) / window

    sta = np.empty((n_traces, n_samples), dtype=np.float64)
    for i in range(n_samples):
        end = min(i + sta_samples, n_samples)
        window = end - i
        sta[:, i] = (cumsum[:, end] - cumsum[:, i]) / window

    ratio = sta / np.maximum(lta, EPS)

    ratio_search = ratio[:, min_search_sample:]
    crossed = ratio_search >= threshold
    any_cross = crossed.any(axis=1)
    first_pick = np.where(any_cross, crossed.argmax(axis=1) + min_search_sample, -1)

    peak_ratio = ratio.max(axis=1)
    pick_clipped = np.clip(first_pick, 0, n_samples - 1)
    ratio_at_pick = ratio[np.arange(n_traces), pick_clipped]
    ratio_at_pick = np.where(first_pick >= 0, ratio_at_pick, 0.0)

    return {
        "stalta_pick_sample": first_pick.astype(np.int64),
        "stalta_peak_ratio": peak_ratio.astype(np.float64),
        "stalta_ratio_at_pick": ratio_at_pick.astype(np.float64),
        "stalta_failed": (first_pick < 0).astype(np.int64),
    }


def _fit_hyperbolic_residual(offset: np.ndarray, pick_ms: np.ndarray) -> np.ndarray:
    residual = np.zeros_like(pick_ms, dtype=np.float64)
    valid = np.isfinite(pick_ms) & (pick_ms > 0)
    if valid.sum() < 5:
        return residual

    x2 = np.square(offset[valid].astype(np.float64))
    t2 = np.square(pick_ms[valid].astype(np.float64))

    design = np.column_stack([np.ones_like(x2), x2])
    coeff, *_ = np.linalg.lstsq(design, t2, rcond=None)
    fitted_t2 = coeff[0] + coeff[1] * np.square(offset.astype(np.float64))
    fitted_t2 = np.maximum(fitted_t2, 0.0)
    fitted_t = np.sqrt(fitted_t2)
    residual = pick_ms - fitted_t
    residual[~np.isfinite(residual)] = 0.0
    return residual


def augment_asset_with_stalta(asset_key: str) -> Dict[str, object]:
    metadata_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    features_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
    if not metadata_path.exists() or not features_path.exists():
        raise FileNotFoundError(f"Missing inputs for asset={asset_key}")

    metadata_head = pd.read_csv(metadata_path, nrows=1)
    offset_col = "offset" if "offset" in metadata_head.columns else "stored_offset"

    metadata_df = pd.read_csv(
        metadata_path,
        usecols=[
            "trace_index",
            "shot_id",
            "gather_sequence_index",
            "trace_index_within_gather",
            offset_col,
            "samp_rate_us",
        ],
    )
    if offset_col != "offset":
        metadata_df = metadata_df.rename(columns={offset_col: "offset"})
    features_df = pd.read_csv(features_path)

    required_cols = {"trace_index", "shot_id", "gather_sequence_index", "trace_index_within_gather"}
    if not required_cols.issubset(features_df.columns):
        raise ValueError(f"features_{asset_key}.csv missing key columns: {required_cols - set(features_df.columns)}")

    merged = features_df.merge(
        metadata_df,
        on=["trace_index", "shot_id", "gather_sequence_index", "trace_index_within_gather"],
        how="left",
        validate="one_to_one",
    )
    if "offset" not in merged.columns:
        if "offset_x" in merged.columns and "offset_y" in merged.columns:
            merged["offset"] = merged["offset_x"].to_numpy(dtype=np.float64)
            merged = merged.drop(columns=["offset_x", "offset_y"])
        elif "offset_x" in merged.columns:
            merged = merged.rename(columns={"offset_x": "offset"})
        elif "offset_y" in merged.columns:
            merged = merged.rename(columns={"offset_y": "offset"})

    if merged["samp_rate_us"].isna().any():
        missing = int(merged["samp_rate_us"].isna().sum())
        raise ValueError(f"Asset {asset_key}: missing sampling rate for {missing} rows")

    trace_indices = merged["trace_index"].to_numpy(dtype=np.int64)
    samp_rate_us = int(round(float(merged["samp_rate_us"].median())))

    sta_samples = _samples_from_ms(config.STALTA_STA_WINDOW_MS, samp_rate_us)
    lta_samples = _samples_from_ms(config.STALTA_LTA_WINDOW_MS, samp_rate_us)
    threshold = float(config.STALTA_THRESHOLD_BY_ASSET[asset_key])
    min_search_sample = int(config.STALTA_MIN_SEARCH_SAMPLE_BY_ASSET[asset_key])

    stalta_pick_sample = np.full(len(merged), -1, dtype=np.int64)
    stalta_peak_ratio = np.zeros(len(merged), dtype=np.float64)
    stalta_ratio_at_pick = np.zeros(len(merged), dtype=np.float64)
    stalta_failed = np.ones(len(merged), dtype=np.int64)

    with h5py.File(config.get_asset_path(asset_key), "r") as h5f:
        data_array = h5f["TRACE_DATA"]["DEFAULT"]["data_array"]
        for start in range(0, len(merged), CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, len(merged))
            idx = trace_indices[start:end]
            traces = _read_traces_by_index(data_array, idx)
            out = _compute_stalta_for_chunk(
                traces=traces,
                sta_samples=sta_samples,
                lta_samples=lta_samples,
                threshold=threshold,
                min_search_sample=min_search_sample,
            )
            stalta_pick_sample[start:end] = out["stalta_pick_sample"]
            stalta_peak_ratio[start:end] = out["stalta_peak_ratio"]
            stalta_ratio_at_pick[start:end] = out["stalta_ratio_at_pick"]
            stalta_failed[start:end] = out["stalta_failed"]

    stalta_pick_ms = stalta_pick_sample * (samp_rate_us / 1000.0)
    stalta_pick_ms = np.where(stalta_pick_sample >= 0, stalta_pick_ms, np.nan)

    merged["stalta_pick_sample"] = stalta_pick_sample
    merged["stalta_pick_ms"] = stalta_pick_ms
    merged["stalta_peak_ratio"] = stalta_peak_ratio
    merged["stalta_ratio_at_pick"] = stalta_ratio_at_pick
    merged["stalta_failed"] = stalta_failed

    signal_window = int(config.STALTA_SIGNAL_WINDOW_SAMPLES)
    # NOTE: The following four features are diagnostic proxies reusing already-computed
    # columns. They are NOT model inputs (not in final_model_input_feature_columns).
    # True per-sample computation would require raw trace access inside the chunk loop.
    # They are retained in the CSV for EDA purposes only.
    merged["amplitude_at_stalta_pick"] = merged["max_abs_amplitude"].astype(np.float64)
    merged["noise_energy_first_20samples"] = merged["pre_break_noise_energy"].astype(np.float64)
    merged["signal_energy_after_stalta"] = merged["max_abs_amplitude"].astype(np.float64)
    merged["dominant_frequency_proxy"] = merged["zero_crossing_rate"].astype(np.float64)

    stalta_pick_ms_safe = merged["stalta_pick_ms"].to_numpy(dtype=np.float64)
    offset_safe = merged["offset"].to_numpy(dtype=np.float64)
    velocity = np.divide(
        offset_safe,
        np.maximum(stalta_pick_ms_safe / 1000.0, EPS),
        out=np.zeros_like(offset_safe),
        where=np.isfinite(stalta_pick_ms_safe) & (stalta_pick_ms_safe > 0),
    )
    merged["velocity_estimate_stalta"] = np.clip(velocity, 0.0, 15000.0)
    # Result in milliseconds: elevation_diff(m) / velocity(m/s) * 1000(ms/s)
    merged["slant_time_correction"] = (
        merged["elevation_diff"].to_numpy(dtype=np.float64) / 2000.0 * 1000.0
    )

    gather_median = merged.groupby("gather_sequence_index")["stalta_pick_ms"].transform("median")
    gather_std = merged.groupby("gather_sequence_index")["stalta_pick_ms"].transform("std").fillna(0.0)
    merged["gather_median_pick_ms"] = gather_median
    merged["pick_deviation_from_gather_median"] = merged["stalta_pick_ms"] - gather_median
    merged["gather_pick_std"] = gather_std

    hyper_residual = np.zeros(len(merged), dtype=np.float64)
    for gather_id, group in merged.groupby("gather_sequence_index", sort=False):
        off = group["offset"].to_numpy(dtype=np.float64)
        pick = group["stalta_pick_ms"].to_numpy(dtype=np.float64)
        residuals = _fit_hyperbolic_residual(off, pick)
        hyper_residual[group.index] = residuals
    merged["hyperbolic_residual"] = hyper_residual

    drop_cols = ["samp_rate_us"]
    merged = merged.drop(columns=[c for c in drop_cols if c in merged.columns])
    merged.to_csv(features_path, index=False)

    report = {
        "asset": asset_key,
        "rows": int(len(merged)),
        "sta_samples": sta_samples,
        "lta_samples": lta_samples,
        "threshold": threshold,
        "min_search_sample": min_search_sample,
        "failed_count": int((merged["stalta_failed"] == 1).sum()),
        "failed_pct": float(100.0 * (merged["stalta_failed"] == 1).mean()),
        "signal_window_samples": signal_window,
    }
    return report


def update_feature_config_with_stalta() -> None:
    config_path = config.PREPROCESSING_DIR / "feature_engineering_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    stalta_feature_columns = [
        "stalta_pick_ms",
        "stalta_peak_ratio",
        "stalta_ratio_at_pick",
        "stalta_pick_sample",
        "stalta_failed",
        "velocity_estimate_stalta",
        "slant_time_correction",
        "gather_median_pick_ms",
        "pick_deviation_from_gather_median",
        "gather_pick_std",
        "hyperbolic_residual",
    ]
    payload["stalta_diagnostic_proxy_columns"] = [
        "noise_energy_first_20samples",
        "signal_energy_after_stalta",
        "amplitude_at_stalta_pick",
        "dominant_frequency_proxy",
    ]

    payload["stalta_feature_columns"] = stalta_feature_columns
    payload["stalta_config"] = {
        "sta_window_ms": config.STALTA_STA_WINDOW_MS,
        "lta_window_ms": config.STALTA_LTA_WINDOW_MS,
        "threshold_by_asset": config.STALTA_THRESHOLD_BY_ASSET,
        "min_search_sample_by_asset": config.STALTA_MIN_SEARCH_SAMPLE_BY_ASSET,
        "signal_window_samples": config.STALTA_SIGNAL_WINDOW_SAMPLES,
    }

    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_stalta_feature_stage() -> None:
    config.ensure_output_dirs()
    reports: List[Dict[str, object]] = []

    for asset_key in config.DATASET_ASSETS.keys():
        print(f"[03b_stalta_features] Processing {asset_key}")
        reports.append(augment_asset_with_stalta(asset_key))
        print(f"[03b_stalta_features] Completed {asset_key}")

    update_feature_config_with_stalta()
    report_df = pd.DataFrame(reports)
    report_path = config.PREPROCESSING_DIR / "stalta_feature_report_all_assets.csv"
    report_df.to_csv(report_path, index=False)

    txt_path = config.PREPROCESSING_DIR / "stalta_feature_report_all_assets.txt"
    txt_lines = ["STA/LTA feature stage summary", "", report_df.to_string(index=False)]
    txt_path.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")

    print(f"[03b_stalta_features] Outputs written to: {config.PREPROCESSING_DIR}")


if __name__ == "__main__":
    run_stalta_feature_stage()
