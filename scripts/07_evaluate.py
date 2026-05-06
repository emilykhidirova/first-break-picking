from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config

_EVAL_LOG_PATH: Path | None = None


def _log(message: str) -> None:
    line = f"[07_evaluate] {message}"
    print(line, flush=True)
    if _EVAL_LOG_PATH is not None:
        with _EVAL_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _init_eval_log() -> None:
    global _EVAL_LOG_PATH
    config.TRAINING_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _EVAL_LOG_PATH = config.TRAINING_LOGS_DIR / "test_live.log"
    _EVAL_LOG_PATH.write_text("", encoding="utf-8")
    _log(f"Log file: {_EVAL_LOG_PATH}")


def _tail_lines(path: Path, max_lines: int = 80) -> List[str]:
    if not path.exists():
        return [f"(missing: {path})"]
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return ["(empty log)"]
    return lines[-max_lines:]


def _experiment_suffix(experiment_tag: str) -> str:
    tag = experiment_tag.strip().lower()
    return "_experimentb" if tag in {"b", "experimentb"} else ""


def _normalized_experiment_tag(experiment_tag: str) -> str:
    tag = experiment_tag.strip().lower()
    if tag in {"b", "experimentb"}:
        return "experimentb"
    return tag


def _load_predictions(name: str, experiment_tag: str) -> pd.DataFrame:
    suffix = _experiment_suffix(experiment_tag)
    candidates = []
    if suffix:
        candidates.extend(
            [
                config.EVALUATION_DIR / f"predictions_{name}{suffix}_smoothed.csv",
                config.EVALUATION_DIR / f"predictions_{name}{suffix}.csv",
            ]
        )
    candidates.extend(
        [
            config.EVALUATION_DIR / f"predictions_{name}_smoothed.csv",
            config.EVALUATION_DIR / f"predictions_{name}.csv",
        ]
    )
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        _log(f"Split={name} not found for experiment_tag={experiment_tag}")
        return pd.DataFrame()

    _log(f"Loading split={name} from {path.name}")
    df = pd.read_csv(path)
    if "prediction_status" not in df.columns:
        df["prediction_status"] = "predicted_labeled"
    pred_col = "predicted_ms_smoothed" if "predicted_ms_smoothed" in df.columns else "predicted_ms"
    if pred_col != "predicted_ms":
        df["predicted_ms"] = df[pred_col]
    before = len(df)
    df = df[np.isfinite(df["label_ms"])].copy()
    _log(f"Split={name} rows: {before:,} -> {len(df):,} after finite label filtering")
    return df


def _labeled_metric_rows(df: pd.DataFrame, split_name: str) -> pd.DataFrame:
    out = df[df["prediction_status"] == "predicted_labeled"].copy()
    before = len(out)
    out = out[np.isfinite(out["predicted_ms"])].copy()
    out = out[out["label_ms"] > 0].copy()
    _log(f"Split={split_name} labeled metric rows: {before:,} -> {len(out):,}")
    return out


def _assert_labels_by_asset(df: pd.DataFrame, split_name: str) -> None:
    labeled = df[df["prediction_status"] == "predicted_labeled"].copy()
    if labeled.empty:
        return
    for asset, grp in labeled.groupby("asset", sort=True):
        sentinels = set(config.UNLABELED_SENTINELS_BY_ASSET.get(asset, ()))
        if (grp["label_ms"] <= 0).any():
            raise ValueError(f"{split_name}:{asset} has non-positive labels in predicted_labeled rows.")
        if sentinels and grp["label_ms"].isin(list(sentinels)).any():
            raise ValueError(f"{split_name}:{asset} has sentinel labels in predicted_labeled rows.")


def _roc_curve(y_true: np.ndarray, y_score: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(-y_score, kind="mergesort")
    y_true_sorted = y_true[order].astype(np.int64)
    y_score_sorted = y_score[order]
    distinct = np.where(np.diff(y_score_sorted))[0]
    idx = np.r_[distinct, y_true_sorted.size - 1]
    tps = np.cumsum(y_true_sorted)[idx]
    fps = 1 + idx - tps
    tps = np.r_[0, tps]
    fps = np.r_[0, fps]
    pos = max(int(y_true.sum()), 1)
    neg = max(int((1 - y_true).sum()), 1)
    tpr = tps / pos
    fpr = fps / neg
    thresholds = np.r_[np.inf, y_score_sorted[idx]]
    return fpr, tpr, thresholds


def _auc(fpr: np.ndarray, tpr: np.ndarray) -> float:
    return float(np.trapezoid(tpr, fpr))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _evaluate_block(df: pd.DataFrame, threshold_ms: float, block_name: str) -> Dict[str, float]:
    y_true_ms = df["label_ms"].to_numpy(dtype=np.float64)
    y_pred_ms = df["predicted_ms"].to_numpy(dtype=np.float64)

    abs_err = np.abs(y_pred_ms - y_true_ms)
    sq_err = np.square(y_pred_ms - y_true_ms)
    mae = float(abs_err.mean())
    rmse = float(np.sqrt(sq_err.mean()))
    medae = float(np.median(abs_err))
    within_5 = float(np.mean(abs_err <= 5.0) * 100.0)
    within_10 = float(np.mean(abs_err <= 10.0) * 100.0)
    within_20 = float(np.mean(abs_err <= 20.0) * 100.0)
    within_50 = float(np.mean(abs_err <= 50.0) * 100.0)

    y_true_bin = (y_true_ms <= threshold_ms).astype(np.int64)
    y_pred_bin = (y_pred_ms <= threshold_ms).astype(np.int64)
    score = -y_pred_ms

    tp = int(np.sum((y_true_bin == 1) & (y_pred_bin == 1)))
    tn = int(np.sum((y_true_bin == 0) & (y_pred_bin == 0)))
    fp = int(np.sum((y_true_bin == 0) & (y_pred_bin == 1)))
    fn = int(np.sum((y_true_bin == 1) & (y_pred_bin == 0)))

    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    accuracy = _safe_div(tp + tn, tp + tn + fp + fn)
    fpr, tpr, _ = _roc_curve(y_true_bin, score)
    auc_roc = _auc(fpr, tpr)

    return {
        "split": block_name,
        "rows": int(len(df)),
        "loss_l1_mae_ms": mae,
        "mae_ms": mae,
        "rmse_ms": rmse,
        "median_ae_ms": medae,
        "within_5ms_pct": within_5,
        "within_10ms_pct": within_10,
        "within_20ms_pct": within_20,
        "within_50ms_pct": within_50,
        "classification_threshold_ms": float(threshold_ms),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive": fp,
        "false_negative": fn,
        "true_positive": tp,
        "true_negative": tn,
        "auc_roc": auc_roc,
    }


def _save_roc_plot(df: pd.DataFrame, threshold_ms: float, out_path: Path, title: str) -> None:
    y_true = (df["label_ms"].to_numpy(dtype=np.float64) <= threshold_ms).astype(np.int64)
    y_score = -df["predicted_ms"].to_numpy(dtype=np.float64)
    fpr, tpr, _ = _roc_curve(y_true, y_score)
    auc_val = _auc(fpr, tpr)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, label=f"AUC={auc_val:.4f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(title)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    _log(f"Saved ROC plot: {out_path.name}")


def _build_holdout_report(train_metrics: pd.DataFrame, test_metrics: pd.DataFrame) -> pd.DataFrame:
    train_all = train_metrics[train_metrics["split"] == "train_all"]
    train_mae = float(train_all["mae_ms"].iloc[0]) if not train_all.empty else np.nan
    holdout = test_metrics[test_metrics["split"].str.startswith("test_") & (test_metrics["split"] != "test_all")].copy()
    if holdout.empty:
        return pd.DataFrame()
    holdout["asset"] = holdout["split"].str.replace("test_", "", regex=False)
    holdout["mae_gap_vs_train_all_ms"] = holdout["mae_ms"] - train_mae
    holdout["mae_ratio_vs_train_all"] = holdout["mae_ms"] / train_mae if train_mae and np.isfinite(train_mae) else np.nan
    cols = [
        "asset",
        "rows",
        "mae_ms",
        "rmse_ms",
        "median_ae_ms",
        "within_50ms_pct",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc_roc",
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
        "mae_gap_vs_train_all_ms",
        "mae_ratio_vs_train_all",
    ]
    return holdout[cols].sort_values("asset").reset_index(drop=True)


def _format_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "(no rows)"
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    def _cell(v: object) -> str:
        if isinstance(v, (float, np.floating)):
            return f"{float(v):.6g}"
        if isinstance(v, (int, np.integer)):
            return str(int(v))
        if pd.isna(v):
            return ""
        return str(v)

    rows = ["| " + " | ".join(_cell(x) for x in row) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *rows])


def _maybe_write_experiment_comparison() -> None:
    a_path = config.EVALUATION_DIR / "metrics_test_global_threshold_a.csv"
    b_candidates = [
        config.EVALUATION_DIR / "metrics_test_global_threshold_experimentb.csv",
        config.EVALUATION_DIR / "metrics_test_global_threshold_b.csv",
    ]
    b_path = next((p for p in b_candidates if p.exists()), b_candidates[0])
    if not (a_path.exists() and b_path.exists()):
        return
    a = pd.read_csv(a_path)
    b = pd.read_csv(b_path)
    keep = ["split", "mae_ms", "rmse_ms", "within_50ms_pct", "accuracy", "precision", "recall", "f1_score", "auc_roc"]
    a = a[keep].rename(columns={c: f"{c}_exp_a" for c in keep if c != "split"})
    b = b[keep].rename(columns={c: f"{c}_exp_b" for c in keep if c != "split"})
    comp = a.merge(b, on="split", how="outer")
    out = config.EVALUATION_DIR / "experiment_comparison_a_vs_b.csv"
    comp.to_csv(out, index=False)
    _log(f"Saved experiment comparison: {out.name}")


def _write_markdown_summary(
    train_global: pd.DataFrame,
    test_global: pd.DataFrame,
    test_asset_threshold: pd.DataFrame,
    holdout_report: pd.DataFrame,
    experiment_tag: str,
) -> None:
    train_log_tail = _tail_lines(config.TRAINING_LOGS_DIR / "training_live.log", max_lines=80)
    test_log_tail = _tail_lines(config.TRAINING_LOGS_DIR / "test_live.log", max_lines=80)
    lines = [
        "# Evaluation Summary",
        "",
        f"Experiment tag: {experiment_tag}",
        "",
        "Binary target for ROC/classification is derived by thresholding arrival time (`label_ms <= threshold_ms`), with score = `-predicted_ms`.",
        "",
        "## Training Metrics (Global Threshold)",
        "",
        _format_markdown_table(train_global),
        "",
        "## Test Metrics (Global Threshold)",
        "",
        _format_markdown_table(test_global),
        "",
        "## Test Metrics (Per-Asset Threshold)",
        "",
        _format_markdown_table(test_asset_threshold),
        "",
        "## Per-Asset Holdout Report",
        "",
        _format_markdown_table(holdout_report),
        "",
        "## Training Log (latest)",
        "",
        "```text",
        *train_log_tail,
        "```",
        "",
        "## Test Log (latest)",
        "",
        "```text",
        *test_log_tail,
        "```",
        "",
        "## Output Artifacts",
        "",
        f"- metrics_train_global_threshold_{experiment_tag}.csv",
        f"- metrics_test_global_threshold_{experiment_tag}.csv",
        f"- metrics_test_asset_threshold_{experiment_tag}.csv",
        f"- holdout_report_by_asset_{experiment_tag}.csv",
        f"- roc_curve_train_{experiment_tag}.png",
        f"- roc_curve_test_{experiment_tag}.png",
        "- experiment_comparison_a_vs_b.csv (if both experiments available)",
    ]
    path = config.EVALUATION_DIR / f"evaluation_summary_{experiment_tag}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log(f"Saved markdown summary: {path.name}")
    if experiment_tag in {"a", "latest"}:
        default_path = config.EVALUATION_DIR / "evaluation_summary.md"
        default_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _log(f"Saved markdown summary: {default_path.name}")


def run_evaluation(experiment_tag: str, prefer_val_as_test: bool = True) -> None:
    config.ensure_output_dirs()
    _init_eval_log()
    tag = _normalized_experiment_tag(experiment_tag)
    suffix = _experiment_suffix(experiment_tag)
    if suffix:
        _log(f"Using artifact suffix: {suffix}")

    train_df_raw = _load_predictions("train", experiment_tag=experiment_tag)
    val_df_raw = _load_predictions("val", experiment_tag=experiment_tag)
    test_df_raw = _load_predictions("test", experiment_tag=experiment_tag)

    if train_df_raw.empty:
        raise FileNotFoundError("predictions_train.csv not found. Run training first.")
    if test_df_raw.empty and not val_df_raw.empty and prefer_val_as_test:
        _log("Using validation split as test fallback")
        test_df_raw = val_df_raw.copy()
        test_df_raw["split"] = "test_from_val"
    if test_df_raw.empty:
        raise FileNotFoundError("No test/val prediction file found.")

    _assert_labels_by_asset(train_df_raw, "train")
    _assert_labels_by_asset(test_df_raw, "test")

    train_df = _labeled_metric_rows(train_df_raw, "train")
    test_df = _labeled_metric_rows(test_df_raw, "test")
    if train_df.empty or test_df.empty:
        raise ValueError("No labeled rows available for evaluation after filtering.")

    threshold_ms_global = float(np.median(train_df["label_ms"].to_numpy(dtype=np.float64)))
    _log(f"Global classification threshold (median train label): {threshold_ms_global:.3f} ms")

    train_rows = [_evaluate_block(train_df, threshold_ms_global, "train_all")]
    for asset, grp in train_df.groupby("asset", sort=True):
        train_rows.append(_evaluate_block(grp, threshold_ms_global, f"train_{asset}"))
    train_global = pd.DataFrame(train_rows)

    test_rows_global = [_evaluate_block(test_df, threshold_ms_global, "test_all")]
    for asset, grp in test_df.groupby("asset", sort=True):
        _log(f"Evaluating test asset={asset} rows={len(grp):,} (global threshold)")
        test_rows_global.append(_evaluate_block(grp, threshold_ms_global, f"test_{asset}"))
    test_global = pd.DataFrame(test_rows_global)

    test_rows_asset_threshold = []
    for asset, grp in test_df.groupby("asset", sort=True):
        asset_threshold = float(np.median(grp["label_ms"].to_numpy(dtype=np.float64)))
        _log(f"Evaluating test asset={asset} rows={len(grp):,} (asset threshold={asset_threshold:.3f} ms)")
        row = _evaluate_block(grp, asset_threshold, f"test_{asset}")
        row["threshold_kind"] = "per_asset"
        test_rows_asset_threshold.append(row)
    test_asset_threshold = pd.DataFrame(test_rows_asset_threshold)

    holdout_report = _build_holdout_report(train_global, test_global)

    train_csv = config.EVALUATION_DIR / f"metrics_train_global_threshold_{tag}.csv"
    test_global_csv = config.EVALUATION_DIR / f"metrics_test_global_threshold_{tag}.csv"
    test_asset_csv = config.EVALUATION_DIR / f"metrics_test_asset_threshold_{tag}.csv"
    holdout_csv = config.EVALUATION_DIR / f"holdout_report_by_asset_{tag}.csv"
    train_global.to_csv(train_csv, index=False)
    test_global.to_csv(test_global_csv, index=False)
    test_asset_threshold.to_csv(test_asset_csv, index=False)
    holdout_report.to_csv(holdout_csv, index=False)
    _log(f"Saved metrics CSV: {train_csv.name}")
    _log(f"Saved metrics CSV: {test_global_csv.name}")
    _log(f"Saved metrics CSV: {test_asset_csv.name}")
    _log(f"Saved holdout report: {holdout_csv.name}")

    if not suffix:
        # Backward-compatible filenames for default (non-experimentb) artifacts.
        train_global.to_csv(config.EVALUATION_DIR / "metrics_train.csv", index=False)
        test_global.to_csv(config.EVALUATION_DIR / "metrics_test.csv", index=False)

    _save_roc_plot(train_df, threshold_ms_global, config.EVALUATION_DIR / f"roc_curve_train_{tag}.png", f"ROC Curve - Train ({tag})")
    _save_roc_plot(test_df, threshold_ms_global, config.EVALUATION_DIR / f"roc_curve_test_{tag}.png", f"ROC Curve - Test ({tag})")
    if not suffix:
        _save_roc_plot(train_df, threshold_ms_global, config.EVALUATION_DIR / "roc_curve_train.png", "ROC Curve - Train")
        _save_roc_plot(test_df, threshold_ms_global, config.EVALUATION_DIR / "roc_curve_test.png", "ROC Curve - Test")

    _maybe_write_experiment_comparison()
    _write_markdown_summary(train_global, test_global, test_asset_threshold, holdout_report, experiment_tag=tag)

    payload = {
        "experiment_tag": tag,
        "classification_threshold_ms_global": threshold_ms_global,
        "evaluation_tolerance_ms": config.EVAL_HIT_TOLERANCE_MS,
        "notes": [
            "Binary classification is defined as early-arrival prediction: label_ms <= threshold_ms.",
            "AUC/ROC is computed from score = -predicted_ms.",
            "Per-asset threshold metrics are written to metrics_test_asset_threshold_<tag>.csv.",
            "Rows with prediction_status != predicted_labeled are excluded from metrics.",
        ],
    }
    cfg_path = config.EVALUATION_DIR / f"evaluation_config_{tag}.json"
    cfg_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log(f"Saved evaluation config: {cfg_path.name}")
    if not suffix:
        legacy_cfg_path = config.EVALUATION_DIR / "evaluation_config.json"
        legacy_cfg_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _log(f"Saved evaluation config: {legacy_cfg_path.name}")
    _log(f"Done. Outputs in: {config.EVALUATION_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate first-break predictions with global and per-asset thresholds")
    parser.add_argument(
        "--experiment-tag",
        type=str,
        default="latest",
        help="Used for output file suffixes (for example: a, b)",
    )
    parser.add_argument(
        "--no-val-fallback",
        action="store_true",
        help="If test predictions are missing, do not fallback to validation split",
    )
    args = parser.parse_args()
    run_evaluation(experiment_tag=args.experiment_tag, prefer_val_as_test=not args.no_val_fallback)
