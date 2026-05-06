from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import h5py
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


TRACE_METADATA_COLUMNS = [
    "asset",
    "trace_index",
    "gather_sequence_index",
    "trace_index_within_gather",
    "shot_id",
    "shot_peg",
    "rec_peg",
    "source_x",
    "source_y",
    "source_ht",
    "rec_x",
    "rec_y",
    "rec_ht",
    "elevation_diff",
    "offset",
    "samp_rate_us",
    "samp_num",
    "recording_time_ms",
    "label_column",
    "label_ms",
    "first_break_sample",
    "exclude_from_training",
]

INFERENCE_METADATA_COLUMNS = [
    "asset",
    "trace_index",
    "gather_sequence_index",
    "trace_index_within_gather",
    "shot_id",
    "shot_peg",
    "rec_peg",
    "source_x",
    "source_y",
    "source_ht",
    "rec_x",
    "rec_y",
    "rec_ht",
    "elevation_diff",
    "offset",
    "samp_rate_us",
    "samp_num",
    "recording_time_ms",
    "label_column",
    "label_ms",
    "label_status",
]

GATHER_METADATA_COLUMNS = [
    "asset",
    "gather_sequence_index",
    "shot_id",
    "shot_x",
    "shot_y",
    "number_of_traces",
    "offset_min",
    "offset_max",
    "is_small_gather",
    "exclude_from_training",
]


def safe_scale(scale_arr: np.ndarray) -> np.ndarray:
    scale = np.asarray(scale_arr, dtype=np.float64)
    bad = (scale == 0) | ~np.isfinite(scale)
    if bad.any():
        scale = scale.copy()
        scale[bad] = 1.0
    return scale


def init_csv(path: Path, columns: List[str]) -> None:
    if path.exists():
        path.unlink()
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def append_frame(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    frame.to_csv(path, mode="a", header=False, index=False)


def empty_chunk_store() -> Dict[str, np.ndarray]:
    return {}


def concat_store(store: Dict[str, np.ndarray], update: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    if not update:
        return store
    if not store:
        return {key: value.copy() for key, value in update.items()}
    out: Dict[str, np.ndarray] = {}
    for key in store.keys():
        out[key] = np.concatenate([store[key], update[key]])
    return out


def subset_columns(columns: Dict[str, np.ndarray], mask: np.ndarray) -> Dict[str, np.ndarray]:
    if not np.any(mask):
        return {}
    return {key: value[mask] for key, value in columns.items()}


def sort_store_by_offset(store: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    if not store:
        return store
    order = np.argsort(store["offset"], kind="stable")
    return {key: value[order] for key, value in store.items()}


def get_min_gather_traces(asset_key: str) -> int:
    return config.MIN_GATHER_TRACES_BY_ASSET.get(asset_key, config.MIN_GATHER_TRACES)


def flush_shot(
    asset_key: str,
    gather_sequence_index: int,
    valid_store: Dict[str, np.ndarray],
    inference_store: Dict[str, np.ndarray],
    valid_path: Path,
    inference_path: Path,
    gather_path: Path,
    summary: Dict[str, float],
) -> None:
    if valid_store:
        sorted_valid = sort_store_by_offset(valid_store)
        trace_count = len(sorted_valid["trace_index"])
        exclude_from_training = trace_count < get_min_gather_traces(asset_key)
        valid_df = pd.DataFrame(
            {
                "asset": asset_key,
                "trace_index": sorted_valid["trace_index"],
                "gather_sequence_index": gather_sequence_index,
                "trace_index_within_gather": np.arange(trace_count, dtype=np.int64),
                "shot_id": sorted_valid["shot_id"],
                "shot_peg": sorted_valid["shot_peg"],
                "rec_peg": sorted_valid["rec_peg"],
                "source_x": sorted_valid["source_x"],
                "source_y": sorted_valid["source_y"],
                "source_ht": sorted_valid["source_ht"],
                "rec_x": sorted_valid["rec_x"],
                "rec_y": sorted_valid["rec_y"],
                "rec_ht": sorted_valid["rec_ht"],
                "elevation_diff": sorted_valid["elevation_diff"],
                "offset": sorted_valid["offset"],
                "samp_rate_us": sorted_valid["samp_rate_us"],
                "samp_num": sorted_valid["samp_num"],
                "recording_time_ms": sorted_valid["recording_time_ms"],
                "label_column": config.WORKING_LABEL_COLUMN,
                "label_ms": sorted_valid["label_ms"],
                "first_break_sample": sorted_valid["first_break_sample"],
                "exclude_from_training": exclude_from_training,
            }
        )
        append_frame(valid_path, valid_df[TRACE_METADATA_COLUMNS])

        gather_df = pd.DataFrame(
            {
                "asset": [asset_key],
                "gather_sequence_index": [gather_sequence_index],
                "shot_id": [int(sorted_valid["shot_id"][0])],
                "shot_x": [float(sorted_valid["source_x"][0])],
                "shot_y": [float(sorted_valid["source_y"][0])],
                "number_of_traces": [trace_count],
                "offset_min": [float(np.min(sorted_valid["offset"]))],
                "offset_max": [float(np.max(sorted_valid["offset"]))],
                "is_small_gather": [exclude_from_training],
                "exclude_from_training": [exclude_from_training],
            }
        )
        append_frame(gather_path, gather_df[GATHER_METADATA_COLUMNS])

        summary["valid_labeled_kept"] += trace_count
        summary["valid_gather_count"] += 1
        if exclude_from_training:
            summary["small_gather_count"] += 1
            summary["small_gather_trace_count"] += trace_count

    if inference_store:
        sorted_inference = sort_store_by_offset(inference_store)
        trace_count = len(sorted_inference["trace_index"])
        inference_df = pd.DataFrame(
            {
                "asset": asset_key,
                "trace_index": sorted_inference["trace_index"],
                "gather_sequence_index": gather_sequence_index,
                "trace_index_within_gather": np.arange(trace_count, dtype=np.int64),
                "shot_id": sorted_inference["shot_id"],
                "shot_peg": sorted_inference["shot_peg"],
                "rec_peg": sorted_inference["rec_peg"],
                "source_x": sorted_inference["source_x"],
                "source_y": sorted_inference["source_y"],
                "source_ht": sorted_inference["source_ht"],
                "rec_x": sorted_inference["rec_x"],
                "rec_y": sorted_inference["rec_y"],
                "rec_ht": sorted_inference["rec_ht"],
                "elevation_diff": sorted_inference["elevation_diff"],
                "offset": sorted_inference["offset"],
                "samp_rate_us": sorted_inference["samp_rate_us"],
                "samp_num": sorted_inference["samp_num"],
                "recording_time_ms": sorted_inference["recording_time_ms"],
                "label_column": config.WORKING_LABEL_COLUMN,
                "label_ms": sorted_inference["label_ms"],
                "label_status": sorted_inference["label_status"],
            }
        )
        append_frame(inference_path, inference_df[INFERENCE_METADATA_COLUMNS])
        summary["inference_unlabeled_kept"] += trace_count


def iter_chunk_ranges(size: int, chunk_size: int) -> Iterable[tuple[int, int]]:
    for start in range(0, size, chunk_size):
        end = min(start + chunk_size, size)
        yield start, end


def analyze_asset(asset_key: str) -> Dict[str, float]:
    asset_path = config.get_asset_path(asset_key)
    unlabeled_sentinels = np.array(config.UNLABELED_SENTINELS_BY_ASSET[asset_key], dtype=np.float64)
    primary_offset_column = "derived_from_coordinates"
    valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    inference_path = config.PREPROCESSING_DIR / f"inference_trace_metadata_{asset_key}.csv"
    gather_path = config.PREPROCESSING_DIR / f"gather_metadata_{asset_key}.csv"
    removal_path = config.PREPROCESSING_DIR / f"removed_trace_counts_{asset_key}.csv"
    summary_path = config.PREPROCESSING_DIR / f"preprocessing_summary_{asset_key}.csv"
    report_path = config.PREPROCESSING_DIR / f"preprocessing_report_{asset_key}.txt"

    init_csv(valid_path, TRACE_METADATA_COLUMNS)
    init_csv(inference_path, INFERENCE_METADATA_COLUMNS)
    init_csv(gather_path, GATHER_METADATA_COLUMNS)

    summary: Dict[str, float] = {
        "total_traces": 0,
        "removed_spare1_zero": 0,
        "removed_spare1_minus_one": 0,
        "removed_spare1_gt_recording_time": 0,
        "removed_dead_trace": 0,
        "removed_missing_source_geometry": 0,
        "removed_missing_receiver_geometry": 0,
        "removed_first_break_sample_out_of_bounds": 0,
        "removed_any_reason": 0,
        "valid_labeled_kept": 0,
        "inference_unlabeled_kept": 0,
        "valid_gather_count": 0,
        "small_gather_count": 0,
        "small_gather_trace_count": 0,
        "coord_scale_varies_flag": 0,
        "ht_scale_varies_flag": 0,
    }
    coord_scale_values: set[float] = set()
    ht_scale_values: set[float] = set()

    current_shot_id: int | None = None
    current_valid_store = empty_chunk_store()
    current_inference_store = empty_chunk_store()
    gather_sequence_index = 0

    with h5py.File(asset_path, "r") as h5f:
        group = h5f["TRACE_DATA"]["DEFAULT"]
        trace_count = group["SHOTID"].shape[0]
        summary["total_traces"] = trace_count

        for start, end in iter_chunk_ranges(trace_count, config.PREPROCESSING_CHUNK_SIZE):
            shot_id = np.asarray(group["SHOTID"][start:end], dtype=np.int64).reshape(-1)
            shot_peg = np.asarray(group["SHOT_PEG"][start:end], dtype=np.float64).reshape(-1)
            rec_peg = np.asarray(group["REC_PEG"][start:end], dtype=np.float64).reshape(-1)
            label_ms = np.asarray(group[config.WORKING_LABEL_COLUMN][start:end], dtype=np.float64).reshape(-1)
            samp_rate_us = np.asarray(group["SAMP_RATE"][start:end], dtype=np.float64).reshape(-1)
            samp_num = np.asarray(group["SAMP_NUM"][start:end], dtype=np.int64).reshape(-1)
            coord_scale = safe_scale(np.asarray(group["COORD_SCALE"][start:end], dtype=np.float64).reshape(-1))
            ht_scale = safe_scale(np.asarray(group["HT_SCALE"][start:end], dtype=np.float64).reshape(-1))
            source_x_raw = np.asarray(group["SOURCE_X"][start:end], dtype=np.float64).reshape(-1)
            source_y_raw = np.asarray(group["SOURCE_Y"][start:end], dtype=np.float64).reshape(-1)
            source_ht_raw = np.asarray(group["SOURCE_HT"][start:end], dtype=np.float64).reshape(-1)
            rec_x_raw = np.asarray(group["REC_X"][start:end], dtype=np.float64).reshape(-1)
            rec_y_raw = np.asarray(group["REC_Y"][start:end], dtype=np.float64).reshape(-1)
            rec_ht_raw = np.asarray(group["REC_HT"][start:end], dtype=np.float64).reshape(-1)
            # HT_SCALE note: raw HT values = elevation_metres * abs(HT_SCALE).
            # Division by abs(HT_SCALE) yields elevation in metres.
            # Halfmile HT_SCALE = -10000: verified correct, raw values are in 0.1mm units.
            # Brunswick/Lalor HT_SCALE = -10: raw values are in 0.1m units.
            # Sudbury HT_SCALE = 10: raw values are in 0.1m units (positive scale).
            source_x = source_x_raw / np.abs(coord_scale)
            source_y = source_y_raw / np.abs(coord_scale)
            source_ht = source_ht_raw / np.abs(ht_scale)
            rec_x = rec_x_raw / np.abs(coord_scale)
            rec_y = rec_y_raw / np.abs(coord_scale)
            rec_ht = rec_ht_raw / np.abs(ht_scale)
            elevation_diff = source_ht - rec_ht
            recording_time_ms = samp_num * samp_rate_us / 1000.0
            traces = np.asarray(group["data_array"][start:end, :], dtype=np.float32)
            offset = np.sqrt((source_x - rec_x) ** 2 + (source_y - rec_y) ** 2)

            coord_scale_values.update(np.unique(coord_scale).tolist())
            ht_scale_values.update(np.unique(ht_scale).tolist())

            dead_trace = np.all(traces == 0, axis=1)
            missing_source_geometry = (source_x == 0) & (source_y == 0)
            missing_receiver_geometry = (rec_x == 0) & (rec_y == 0)
            spare1_zero = label_ms == 0
            spare1_minus_one = label_ms == -1
            unlabeled_mask = np.isin(label_ms, unlabeled_sentinels)
            positive_label = label_ms > 0
            spare1_gt_recording_time = positive_label & (label_ms > recording_time_ms)
            first_break_sample = np.rint(label_ms / (samp_rate_us / 1000.0)).astype(np.int64)
            first_break_sample_out_of_bounds = positive_label & (
                (first_break_sample < 0) | (first_break_sample >= samp_num)
            )
            summary["removed_spare1_zero"] += int(spare1_zero.sum())
            summary["removed_spare1_minus_one"] += int(spare1_minus_one.sum())
            summary["removed_spare1_gt_recording_time"] += int(spare1_gt_recording_time.sum())
            summary["removed_dead_trace"] += int(dead_trace.sum())
            summary["removed_missing_source_geometry"] += int(missing_source_geometry.sum())
            summary["removed_missing_receiver_geometry"] += int(missing_receiver_geometry.sum())
            summary["removed_first_break_sample_out_of_bounds"] += int(first_break_sample_out_of_bounds.sum())

            removed_any = (
                unlabeled_mask
                | spare1_gt_recording_time
                | dead_trace
                | missing_source_geometry
                | missing_receiver_geometry
                | first_break_sample_out_of_bounds
            )
            summary["removed_any_reason"] += int(removed_any.sum())

            valid_labeled = (
                positive_label
                & ~unlabeled_mask
                & ~spare1_gt_recording_time
                & ~dead_trace
                & ~missing_source_geometry
                & ~missing_receiver_geometry
                & ~first_break_sample_out_of_bounds
            )
            inference_unlabeled = (
                unlabeled_mask
                & ~missing_source_geometry
                & ~missing_receiver_geometry
            )

            trace_index = np.arange(start, end, dtype=np.int64)
            label_status = np.full(len(label_ms), "labeled", dtype=object)
            for sentinel in unlabeled_sentinels:
                label_status = np.where(label_ms == sentinel, f"sentinel_{int(sentinel)}", label_status)
            label_status = np.where(dead_trace, "dead_trace", label_status)

            common_columns = {
                "trace_index": trace_index,
                "shot_id": shot_id,
                "shot_peg": shot_peg,
                "rec_peg": rec_peg,
                "source_x": source_x,
                "source_y": source_y,
                "source_ht": source_ht,
                "rec_x": rec_x,
                "rec_y": rec_y,
                "rec_ht": rec_ht,
                "elevation_diff": elevation_diff,
                "offset": offset,
                "samp_rate_us": samp_rate_us,
                "samp_num": samp_num,
                "recording_time_ms": recording_time_ms,
                "label_ms": label_ms,
            }
            valid_columns = {
                **common_columns,
                "first_break_sample": first_break_sample,
            }
            inference_columns = {
                **common_columns,
                "label_status": label_status,
            }

            boundaries = np.where(np.diff(shot_id) != 0)[0] + 1
            split_points = np.concatenate(([0], boundaries, [len(shot_id)]))

            for i in range(len(split_points) - 1):
                seg_start = split_points[i]
                seg_end = split_points[i + 1]
                seg_shot_id = int(shot_id[seg_start])

                valid_segment = subset_columns(
                    {key: value[seg_start:seg_end] for key, value in valid_columns.items()},
                    valid_labeled[seg_start:seg_end],
                )
                inference_segment = subset_columns(
                    {key: value[seg_start:seg_end] for key, value in inference_columns.items()},
                    inference_unlabeled[seg_start:seg_end],
                )

                if current_shot_id is None:
                    current_shot_id = seg_shot_id

                if seg_shot_id != current_shot_id:
                    flush_shot(
                        asset_key=asset_key,
                        gather_sequence_index=gather_sequence_index,
                        valid_store=current_valid_store,
                        inference_store=current_inference_store,
                        valid_path=valid_path,
                        inference_path=inference_path,
                        gather_path=gather_path,
                        summary=summary,
                    )
                    gather_sequence_index += 1
                    current_shot_id = seg_shot_id
                    current_valid_store = empty_chunk_store()
                    current_inference_store = empty_chunk_store()

                current_valid_store = concat_store(current_valid_store, valid_segment)
                current_inference_store = concat_store(current_inference_store, inference_segment)

        if current_shot_id is not None:
            flush_shot(
                asset_key=asset_key,
                gather_sequence_index=gather_sequence_index,
                valid_store=current_valid_store,
                inference_store=current_inference_store,
                valid_path=valid_path,
                inference_path=inference_path,
                gather_path=gather_path,
                summary=summary,
            )

    summary["coord_scale_varies_flag"] = int(len(coord_scale_values) > 1)
    summary["ht_scale_varies_flag"] = int(len(ht_scale_values) > 1)

    removal_rows = [
        {"asset": asset_key, "reason": "spare1_zero", "count": int(summary["removed_spare1_zero"])},
        {"asset": asset_key, "reason": "spare1_minus_one", "count": int(summary["removed_spare1_minus_one"])},
        {
            "asset": asset_key,
            "reason": "spare1_gt_recording_time",
            "count": int(summary["removed_spare1_gt_recording_time"]),
        },
        {"asset": asset_key, "reason": "dead_trace", "count": int(summary["removed_dead_trace"])},
        {
            "asset": asset_key,
            "reason": "missing_source_geometry",
            "count": int(summary["removed_missing_source_geometry"]),
        },
        {
            "asset": asset_key,
            "reason": "missing_receiver_geometry",
            "count": int(summary["removed_missing_receiver_geometry"]),
        },
        {
            "asset": asset_key,
            "reason": "first_break_sample_out_of_bounds",
            "count": int(summary["removed_first_break_sample_out_of_bounds"]),
        },
        {"asset": asset_key, "reason": "removed_any_reason", "count": int(summary["removed_any_reason"])},
    ]
    pd.DataFrame(removal_rows).to_csv(removal_path, index=False)

    summary_df = pd.DataFrame(
        [
            {
                "asset": asset_key,
                "total_traces": int(summary["total_traces"]),
                "valid_labeled_kept": int(summary["valid_labeled_kept"]),
                "inference_unlabeled_kept": int(summary["inference_unlabeled_kept"]),
                "valid_gather_count": int(summary["valid_gather_count"]),
                "small_gather_count": int(summary["small_gather_count"]),
                "small_gather_trace_count": int(summary["small_gather_trace_count"]),
                "coord_scale_unique_count": len(coord_scale_values),
                "coord_scale_values": json.dumps(sorted(coord_scale_values)[:20]),
                "coord_scale_varies_flag": bool(summary["coord_scale_varies_flag"]),
                "ht_scale_unique_count": len(ht_scale_values),
                "ht_scale_values": json.dumps(sorted(ht_scale_values)[:20]),
                "ht_scale_varies_flag": bool(summary["ht_scale_varies_flag"]),
                "min_gather_traces": get_min_gather_traces(asset_key),
                "working_label_column": config.WORKING_LABEL_COLUMN,
                "primary_offset_column": primary_offset_column,
                "normalization_method": config.NORMALIZATION_METHOD,
                "trace_harmonization_strategy": config.TRACE_HARMONIZATION_STRATEGY,
            }
        ]
    )
    summary_df.to_csv(summary_path, index=False)

    report_lines = [
        f"Asset: {asset_key}",
        f"File: {asset_path.name}",
        f"Total traces: {int(summary['total_traces'])}",
        f"Valid labeled kept: {int(summary['valid_labeled_kept'])}",
        f"Inference unlabeled kept: {int(summary['inference_unlabeled_kept'])}",
        f"Removed (any reason): {int(summary['removed_any_reason'])}",
        f"Small gather threshold: {get_min_gather_traces(asset_key)}",
        f"Small gather count: {int(summary['small_gather_count'])}",
        f"Small gather trace count: {int(summary['small_gather_trace_count'])}",
        f"Working label column: {config.WORKING_LABEL_COLUMN}",
        f"Primary offset column: {primary_offset_column}",
        f"Normalization method for runtime dataset building: {config.NORMALIZATION_METHOD}",
        f"Trace harmonization strategy: {config.TRACE_HARMONIZATION_STRATEGY}",
        f"COORD_SCALE values: {sorted(coord_scale_values)[:20]}",
        f"COORD_SCALE varies flag: {bool(summary['coord_scale_varies_flag'])}",
        f"HT_SCALE values: {sorted(ht_scale_values)[:20]}",
        f"HT_SCALE varies flag: {bool(summary['ht_scale_varies_flag'])}",
        "",
        "Removed counts by reason:",
    ]
    for row in removal_rows:
        report_lines.append(f"  {row['reason']}: {row['count']}")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "asset": asset_key,
        "total_traces": int(summary["total_traces"]),
        "valid_labeled_kept": int(summary["valid_labeled_kept"]),
        "inference_unlabeled_kept": int(summary["inference_unlabeled_kept"]),
        "removed_any_reason": int(summary["removed_any_reason"]),
        "valid_gather_count": int(summary["valid_gather_count"]),
        "small_gather_count": int(summary["small_gather_count"]),
        "small_gather_trace_count": int(summary["small_gather_trace_count"]),
        "coord_scale_varies_flag": bool(summary["coord_scale_varies_flag"]),
        "ht_scale_varies_flag": bool(summary["ht_scale_varies_flag"]),
        "working_label_column": config.WORKING_LABEL_COLUMN,
        "primary_offset_column": primary_offset_column,
        "normalization_method": config.NORMALIZATION_METHOD,
        "trace_harmonization_strategy": config.TRACE_HARMONIZATION_STRATEGY,
    }


def combine_outputs(asset_keys: List[str]) -> None:
    combined_frames = []
    for prefix in [
        "removed_trace_counts",
        "preprocessing_summary",
    ]:
        frames = []
        for asset_key in asset_keys:
            path = config.PREPROCESSING_DIR / f"{prefix}_{asset_key}.csv"
            if path.exists():
                frames.append(pd.read_csv(path))
        if frames:
            combined = pd.concat(frames, ignore_index=True)
            combined.to_csv(config.PREPROCESSING_DIR / f"{prefix}_all_assets.csv", index=False)
            combined_frames.append(prefix)

    report_sections: List[str] = []
    for asset_key in asset_keys:
        path = config.PREPROCESSING_DIR / f"preprocessing_report_{asset_key}.txt"
        if path.exists():
            report_sections.append(f"===== {asset_key.upper()} =====")
            report_sections.append(path.read_text(encoding="utf-8"))
            report_sections.append("")
    if report_sections:
        (config.PREPROCESSING_DIR / "preprocessing_report_all_assets.txt").write_text(
            "\n".join(report_sections).strip() + "\n",
            encoding="utf-8",
        )


def save_normalization_choice() -> None:
    payload = {
        "working_label_column": config.WORKING_LABEL_COLUMN,
        "normalization_method": config.NORMALIZATION_METHOD,
        "primary_offset_column_by_asset": {key: "derived_from_coordinates" for key in config.DATASET_ASSETS},
        "unlabeled_sentinels_by_asset": config.UNLABELED_SENTINELS_BY_ASSET,
        "min_gather_traces_by_asset": config.MIN_GATHER_TRACES_BY_ASSET,
        "trace_harmonization_strategy": config.TRACE_HARMONIZATION_STRATEGY,
        "trace_harmonization_target_samp_rate_us": config.TRACE_HARMONIZATION_TARGET_SAMP_RATE_US,
        "trace_harmonization_target_samp_num": config.TRACE_HARMONIZATION_TARGET_SAMP_NUM,
        "asset_sampling_specs": {
            key: {
                "samp_rate_us": spec.samp_rate_us,
                "samp_num": spec.samp_num,
                "recording_time_ms": spec.recording_time_ms,
            }
            for key, spec in config.ASSET_SAMPLING_SPECS.items()
        },
        "description": (
            "Normalize at runtime during dataset building. "
            "per_trace divides each trace by its own absolute max; "
            "per_gather divides all traces in a gather by the gather absolute max."
        ),
    }
    (config.PREPROCESSING_DIR / "normalization_strategy.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def run_preprocessing() -> None:
    config.ensure_output_dirs()
    save_normalization_choice()

    asset_keys = list(config.DATASET_ASSETS.keys())
    all_rows = []
    for asset_key in asset_keys:
        print(f"[02_preprocessing] Processing {asset_key}")
        all_rows.append(analyze_asset(asset_key))
        print(f"[02_preprocessing] Completed {asset_key}")

    combine_outputs(asset_keys)
    pd.DataFrame(all_rows).to_csv(
        config.PREPROCESSING_DIR / "preprocessing_asset_overview_all_assets.csv",
        index=False,
    )
    print(f"[02_preprocessing] All outputs written to: {config.PREPROCESSING_DIR}")


if __name__ == "__main__":
    run_preprocessing()
