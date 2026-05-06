from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


TRAIN_ASSETS = [key for key, asset in config.DATASET_ASSETS.items() if asset.role == "train"]
EVAL_ASSETS = [key for key, asset in config.DATASET_ASSETS.items() if asset.role in {"validate", "stress_test"}]
SPLIT_FRACTION_TRAIN = 0.85
LALOR_EXPERIMENT_B_TRAIN_FRACTION = config.EXPERIMENT_B_LALOR_TRAIN_FRACTION
LALOR_ASSET_KEY = "lalor"

BANNED_FEATURE_COLUMNS = [
    "source_x_normalized",
    "source_y_normalized",
    "trace_position",
    "total_static",
    "ref_total_static",
    "source_static",
    "rec_static",
    "normalized_label",
    "harmonized_first_break_sample_2ms",
]


def write_shot_ids(path: Path, shot_ids: np.ndarray) -> None:
    text = "\n".join(str(int(v)) for v in shot_ids.tolist()) + "\n"
    path.write_text(text, encoding="utf-8")


def read_shot_ids(path: Path) -> Set[int]:
    return {int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def load_gather_metadata(asset_key: str) -> pd.DataFrame:
    path = config.PREPROCESSING_DIR / f"gather_metadata_{asset_key}.csv"
    df = pd.read_csv(path)
    df = df[df["exclude_from_training"] == False].copy()
    return df


def split_asset_shots(asset_key: str, gather_df: pd.DataFrame) -> Dict[str, object]:
    rng = np.random.default_rng(config.RANDOM_SEED)
    shot_ids = gather_df["shot_id"].drop_duplicates().to_numpy(dtype=np.int64)
    shuffled = rng.permutation(shot_ids)

    n_total = len(shuffled)
    n_train = max(1, int(round(n_total * SPLIT_FRACTION_TRAIN)))
    n_train = min(n_train, n_total - 1) if n_total > 1 else n_total
    train_ids = np.sort(shuffled[:n_train])
    val_ids = np.sort(shuffled[n_train:])

    train_df = gather_df[gather_df["shot_id"].isin(train_ids)]
    val_df = gather_df[gather_df["shot_id"].isin(val_ids)]

    return {
        "asset": asset_key,
        "train_ids": train_ids,
        "val_ids": val_ids,
        "train_gather_count": int(len(train_ids)),
        "val_gather_count": int(len(val_ids)),
        "train_trace_count": int(train_df["number_of_traces"].sum()),
        "val_trace_count": int(val_df["number_of_traces"].sum()),
    }


def _corr(sum_x: float, sum_y: float, sum_x2: float, sum_y2: float, sum_xy: float, n: int) -> float:
    numerator = n * sum_xy - sum_x * sum_y
    denom_left = n * sum_x2 - sum_x * sum_x
    denom_right = n * sum_y2 - sum_y * sum_y
    denom = math.sqrt(max(denom_left, 0.0) * max(denom_right, 0.0))
    if denom == 0:
        return math.nan
    return numerator / denom


def _iter_filtered_feature_chunks(asset_key: str, allowed_shots: Set[int]) -> Iterable[pd.DataFrame]:
    path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
    usecols = ["shot_id", "trace_index", "total_static", "ref_total_static"]
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=250_000):
        filtered = chunk[chunk["shot_id"].isin(allowed_shots)]
        if not filtered.empty:
            yield filtered


def _load_train_labels_for_asset(asset_key: str, allowed_shots: Set[int]) -> pd.DataFrame:
    path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
    usecols = ["shot_id", "trace_index", "label_ms"]
    frames: List[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=250_000):
        filtered = chunk[chunk["shot_id"].isin(allowed_shots)]
        if not filtered.empty:
            frames.append(filtered)
    if not frames:
        return pd.DataFrame(columns=usecols)
    return pd.concat(frames, ignore_index=True)


def _decision_from_abs_corr(abs_corr: float) -> tuple[str, str]:
    if math.isnan(abs_corr):
        return "drop", "constant_or_unusable_drop"
    if abs_corr > 0.90:
        return "drop", "corr_gt_0.90_drop_for_leakage"
    if abs_corr >= 0.30:
        return "keep", "corr_0.30_to_0.90_keep_geologic_signal"
    return "keep", "corr_lt_0.30_keep_weak_signal"


def compute_static_correlations_trainonly(train_shot_map: Dict[str, Set[int]]) -> pd.DataFrame:
    zero_sums = {
        "label_ms": 0.0,
        "total_static": 0.0,
        "ref_total_static": 0.0,
        "label_sq": 0.0,
        "total_sq": 0.0,
        "ref_total_sq": 0.0,
        "label_total": 0.0,
        "label_ref_total": 0.0,
        "count": 0,
    }
    sums = zero_sums.copy()
    asset_rows = []

    for asset_key in TRAIN_ASSETS:
        asset_sums = zero_sums.copy()
        allowed_shots = train_shot_map[asset_key]
        train_labels = _load_train_labels_for_asset(asset_key, allowed_shots)
        if train_labels.empty:
            continue
        label_by_trace_index = train_labels.set_index("trace_index")["label_ms"]

        for filtered in _iter_filtered_feature_chunks(asset_key, allowed_shots):
            merged = filtered.join(label_by_trace_index, on="trace_index", how="inner")
            if merged.empty:
                continue
            label = merged["label_ms"].to_numpy(dtype=np.float64)
            total = merged["total_static"].to_numpy(dtype=np.float64)
            ref_total = merged["ref_total_static"].to_numpy(dtype=np.float64)
            asset_sums["label_ms"] += float(label.sum())
            asset_sums["total_static"] += float(total.sum())
            asset_sums["ref_total_static"] += float(ref_total.sum())
            asset_sums["label_sq"] += float(np.square(label).sum())
            asset_sums["total_sq"] += float(np.square(total).sum())
            asset_sums["ref_total_sq"] += float(np.square(ref_total).sum())
            asset_sums["label_total"] += float((label * total).sum())
            asset_sums["label_ref_total"] += float((label * ref_total).sum())
            asset_sums["count"] += int(len(filtered))

        total_corr_asset = _corr(
            asset_sums["label_ms"],
            asset_sums["total_static"],
            asset_sums["label_sq"],
            asset_sums["total_sq"],
            asset_sums["label_total"],
            asset_sums["count"],
        )
        ref_total_corr_asset = _corr(
            asset_sums["label_ms"],
            asset_sums["ref_total_static"],
            asset_sums["label_sq"],
            asset_sums["ref_total_sq"],
            asset_sums["label_ref_total"],
            asset_sums["count"],
        )
        for feature_name, corr_value in [
            ("total_static", total_corr_asset),
            ("ref_total_static", ref_total_corr_asset),
        ]:
            abs_corr = abs(corr_value) if not math.isnan(corr_value) else math.nan
            decision, reason = _decision_from_abs_corr(abs_corr)
            asset_rows.append(
                {
                    "scope": "asset_train_subset",
                    "asset": asset_key,
                    "feature_name": feature_name,
                    "pearson_corr_with_label": corr_value,
                    "abs_corr_with_label": abs_corr,
                    "decision": decision,
                    "reason": reason,
                    "trace_count": int(asset_sums["count"]),
                }
            )

        for key in sums:
            sums[key] += asset_sums[key]

    total_corr = _corr(
        sums["label_ms"],
        sums["total_static"],
        sums["label_sq"],
        sums["total_sq"],
        sums["label_total"],
        sums["count"],
    )
    ref_total_corr = _corr(
        sums["label_ms"],
        sums["ref_total_static"],
        sums["label_sq"],
        sums["ref_total_sq"],
        sums["label_ref_total"],
        sums["count"],
    )

    total_abs_corr = abs(total_corr) if not math.isnan(total_corr) else math.nan
    total_decision, total_reason = _decision_from_abs_corr(total_abs_corr)
    ref_total_abs_corr = abs(ref_total_corr) if not math.isnan(ref_total_corr) else math.nan
    ref_total_decision, ref_total_reason = _decision_from_abs_corr(ref_total_abs_corr)

    rows = asset_rows + [
        {
            "scope": "combined_train_only",
            "asset": "brunswick+halfmile",
            "feature_name": "total_static",
            "pearson_corr_with_label": total_corr,
            "abs_corr_with_label": total_abs_corr,
            "decision": total_decision,
            "reason": total_reason,
            "trace_count": int(sums["count"]),
        },
        {
            "scope": "combined_train_only",
            "asset": "brunswick+halfmile",
            "feature_name": "ref_total_static",
            "pearson_corr_with_label": ref_total_corr,
            "abs_corr_with_label": ref_total_abs_corr,
            "decision": ref_total_decision,
            "reason": ref_total_reason,
            "trace_count": int(sums["count"]),
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(config.PREPROCESSING_DIR / "static_leakage_check_trainonly.csv", index=False)
    return df


def save_feature_normalization_stats(train_split_info: List[Dict[str, object]]) -> Dict[str, object]:
    train_frames = []
    for item in train_split_info:
        asset_key = item["asset"]
        gather_df = load_gather_metadata(asset_key)
        train_df = gather_df[gather_df["shot_id"].isin(item["train_ids"])]
        train_frames.append(train_df[["shot_x", "shot_y"]])

    combined = pd.concat(train_frames, ignore_index=True)
    sx_mean = float(combined["shot_x"].mean())
    sx_std = float(combined["shot_x"].std(ddof=1))
    sy_mean = float(combined["shot_y"].mean())
    sy_std = float(combined["shot_y"].std(ddof=1))

    payload = {
        "split_random_seed": config.RANDOM_SEED,
        "coordinate_normalization": {
            "source_x_mean": sx_mean,
            "source_x_std": sx_std if sx_std > 0 else 1.0,
            "source_y_mean": sy_mean,
            "source_y_std": sy_std if sy_std > 0 else 1.0,
            "computed_from_training_shots_only": True,
            "training_assets_used": TRAIN_ASSETS,
        },
        "label_column": config.WORKING_LABEL_COLUMN,
        "normalization_method": config.NORMALIZATION_METHOD,
        "trace_harmonization_strategy": config.TRACE_HARMONIZATION_STRATEGY,
        "notes": [
            "Stats are computed from Brunswick + Halfmile training shots only.",
            "Use these same stats for Lalor validation and Sudbury stress-test inference.",
            "Dead traces should remain zero vectors with a dead-trace flag; no imputation is applied.",
        ],
    }
    out_path = config.PREPROCESSING_DIR / "feature_normalization_stats.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _count_rows_for_shots(path: Path, shot_ids: Set[int]) -> int:
    count = 0
    for chunk in pd.read_csv(path, usecols=["shot_id"], chunksize=250_000):
        count += int(chunk["shot_id"].isin(shot_ids).sum())
    return count


def _count_all_rows(path: Path) -> int:
    count = 0
    for chunk in pd.read_csv(path, usecols=["trace_index"], chunksize=250_000):
        count += len(chunk)
    return count


def drop_banned_columns_from_feature_csv(asset_key: str) -> int:
    """Remove banned columns from features CSV in-place. Returns columns dropped count."""
    path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
    if not path.exists():
        return 0

    header = pd.read_csv(path, nrows=0)
    cols_present = [c for c in BANNED_FEATURE_COLUMNS if c in header.columns]
    if not cols_present:
        print(f"  [drop_banned] {asset_key}: no banned columns found, skipping")
        return 0

    tmp_path = path.with_suffix(".tmp.csv")
    if tmp_path.exists():
        tmp_path.unlink()
    first_chunk = True
    for chunk in pd.read_csv(path, chunksize=200_000):
        chunk = chunk.drop(columns=cols_present, errors="ignore")
        chunk.to_csv(tmp_path, mode="a", header=first_chunk, index=False)
        first_chunk = False

    path.unlink()
    tmp_path.rename(path)
    print(f"  [drop_banned] {asset_key}: dropped {cols_present}")
    return len(cols_present)


def generate_lalor_experiment_b_split() -> Dict[str, object]:
    """Generate and persist the 80/20 shot split for Lalor for Experiment B only."""
    gather_df = load_gather_metadata(LALOR_ASSET_KEY)
    rng = np.random.default_rng(config.RANDOM_SEED)
    shot_ids = gather_df["shot_id"].drop_duplicates().to_numpy(dtype=np.int64)
    shuffled = rng.permutation(shot_ids)

    n_total = len(shuffled)
    n_train = max(1, int(round(n_total * LALOR_EXPERIMENT_B_TRAIN_FRACTION)))
    n_train = min(n_train, n_total - 1) if n_total > 1 else n_total
    train_ids = np.sort(shuffled[:n_train])
    val_ids = np.sort(shuffled[n_train:])

    write_shot_ids(
        config.PREPROCESSING_DIR / "train_shot_ids_lalor_expB.txt",
        train_ids,
    )
    write_shot_ids(
        config.PREPROCESSING_DIR / "val_shot_ids_lalor_expB.txt",
        val_ids,
    )

    train_df = gather_df[gather_df["shot_id"].isin(train_ids)]
    val_df = gather_df[gather_df["shot_id"].isin(val_ids)]

    summary = {
        "asset": LALOR_ASSET_KEY,
        "experiment": "B",
        "train_fraction": LALOR_EXPERIMENT_B_TRAIN_FRACTION,
        "total_shots": int(n_total),
        "train_shots": int(len(train_ids)),
        "val_shots": int(len(val_ids)),
        "train_traces": int(train_df["number_of_traces"].sum()),
        "val_traces": int(val_df["number_of_traces"].sum()),
        "random_seed": config.RANDOM_SEED,
    }
    pd.DataFrame([summary]).to_csv(
        config.PREPROCESSING_DIR / "lalor_experiment_b_split_summary.csv",
        index=False,
    )

    assert len(set(train_ids.tolist()) & set(val_ids.tolist())) == 0, (
        "Lalor Experiment B split: train and val shot sets are not disjoint"
    )

    print(
        f"[04_dataset_builder] Lalor Experiment B split: "
        f"{len(train_ids)} train shots / {len(val_ids)} val shots"
    )

    return {
        **summary,
        "train_ids": train_ids,
        "val_ids": val_ids,
    }


def save_split_manifest(
    split_rows: List[Dict[str, object]],
    lalor_experiment_b_split: Dict[str, object] | None = None,
) -> pd.DataFrame:
    rows = []
    split_map = {item["asset"]: item for item in split_rows}
    for asset_key in TRAIN_ASSETS:
        train_ids = set(split_map[asset_key]["train_ids"].tolist())
        val_ids = set(split_map[asset_key]["val_ids"].tolist())
        features_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
        valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
        inference_path = config.PREPROCESSING_DIR / f"inference_trace_metadata_{asset_key}.csv"
        rows.append(
            {
                "asset": f"{asset_key}_train",
                "role": "training",
                "num_shots": len(train_ids),
                "num_labeled_traces": _count_rows_for_shots(features_path, train_ids),
                "num_total_traces": _count_rows_for_shots(valid_path, train_ids)
                + _count_rows_for_shots(inference_path, train_ids),
                "notes": f"{int(round(SPLIT_FRACTION_TRAIN * 100))}% of {asset_key} shots",
            }
        )
        rows.append(
            {
                "asset": f"{asset_key}_val",
                "role": "internal_val",
                "num_shots": len(val_ids),
                "num_labeled_traces": _count_rows_for_shots(features_path, val_ids),
                "num_total_traces": _count_rows_for_shots(valid_path, val_ids)
                + _count_rows_for_shots(inference_path, val_ids),
                "notes": f"{int(round((1 - SPLIT_FRACTION_TRAIN) * 100))}% of {asset_key} shots",
            }
        )

    for asset_key in EVAL_ASSETS:
        gather_df = load_gather_metadata(asset_key)
        features_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
        valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"
        inference_path = config.PREPROCESSING_DIR / f"inference_trace_metadata_{asset_key}.csv"
        rows.append(
            {
                "asset": asset_key,
                "role": "external_val" if config.DATASET_ASSETS[asset_key].role == "validate" else "stress_test",
                "num_shots": int(gather_df["shot_id"].nunique()),
                "num_labeled_traces": _count_all_rows(features_path),
                "num_total_traces": _count_all_rows(valid_path) + _count_all_rows(inference_path),
                "notes": (
                    "fully held out"
                    if config.DATASET_ASSETS[asset_key].role == "validate"
                    else "fully held out, unlabeled sentinel=0"
                ),
            }
        )

    if lalor_experiment_b_split is not None:
        lalor_features_path = config.PREPROCESSING_DIR / f"features_{LALOR_ASSET_KEY}.csv"
        lalor_valid_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{LALOR_ASSET_KEY}.csv"
        lalor_inference_path = config.PREPROCESSING_DIR / f"inference_trace_metadata_{LALOR_ASSET_KEY}.csv"
        lalor_train_ids = set(lalor_experiment_b_split["train_ids"].tolist())
        lalor_val_ids = set(lalor_experiment_b_split["val_ids"].tolist())
        rows.append(
            {
                "asset": "lalor_expB_train",
                "role": "domain_adapt_train",
                "num_shots": len(lalor_train_ids),
                "num_labeled_traces": _count_rows_for_shots(lalor_features_path, lalor_train_ids),
                "num_total_traces": _count_rows_for_shots(lalor_valid_path, lalor_train_ids)
                + _count_rows_for_shots(lalor_inference_path, lalor_train_ids),
                "notes": "80% Lalor shots for Experiment B",
            }
        )
        rows.append(
            {
                "asset": "lalor_expB_val",
                "role": "domain_adapt_holdout",
                "num_shots": len(lalor_val_ids),
                "num_labeled_traces": _count_rows_for_shots(lalor_features_path, lalor_val_ids),
                "num_total_traces": _count_rows_for_shots(lalor_valid_path, lalor_val_ids)
                + _count_rows_for_shots(lalor_inference_path, lalor_val_ids),
                "notes": "20% Lalor shots holdout for Experiment B",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(config.PREPROCESSING_DIR / "dataset_split_summary.csv", index=False)
    return df


def save_eval_asset_manifest() -> pd.DataFrame:
    rows = []
    for asset_key in EVAL_ASSETS:
        gather_df = load_gather_metadata(asset_key)
        rows.append(
            {
                "asset": asset_key,
                "role": config.DATASET_ASSETS[asset_key].role,
                "gather_count": int(gather_df["shot_id"].nunique()),
                "trace_count": int(gather_df["number_of_traces"].sum()),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(config.PREPROCESSING_DIR / "evaluation_asset_manifest.csv", index=False)
    return df


def save_dataset_builder_report(
    split_summary: pd.DataFrame,
    eval_manifest: pd.DataFrame,
    norm_stats: Dict[str, object],
) -> None:
    lines = [
        f"Random seed: {config.RANDOM_SEED}",
        "Train/validation split strategy: separate 85/15 split within each training asset at shot/gather level.",
        "",
        "Split summary:",
        split_summary.to_string(index=False),
        "",
        "Evaluation assets:",
        eval_manifest.to_string(index=False),
        "",
        "Feature normalization stats:",
        json.dumps(norm_stats, indent=2),
    ]
    (config.PREPROCESSING_DIR / "dataset_builder_report.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def update_feature_config_with_final_features(norm_stats: Dict[str, object]) -> None:
    config_path = config.PREPROCESSING_DIR / "feature_engineering_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    final_model_input_feature_columns = [
        "offset_rank",
        "elevation_diff",
        "slant_distance",
        "pre_break_noise_energy",
        "zero_crossing_rate",
        "max_abs_amplitude",
        "stalta_pick_ms",
        "gather_median_pick_ms",
        "pick_deviation_from_gather_median",
        "hyperbolic_residual",
    ]
    payload["coordinate_normalization_stats_training_shots"] = norm_stats["coordinate_normalization"]
    payload["static_leakage_check_source"] = "not_applicable_static_features_removed"
    payload["static_leakage_check_results"] = []
    payload["final_model_input_feature_columns"] = final_model_input_feature_columns
    payload["final_confirmed_feature_columns"] = final_model_input_feature_columns
    payload["auxiliary_flag_columns"] = []
    payload["dropped_after_step5"] = [
        "source_x_normalized",
        "source_y_normalized",
        "trace_position",
        "total_static",
        "ref_total_static",
        "stalta_pick_sample",
    ]
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_dataset_builder() -> None:
    config.ensure_output_dirs()

    split_rows: List[Dict[str, object]] = []
    for asset_key in TRAIN_ASSETS:
        gather_df = load_gather_metadata(asset_key)
        split_info = split_asset_shots(asset_key, gather_df)
        split_rows.append(split_info)

        write_shot_ids(
            config.PREPROCESSING_DIR / f"train_shot_ids_{asset_key}.txt",
            split_info["train_ids"],
        )
        write_shot_ids(
            config.PREPROCESSING_DIR / f"val_shot_ids_{asset_key}.txt",
            split_info["val_ids"],
        )

    (config.PREPROCESSING_DIR / "split_random_seed.txt").write_text(
        f"{config.RANDOM_SEED}\n",
        encoding="utf-8",
    )

    lalor_b_summary = generate_lalor_experiment_b_split()
    split_summary = save_split_manifest(split_rows, lalor_experiment_b_split=lalor_b_summary)
    eval_manifest = save_eval_asset_manifest()

    norm_stats = save_feature_normalization_stats(split_rows)
    update_feature_config_with_final_features(norm_stats)
    save_dataset_builder_report(split_summary, eval_manifest, norm_stats)
    print("[04_dataset_builder] Removing banned columns from feature CSVs")
    for asset_key in config.DATASET_ASSETS.keys():
        drop_banned_columns_from_feature_csv(asset_key)

    print(f"[04_dataset_builder] Outputs written to: {config.PREPROCESSING_DIR}")


if __name__ == "__main__":
    run_dataset_builder()
