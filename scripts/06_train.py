from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config

_TRAIN_LOG_PATH: Path | None = None
LALOR_ADAPT_TRAIN_FRACTION = config.LALOR_ADAPT_TRAIN_FRACTION


def _log(message: str) -> None:
    line = f"[06_train] {message}"
    print(line, flush=True)
    if _TRAIN_LOG_PATH is not None:
        with _TRAIN_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _init_train_log() -> None:
    global _TRAIN_LOG_PATH
    config.TRAINING_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _TRAIN_LOG_PATH = config.TRAINING_LOGS_DIR / "training_live.log"
    _TRAIN_LOG_PATH.write_text("", encoding="utf-8")
    _log(f"Log file: {_TRAIN_LOG_PATH}")


@dataclass(frozen=True)
class SplitSpec:
    name: str
    asset_keys: Sequence[str]
    shot_id_files: Dict[str, Path] | None = None


def _ensure_lalor_split_files(train_fraction: float = LALOR_ADAPT_TRAIN_FRACTION) -> Tuple[Path, Path]:
    train_path = config.PREPROCESSING_DIR / "train_shot_ids_lalor_expB.txt"
    val_path = config.PREPROCESSING_DIR / "val_shot_ids_lalor_expB.txt"
    if train_path.exists() and val_path.exists():
        return train_path, val_path

    legacy_train_path = config.PREPROCESSING_DIR / "train_shot_ids_lalor.txt"
    legacy_val_path = config.PREPROCESSING_DIR / "val_shot_ids_lalor.txt"
    if legacy_train_path.exists() and legacy_val_path.exists():
        train_path.write_text(legacy_train_path.read_text(encoding="utf-8"), encoding="utf-8")
        val_path.write_text(legacy_val_path.read_text(encoding="utf-8"), encoding="utf-8")
        _log("Using legacy Lalor split files and mirrored them to *_expB names")
        return train_path, val_path

    gather_path = config.PREPROCESSING_DIR / "gather_metadata_lalor.csv"
    gather_df = pd.read_csv(gather_path)
    gather_df = gather_df[gather_df["exclude_from_training"] == False].copy()  # noqa: E712
    shot_ids = np.sort(gather_df["shot_id"].drop_duplicates().to_numpy(dtype=np.int64))
    if len(shot_ids) < 2:
        raise ValueError("Not enough Lalor shots to build adaptation split.")

    rng = np.random.default_rng(config.RANDOM_SEED)
    shuffled = rng.permutation(shot_ids)
    n_train = max(1, int(round(len(shuffled) * train_fraction)))
    n_train = min(n_train, len(shuffled) - 1)
    train_ids = np.sort(shuffled[:n_train])
    val_ids = np.sort(shuffled[n_train:])

    train_text = "\n".join(str(int(x)) for x in train_ids) + "\n"
    val_text = "\n".join(str(int(x)) for x in val_ids) + "\n"
    train_path.write_text(train_text, encoding="utf-8")
    val_path.write_text(val_text, encoding="utf-8")
    # Backward compatibility with prior naming.
    legacy_train_path.write_text(train_text, encoding="utf-8")
    legacy_val_path.write_text(val_text, encoding="utf-8")
    _log(f"Created Lalor split files: train={len(train_ids):,} shots, val={len(val_ids):,} shots")
    return train_path, val_path


def _load_feature_columns() -> List[str]:
    cfg = json.loads((config.PREPROCESSING_DIR / "feature_engineering_config.json").read_text(encoding="utf-8"))
    cols = cfg.get("final_model_input_feature_columns", [])
    if not cols:
        raise ValueError("final_model_input_feature_columns is empty in feature_engineering_config.json")
    _log(f"Loaded {len(cols)} model feature columns")
    return cols


def _read_shot_ids(path: Path) -> set[int]:
    shot_ids = {int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    _log(f"Loaded shot split file {path.name}: {len(shot_ids):,} shot IDs")
    return shot_ids


def _load_asset_frame(
    asset_key: str,
    feature_columns: Sequence[str],
    allowed_shots: set[int] | None,
) -> pd.DataFrame:
    _log(f"Reading asset={asset_key}")
    feature_path = config.PREPROCESSING_DIR / f"features_{asset_key}.csv"
    label_path = config.PREPROCESSING_DIR / f"valid_trace_metadata_{asset_key}.csv"

    feature_head = pd.read_csv(feature_path, nrows=1)
    offset_col = "offset" if "offset" in feature_head.columns else "stored_offset"
    usecols_features = ["shot_id", "trace_index", offset_col, *feature_columns]
    usecols_labels = ["shot_id", "trace_index", "label_ms"]

    features = pd.read_csv(feature_path, usecols=usecols_features)
    if offset_col != "offset":
        features = features.rename(columns={offset_col: "offset"})
    labels = pd.read_csv(label_path, usecols=usecols_labels)

    if allowed_shots is not None:
        features = features[features["shot_id"].isin(allowed_shots)]
        labels = labels[labels["shot_id"].isin(allowed_shots)]

    merged = features.merge(labels, on=["shot_id", "trace_index"], how="inner", validate="one_to_one")
    merged.insert(0, "asset", asset_key)
    _log(f"Asset={asset_key} merged rows={len(merged):,}")
    return merged


def _sample_frame(df: pd.DataFrame, max_rows: int, seed: int) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df
    _log(f"Sampling from {len(df):,} to {max_rows:,} rows (seed={seed})")
    return df.sample(n=max_rows, random_state=seed).reset_index(drop=True)


def _prepare_split(
    split: SplitSpec,
    feature_columns: Sequence[str],
    max_rows: int | None,
    seed: int,
) -> pd.DataFrame:
    _log(f"Preparing split={split.name}")
    frames: List[pd.DataFrame] = []
    for asset_key in split.asset_keys:
        allowed = None
        if split.shot_id_files is not None and asset_key in split.shot_id_files:
            allowed = _read_shot_ids(split.shot_id_files[asset_key])
        frame = _load_asset_frame(asset_key, feature_columns, allowed)
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    _log(f"Split={split.name} rows before sampling: {len(combined):,}")
    if max_rows is not None and max_rows > 0:
        combined = _sample_frame(combined, max_rows=max_rows, seed=seed)
    _log(f"Split={split.name} rows final: {len(combined):,}")
    return combined.reset_index(drop=True)


def _ensure_numeric(df: pd.DataFrame, feature_columns: Sequence[str], split_name: str) -> pd.DataFrame:
    out = df.copy()
    for col in feature_columns:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["label_ms"] = pd.to_numeric(out["label_ms"], errors="coerce")
    before = len(out)
    out = out[np.isfinite(out["label_ms"]) & (out["label_ms"] > 0)].reset_index(drop=True)
    _log(f"Split={split_name} numeric cleanup: {before:,} -> {len(out):,}")
    return out


def _train_and_save(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_columns: Sequence[str],
    extra_valids: Dict[str, pd.DataFrame] | None = None,
    artifact_suffix: str = "",
) -> Tuple[lgb.Booster, Dict[str, object]]:
    X_train = train_df[list(feature_columns)].to_numpy(dtype=np.float32)
    y_train = train_df["label_ms"].to_numpy(dtype=np.float32)
    X_val = val_df[list(feature_columns)].to_numpy(dtype=np.float32)
    y_val = val_df["label_ms"].to_numpy(dtype=np.float32)

    _log(f"Train matrix shape={X_train.shape}, Val matrix shape={X_val.shape}")

    dtrain = lgb.Dataset(X_train, label=y_train, feature_name=list(feature_columns))
    dval = lgb.Dataset(X_val, label=y_val, feature_name=list(feature_columns), reference=dtrain)
    valid_sets = [dtrain, dval]
    valid_names = ["train", "val_indistribution"]

    valid_row_counts: Dict[str, int] = {"train": int(len(train_df)), "val_indistribution": int(len(val_df))}
    if extra_valids:
        for name, frame in extra_valids.items():
            x_extra = frame[list(feature_columns)].to_numpy(dtype=np.float32)
            y_extra = frame["label_ms"].to_numpy(dtype=np.float32)
            d_extra = lgb.Dataset(x_extra, label=y_extra, feature_name=list(feature_columns), reference=dtrain)
            valid_sets.append(d_extra)
            valid_names.append(name)
            valid_row_counts[name] = int(len(frame))

    params = {
        "objective": config.LIGHTGBM_OBJECTIVE,
        "metric": "l1",
        "learning_rate": config.LIGHTGBM_LEARNING_RATE,
        "num_leaves": config.LIGHTGBM_NUM_LEAVES,
        "max_depth": config.LIGHTGBM_MAX_DEPTH,
        "feature_fraction": config.LIGHTGBM_FEATURE_FRACTION,
        "bagging_fraction": config.LIGHTGBM_BAGGING_FRACTION,
        "bagging_freq": config.LIGHTGBM_BAGGING_FREQ,
        "min_data_in_leaf": config.LIGHTGBM_MIN_DATA_IN_LEAF,
        "verbosity": -1,
        "seed": config.RANDOM_SEED,
        "num_threads": 0,
    }

    _log(
        "LightGBM rounds: "
        f"max={config.LIGHTGBM_NUM_BOOST_ROUND}, early_stopping={config.LIGHTGBM_EARLY_STOPPING_ROUNDS}"
    )

    evals_result: Dict[str, Dict[str, List[float]]] = {}
    booster = lgb.train(
        params=params,
        train_set=dtrain,
        num_boost_round=config.LIGHTGBM_NUM_BOOST_ROUND,
        valid_sets=valid_sets,
        valid_names=valid_names,
        callbacks=[
            lgb.log_evaluation(period=25),
            lgb.early_stopping(stopping_rounds=config.LIGHTGBM_EARLY_STOPPING_ROUNDS, verbose=True),
            lgb.record_evaluation(evals_result),
        ],
    )

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = config.MODELS_DIR / f"lightgbm_first_break{artifact_suffix}.txt"
    booster.save_model(str(model_path))

    importance = pd.DataFrame(
        {
            "feature": list(feature_columns),
            "importance_gain": booster.feature_importance(importance_type="gain"),
            "importance_split": booster.feature_importance(importance_type="split"),
        }
    ).sort_values("importance_gain", ascending=False)
    importance.to_csv(config.MODELS_DIR / f"lightgbm_feature_importance{artifact_suffix}.csv", index=False)

    metadata = {
        "model_name": config.MODEL_NAME,
        "model_path": str(model_path),
        "feature_columns": list(feature_columns),
        "best_iteration": int(booster.best_iteration or config.LIGHTGBM_NUM_BOOST_ROUND),
        "params": params,
        "train_rows": int(len(train_df)),
        "val_rows": valid_row_counts,
        "eval_history": evals_result,
    }
    (config.MODELS_DIR / f"lightgbm_training_metadata{artifact_suffix}.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    _log(f"Best iteration: {metadata['best_iteration']}")
    _log("Saved model + training metadata + feature importance")

    return booster, metadata


def run_training(
    experiment: str = "a",
    max_train_rows: int | None = None,
    max_val_rows: int | None = None,
    max_test_rows: int | None = None,
) -> None:
    config.ensure_output_dirs()
    _init_train_log()
    feature_columns = _load_feature_columns()
    experiment = experiment.lower().strip()
    if experiment not in {"a", "b"}:
        raise ValueError("experiment must be one of: a, b")

    _log(f"Running experiment={experiment}")
    artifact_suffix = "_experimentb" if experiment == "b" else ""

    train_shots = {
        "brunswick": config.PREPROCESSING_DIR / "train_shot_ids_brunswick.txt",
        "halfmile": config.PREPROCESSING_DIR / "train_shot_ids_halfmile.txt",
    }
    val_shots = {
        "brunswick": config.PREPROCESSING_DIR / "val_shot_ids_brunswick.txt",
        "halfmile": config.PREPROCESSING_DIR / "val_shot_ids_halfmile.txt",
    }
    train_assets = ["brunswick", "halfmile"]
    extra_valid_split: SplitSpec | None = None
    if experiment == "b":
        lalor_train, lalor_val = _ensure_lalor_split_files()
        train_assets.append("lalor")
        train_shots["lalor"] = lalor_train
        extra_valid_split = SplitSpec(name="val_lalor", asset_keys=["lalor"], shot_id_files={"lalor": lalor_val})
        test_split = SplitSpec(
            name="test",
            asset_keys=["lalor", "sudbury"],
            shot_id_files={"lalor": lalor_val},
        )
    else:
        test_split = SplitSpec(
            name="test",
            asset_keys=["lalor", "sudbury"],
            shot_id_files=None,
        )

    train_split = SplitSpec(name="train", asset_keys=train_assets, shot_id_files=train_shots)
    val_split = SplitSpec(name="val_indistribution", asset_keys=["brunswick", "halfmile"], shot_id_files=val_shots)

    train_df = _prepare_split(
        train_split,
        feature_columns,
        max_rows=config.LIGHTGBM_MAX_TRAIN_ROWS if max_train_rows is None else max_train_rows,
        seed=config.RANDOM_SEED,
    )
    val_df = _prepare_split(
        val_split,
        feature_columns,
        max_rows=config.LIGHTGBM_MAX_VAL_ROWS if max_val_rows is None else max_val_rows,
        seed=config.RANDOM_SEED,
    )
    test_df = _prepare_split(
        test_split,
        feature_columns,
        max_rows=config.LIGHTGBM_MAX_VAL_ROWS if max_test_rows is None else max_test_rows,
        seed=config.RANDOM_SEED + 1,
    )

    train_df = _ensure_numeric(train_df, feature_columns, split_name="train")
    val_df = _ensure_numeric(val_df, feature_columns, split_name="val_indistribution")
    test_df = _ensure_numeric(test_df, feature_columns, split_name="test")
    extra_valids: Dict[str, pd.DataFrame] = {}
    if extra_valid_split is not None:
        val_lalor_df = _prepare_split(
            extra_valid_split,
            feature_columns,
            max_rows=config.LIGHTGBM_MAX_VAL_ROWS if max_val_rows is None else max_val_rows,
            seed=config.RANDOM_SEED + 7,
        )
        val_lalor_df = _ensure_numeric(val_lalor_df, feature_columns, split_name="val_lalor")
        extra_valids["val_lalor"] = val_lalor_df

    booster, metadata = _train_and_save(
        train_df,
        val_df,
        feature_columns,
        extra_valids=extra_valids,
        artifact_suffix=artifact_suffix,
    )

    out_dir = config.EVALUATION_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    def _load_inference_rows(split: SplitSpec) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        allowed_cache: Dict[str, set[int] | None] = {}
        for asset_key in split.asset_keys:
            if split.shot_id_files is not None and asset_key in split.shot_id_files:
                allowed_cache[asset_key] = _read_shot_ids(split.shot_id_files[asset_key])
            else:
                allowed_cache[asset_key] = None

            path = config.PREPROCESSING_DIR / f"inference_trace_metadata_{asset_key}.csv"
            if not path.exists():
                continue
            head = pd.read_csv(path, nrows=1)
            offset_col = "offset" if "offset" in head.columns else "stored_offset"
            usecols = ["shot_id", "trace_index", offset_col, "label_ms", "label_status"]
            inf = pd.read_csv(path, usecols=usecols)
            if offset_col != "offset":
                inf = inf.rename(columns={offset_col: "offset"})
            allowed = allowed_cache[asset_key]
            if allowed is not None:
                inf = inf[inf["shot_id"].isin(allowed)]
            if inf.empty:
                continue
            inf.insert(0, "asset", asset_key)
            inf["predicted_ms"] = np.nan
            inf["prediction_status"] = np.where(
                inf["label_status"] == "dead_trace",
                "dead_trace",
                "unlabeled",
            )
            frames.append(inf[["asset", "shot_id", "trace_index", "label_ms", "offset", "predicted_ms", "prediction_status"]])
        if not frames:
            return pd.DataFrame(columns=["asset", "shot_id", "trace_index", "label_ms", "offset", "predicted_ms", "prediction_status"])
        return pd.concat(frames, ignore_index=True)

    def _write_preds(df: pd.DataFrame, split_name: str, split_spec: SplitSpec) -> None:
        _log(f"Predicting split={split_name} rows={len(df):,}")
        x = df[list(feature_columns)].to_numpy(dtype=np.float32)
        pred = booster.predict(x, num_iteration=booster.best_iteration)
        preds = df[["asset", "shot_id", "trace_index", "label_ms", "offset"]].copy()
        preds["predicted_ms"] = pred
        preds["prediction_status"] = "predicted_labeled"
        preds["split"] = split_name
        inference_rows = _load_inference_rows(split_spec) if split_name == "test" else pd.DataFrame()
        if not inference_rows.empty:
            inference_rows = inference_rows.copy()
            inference_rows["split"] = split_name
            preds = pd.concat([preds, inference_rows], ignore_index=True)
        out_path = out_dir / f"predictions_{split_name}{artifact_suffix}.csv"
        preds.to_csv(out_path, index=False)
        _log(f"Saved {out_path.name}")

    _write_preds(train_df, "train", train_split)
    _write_preds(val_df, "val", val_split)
    _write_preds(test_df, "test", test_split)

    _log("Training completed")
    _log(f"Model: {metadata['model_path']}")
    val_rows_obj = metadata.get("val_rows", {})
    if isinstance(val_rows_obj, dict):
        val_rows_text = ", ".join(f"{k}={int(v):,}" for k, v in val_rows_obj.items())
    else:
        val_rows_text = f"{int(val_rows_obj):,}"
    _log(
        f"Train rows: {metadata['train_rows']:,}, "
        f"Val rows: {val_rows_text}, "
        f"Test rows: {len(test_df):,}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LightGBM first-break model with detailed live logs")
    parser.add_argument(
        "--experiment",
        type=str,
        default="a",
        choices=["a", "b", "A", "B"],
        help="a: strict OOD (train brunswick+halfmile), b: adaptation (add lalor 80/20 split)",
    )
    parser.add_argument("--max-train-rows", type=int, default=None, help="Override max sampled train rows")
    parser.add_argument("--max-val-rows", type=int, default=None, help="Override max sampled val rows")
    parser.add_argument("--max-test-rows", type=int, default=None, help="Override max sampled test rows")
    args = parser.parse_args()

    run_training(
        experiment=args.experiment,
        max_train_rows=args.max_train_rows,
        max_val_rows=args.max_val_rows,
        max_test_rows=args.max_test_rows,
    )
