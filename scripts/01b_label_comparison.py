from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


SCATTER_SAMPLE_SIZE = 50_000


def flatten_1d(ds: h5py.Dataset) -> np.ndarray:
    return np.asarray(ds[:]).reshape(-1)


def safe_scale(scale_arr: np.ndarray) -> np.ndarray:
    scale = np.asarray(scale_arr, dtype=np.float64)
    bad = (scale == 0) | ~np.isfinite(scale)
    if bad.any():
        scale = scale.copy()
        scale[bad] = 1.0
    return scale


def rmse(arr: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(arr)))) if arr.size else math.nan


def pct_within(arr: np.ndarray, threshold: float) -> float:
    return float(100.0 * np.mean(arr <= threshold)) if arr.size else math.nan


def choose_label_recommendation(spare1: np.ndarray, first_break_time: np.ndarray) -> str:
    if spare1.size == 0:
        return "no_labeled_traces"
    if np.all(first_break_time == 0):
        return "SPARE1"
    diff = first_break_time - spare1
    if np.all(diff == 0):
        return "FIRST_BREAK_TIME"
    if np.allclose(diff, 0.0, atol=1e-6):
        return "FIRST_BREAK_TIME"
    return "review_required_nonzero_difference"


def summarize_auxiliary_field(name: str, arr: np.ndarray) -> Dict[str, float | str]:
    return {
        "field_name": name,
        "count": int(arr.size),
        "min": float(np.min(arr)) if arr.size else math.nan,
        "max": float(np.max(arr)) if arr.size else math.nan,
        "mean": float(np.mean(arr)) if arr.size else math.nan,
        "median": float(np.median(arr)) if arr.size else math.nan,
        "std": float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
    }


def plot_label_scatter(asset_key: str, spare1: np.ndarray, first_break_time: np.ndarray, out_path: Path) -> None:
    sample_size = min(SCATTER_SAMPLE_SIZE, spare1.size)
    rng = np.random.default_rng(config.RANDOM_SEED)
    idx = np.sort(rng.choice(spare1.size, size=sample_size, replace=False))
    x = spare1[idx]
    y = first_break_time[idx]
    plt.figure(figsize=(7, 6))
    plt.scatter(x, y, s=4, alpha=0.25, color="#1f77b4")
    min_v = float(min(np.min(x), np.min(y)))
    max_v = float(max(np.max(x), np.max(y)))
    plt.plot([min_v, max_v], [min_v, max_v], linestyle="--", color="#d62728", linewidth=1)
    plt.xlabel("SPARE1")
    plt.ylabel("FIRST_BREAK_TIME")
    plt.title(f"{asset_key} SPARE1 vs FIRST_BREAK_TIME")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_model_error_hist(asset_key: str, abs_error: np.ndarray, out_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    plt.hist(abs_error, bins=120, color="#2ca02c", alpha=0.9)
    plt.xlabel("Absolute Error (ms)")
    plt.ylabel("Count")
    plt.title(f"{asset_key} MODELLED_BREAK_TIME absolute error")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def combine_tables(prefixes: List[str]) -> None:
    asset_keys = list(config.DATASET_ASSETS.keys())
    for prefix in prefixes:
        frames = []
        for asset_key in asset_keys:
            path = config.EDA_DIR / f"{prefix}_{asset_key}.csv"
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                continue
            if "asset" not in df.columns:
                df.insert(0, "asset", asset_key)
            frames.append(df)
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(
                config.EDA_DIR / f"{prefix}_all_assets.csv",
                index=False,
            )


def combine_reports(asset_keys: List[str]) -> None:
    sections: List[str] = []
    for asset_key in asset_keys:
        path = config.EDA_DIR / f"label_investigation_report_{asset_key}.txt"
        if not path.exists():
            continue
        sections.append(f"===== {asset_key.upper()} =====")
        sections.append(path.read_text(encoding="utf-8"))
        sections.append("")
    if sections:
        (config.EDA_DIR / "label_investigation_report_all_assets.txt").write_text(
            "\n".join(sections).strip() + "\n",
            encoding="utf-8",
        )


def combine_graph_panels(asset_keys: List[str], prefix: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    used = 0
    for ax, asset_key in zip(axes, asset_keys):
        path = config.EDA_DIR / f"{prefix}_{asset_key}.png"
        if not path.exists():
            ax.axis("off")
            continue
        img = plt.imread(path)
        ax.imshow(img)
        ax.set_title(asset_key)
        ax.axis("off")
        used += 1
    for ax in axes[len(asset_keys):]:
        ax.axis("off")
    if used:
        plt.tight_layout()
        plt.savefig(config.EDA_DIR / f"{prefix}_all_assets.png", dpi=150)
    plt.close(fig)


def analyze_asset(asset_key: str) -> Dict[str, object]:
    path = config.get_asset_path(asset_key)
    sentinels = config.UNLABELED_SENTINELS_BY_ASSET[asset_key]

    with h5py.File(path, "r") as h5f:
        g = h5f["TRACE_DATA"]["DEFAULT"]

        spare1 = flatten_1d(g["SPARE1"]).astype(np.float64)
        first_break_time = flatten_1d(g["FIRST_BREAK_TIME"]).astype(np.float64)
        modelled_break_time = flatten_1d(g["MODELLED_BREAK_TIME"]).astype(np.float64)
        offset_flt = flatten_1d(g["OFFSET_FLT"]).astype(np.float64)
        offset_int = flatten_1d(g["OFFSET"]).astype(np.float64)
        coord_scale = safe_scale(flatten_1d(g["COORD_SCALE"]).astype(np.float64))
        source_x_raw = flatten_1d(g["SOURCE_X"]).astype(np.float64)
        source_y_raw = flatten_1d(g["SOURCE_Y"]).astype(np.float64)
        rec_x_raw = flatten_1d(g["REC_X"]).astype(np.float64)
        rec_y_raw = flatten_1d(g["REC_Y"]).astype(np.float64)
        source_x = source_x_raw / np.abs(coord_scale)
        source_y = source_y_raw / np.abs(coord_scale)
        rec_x = rec_x_raw / np.abs(coord_scale)
        rec_y = rec_y_raw / np.abs(coord_scale)
        derived_offset_scaled = np.sqrt((source_x - rec_x) ** 2 + (source_y - rec_y) ** 2)
        derived_offset_raw = np.sqrt((source_x_raw - rec_x_raw) ** 2 + (source_y_raw - rec_y_raw) ** 2)

        labeled_mask = spare1 > 0
        spare1_labeled = spare1[labeled_mask]
        first_break_labeled = first_break_time[labeled_mask]
        modelled_labeled = modelled_break_time[labeled_mask]

        diff = first_break_labeled - spare1_labeled
        abs_diff = np.abs(diff)
        identical_count = int(np.sum(diff == 0))
        nonzero_count = int(np.sum(diff != 0))

        recommended_label_column = choose_label_recommendation(spare1_labeled, first_break_labeled)
        label_comparison_df = pd.DataFrame(
            [
                {
                    "asset": asset_key,
                    "labeled_trace_count": int(diff.size),
                    "first_break_time_nonzero_count_on_labeled": int(np.sum(first_break_labeled != 0)),
                    "modelled_break_time_nonzero_count_on_labeled": int(np.sum(modelled_labeled != 0)),
                    "difference_mean": float(np.mean(diff)) if diff.size else math.nan,
                    "difference_std": float(np.std(diff, ddof=1)) if diff.size > 1 else 0.0,
                    "difference_min": float(np.min(diff)) if diff.size else math.nan,
                    "difference_max": float(np.max(diff)) if diff.size else math.nan,
                    "absolute_difference_mean": float(np.mean(abs_diff)) if abs_diff.size else math.nan,
                    "absolute_difference_median": float(np.median(abs_diff)) if abs_diff.size else math.nan,
                    "count_identical_zero_difference": identical_count,
                    "count_nonzero_difference": nonzero_count,
                    "fraction_identical": float(identical_count / diff.size) if diff.size else math.nan,
                    "recommended_label_column": recommended_label_column,
                    "unlabeled_sentinels": json.dumps(list(sentinels)),
                }
            ]
        )
        label_comparison_df.to_csv(config.EDA_DIR / f"label_comparison_{asset_key}.csv", index=False)

        plot_label_scatter(
            asset_key=asset_key,
            spare1=spare1_labeled,
            first_break_time=first_break_labeled,
            out_path=config.EDA_DIR / f"label_comparison_scatter_{asset_key}.png",
        )

        # MODELLED_BREAK_TIME baseline against both columns, with the recommended label marked explicitly.
        model_error_first_break = modelled_labeled - first_break_labeled
        abs_error_first_break = np.abs(model_error_first_break)
        model_error_spare1 = modelled_labeled - spare1_labeled
        abs_error_spare1 = np.abs(model_error_spare1)

        baseline_df = pd.DataFrame(
            [
                {
                    "asset": asset_key,
                    "target_label_column": "FIRST_BREAK_TIME",
                    "is_recommended_target": recommended_label_column == "FIRST_BREAK_TIME",
                    "trace_count": int(abs_error_first_break.size),
                    "mae_ms": float(np.mean(abs_error_first_break)) if abs_error_first_break.size else math.nan,
                    "rmse_ms": rmse(model_error_first_break),
                    "median_absolute_error_ms": float(np.median(abs_error_first_break))
                    if abs_error_first_break.size
                    else math.nan,
                    "pct_within_5ms": pct_within(abs_error_first_break, 5.0),
                    "pct_within_10ms": pct_within(abs_error_first_break, 10.0),
                    "pct_within_20ms": pct_within(abs_error_first_break, 20.0),
                    "pct_within_50ms": pct_within(abs_error_first_break, 50.0),
                },
                {
                    "asset": asset_key,
                    "target_label_column": "SPARE1",
                    "is_recommended_target": recommended_label_column == "SPARE1",
                    "trace_count": int(abs_error_spare1.size),
                    "mae_ms": float(np.mean(abs_error_spare1)) if abs_error_spare1.size else math.nan,
                    "rmse_ms": rmse(model_error_spare1),
                    "median_absolute_error_ms": float(np.median(abs_error_spare1))
                    if abs_error_spare1.size
                    else math.nan,
                    "pct_within_5ms": pct_within(abs_error_spare1, 5.0),
                    "pct_within_10ms": pct_within(abs_error_spare1, 10.0),
                    "pct_within_20ms": pct_within(abs_error_spare1, 20.0),
                    "pct_within_50ms": pct_within(abs_error_spare1, 50.0),
                },
            ]
        )
        baseline_df.to_csv(config.EDA_DIR / f"modelled_break_time_baseline_{asset_key}.csv", index=False)
        plot_model_error_hist(
            asset_key=asset_key,
            abs_error=abs_error_first_break,
            out_path=config.EDA_DIR / f"modelled_break_time_error_hist_{asset_key}.png",
        )

        # Auxiliary fields exist in every asset except Halfmile.
        auxiliary_rows: List[Dict[str, float | str]] = []
        for field_name in ["FIRST_BREAK_AMPLIT", "FIRST_BREAK_VELOCITY"]:
            if field_name in g:
                arr = flatten_1d(g[field_name]).astype(np.float64)[labeled_mask]
                row = summarize_auxiliary_field(field_name, arr)
                row["asset"] = asset_key
                row["use_as_training_feature"] = "no_label_adjacent"
                auxiliary_rows.append(row)
        auxiliary_df = pd.DataFrame(auxiliary_rows)
        auxiliary_df.to_csv(config.EDA_DIR / f"first_break_auxiliary_stats_{asset_key}.csv", index=False)

        # Offset cross-check: measure which stored offset column is actually usable.
        offset_rows = []
        for stored_name, stored_arr, derived_name, derived_arr in [
            ("OFFSET_FLT", offset_flt, "derived_offset_scaled", derived_offset_scaled),
            ("OFFSET", offset_int, "derived_offset_raw", derived_offset_raw),
            ("OFFSET", offset_int, "derived_offset_scaled", derived_offset_scaled),
        ]:
            offset_diff = stored_arr - derived_arr
            abs_offset_diff = np.abs(offset_diff)
            offset_rows.append(
                {
                    "asset": asset_key,
                    "stored_offset_column": stored_name,
                    "derived_offset_reference": derived_name,
                    "trace_count": int(offset_diff.size),
                    "stored_nonzero_count": int(np.sum(stored_arr != 0)),
                    "stored_nonzero_pct": float(100.0 * np.mean(stored_arr != 0)),
                    "difference_mean": float(np.mean(offset_diff)),
                    "difference_std": float(np.std(offset_diff, ddof=1)) if offset_diff.size > 1 else 0.0,
                    "difference_min": float(np.min(offset_diff)),
                    "difference_max": float(np.max(offset_diff)),
                    "absolute_difference_mean": float(np.mean(abs_offset_diff)),
                    "absolute_difference_median": float(np.median(abs_offset_diff)),
                    "count_abs_diff_gt_1m": int(np.sum(abs_offset_diff > 1.0)),
                    "pct_abs_diff_gt_1m": float(100.0 * np.mean(abs_offset_diff > 1.0)),
                }
            )
        offset_cross_check_df = pd.DataFrame(offset_rows)
        offset_cross_check_df.to_csv(config.EDA_DIR / f"offset_cross_check_{asset_key}.csv", index=False)

        report_lines = [
            f"Asset: {asset_key}",
            f"File: {path.name}",
            f"Unlabeled sentinels: {list(sentinels)}",
            "",
            "SPARE1 vs FIRST_BREAK_TIME:",
            label_comparison_df.to_string(index=False),
            "",
            "MODELLED_BREAK_TIME baseline:",
            baseline_df.to_string(index=False),
            "",
            "Offset cross-check:",
            offset_cross_check_df.to_string(index=False),
        ]
        if not auxiliary_df.empty:
            report_lines.extend(
                [
                    "",
                    "Auxiliary first-break fields:",
                    auxiliary_df.to_string(index=False),
                ]
            )
        (config.EDA_DIR / f"label_investigation_report_{asset_key}.txt").write_text(
            "\n".join(report_lines) + "\n",
            encoding="utf-8",
        )

        return {
            "asset": asset_key,
            "recommended_label_column": recommended_label_column,
            "labeled_trace_count": int(diff.size),
            "identical_count": identical_count,
            "nonzero_difference_count": nonzero_count,
            "baseline_mae_recommended_ms": baseline_df.loc[
                baseline_df["is_recommended_target"], "mae_ms"
            ].iloc[0],
            "baseline_rmse_recommended_ms": baseline_df.loc[
                baseline_df["is_recommended_target"], "rmse_ms"
            ].iloc[0],
            "offset_pct_abs_diff_gt_1m_best_match": offset_cross_check_df["pct_abs_diff_gt_1m"].min(),
        }


def run() -> None:
    config.ensure_output_dirs()
    asset_keys = list(config.DATASET_ASSETS.keys())
    overview_rows = []
    for asset_key in asset_keys:
        print(f"[01b_label_comparison] Processing {asset_key}")
        overview_rows.append(analyze_asset(asset_key))
        print(f"[01b_label_comparison] Completed {asset_key}")

    combine_tables(
        [
            "label_comparison",
            "modelled_break_time_baseline",
            "first_break_auxiliary_stats",
            "offset_cross_check",
        ]
    )
    combine_reports(asset_keys)
    combine_graph_panels(asset_keys, "label_comparison_scatter")
    combine_graph_panels(asset_keys, "modelled_break_time_error_hist")

    pd.DataFrame(overview_rows).to_csv(
        config.EDA_DIR / "label_investigation_overview_all_assets.csv",
        index=False,
    )
    print(f"[01b_label_comparison] Outputs written to: {config.EDA_DIR}")


if __name__ == "__main__":
    run()
