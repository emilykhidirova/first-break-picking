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


FEATURE_COLUMNS = [
    "asset",
    "trace_index",
    "shot_id",
    "gather_sequence_index",
    "trace_index_within_gather",
    "number_of_traces_in_gather",
    "offset",
    "offset_gather_zscore",
    "offset_rank",
    "trace_position",
    "source_ht_scaled",
    "rec_ht_scaled",
    "elevation_diff",
    "slant_distance",
    "pre_break_noise_energy",
    "zero_crossing_rate",
    "max_abs_amplitude",
    "is_dead_trace",
]


def compute_gather_offset_stats(asset_key: str) -> pd.DataFrame:
    valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    gather_path = config.PREPROCESSING_DIR / f"gather_metadata_{asset_key}.csv"
    gather_df = pd.read_csv(gather_path)
    valid_head = pd.read_csv(valid_path, nrows=1)
    offset_col = "offset" if "offset" in valid_head.columns else "stored_offset"

    accum: Dict[int, Dict[str, float]] = {}
    chunk_iter = pd.read_csv(
        valid_path,
        usecols=["gather_sequence_index", offset_col],
        chunksize=200_000,
    )
    for chunk in chunk_iter:
        grouped = chunk.groupby("gather_sequence_index")[offset_col].agg(["count", "sum"])
        grouped["sum_sq"] = chunk.assign(offset_sq=chunk[offset_col] ** 2).groupby(
            "gather_sequence_index"
        )["offset_sq"].sum()
        for gather_idx, row in grouped.iterrows():
            gather_idx = int(gather_idx)
            if gather_idx not in accum:
                accum[gather_idx] = {"count": 0.0, "sum": 0.0, "sum_sq": 0.0}
            accum[gather_idx]["count"] += float(row["count"])
            accum[gather_idx]["sum"] += float(row["sum"])
            accum[gather_idx]["sum_sq"] += float(row["sum_sq"])

    rows = []
    for gather_idx, values in accum.items():
        count = values["count"]
        mean = values["sum"] / count if count else 0.0
        if count > 1:
            variance = max((values["sum_sq"] - (values["sum"] ** 2) / count) / (count - 1), 0.0)
            std = math.sqrt(variance)
        else:
            std = 0.0
        rows.append(
            {
                "gather_sequence_index": gather_idx,
                "offset_mean": mean,
                "offset_std": std,
            }
        )

    stats_df = pd.DataFrame(rows)
    stats_df = gather_df.merge(stats_df, on="gather_sequence_index", how="left")
    stats_df.to_csv(config.PREPROCESSING_DIR / f"offset_gather_stats_{asset_key}.csv", index=False)
    return stats_df


def read_trace_block(data_array: h5py.Dataset, trace_indices: np.ndarray) -> np.ndarray:
    order = np.argsort(trace_indices, kind="stable")
    sorted_idx = trace_indices[order]
    traces_sorted = np.asarray(data_array[sorted_idx, :], dtype=np.float32)
    inverse = np.empty_like(order)
    inverse[order] = np.arange(order.size)
    return traces_sorted[inverse]


def engineer_asset_features(asset_key: str) -> Dict[str, object]:
    valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    gather_stats_path = config.PREPROCESSING_DIR / f"offset_gather_stats_{asset_key}.csv"
    features_csv_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
    features_parquet_path = config.PREPROCESSING_DIR / f"features_{asset_key}.parquet"
    report_path = config.PREPROCESSING_DIR / f"feature_engineering_report_{asset_key}.txt"

    gather_stats = compute_gather_offset_stats(asset_key)
    gather_stats = gather_stats.set_index("gather_sequence_index")
    if features_csv_path.exists():
        features_csv_path.unlink()

    feature_rows_written = 0
    sample_frames: List[pd.DataFrame] = []

    with h5py.File(config.get_asset_path(asset_key), "r") as h5f:
        data_array = h5f["TRACE_DATA"]["DEFAULT"]["data_array"]
        valid_head = pd.read_csv(valid_path, nrows=1)
        offset_col = "offset" if "offset" in valid_head.columns else "stored_offset"
        gather_offset_min_col = "offset_min" if "offset_min" in gather_stats.columns else "stored_offset_min"
        gather_offset_max_col = "offset_max" if "offset_max" in gather_stats.columns else "stored_offset_max"
        chunk_iter = pd.read_csv(valid_path, chunksize=config.FEATURE_ENGINEERING_METADATA_CHUNK_SIZE)
        for idx, chunk in enumerate(chunk_iter):
            chunk = chunk.merge(
                gather_stats[
                    [
                        "number_of_traces",
                        gather_offset_min_col,
                        gather_offset_max_col,
                        "offset_mean",
                        "offset_std",
                    ]
                ],
                left_on="gather_sequence_index",
                right_index=True,
                how="left",
            )

            trace_indices = chunk["trace_index"].to_numpy(dtype=np.int64)
            traces = read_trace_block(data_array, trace_indices)
            max_abs_amplitude = np.max(np.abs(traces), axis=1)
            is_dead_trace = (max_abs_amplitude == 0).astype(np.int64)

            noise_window = min(config.PRE_BREAK_NOISE_WINDOW_SAMPLES, traces.shape[1])
            noise_slice = traces[:, :noise_window]
            pre_break_noise_energy = np.sqrt(np.mean(np.square(noise_slice), axis=1))

            half_window = max(2, int(traces.shape[1] * config.ZERO_CROSSING_WINDOW_FRACTION))
            signs = np.signbit(traces[:, :half_window])
            zero_crossing_rate = np.sum(signs[:, 1:] != signs[:, :-1], axis=1) / max(1, half_window - 1)

            offset_std = chunk["offset_std"].to_numpy(dtype=np.float64)
            offset_min = chunk[gather_offset_min_col].to_numpy(dtype=np.float64)
            offset_max = chunk[gather_offset_max_col].to_numpy(dtype=np.float64)
            gather_count = chunk["number_of_traces"].to_numpy(dtype=np.int64)
            offset_values = chunk[offset_col].to_numpy(dtype=np.float64)
            trace_pos_idx = chunk["trace_index_within_gather"].to_numpy(dtype=np.float64)

            offset_gather_zscore = np.divide(
                offset_values - chunk["offset_mean"].to_numpy(dtype=np.float64),
                offset_std,
                out=np.zeros_like(offset_values, dtype=np.float64),
                where=offset_std > 0,
            )
            offset_rank = np.divide(
                offset_values - offset_min,
                offset_max - offset_min,
                out=np.zeros_like(offset_values, dtype=np.float64),
                where=(offset_max - offset_min) > 0,
            )
            trace_position = np.divide(
                trace_pos_idx,
                gather_count - 1,
                out=np.zeros_like(trace_pos_idx, dtype=np.float64),
                where=(gather_count - 1) > 0,
            )

            feature_df = pd.DataFrame(
                {
                    "asset": asset_key,
                    "trace_index": trace_indices,
                    "shot_id": chunk["shot_id"].to_numpy(dtype=np.int64),
                    "gather_sequence_index": chunk["gather_sequence_index"].to_numpy(dtype=np.int64),
                    "trace_index_within_gather": chunk["trace_index_within_gather"].to_numpy(dtype=np.int64),
                    "number_of_traces_in_gather": gather_count,
                    "offset": offset_values,
                    "offset_gather_zscore": offset_gather_zscore,
                    "offset_rank": offset_rank,
                    "trace_position": trace_position,
                    "source_ht_scaled": chunk["source_ht"].to_numpy(dtype=np.float64),
                    "rec_ht_scaled": chunk["rec_ht"].to_numpy(dtype=np.float64),
                    "elevation_diff": chunk["elevation_diff"].to_numpy(dtype=np.float64),
                    "slant_distance": np.sqrt(
                        np.square(offset_values) + np.square(chunk["elevation_diff"].to_numpy(dtype=np.float64))
                    ),
                    "pre_break_noise_energy": pre_break_noise_energy,
                    "zero_crossing_rate": zero_crossing_rate,
                    "max_abs_amplitude": max_abs_amplitude,
                    "is_dead_trace": is_dead_trace,
                }
            )

            write_header = idx == 0
            feature_df.to_csv(features_csv_path, mode="a", header=write_header, index=False)
            feature_rows_written += len(feature_df)

            if len(sample_frames) < 3:
                sample_frames.append(feature_df.head(3))

    combined_sample = pd.concat(sample_frames, ignore_index=True) if sample_frames else pd.DataFrame()
    report_lines = [
        f"Asset: {asset_key}",
        "Working offset source for modeling: derived_from_coordinates",
        f"Working label column: {config.WORKING_LABEL_COLUMN}",
        f"Rows written: {feature_rows_written}",
        f"CSV output: {features_csv_path.name}",
        f"Parquet output written successfully: False",
        f"Noise window samples: {config.PRE_BREAK_NOISE_WINDOW_SAMPLES}",
        f"Zero crossing window fraction: {config.ZERO_CROSSING_WINDOW_FRACTION}",
    ]
    if not combined_sample.empty:
        report_lines.extend(["", "Feature sample:", combined_sample.to_string(index=False)])
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "asset": asset_key,
        "feature_rows_written": feature_rows_written,
        "parquet_written": False,
        "working_label_column": config.WORKING_LABEL_COLUMN,
        "working_offset_column": "derived_from_coordinates",
    }


def save_feature_config() -> None:
    payload = {
        "working_label_column": config.WORKING_LABEL_COLUMN,
        "primary_offset_column_by_asset": {key: "derived_from_coordinates" for key in config.DATASET_ASSETS},
        "feature_columns": FEATURE_COLUMNS,
        "pre_break_noise_window_samples": config.PRE_BREAK_NOISE_WINDOW_SAMPLES,
        "zero_crossing_window_fraction": config.ZERO_CROSSING_WINDOW_FRACTION,
        "trace_harmonization_strategy": config.TRACE_HARMONIZATION_STRATEGY,
        "notes": [
            "Offset is derived from scaled source/receiver coordinates for all assets.",
            "Static fields and coordinate-normalized source location features are excluded from model inputs.",
            "FIRST_BREAK_AMPLIT, FIRST_BREAK_VELOCITY, and MODELLED_BREAK_TIME are excluded from model inputs due to leakage or baseline-only use.",
        ],
    }
    (config.PREPROCESSING_DIR / "feature_engineering_config.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def save_excluded_feature_manifest() -> None:
    rows = [
        {"column_name": "FIRST_BREAK_AMPLIT", "reason": "label_adjacent_leakage_risk"},
        {"column_name": "FIRST_BREAK_VELOCITY", "reason": "label_adjacent_leakage_risk"},
        {"column_name": "MODELLED_BREAK_TIME", "reason": "baseline_only_not_model_input"},
        {"column_name": "REC_PEG", "reason": "identifier_not_physical_feature"},
        {"column_name": "SHOT_PEG", "reason": "identifier_not_physical_feature"},
        {"column_name": "SHOTID", "reason": "identifier_not_physical_feature"},
    ]
    pd.DataFrame(rows).to_csv(
        config.PREPROCESSING_DIR / "excluded_model_features.csv",
        index=False,
    )


def run_feature_engineering() -> None:
    config.ensure_output_dirs()
    save_feature_config()
    save_excluded_feature_manifest()

    overview_rows = []
    for asset_key in config.DATASET_ASSETS.keys():
        print(f"[03_feature_engineering] Processing {asset_key}")
        overview_rows.append(engineer_asset_features(asset_key))
        print(f"[03_feature_engineering] Completed {asset_key}")

    pd.DataFrame(overview_rows).to_csv(
        config.PREPROCESSING_DIR / "feature_engineering_overview_all_assets.csv",
        index=False,
    )

    report_sections = []
    for asset_key in config.DATASET_ASSETS.keys():
        report_path = config.PREPROCESSING_DIR / f"feature_engineering_report_{asset_key}.txt"
        if report_path.exists():
            report_sections.append(f"===== {asset_key.upper()} =====")
            report_sections.append(report_path.read_text(encoding="utf-8"))
            report_sections.append("")
    if report_sections:
        (config.PREPROCESSING_DIR / "feature_engineering_report_all_assets.txt").write_text(
            "\n".join(report_sections).strip() + "\n",
            encoding="utf-8",
        )

    print(f"[03_feature_engineering] All outputs written to: {config.PREPROCESSING_DIR}")


if __name__ == "__main__":
    run_feature_engineering()
