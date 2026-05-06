from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


CHUNK_SIZE_1D = 250_000
TRACE_CHUNK_SIZE = 2_000
AMP_SAMPLE_TRACES = 1_000
RNG_SEED = 42


@dataclass
class RunningNumericStats:
    count: int = 0
    null_count: int = 0
    min_value: float = math.inf
    max_value: float = -math.inf
    mean: float = 0.0
    m2: float = 0.0
    first_value: float | None = None
    is_constant: bool = True

    def update(self, arr: np.ndarray) -> None:
        flat = np.asarray(arr).reshape(-1)
        if flat.size == 0:
            return
        valid_mask = np.isfinite(flat)
        self.null_count += int(flat.size - valid_mask.sum())
        valid = flat[valid_mask]
        if valid.size == 0:
            return

        vmin = float(valid.min())
        vmax = float(valid.max())
        if vmin < self.min_value:
            self.min_value = vmin
        if vmax > self.max_value:
            self.max_value = vmax

        if self.first_value is None:
            self.first_value = float(valid[0])
        if self.is_constant and not np.all(valid == self.first_value):
            self.is_constant = False

        n_b = int(valid.size)
        mean_b = float(valid.mean())
        m2_b = float(((valid - mean_b) ** 2).sum())
        if self.count == 0:
            self.count = n_b
            self.mean = mean_b
            self.m2 = m2_b
            return

        delta = mean_b - self.mean
        total = self.count + n_b
        self.mean += delta * n_b / total
        self.m2 += m2_b + delta * delta * self.count * n_b / total
        self.count = total

    @property
    def std(self) -> float:
        if self.count <= 1:
            return 0.0
        return math.sqrt(self.m2 / (self.count - 1))


def iter_1d_chunks(ds: h5py.Dataset, chunk_size: int = CHUNK_SIZE_1D) -> Iterable[np.ndarray]:
    n = ds.shape[0]
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        yield ds[start:end]


def compute_dataset_stats(ds: h5py.Dataset) -> Dict[str, object]:
    shape = tuple(ds.shape)
    dtype = str(ds.dtype)
    if len(shape) == 0:
        value = ds[()]
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        is_const = True
        null_count = int(pd.isna(value))
        min_v = None if null_count else value
        max_v = None if null_count else value
        return {
            "dtype": dtype,
            "shape": str(shape),
            "is_constant": is_const,
            "min_value": min_v,
            "max_value": max_v,
            "null_count": null_count,
        }

    if len(shape) > 1:
        return {
            "dtype": dtype,
            "shape": str(shape),
            "is_constant": "",
            "min_value": "",
            "max_value": "",
            "null_count": "",
        }

    kind = ds.dtype.kind
    if kind in {"i", "u", "f", "b"}:
        stats = RunningNumericStats()
        for chunk in iter_1d_chunks(ds):
            stats.update(chunk)
        min_v = "" if stats.min_value == math.inf else stats.min_value
        max_v = "" if stats.max_value == -math.inf else stats.max_value
        return {
            "dtype": dtype,
            "shape": str(shape),
            "is_constant": bool(stats.is_constant),
            "min_value": min_v,
            "max_value": max_v,
            "null_count": int(stats.null_count),
        }

    # String/object fall-back
    first_val = None
    is_constant = True
    null_count = 0
    min_v = None
    max_v = None
    for chunk in iter_1d_chunks(ds):
        flat = np.asarray(chunk).reshape(-1)
        vals = []
        for v in flat:
            if isinstance(v, bytes):
                v = v.decode("utf-8", errors="ignore")
            if pd.isna(v):
                null_count += 1
                continue
            vals.append(str(v))
        if not vals:
            continue
        if first_val is None:
            first_val = vals[0]
        if is_constant and any(v != first_val for v in vals):
            is_constant = False
        cmin = min(vals)
        cmax = max(vals)
        min_v = cmin if min_v is None else min(min_v, cmin)
        max_v = cmax if max_v is None else max(max_v, cmax)

    return {
        "dtype": dtype,
        "shape": str(shape),
        "is_constant": is_constant,
        "min_value": min_v if min_v is not None else "",
        "max_value": max_v if max_v is not None else "",
        "null_count": int(null_count),
    }


def sample_amplitudes(
    data_array: h5py.Dataset,
    rng: np.random.Generator,
    report_lines: List[str],
    out_dir: Path,
    asset: str,
) -> Dict[str, float]:
    n_traces = data_array.shape[0]
    sample_size = min(AMP_SAMPLE_TRACES, n_traces)
    indices = np.sort(rng.choice(n_traces, size=sample_size, replace=False))
    sampled = data_array[indices, :]
    flat = sampled.reshape(-1)

    amp_stats = {
        "sample_trace_count": int(sample_size),
        "mean": float(np.mean(flat)),
        "std": float(np.std(flat, ddof=1)),
        "min": float(np.min(flat)),
        "max": float(np.max(flat)),
        "p05": float(np.percentile(flat, 5)),
        "p25": float(np.percentile(flat, 25)),
        "p75": float(np.percentile(flat, 75)),
        "p95": float(np.percentile(flat, 95)),
    }
    report_lines.append("data_array sample amplitude stats (1000 traces or fewer):")
    for k, v in amp_stats.items():
        report_lines.append(f"  {k}: {v}")

    plt.figure(figsize=(8, 5))
    plt.hist(flat, bins=120, color="#1f77b4", alpha=0.9)
    plt.title(f"{asset} amplitude distribution (sampled)")
    plt.xlabel("Amplitude")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(out_dir / f"amplitude_hist_{asset}.png", dpi=150)
    plt.close()
    return amp_stats


def count_dead_traces(data_array: h5py.Dataset) -> int:
    n_traces = data_array.shape[0]
    dead = 0
    for start in range(0, n_traces, TRACE_CHUNK_SIZE):
        end = min(start + TRACE_CHUNK_SIZE, n_traces)
        block = data_array[start:end, :]
        dead += int(np.all(block == 0, axis=1).sum())
    return dead


def safe_scale(scale_arr: np.ndarray) -> np.ndarray:
    scale = np.asarray(scale_arr, dtype=np.float64)
    bad = (scale == 0) | ~np.isfinite(scale)
    if bad.any():
        scale = scale.copy()
        scale[bad] = 1.0
    return scale


def compute_streaming_correlation(
    vars_dict: Dict[str, np.ndarray],
) -> pd.DataFrame:
    keys = list(vars_dict.keys())
    mat = np.column_stack([vars_dict[k] for k in keys]).astype(np.float64, copy=False)
    n = mat.shape[1]
    out = np.full((n, n), np.nan, dtype=np.float64)
    std = np.std(mat, axis=0, ddof=1)
    for i in range(n):
        out[i, i] = 1.0 if std[i] > 0 else np.nan
    for i in range(n):
        for j in range(i + 1, n):
            if std[i] == 0 or std[j] == 0:
                c = np.nan
            else:
                c = float(np.corrcoef(mat[:, i], mat[:, j])[0, 1])
            out[i, j] = c
            out[j, i] = c
    return pd.DataFrame(out, index=keys, columns=keys)


def check_sorted_within_gathers(
    shotid: np.ndarray,
    offset: np.ndarray,
    rec_x: np.ndarray,
    rec_y: np.ndarray,
) -> Dict[str, object]:
    monotonic_shot = bool(np.all(np.diff(shotid) >= 0))

    if not monotonic_shot:
        return {
            "shotid_monotonic_non_decreasing": False,
            "gathers_checked": 0,
            "offset_sorted_fraction": None,
            "rec_x_sorted_fraction": None,
            "rec_y_sorted_fraction": None,
        }

    change_idx = np.where(np.diff(shotid) != 0)[0] + 1
    bounds = np.concatenate(([0], change_idx, [len(shotid)]))
    total = len(bounds) - 1
    ok_offset = 0
    ok_rx = 0
    ok_ry = 0
    for i in range(total):
        s = bounds[i]
        e = bounds[i + 1]
        if e - s <= 1:
            ok_offset += 1
            ok_rx += 1
            ok_ry += 1
            continue
        if np.all(np.diff(offset[s:e]) >= 0):
            ok_offset += 1
        if np.all(np.diff(rec_x[s:e]) >= 0):
            ok_rx += 1
        if np.all(np.diff(rec_y[s:e]) >= 0):
            ok_ry += 1
    return {
        "shotid_monotonic_non_decreasing": True,
        "gathers_checked": int(total),
        "offset_sorted_fraction": float(ok_offset / total),
        "rec_x_sorted_fraction": float(ok_rx / total),
        "rec_y_sorted_fraction": float(ok_ry / total),
    }


def first_break_metrics(spare1: np.ndarray, total_recording_ms: float) -> Dict[str, float]:
    zeros = int(np.sum(spare1 == 0))
    neg_ones = int(np.sum(spare1 == -1))
    valid_mask = spare1 > 0
    valid = spare1[valid_mask]
    corrupted = int(np.sum(valid > total_recording_ms))
    return {
        "count_zero": zeros,
        "count_minus_one": neg_ones,
        "count_valid_positive": int(valid.size),
        "valid_min": float(np.min(valid)) if valid.size else math.nan,
        "valid_max": float(np.max(valid)) if valid.size else math.nan,
        "valid_mean": float(np.mean(valid)) if valid.size else math.nan,
        "valid_median": float(np.median(valid)) if valid.size else math.nan,
        "valid_std": float(np.std(valid, ddof=1)) if valid.size > 1 else 0.0,
        "labeled_percentage": float(100.0 * valid.size / spare1.size),
        "count_corrupted_gt_recording_time": corrupted,
    }


def write_key_list(asset: str, keys: List[str], out_dir: Path) -> None:
    key_path = out_dir / f"all_keys_{asset}.txt"
    key_path.write_text("\n".join(keys), encoding="utf-8")


def analyze_asset(asset_key: str, asset_path: Path, out_dir: Path) -> None:
    rng = np.random.default_rng(RNG_SEED)
    report_lines: List[str] = [f"Asset: {asset_key}", f"File: {asset_path.name}"]

    with h5py.File(asset_path, "r") as f:
        g = f["TRACE_DATA"]["DEFAULT"]
        keys = sorted(list(g.keys()))
        write_key_list(asset_key, keys, out_dir)
        report_lines.append(f"Total keys in TRACE_DATA/DEFAULT: {len(keys)}")
        report_lines.append("All keys saved to all_keys_<asset>.txt")

        # 2.1 column inventory
        inventory_rows: List[Dict[str, object]] = []
        for key in keys:
            ds = g[key]
            stats = compute_dataset_stats(ds)
            inventory_rows.append(
                {
                    "key_name": key,
                    "dtype": stats["dtype"],
                    "shape": stats["shape"],
                    "is_constant": stats["is_constant"],
                    "min_value": stats["min_value"],
                    "max_value": stats["max_value"],
                    "null_count": stats["null_count"],
                }
            )
        inventory_df = pd.DataFrame(inventory_rows)
        inventory_df.to_csv(out_dir / f"column_inventory_{asset_key}.csv", index=False)

        # Pull required core columns fully (1D) for required analyses
        spare1 = np.asarray(g["SPARE1"][:], dtype=np.float64)
        samp_rate = np.asarray(g["SAMP_RATE"][:], dtype=np.float64)
        samp_num = np.asarray(g["SAMP_NUM"][:], dtype=np.float64)
        shotid = np.asarray(g["SHOTID"][:], dtype=np.int64)
        shot_peg = np.asarray(g["SHOT_PEG"][:], dtype=np.float64)
        rec_peg = np.asarray(g["REC_PEG"][:], dtype=np.float64)
        source_x_raw = np.asarray(g["SOURCE_X"][:], dtype=np.float64)
        source_y_raw = np.asarray(g["SOURCE_Y"][:], dtype=np.float64)
        source_ht_raw = np.asarray(g["SOURCE_HT"][:], dtype=np.float64)
        rec_x_raw = np.asarray(g["REC_X"][:], dtype=np.float64)
        rec_y_raw = np.asarray(g["REC_Y"][:], dtype=np.float64)
        rec_ht_raw = np.asarray(g["REC_HT"][:], dtype=np.float64)
        coord_scale = safe_scale(np.asarray(g["COORD_SCALE"][:], dtype=np.float64))
        ht_scale = safe_scale(np.asarray(g["HT_SCALE"][:], dtype=np.float64))
        data_array = g["data_array"]

        source_x = source_x_raw / coord_scale
        source_y = source_y_raw / coord_scale
        rec_x = rec_x_raw / coord_scale
        rec_y = rec_y_raw / coord_scale
        source_ht = source_ht_raw / ht_scale
        rec_ht = rec_ht_raw / ht_scale
        offset = np.sqrt((source_x - rec_x) ** 2 + (source_y - rec_y) ** 2)

        # 2.2 detailed value counts and distributions
        total_recording_ms_arr = samp_num * samp_rate / 1000.0
        total_recording_ms = float(np.median(total_recording_ms_arr))
        fb = first_break_metrics(spare1, total_recording_ms)

        samp_rate_unique = np.unique(samp_rate)
        samp_num_unique = np.unique(samp_num)

        unique_shots, shot_counts = np.unique(shotid, return_counts=True)
        shotid_null_count = int(np.sum(~np.isfinite(shotid.astype(np.float64))))
        shotid_negative_count = int(np.sum(shotid < 0))

        coord_summary = []
        for name, arr in [
            ("SOURCE_X", source_x),
            ("SOURCE_Y", source_y),
            ("SOURCE_HT", source_ht),
            ("REC_X", rec_x),
            ("REC_Y", rec_y),
            ("REC_HT", rec_ht),
            ("OFFSET", offset),
        ]:
            coord_summary.append(
                {
                    "variable": name,
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "mean": float(np.mean(arr)),
                    "std": float(np.std(arr, ddof=1)),
                    "zero_count": int(np.sum(arr == 0)),
                }
            )

        receiver_pairs = np.stack([rec_x, rec_y], axis=1)
        unique_receiver_count = int(np.unique(receiver_pairs, axis=0).shape[0])
        receiver_duplicate_count = int(len(rec_x) - unique_receiver_count)

        amp_stats = sample_amplitudes(data_array, rng, report_lines, out_dir, asset_key)
        dead_trace_count = count_dead_traces(data_array)

        # 2.3 missing variables and useful checks
        exists_sht_real = "SHT_real" in g.keys()
        exists_rht_real = "RHT_real" in g.keys()
        missing_rows = [
            {"variable": "offset", "status": "not_stored_derived_required"},
            {"variable": "incidence_angle", "status": "not_stored_derivable"},
            {"variable": "trace_quality_flag", "status": "not_stored_derive_from_data"},
            {"variable": "gather_index", "status": "not_stored_derive_from_SHOTID"},
            {"variable": "trace_index_within_gather", "status": "not_stored_derive_after_grouping"},
            {"variable": "SHT_real", "status": "present" if exists_sht_real else "absent"},
            {"variable": "RHT_real", "status": "present" if exists_rht_real else "absent"},
            {"variable": "REC_PEG", "status": "present"},
            {"variable": "SHOT_PEG", "status": "present"},
        ]
        pd.DataFrame(missing_rows).to_csv(out_dir / f"missing_variables_{asset_key}.csv", index=False)

        # 2.4 correlations (valid labels only)
        valid_mask = spare1 > 0
        corr_inputs = {
            "offset": offset[valid_mask],
            "SOURCE_X": source_x[valid_mask],
            "SOURCE_Y": source_y[valid_mask],
            "REC_X": rec_x[valid_mask],
            "REC_Y": rec_y[valid_mask],
            "SAMP_RATE": samp_rate[valid_mask],
            "SPARE1": spare1[valid_mask],
        }
        corr_df = compute_streaming_correlation(corr_inputs)
        corr_df.to_csv(out_dir / f"correlation_table_{asset_key}.csv")

        # 2.5 time ordering
        corrupted_mask = (spare1 > 0) & (spare1 > total_recording_ms_arr)
        time_order_info = check_sorted_within_gathers(shotid, offset, rec_x, rec_y)

        # Save detailed tables
        pd.DataFrame([fb]).to_csv(out_dir / f"spare1_stats_{asset_key}.csv", index=False)
        pd.DataFrame(
            [
                {
                    "samp_rate_unique_count": int(len(samp_rate_unique)),
                    "samp_rate_unique_values_us": json.dumps(samp_rate_unique[:20].tolist()),
                    "samp_num_unique_count": int(len(samp_num_unique)),
                    "samp_num_unique_values": json.dumps(samp_num_unique[:20].tolist()),
                    "total_recording_time_ms_median": total_recording_ms,
                    "recording_time_min_ms": float(np.min(total_recording_ms_arr)),
                    "recording_time_max_ms": float(np.max(total_recording_ms_arr)),
                    "samp_rate_varies_flag": bool(len(samp_rate_unique) > 1),
                    "samp_num_varies_flag": bool(len(samp_num_unique) > 1),
                }
            ]
        ).to_csv(out_dir / f"sampling_stats_{asset_key}.csv", index=False)
        pd.DataFrame(
            [
                {
                    "unique_shot_count": int(len(unique_shots)),
                    "traces_per_shot_mean": float(np.mean(shot_counts)),
                    "traces_per_shot_min": int(np.min(shot_counts)),
                    "traces_per_shot_max": int(np.max(shot_counts)),
                    "traces_per_shot_std": float(np.std(shot_counts, ddof=1)),
                    "shotid_null_count": shotid_null_count,
                    "shotid_negative_count": shotid_negative_count,
                    "shot_peg_unique_count": int(np.unique(shot_peg).size),
                    "rec_peg_unique_count": int(np.unique(rec_peg).size),
                }
            ]
        ).to_csv(out_dir / f"shot_stats_{asset_key}.csv", index=False)
        pd.DataFrame(coord_summary).to_csv(out_dir / f"coordinate_offset_stats_{asset_key}.csv", index=False)
        pd.DataFrame(
            [
                {
                    "receiver_unique_xy_count": unique_receiver_count,
                    "receiver_duplicate_xy_count": receiver_duplicate_count,
                }
            ]
        ).to_csv(out_dir / f"receiver_duplicate_stats_{asset_key}.csv", index=False)
        pd.DataFrame(
            [
                {
                    "dead_trace_count": dead_trace_count,
                    "dead_trace_percentage": 100.0 * dead_trace_count / len(spare1),
                }
            ]
        ).to_csv(out_dir / f"dead_trace_stats_{asset_key}.csv", index=False)
        pd.DataFrame([amp_stats]).to_csv(out_dir / f"amplitude_sample_stats_{asset_key}.csv", index=False)
        pd.DataFrame([time_order_info]).to_csv(out_dir / f"time_order_checks_{asset_key}.csv", index=False)
        pd.DataFrame(
            [
                {
                    "corrupted_spare1_count": int(corrupted_mask.sum()),
                    "corrupted_spare1_percentage": float(100.0 * corrupted_mask.mean()),
                }
            ]
        ).to_csv(out_dir / f"corrupted_label_stats_{asset_key}.csv", index=False)

        # Graphs requested by user
        valid_spare1 = spare1[spare1 > 0]
        plt.figure(figsize=(8, 5))
        plt.hist(valid_spare1, bins=120, color="#2ca02c", alpha=0.9)
        plt.title(f"{asset_key} SPARE1 distribution (valid labels)")
        plt.xlabel("SPARE1 (ms)")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(out_dir / f"spare1_hist_{asset_key}.png", dpi=150)
        plt.close()

        n_scatter = min(30_000, valid_spare1.size)
        scatter_idx = np.random.default_rng(RNG_SEED).choice(valid_spare1.size, n_scatter, replace=False)
        vx = offset[valid_mask][scatter_idx]
        vy = valid_spare1[scatter_idx]
        plt.figure(figsize=(7, 6))
        plt.scatter(vx, vy, s=4, alpha=0.25, color="#d62728")
        plt.title(f"{asset_key} offset vs SPARE1 (sampled)")
        plt.xlabel("Offset")
        plt.ylabel("SPARE1 (ms)")
        plt.tight_layout()
        plt.savefig(out_dir / f"offset_vs_spare1_{asset_key}.png", dpi=150)
        plt.close()

        # Text report
        report_lines.extend(
            [
                "",
                "SPARE1 summary:",
                json.dumps(fb, indent=2),
                "",
                "Sampling summary:",
                f"SAMP_RATE unique values (us): {samp_rate_unique[:20].tolist()}",
                f"SAMP_NUM unique values: {samp_num_unique[:20].tolist()}",
                f"Total recording time median (ms): {total_recording_ms}",
                f"SAMP_RATE varies flag: {len(samp_rate_unique) > 1}",
                f"SAMP_NUM varies flag: {len(samp_num_unique) > 1}",
                "",
                "Shot/gather summary:",
                f"Unique SHOTID count: {len(unique_shots)}",
                f"Traces-per-shot mean/min/max/std: {np.mean(shot_counts):.4f} / "
                f"{np.min(shot_counts)} / {np.max(shot_counts)} / {np.std(shot_counts, ddof=1):.4f}",
                f"SHOTID null count: {shotid_null_count}",
                f"SHOTID negative count: {shotid_negative_count}",
                "",
                "Receiver duplicate summary:",
                f"Unique receiver XY count: {unique_receiver_count}",
                f"Duplicate receiver XY rows: {receiver_duplicate_count}",
                "",
                "Time-order checks:",
                json.dumps(time_order_info, indent=2),
                "",
                "Corrupted labels:",
                f"count SPARE1 > recording_time: {int(corrupted_mask.sum())}",
                f"percentage: {100.0 * corrupted_mask.mean():.6f}",
                "",
                "Notes:",
                "- Offset is not stored and is derived from scaled coordinates.",
                "- Incidence angle, gather index, trace index within gather are not stored directly.",
                f"- SHT_real exists: {exists_sht_real}",
                f"- RHT_real exists: {exists_rht_real}",
            ]
        )

        (out_dir / f"eda_report_{asset_key}.txt").write_text("\n".join(report_lines), encoding="utf-8")


def combine_csv_tables(out_dir: Path, asset_keys: List[str]) -> None:
    table_prefixes = [
        "amplitude_sample_stats",
        "column_inventory",
        "coordinate_offset_stats",
        "corrupted_label_stats",
        "dead_trace_stats",
        "missing_variables",
        "receiver_duplicate_stats",
        "sampling_stats",
        "shot_stats",
        "spare1_stats",
        "time_order_checks",
    ]
    for prefix in table_prefixes:
        frames = []
        for asset_key in asset_keys:
            path = out_dir / f"{prefix}_{asset_key}.csv"
            if not path.exists():
                continue
            df = pd.read_csv(path)
            df.insert(0, "asset", asset_key)
            frames.append(df)
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(out_dir / f"{prefix}_all_assets.csv", index=False)


def combine_correlation_tables(out_dir: Path, asset_keys: List[str]) -> None:
    frames = []
    for asset_key in asset_keys:
        path = out_dir / f"correlation_table_{asset_key}.csv"
        if not path.exists():
            continue
        corr_df = pd.read_csv(path, index_col=0)
        long_df = (
            corr_df.rename_axis("row_variable")
            .reset_index()
            .melt(id_vars="row_variable", var_name="column_variable", value_name="correlation")
        )
        long_df.insert(0, "asset", asset_key)
        frames.append(long_df)
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(out_dir / "correlation_table_all_assets.csv", index=False)


def combine_key_lists(out_dir: Path, asset_keys: List[str]) -> None:
    rows: List[Dict[str, str]] = []
    combined_lines: List[str] = []
    for asset_key in asset_keys:
        path = out_dir / f"all_keys_{asset_key}.txt"
        if not path.exists():
            continue
        keys = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        combined_lines.append(f"[{asset_key}]")
        combined_lines.extend(keys)
        combined_lines.append("")
        for key in keys:
            rows.append({"asset": asset_key, "key_name": key})
    if rows:
        pd.DataFrame(rows).to_csv(out_dir / "all_keys_all_assets.csv", index=False)
        (out_dir / "all_keys_all_assets.txt").write_text("\n".join(combined_lines).strip() + "\n", encoding="utf-8")


def combine_reports(out_dir: Path, asset_keys: List[str]) -> None:
    sections: List[str] = []
    for asset_key in asset_keys:
        path = out_dir / f"eda_report_{asset_key}.txt"
        if not path.exists():
            continue
        sections.append(f"===== {asset_key.upper()} =====")
        sections.append(path.read_text(encoding="utf-8"))
        sections.append("")
    if sections:
        (out_dir / "eda_report_all_assets.txt").write_text("\n".join(sections).strip() + "\n", encoding="utf-8")


def combine_graph_panels(out_dir: Path, asset_keys: List[str]) -> None:
    graph_prefixes = [
        "amplitude_hist",
        "offset_vs_spare1",
        "spare1_hist",
    ]
    for prefix in graph_prefixes:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        used = 0
        for ax, asset_key in zip(axes, asset_keys):
            path = out_dir / f"{prefix}_{asset_key}.png"
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
            plt.savefig(out_dir / f"{prefix}_all_assets.png", dpi=150)
        plt.close(fig)


def delete_per_asset_outputs(out_dir: Path, asset_keys: List[str]) -> None:
    file_patterns = [
        "all_keys_{asset}.txt",
        "amplitude_hist_{asset}.png",
        "amplitude_sample_stats_{asset}.csv",
        "column_inventory_{asset}.csv",
        "coordinate_offset_stats_{asset}.csv",
        "correlation_table_{asset}.csv",
        "corrupted_label_stats_{asset}.csv",
        "dead_trace_stats_{asset}.csv",
        "eda_report_{asset}.txt",
        "missing_variables_{asset}.csv",
        "offset_vs_spare1_{asset}.png",
        "receiver_duplicate_stats_{asset}.csv",
        "sampling_stats_{asset}.csv",
        "shot_stats_{asset}.csv",
        "spare1_hist_{asset}.png",
        "spare1_stats_{asset}.csv",
        "time_order_checks_{asset}.csv",
    ]
    for asset_key in asset_keys:
        for pattern in file_patterns:
            path = out_dir / pattern.format(asset=asset_key)
            if path.exists():
                path.unlink()


def run_eda() -> None:
    config.ensure_output_dirs()
    out_dir = config.EDA_DIR
    asset_keys = list(config.DATASET_ASSETS.keys())

    # Always re-emit dataset role summary for audit traceability.
    summary_path = out_dir / "dataset_roles_summary.json"
    payload = {
        key: {
            "file_name": asset.file_name,
            "role": asset.role,
            "total_traces": asset.total_traces,
            "labeled_pct_phase45_report": asset.labeled_pct,
        }
        for key, asset in config.DATASET_ASSETS.items()
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for asset_key, asset in config.DATASET_ASSETS.items():
        path = config.get_asset_path(asset_key)
        print(f"[01_eda] Processing {asset_key}: {path.name}")
        analyze_asset(asset_key=asset_key, asset_path=path, out_dir=out_dir)
        print(f"[01_eda] Completed {asset_key}")

    print("[01_eda] Combining per-asset outputs into unified files")
    combine_csv_tables(out_dir=out_dir, asset_keys=asset_keys)
    combine_correlation_tables(out_dir=out_dir, asset_keys=asset_keys)
    combine_key_lists(out_dir=out_dir, asset_keys=asset_keys)
    combine_reports(out_dir=out_dir, asset_keys=asset_keys)
    combine_graph_panels(out_dir=out_dir, asset_keys=asset_keys)

    print("[01_eda] Deleting per-asset EDA output files")
    delete_per_asset_outputs(out_dir=out_dir, asset_keys=asset_keys)

    print(f"[01_eda] All outputs written to: {out_dir}")


if __name__ == "__main__":
    run_eda()
