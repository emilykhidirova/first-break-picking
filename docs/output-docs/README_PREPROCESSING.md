# Preprocessing Output Documentation

## Scope
Canonical transformed datasets and feature artifacts used for training, split governance, and experiment orchestration.

## Producer Scripts
- `scripts/02_preprocessing.py`
- `scripts/03_feature_engineering.py`
- `scripts/03b_stalta_features.py`
- `scripts/04_dataset_builder.py`

## Consumer Scripts
- `scripts/06_train.py`
- `scripts/08_visualize_predictions.py`
- `scripts/07_evaluate.py (via prediction lineage)`

## Naming Rules and Lineage
- `_experimentb`: artifact generated for Experiment B (domain adaptation split behavior).
- `_smoothed`: post-processed prediction file produced by hyperbolic smoothing stage.
- `_latest`: convenience naming for current default track metrics in evaluation outputs.
- `stalta_*`: baseline-only evaluation artifacts (pure STA/LTA method, no LightGBM).
- `predictions_{split}*.csv`: row-level per-trace prediction artifacts (`train`, `val`, `test`).
- `metrics_*_global_threshold*.csv`: classification/regression summary under one global threshold.
- `metrics_*_asset_threshold*.csv`: same metrics with per-asset thresholds.
- `holdout_report_by_asset*.csv`: per-asset holdout-focused summary diagnostics.

## Artifact Inventory
- Total files documented: `59`
- Source directory: `outputs/preprocessing`

### `dataset_builder_report.txt`
- Path: `outputs/preprocessing/dataset_builder_report.txt`
- Size: `2,290` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `42`
- Content preview:
```text
Random seed: 42
Train/validation split strategy: separate 85/15 split within each training asset at shot/gather level.

Split summary:
           asset                 role  num_shots  num_labeled_traces  num_total_traces                                    notes
 brunswick_train             training       1310             3174731           3817692                   85% of brunswick shots
   brunswick_val         internal_val        231              558490            678848                   15% of brunswick shots
  halfmile_train             training        586              844507            933609                    85% of halfmile shots
```

### `dataset_split_summary.csv`
- Path: `outputs/preprocessing/dataset_split_summary.csv`
- Size: `654` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `8`
- Columns: `6`
- Exact column list:
```text
asset, role, num_shots, num_labeled_traces, num_total_traces, notes
```
- Inferred dtypes:
| column             | inferred_dtype   |
|:-------------------|:-----------------|
| asset              | str              |
| role               | str              |
| num_shots          | int64            |
| num_labeled_traces | int64            |
| num_total_traces   | int64            |
| notes              | str              |
- Null profile:
| column             |   null_count |   null_pct |
|:-------------------|-------------:|-----------:|
| asset              |            0 |          0 |
| role               |            0 |          0 |
| num_shots          |            0 |          0 |
| num_labeled_traces |            0 |          0 |
| num_total_traces   |            0 |          0 |
| notes              |            0 |          0 |
- Sample preview (first rows, summarized):
| asset           | role         |   num_shots |   num_labeled_traces |   num_total_traces | notes                  |
|:----------------|:-------------|------------:|---------------------:|-------------------:|:-----------------------|
| brunswick_train | training     |        1310 |              3174731 |            3817692 | 85% of brunswick shots |
| brunswick_val   | internal_val |         231 |               558490 |             678848 | 15% of brunswick shots |
| halfmile_train  | training     |         586 |               844507 |             933609 | 85% of halfmile shots  |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `evaluation_asset_manifest.csv`
- Path: `outputs/preprocessing/evaluation_asset_manifest.csv`
- Size: `97` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `2`
- Columns: `4`
- Exact column list:
```text
asset, role, gather_count, trace_count
```
- Inferred dtypes:
| column       | inferred_dtype   |
|:-------------|:-----------------|
| asset        | str              |
| role         | str              |
| gather_count | int64            |
| trace_count  | int64            |
- Null profile:
| column       |   null_count |   null_pct |
|:-------------|-------------:|-----------:|
| asset        |            0 |          0 |
| role         |            0 |          0 |
| gather_count |            0 |          0 |
| trace_count  |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   | role        |   gather_count |   trace_count |
|:--------|:------------|---------------:|--------------:|
| lalor   | validate    |            905 |       1211857 |
| sudbury | stress_test |            715 |        200338 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `excluded_model_features.csv`
- Path: `outputs/preprocessing/excluded_model_features.csv`
- Size: `292` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `6`
- Columns: `2`
- Exact column list:
```text
column_name, reason
```
- Inferred dtypes:
| column      | inferred_dtype   |
|:------------|:-----------------|
| column_name | str              |
| reason      | str              |
- Null profile:
| column      |   null_count |   null_pct |
|:------------|-------------:|-----------:|
| column_name |            0 |          0 |
| reason      |            0 |          0 |
- Sample preview (first rows, summarized):
| column_name          | reason                        |
|:---------------------|:------------------------------|
| FIRST_BREAK_AMPLIT   | label_adjacent_leakage_risk   |
| FIRST_BREAK_VELOCITY | label_adjacent_leakage_risk   |
| MODELLED_BREAK_TIME  | baseline_only_not_model_input |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `feature_engineering_config.json`
- Path: `outputs/preprocessing/feature_engineering_config.json`
- Size: `3,471` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured configuration/summary payload.
- Top-level type: `dict`
- Top-level keys (17): `working_label_column, primary_offset_column_by_asset, feature_columns, pre_break_noise_window_samples, zero_crossing_window_fraction, trace_harmonization_strategy, notes, stalta_diagnostic_proxy_columns, stalta_feature_columns, stalta_config, coordinate_normalization_stats_training_shots, static_leakage_check_source, static_leakage_check_results, final_model_input_feature_columns, final_confirmed_feature_columns, auxiliary_flag_columns, dropped_after_step5`
- Key type preview:
```json
{
  "working_label_column": "str",
  "primary_offset_column_by_asset": "dict",
  "feature_columns": "list",
  "pre_break_noise_window_samples": "int",
  "zero_crossing_window_fraction": "float",
  "trace_harmonization_strategy": "str",
  "notes": "list",
  "stalta_diagnostic_proxy_columns": "list",
  "stalta_feature_columns": "list",
  "stalta_config": "dict",
  "coordinate_normalization_stats_training_shots": "dict",
  "static_leakage_check_source": "str",
  "static_leakage_check_results": "list",
  "final_model_input_feature_columns": "list",
  "final_confirmed_feature_columns": "list",
  "auxiliary_flag_columns": "list",
  "dropped_after_step5": "list"
}
```
- Content preview (truncated):
```json
{
  "working_label_column": "SPARE1",
  "primary_offset_column_by_asset": {
    "brunswick": "derived_from_coordinates",
    "halfmile": "derived_from_coordinates",
    "lalor": "derived_from_coordinates",
    "sudbury": "derived_from_coordinates"
  },
  "feature_columns": [
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
    "is_dead_trace"
  ],
  "pre_break_noise_window_samples": 5,
  "zero_crossing_window_fraction": 0.5,
  "trace_harmonization_strategy": "downsample_lalor_to_2ms_then_pad_or_crop_at_runtime",
  "notes": [
    "Offset is derived from scaled source/receiver coordinates for all assets.",
    "Static fields and coordinate-normalized source location features are excluded from model inputs.",
    "FIRST_BREAK_AMPLIT, FIRST_BREAK_VELOCITY, and MODELLED_BREAK_TIME are excluded from model inputs due to leakage or baseline-only use."
  ],
  "stalta_diagnostic_proxy_columns": [
    "noise_energy_first_20samples",
    "signal_energy_after_stalta",
    "amplitude_at_stalta_pick",
    "dominant_frequency_proxy"
  ],
  "stalta_feature_columns": [
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
    "hyperbolic_residual"
  ],
  "stalta_config": {
    "sta_window_ms": 20.0,
    "lta_window_ms": 200.0,
    "threshold_by_asset": {
      "brunswick": 3.0,
      "halfmile": 3.0,
      "lalor": 2.5,
      "sudbury": 3.5
    },
    "min_search_sample_by_asset": {
      "brunswick": 5,
      "halfmile": 5,
      "lalor": 10,
      "sudbury": 5
    },
    "signal_window_samples": 50
  },
  "coordinate_normalization_stats_training_shots": {
    "source_x_mean": 413638.2167721519,
    "source_x_std": 192670.70545003237,
    "source_y_mean": 5252521.314345991,
    "source_y_std": 5511.22845787169,
    "computed_from_training_shots_only": true,
    "training_assets_used": [
      "brunswick",
      "halfmile"
    ]
  },
  "static_leakage_check_source": "not_applicable_static_features_removed",
  "stati
```

### `feature_engineering_overview_all_assets.csv`
- Path: `outputs/preprocessing/feature_engineering_overview_all_assets.csv`
- Size: `306` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `4`
- Columns: `5`
- Exact column list:
```text
asset, feature_rows_written, parquet_written, working_label_column, working_offset_column
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| feature_rows_written  | int64            |
| parquet_written       | bool             |
| working_label_column  | str              |
| working_offset_column | str              |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| feature_rows_written  |            0 |          0 |
| parquet_written       |            0 |          0 |
| working_label_column  |            0 |          0 |
| working_offset_column |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     |   feature_rows_written | parquet_written   | working_label_column   | working_offset_column    |
|:----------|-----------------------:|:------------------|:-----------------------|:-------------------------|
| brunswick |                3733221 | False             | SPARE1                 | derived_from_coordinates |
| halfmile  |                 993180 | False             | SPARE1                 | derived_from_coordinates |
| lalor     |                1211857 | False             | SPARE1                 | derived_from_coordinates |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `feature_engineering_report_all_assets.txt`
- Path: `outputs/preprocessing/feature_engineering_report_all_assets.txt`
- Size: `13,843` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `90`
- Content preview:
```text
===== BRUNSWICK =====
Asset: brunswick
Working offset source for modeling: derived_from_coordinates
Working label column: SPARE1
Rows written: 3733221
CSV output: features_brunswick.csv
Parquet output written successfully: False
Noise window samples: 5
```

### `feature_engineering_report_brunswick.txt`
- Path: `outputs/preprocessing/feature_engineering_report_brunswick.txt`
- Size: `3,463` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `20`
- Content preview:
```text
Asset: brunswick
Working offset source for modeling: derived_from_coordinates
Working label column: SPARE1
Rows written: 3733221
CSV output: features_brunswick.csv
Parquet output written successfully: False
Noise window samples: 5
Zero crossing window fraction: 0.5
```

### `feature_engineering_report_halfmile.txt`
- Path: `outputs/preprocessing/feature_engineering_report_halfmile.txt`
- Size: `3,450` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `20`
- Content preview:
```text
Asset: halfmile
Working offset source for modeling: derived_from_coordinates
Working label column: SPARE1
Rows written: 993180
CSV output: features_halfmile.csv
Parquet output written successfully: False
Noise window samples: 5
Zero crossing window fraction: 0.5
```

### `feature_engineering_report_lalor.txt`
- Path: `outputs/preprocessing/feature_engineering_report_lalor.txt`
- Size: `3,405` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `20`
- Content preview:
```text
Asset: lalor
Working offset source for modeling: derived_from_coordinates
Working label column: SPARE1
Rows written: 1211857
CSV output: features_lalor.csv
Parquet output written successfully: False
Noise window samples: 5
Zero crossing window fraction: 0.5
```

### `feature_engineering_report_sudbury.txt`
- Path: `outputs/preprocessing/feature_engineering_report_sudbury.txt`
- Size: `3,428` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `20`
- Content preview:
```text
Asset: sudbury
Working offset source for modeling: derived_from_coordinates
Working label column: SPARE1
Rows written: 200338
CSV output: features_sudbury.csv
Parquet output written successfully: False
Noise window samples: 5
Zero crossing window fraction: 0.5
```

### `feature_normalization_stats.json`
- Path: `outputs/preprocessing/feature_normalization_stats.json`
- Size: `790` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: structured configuration/summary payload.
- Top-level type: `dict`
- Top-level keys (6): `split_random_seed, coordinate_normalization, label_column, normalization_method, trace_harmonization_strategy, notes`
- Key type preview:
```json
{
  "split_random_seed": "int",
  "coordinate_normalization": "dict",
  "label_column": "str",
  "normalization_method": "str",
  "trace_harmonization_strategy": "str",
  "notes": "list"
}
```
- Content preview (truncated):
```json
{
  "split_random_seed": 42,
  "coordinate_normalization": {
    "source_x_mean": 413638.2167721519,
    "source_x_std": 192670.70545003237,
    "source_y_mean": 5252521.314345991,
    "source_y_std": 5511.22845787169,
    "computed_from_training_shots_only": true,
    "training_assets_used": [
      "brunswick",
      "halfmile"
    ]
  },
  "label_column": "SPARE1",
  "normalization_method": "per_trace",
  "trace_harmonization_strategy": "downsample_lalor_to_2ms_then_pad_or_crop_at_runtime",
  "notes": [
    "Stats are computed from Brunswick + Halfmile training shots only.",
    "Use these same stats for Lalor validation and Sudbury stress-test inference.",
    "Dead traces should remain zero vectors with a dead-trace flag; no imputation is applied."
  ]
}
```

### `features_brunswick.csv`
- Path: `outputs/preprocessing/features_brunswick.csv`
- Size: `1,284,830,573` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `3,733,221`
- Columns: `32`
- Exact column list:
```text
asset, trace_index, shot_id, gather_sequence_index, trace_index_within_gather, number_of_traces_in_gather, offset_gather_zscore, offset_rank, source_ht_scaled, rec_ht_scaled, elevation_diff, slant_distance, pre_break_noise_energy, zero_crossing_rate, max_abs_amplitude, is_dead_trace, stalta_pick_sample, stalta_pick_ms, stalta_peak_ratio, stalta_ratio_at_pick, stalta_failed, amplitude_at_stalta_pick, noise_energy_first_20samples, signal_energy_after_stalta, dominant_frequency_proxy, velocity_estimate_stalta, slant_time_correction, gather_median_pick_ms, pick_deviation_from_gather_median, gather_pick_std, hyperbolic_residual, offset
```
- Inferred dtypes:
| column                            | inferred_dtype   |
|:----------------------------------|:-----------------|
| asset                             | str              |
| trace_index                       | int64            |
| shot_id                           | int64            |
| gather_sequence_index             | int64            |
| trace_index_within_gather         | int64            |
| number_of_traces_in_gather        | int64            |
| offset_gather_zscore              | float64          |
| offset_rank                       | float64          |
| source_ht_scaled                  | float64          |
| rec_ht_scaled                     | float64          |
| elevation_diff                    | float64          |
| slant_distance                    | float64          |
| pre_break_noise_energy            | float64          |
| zero_crossing_rate                | float64          |
| max_abs_amplitude                 | float64          |
| is_dead_trace                     | int64            |
| stalta_pick_sample                | int64            |
| stalta_pick_ms                    | float64          |
| stalta_peak_ratio                 | float64          |
| stalta_ratio_at_pick              | float64          |
| stalta_failed                     | int64            |
| amplitude_at_stalta_pick          | float64          |
| noise_energy_first_20samples      | float64          |
| signal_energy_after_stalta        | float64          |
| dominant_frequency_proxy          | float64          |
| velocity_estimate_stalta          | float64          |
| slant_time_correction             | float64          |
| gather_median_pick_ms             | float64          |
| pick_deviation_from_gather_median | float64          |
| gather_pick_std                   | float64          |
| hyperbolic_residual               | float64          |
| offset                            | float64          |
- Null profile:
| column                            |   null_count |   null_pct |
|:----------------------------------|-------------:|-----------:|
| asset                             |            0 |    0       |
| trace_index                       |            0 |    0       |
| shot_id                           |            0 |    0       |
| gather_sequence_index             |            0 |    0       |
| trace_index_within_gather         |            0 |    0       |
| number_of_traces_in_gather        |            0 |    0       |
| offset_gather_zscore              |            0 |    0       |
| offset_rank                       |            0 |    0       |
| source_ht_scaled                  |            0 |    0       |
| rec_ht_scaled                     |            0 |    0       |
| elevation_diff                    |            0 |    0       |
| slant_distance                    |            0 |    0       |
| pre_break_noise_energy            |            0 |    0       |
| zero_crossing_rate                |            0 |    0       |
| max_abs_amplitude                 |            0 |    0       |
| is_dead_trace                     |            0 |    0       |
| stalta_pick_sample                |            0 |    0       |
| stalta_pick_ms                    |       148559 |    3.97938 |
| stalta_peak_ratio                 |            0 |    0       |
| stalta_ratio_at_pick              |            0 |    0       |
| stalta_failed                     |            0 |    0       |
| amplitude_at_stalta_pick          |            0 |    0       |
| noise_energy_first_20samples      |            0 |    0       |
| signal_energy_after_stalta        |            0 |    0       |
| dominant_frequency_proxy          |            0 |    0       |
| velocity_estimate_stalta          |            0 |    0       |
| slant_time_correction             |            0 |    0       |
| gather_median_pick_ms             |            0 |    0       |
| pick_deviation_from_gather_median |       148559 |    3.97938 |
| gather_pick_std                   |            0 |    0       |
| hyperbolic_residual               |            0 |    0       |
| offset                            |            0 |    0       |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `20` additional columns are omitted from preview.
| asset     |   trace_index |   shot_id |   gather_sequence_index |   trace_index_within_gather |   number_of_traces_in_gather |   offset_gather_zscore |   offset_rank |   source_ht_scaled |   rec_ht_scaled |   elevation_diff |   slant_distance |
|:----------|--------------:|----------:|------------------------:|----------------------------:|-----------------------------:|-----------------------:|--------------:|-------------------:|----------------:|-----------------:|-----------------:|
| brunswick |          2515 |         1 |                       0 |                           0 |                         2279 |               -2.24428 |    0          |                125 |             108 |               17 |          49.5782 |
| brunswick |          2516 |         1 |                       0 |                           1 |                         2279 |               -2.24091 |    0.00078598 |                125 |             108 |               17 |          53.7494 |
| brunswick |          2517 |         1 |                       0 |                           2 |                         2279 |               -2.22723 |    0.00398121 |                125 |             108 |               17 |          71.0141 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `features_halfmile.csv`
- Path: `outputs/preprocessing/features_halfmile.csv`
- Size: `368,429,077` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `993,180`
- Columns: `32`
- Exact column list:
```text
asset, trace_index, shot_id, gather_sequence_index, trace_index_within_gather, number_of_traces_in_gather, offset_gather_zscore, offset_rank, source_ht_scaled, rec_ht_scaled, elevation_diff, slant_distance, pre_break_noise_energy, zero_crossing_rate, max_abs_amplitude, is_dead_trace, stalta_pick_sample, stalta_pick_ms, stalta_peak_ratio, stalta_ratio_at_pick, stalta_failed, amplitude_at_stalta_pick, noise_energy_first_20samples, signal_energy_after_stalta, dominant_frequency_proxy, velocity_estimate_stalta, slant_time_correction, gather_median_pick_ms, pick_deviation_from_gather_median, gather_pick_std, hyperbolic_residual, offset
```
- Inferred dtypes:
| column                            | inferred_dtype   |
|:----------------------------------|:-----------------|
| asset                             | str              |
| trace_index                       | int64            |
| shot_id                           | int64            |
| gather_sequence_index             | int64            |
| trace_index_within_gather         | int64            |
| number_of_traces_in_gather        | int64            |
| offset_gather_zscore              | float64          |
| offset_rank                       | float64          |
| source_ht_scaled                  | float64          |
| rec_ht_scaled                     | float64          |
| elevation_diff                    | float64          |
| slant_distance                    | float64          |
| pre_break_noise_energy            | float64          |
| zero_crossing_rate                | float64          |
| max_abs_amplitude                 | float64          |
| is_dead_trace                     | int64            |
| stalta_pick_sample                | int64            |
| stalta_pick_ms                    | float64          |
| stalta_peak_ratio                 | float64          |
| stalta_ratio_at_pick              | float64          |
| stalta_failed                     | int64            |
| amplitude_at_stalta_pick          | float64          |
| noise_energy_first_20samples      | float64          |
| signal_energy_after_stalta        | float64          |
| dominant_frequency_proxy          | float64          |
| velocity_estimate_stalta          | float64          |
| slant_time_correction             | float64          |
| gather_median_pick_ms             | float64          |
| pick_deviation_from_gather_median | float64          |
| gather_pick_std                   | float64          |
| hyperbolic_residual               | float64          |
| offset                            | float64          |
- Null profile:
| column                            |   null_count |   null_pct |
|:----------------------------------|-------------:|-----------:|
| asset                             |            0 |    0       |
| trace_index                       |            0 |    0       |
| shot_id                           |            0 |    0       |
| gather_sequence_index             |            0 |    0       |
| trace_index_within_gather         |            0 |    0       |
| number_of_traces_in_gather        |            0 |    0       |
| offset_gather_zscore              |            0 |    0       |
| offset_rank                       |            0 |    0       |
| source_ht_scaled                  |            0 |    0       |
| rec_ht_scaled                     |            0 |    0       |
| elevation_diff                    |            0 |    0       |
| slant_distance                    |            0 |    0       |
| pre_break_noise_energy            |            0 |    0       |
| zero_crossing_rate                |            0 |    0       |
| max_abs_amplitude                 |            0 |    0       |
| is_dead_trace                     |            0 |    0       |
| stalta_pick_sample                |            0 |    0       |
| stalta_pick_ms                    |        34593 |    3.48305 |
| stalta_peak_ratio                 |            0 |    0       |
| stalta_ratio_at_pick              |            0 |    0       |
| stalta_failed                     |            0 |    0       |
| amplitude_at_stalta_pick          |            0 |    0       |
| noise_energy_first_20samples      |            0 |    0       |
| signal_energy_after_stalta        |            0 |    0       |
| dominant_frequency_proxy          |            0 |    0       |
| velocity_estimate_stalta          |            0 |    0       |
| slant_time_correction             |            0 |    0       |
| gather_median_pick_ms             |            0 |    0       |
| pick_deviation_from_gather_median |        34593 |    3.48305 |
| gather_pick_std                   |            0 |    0       |
| hyperbolic_residual               |            0 |    0       |
| offset                            |            0 |    0       |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `20` additional columns are omitted from preview.
| asset    |   trace_index |   shot_id |   gather_sequence_index |   trace_index_within_gather |   number_of_traces_in_gather |   offset_gather_zscore |   offset_rank |   source_ht_scaled |   rec_ht_scaled |   elevation_diff |   slant_distance |
|:---------|--------------:|----------:|------------------------:|----------------------------:|-----------------------------:|-----------------------:|--------------:|-------------------:|----------------:|-----------------:|-----------------:|
| halfmile |           174 |  20021449 |                       0 |                           0 |                         1539 |               -2.29426 |    0          |              454.1 |           451.9 |              2.2 |          263.106 |
| halfmile |           175 |  20021449 |                       0 |                           1 |                         1539 |               -2.28956 |    0.00105888 |              454.1 |           452.4 |              1.7 |          267.91  |
| halfmile |           176 |  20021449 |                       0 |                           2 |                         1539 |               -2.28306 |    0.00252532 |              454.1 |           454.2 |             -0.1 |          274.563 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `features_lalor.csv`
- Path: `outputs/preprocessing/features_lalor.csv`
- Size: `437,327,040` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,211,857`
- Columns: `32`
- Exact column list:
```text
asset, trace_index, shot_id, gather_sequence_index, trace_index_within_gather, number_of_traces_in_gather, offset_gather_zscore, offset_rank, source_ht_scaled, rec_ht_scaled, elevation_diff, slant_distance, pre_break_noise_energy, zero_crossing_rate, max_abs_amplitude, is_dead_trace, stalta_pick_sample, stalta_pick_ms, stalta_peak_ratio, stalta_ratio_at_pick, stalta_failed, amplitude_at_stalta_pick, noise_energy_first_20samples, signal_energy_after_stalta, dominant_frequency_proxy, velocity_estimate_stalta, slant_time_correction, gather_median_pick_ms, pick_deviation_from_gather_median, gather_pick_std, hyperbolic_residual, offset
```
- Inferred dtypes:
| column                            | inferred_dtype   |
|:----------------------------------|:-----------------|
| asset                             | str              |
| trace_index                       | int64            |
| shot_id                           | int64            |
| gather_sequence_index             | int64            |
| trace_index_within_gather         | int64            |
| number_of_traces_in_gather        | int64            |
| offset_gather_zscore              | float64          |
| offset_rank                       | float64          |
| source_ht_scaled                  | float64          |
| rec_ht_scaled                     | float64          |
| elevation_diff                    | float64          |
| slant_distance                    | float64          |
| pre_break_noise_energy            | float64          |
| zero_crossing_rate                | float64          |
| max_abs_amplitude                 | float64          |
| is_dead_trace                     | int64            |
| stalta_pick_sample                | int64            |
| stalta_pick_ms                    | float64          |
| stalta_peak_ratio                 | float64          |
| stalta_ratio_at_pick              | float64          |
| stalta_failed                     | int64            |
| amplitude_at_stalta_pick          | float64          |
| noise_energy_first_20samples      | float64          |
| signal_energy_after_stalta        | float64          |
| dominant_frequency_proxy          | float64          |
| velocity_estimate_stalta          | float64          |
| slant_time_correction             | float64          |
| gather_median_pick_ms             | float64          |
| pick_deviation_from_gather_median | float64          |
| gather_pick_std                   | float64          |
| hyperbolic_residual               | float64          |
| offset                            | float64          |
- Null profile:
| column                            |   null_count |   null_pct |
|:----------------------------------|-------------:|-----------:|
| asset                             |            0 |   0        |
| trace_index                       |            0 |   0        |
| shot_id                           |            0 |   0        |
| gather_sequence_index             |            0 |   0        |
| trace_index_within_gather         |            0 |   0        |
| number_of_traces_in_gather        |            0 |   0        |
| offset_gather_zscore              |            0 |   0        |
| offset_rank                       |            0 |   0        |
| source_ht_scaled                  |            0 |   0        |
| rec_ht_scaled                     |            0 |   0        |
| elevation_diff                    |            0 |   0        |
| slant_distance                    |            0 |   0        |
| pre_break_noise_energy            |            0 |   0        |
| zero_crossing_rate                |            0 |   0        |
| max_abs_amplitude                 |            0 |   0        |
| is_dead_trace                     |            0 |   0        |
| stalta_pick_sample                |            0 |   0        |
| stalta_pick_ms                    |          141 |   0.011635 |
| stalta_peak_ratio                 |            0 |   0        |
| stalta_ratio_at_pick              |            0 |   0        |
| stalta_failed                     |            0 |   0        |
| amplitude_at_stalta_pick          |            0 |   0        |
| noise_energy_first_20samples      |            0 |   0        |
| signal_energy_after_stalta        |            0 |   0        |
| dominant_frequency_proxy          |            0 |   0        |
| velocity_estimate_stalta          |            0 |   0        |
| slant_time_correction             |            0 |   0        |
| gather_median_pick_ms             |            0 |   0        |
| pick_deviation_from_gather_median |          141 |   0.011635 |
| gather_pick_std                   |            0 |   0        |
| hyperbolic_residual               |            0 |   0        |
| offset                            |            0 |   0        |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `20` additional columns are omitted from preview.
| asset   |   trace_index |   shot_id |   gather_sequence_index |   trace_index_within_gather |   number_of_traces_in_gather |   offset_gather_zscore |   offset_rank |   source_ht_scaled |   rec_ht_scaled |   elevation_diff |   slant_distance |
|:--------|--------------:|----------:|------------------------:|----------------------------:|-----------------------------:|-----------------------:|--------------:|-------------------:|----------------:|-----------------:|-----------------:|
| lalor   |            44 |        24 |                       0 |                           0 |                         1253 |               -2.375   |    0          |              298.9 |           299.3 |             -0.4 |          20.4326 |
| lalor   |            43 |        24 |                       0 |                           1 |                         1253 |               -2.36334 |    0.00297434 |              298.9 |           299.3 |             -0.4 |          27.8031 |
| lalor   |            45 |        24 |                       0 |                           2 |                         1253 |               -2.34707 |    0.00712773 |              298.9 |           299.4 |             -0.5 |          38.0971 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `features_sudbury.csv`
- Path: `outputs/preprocessing/features_sudbury.csv`
- Size: `71,851,977` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `200,338`
- Columns: `32`
- Exact column list:
```text
asset, trace_index, shot_id, gather_sequence_index, trace_index_within_gather, number_of_traces_in_gather, offset_gather_zscore, offset_rank, source_ht_scaled, rec_ht_scaled, elevation_diff, slant_distance, pre_break_noise_energy, zero_crossing_rate, max_abs_amplitude, is_dead_trace, stalta_pick_sample, stalta_pick_ms, stalta_peak_ratio, stalta_ratio_at_pick, stalta_failed, amplitude_at_stalta_pick, noise_energy_first_20samples, signal_energy_after_stalta, dominant_frequency_proxy, velocity_estimate_stalta, slant_time_correction, gather_median_pick_ms, pick_deviation_from_gather_median, gather_pick_std, hyperbolic_residual, offset
```
- Inferred dtypes:
| column                            | inferred_dtype   |
|:----------------------------------|:-----------------|
| asset                             | str              |
| trace_index                       | int64            |
| shot_id                           | int64            |
| gather_sequence_index             | int64            |
| trace_index_within_gather         | int64            |
| number_of_traces_in_gather        | int64            |
| offset_gather_zscore              | float64          |
| offset_rank                       | float64          |
| source_ht_scaled                  | float64          |
| rec_ht_scaled                     | float64          |
| elevation_diff                    | float64          |
| slant_distance                    | float64          |
| pre_break_noise_energy            | float64          |
| zero_crossing_rate                | float64          |
| max_abs_amplitude                 | float64          |
| is_dead_trace                     | int64            |
| stalta_pick_sample                | int64            |
| stalta_pick_ms                    | float64          |
| stalta_peak_ratio                 | float64          |
| stalta_ratio_at_pick              | float64          |
| stalta_failed                     | int64            |
| amplitude_at_stalta_pick          | float64          |
| noise_energy_first_20samples      | float64          |
| signal_energy_after_stalta        | float64          |
| dominant_frequency_proxy          | float64          |
| velocity_estimate_stalta          | float64          |
| slant_time_correction             | float64          |
| gather_median_pick_ms             | float64          |
| pick_deviation_from_gather_median | float64          |
| gather_pick_std                   | float64          |
| hyperbolic_residual               | float64          |
| offset                            | float64          |
- Null profile:
| column                            |   null_count |   null_pct |
|:----------------------------------|-------------:|-----------:|
| asset                             |            0 |    0       |
| trace_index                       |            0 |    0       |
| shot_id                           |            0 |    0       |
| gather_sequence_index             |            0 |    0       |
| trace_index_within_gather         |            0 |    0       |
| number_of_traces_in_gather        |            0 |    0       |
| offset_gather_zscore              |            0 |    0       |
| offset_rank                       |            0 |    0       |
| source_ht_scaled                  |            0 |    0       |
| rec_ht_scaled                     |            0 |    0       |
| elevation_diff                    |            0 |    0       |
| slant_distance                    |            0 |    0       |
| pre_break_noise_energy            |            0 |    0       |
| zero_crossing_rate                |            0 |    0       |
| max_abs_amplitude                 |            0 |    0       |
| is_dead_trace                     |            0 |    0       |
| stalta_pick_sample                |            0 |    0       |
| stalta_pick_ms                    |         7013 |    3.50058 |
| stalta_peak_ratio                 |            0 |    0       |
| stalta_ratio_at_pick              |            0 |    0       |
| stalta_failed                     |            0 |    0       |
| amplitude_at_stalta_pick          |            0 |    0       |
| noise_energy_first_20samples      |            0 |    0       |
| signal_energy_after_stalta        |            0 |    0       |
| dominant_frequency_proxy          |            0 |    0       |
| velocity_estimate_stalta          |            0 |    0       |
| slant_time_correction             |            0 |    0       |
| gather_median_pick_ms             |            0 |    0       |
| pick_deviation_from_gather_median |         7013 |    3.50058 |
| gather_pick_std                   |            0 |    0       |
| hyperbolic_residual               |            0 |    0       |
| offset                            |            0 |    0       |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `20` additional columns are omitted from preview.
| asset   |   trace_index |   shot_id |   gather_sequence_index |   trace_index_within_gather |   number_of_traces_in_gather |   offset_gather_zscore |   offset_rank |   source_ht_scaled |   rec_ht_scaled |   elevation_diff |   slant_distance |
|:--------|--------------:|----------:|------------------------:|----------------------------:|-----------------------------:|-----------------------:|--------------:|-------------------:|----------------:|-----------------:|-----------------:|
| sudbury |         43273 |        42 |                      38 |                           0 |                          299 |               -2.00523 |   0           |              312.4 |           334.6 |            -22.2 |          434.187 |
| sudbury |         43272 |        42 |                      38 |                           1 |                          299 |               -2.00311 |   0.00057291  |              312.4 |           337.4 |            -25   |          435.043 |
| sudbury |         43274 |        42 |                      38 |                           2 |                          299 |               -2.00157 |   0.000988189 |              312.4 |           330.4 |            -18   |          435.208 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `gather_metadata_brunswick.csv`
- Path: `outputs/preprocessing/gather_metadata_brunswick.csv`
- Size: `141,458` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,541`
- Columns: `10`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |
|:----------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|
| brunswick |                       0 |         1 |   287670 | 5.25307e+06 |               2279 |      46.5725 |      5667.16 | False             | False                   |
| brunswick |                       1 |         2 |   286862 | 5.25289e+06 |               1340 |      43.8634 |      4909.88 | False             | False                   |
| brunswick |                       2 |         3 |   287670 | 5.25313e+06 |               1722 |      97.6934 |      5621.74 | False             | False                   |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `gather_metadata_halfmile.csv`
- Path: `outputs/preprocessing/gather_metadata_halfmile.csv`
- Size: `65,880` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `690`
- Columns: `10`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
- Sample preview (first rows, summarized):
| asset    |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |
|:---------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|
| halfmile |                       0 |  20021449 |   704570 | 5.24358e+06 |               1539 |      263.097 |      4803.65 | False             | False                   |
| halfmile |                       1 |  20021451 |   704546 | 5.24355e+06 |               1532 |      230.209 |      4785.16 | False             | False                   |
| halfmile |                       2 |  20021453 |   704503 | 5.24351e+06 |               1528 |      180.25  |      4752.22 | False             | False                   |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `gather_metadata_lalor.csv`
- Path: `outputs/preprocessing/gather_metadata_lalor.csv`
- Size: `75,415` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `905`
- Columns: `10`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   |   gather_sequence_index |   shot_id |   shot_x |   shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |
|:--------|------------------------:|----------:|---------:|---------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|
| lalor   |                       0 |        24 |   2237.6 |  13738.8 |               1253 |      20.4287 |      2498.8  | False             | False                   |
| lalor   |                       1 |        25 |   2274.9 |  13704   |               1213 |      71.0634 |      2499.33 | False             | False                   |
| lalor   |                       2 |        26 |   2302.1 |  13663.1 |               1201 |     118.893  |      2499.01 | False             | False                   |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `gather_metadata_sudbury.csv`
- Path: `outputs/preprocessing/gather_metadata_sudbury.csv`
- Size: `63,939` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `715`
- Columns: `10`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |
|:--------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|
| sudbury |                      38 |        42 |   460809 | 5.14817e+06 |                299 |     433.619  |      1665.31 | False             | False                   |
| sudbury |                      48 |        52 |   460354 | 5.14827e+06 |                280 |      33.4845 |      1448.99 | False             | False                   |
| sudbury |                      49 |        53 |   460315 | 5.14831e+06 |                299 |      22.0499 |      1421.43 | False             | False                   |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `inference_trace_metadata_brunswick.csv`
- Path: `outputs/preprocessing/inference_trace_metadata_brunswick.csv`
- Size: `125,520,415` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `763,319`
- Columns: `21`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, label_status
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| label_status              | str              |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| label_status              |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `9` additional columns are omitted from preview.
| asset     |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:----------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|------------:|------------:|--------:|------------:|
| brunswick |          2439 |                       0 |                           0 |         1 |      11108 |    561025 |     287670 | 5.25307e+06 |         125 |  287181 | 5.25318e+06 |
| brunswick |          2445 |                       0 |                           1 |         1 |      11108 |    561031 |     287670 | 5.25307e+06 |         125 |  287062 | 5.25312e+06 |
| brunswick |          2541 |                       0 |                           2 |         1 |      11108 |    581027 |     287670 | 5.25307e+06 |         125 |  287068 | 5.25297e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `inference_trace_metadata_halfmile.csv`
- Path: `outputs/preprocessing/inference_trace_metadata_halfmile.csv`
- Size: `19,452,533` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `106,370`
- Columns: `21`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, label_status
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| label_status              | str              |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| label_status              |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `9` additional columns are omitted from preview.
| asset    |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |    shot_peg |     rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:---------|--------------:|------------------------:|----------------------------:|----------:|------------:|------------:|-----------:|------------:|------------:|--------:|------------:|
| halfmile |           172 |                       0 |                           0 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704374 | 5.24341e+06 |
| halfmile |           171 |                       0 |                           1 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704387 | 5.2434e+06  |
| halfmile |           173 |                       0 |                           2 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704360 | 5.24342e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `inference_trace_metadata_lalor.csv`
- Path: `outputs/preprocessing/inference_trace_metadata_lalor.csv`
- Size: `198,802,821` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,213,066`
- Columns: `21`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, label_status
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| label_status              | str              |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| label_status              |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `9` additional columns are omitted from preview.
| asset   |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |   source_y |   source_ht |   rec_x |   rec_y |
|:--------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|-----------:|------------:|--------:|--------:|
| lalor   |           316 |                       0 |                           0 |        24 |     214101 |    109112 |     2237.6 |    13738.8 |       298.9 |  3170   | 13940.2 |
| lalor   |           310 |                       0 |                           1 |        24 |     214101 |    109106 |     2237.6 |    13738.8 |       298.9 |  3291.8 | 14028.2 |
| lalor   |           674 |                       0 |                           2 |        24 |     214101 |    117164 |     2237.6 |    13738.8 |       298.9 |  2528.3 | 12682.6 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `inference_trace_metadata_sudbury.csv`
- Path: `outputs/preprocessing/inference_trace_metadata_sudbury.csv`
- Size: `269,912,134` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,609,882`
- Columns: `21`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, label_status
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| label_status              | str              |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| label_status              |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `9` additional columns are omitted from preview.
| asset   |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:--------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|------------:|------------:|--------:|------------:|
| sudbury |          1135 |                       0 |                           0 |         2 |          0 |     21218 |     460879 | 5.15144e+06 |       332.4 |  460938 | 5.15155e+06 |
| sudbury |          1136 |                       0 |                           1 |         2 |          0 |     21219 |     460879 | 5.15144e+06 |       332.4 |  460938 | 5.15155e+06 |
| sudbury |          1137 |                       0 |                           2 |         2 |          0 |     21220 |     460879 | 5.15144e+06 |       332.4 |  460938 | 5.15155e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `lalor_experiment_b_split_summary.csv`
- Path: `outputs/preprocessing/lalor_experiment_b_split_summary.csv`
- Size: `145` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1`
- Columns: `9`
- Exact column list:
```text
asset, experiment, train_fraction, total_shots, train_shots, val_shots, train_traces, val_traces, random_seed
```
- Inferred dtypes:
| column         | inferred_dtype   |
|:---------------|:-----------------|
| asset          | str              |
| experiment     | str              |
| train_fraction | float64          |
| total_shots    | int64            |
| train_shots    | int64            |
| val_shots      | int64            |
| train_traces   | int64            |
| val_traces     | int64            |
| random_seed    | int64            |
- Null profile:
| column         |   null_count |   null_pct |
|:---------------|-------------:|-----------:|
| asset          |            0 |          0 |
| experiment     |            0 |          0 |
| train_fraction |            0 |          0 |
| total_shots    |            0 |          0 |
| train_shots    |            0 |          0 |
| val_shots      |            0 |          0 |
| train_traces   |            0 |          0 |
| val_traces     |            0 |          0 |
| random_seed    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   | experiment   |   train_fraction |   total_shots |   train_shots |   val_shots |   train_traces |   val_traces |   random_seed |
|:--------|:-------------|-----------------:|--------------:|--------------:|------------:|---------------:|-------------:|--------------:|
| lalor   | B            |              0.8 |           905 |           724 |         181 |         978491 |       233366 |            42 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `normalization_strategy.json`
- Path: `outputs/preprocessing/normalization_strategy.json`
- Size: `1,470` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured configuration/summary payload.
- Top-level type: `dict`
- Top-level keys (10): `working_label_column, normalization_method, primary_offset_column_by_asset, unlabeled_sentinels_by_asset, min_gather_traces_by_asset, trace_harmonization_strategy, trace_harmonization_target_samp_rate_us, trace_harmonization_target_samp_num, asset_sampling_specs, description`
- Key type preview:
```json
{
  "working_label_column": "str",
  "normalization_method": "str",
  "primary_offset_column_by_asset": "dict",
  "unlabeled_sentinels_by_asset": "dict",
  "min_gather_traces_by_asset": "dict",
  "trace_harmonization_strategy": "str",
  "trace_harmonization_target_samp_rate_us": "int",
  "trace_harmonization_target_samp_num": "int",
  "asset_sampling_specs": "dict",
  "description": "str"
}
```
- Content preview (truncated):
```json
{
  "working_label_column": "SPARE1",
  "normalization_method": "per_trace",
  "primary_offset_column_by_asset": {
    "brunswick": "derived_from_coordinates",
    "halfmile": "derived_from_coordinates",
    "lalor": "derived_from_coordinates",
    "sudbury": "derived_from_coordinates"
  },
  "unlabeled_sentinels_by_asset": {
    "brunswick": [
      -1
    ],
    "halfmile": [
      -1
    ],
    "lalor": [
      -1
    ],
    "sudbury": [
      0
    ]
  },
  "min_gather_traces_by_asset": {
    "brunswick": 5,
    "halfmile": 5,
    "lalor": 10,
    "sudbury": 5
  },
  "trace_harmonization_strategy": "downsample_lalor_to_2ms_then_pad_or_crop_at_runtime",
  "trace_harmonization_target_samp_rate_us": 2000,
  "trace_harmonization_target_samp_num": 751,
  "asset_sampling_specs": {
    "brunswick": {
      "samp_rate_us": 2000,
      "samp_num": 751,
      "recording_time_ms": 1502
    },
    "halfmile": {
      "samp_rate_us": 2000,
      "samp_num": 751,
      "recording_time_ms": 1502
    },
    "lalor": {
      "samp_rate_us": 1000,
      "samp_num": 1501,
      "recording_time_ms": 1501
    },
    "sudbury": {
      "samp_rate_us": 2000,
      "samp_num": 1001,
      "recording_time_ms": 2002
    }
  },
  "description": "Normalize at runtime during dataset building. per_trace divides each trace by its own absolute max; per_gather divides all traces in a gather by the gather absolute max."
}
```

### `offset_gather_stats_brunswick.csv`
- Path: `outputs/preprocessing/offset_gather_stats_brunswick.csv`
- Size: `198,363` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,541`
- Columns: `12`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training, offset_mean, offset_std
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
| offset_mean           | float64          |
| offset_std            | float64          |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
| offset_mean           |            0 |          0 |
| offset_std            |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |   offset_mean |   offset_std |
|:----------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|--------------:|-------------:|
| brunswick |                       0 |         1 |   287670 | 5.25307e+06 |               2279 |      46.5725 |      5667.16 | False             | False                   |       2992.13 |      1312.47 |
| brunswick |                       1 |         2 |   286862 | 5.25289e+06 |               1340 |      43.8634 |      4909.88 | False             | False                   |       2128.51 |      1152.68 |
| brunswick |                       2 |         3 |   287670 | 5.25313e+06 |               1722 |      97.6934 |      5621.74 | False             | False                   |       2638.44 |      1253.93 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `offset_gather_stats_halfmile.csv`
- Path: `outputs/preprocessing/offset_gather_stats_halfmile.csv`
- Size: `91,055` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `690`
- Columns: `12`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training, offset_mean, offset_std
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
| offset_mean           | float64          |
| offset_std            | float64          |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
| offset_mean           |            0 |          0 |
| offset_std            |            0 |          0 |
- Sample preview (first rows, summarized):
| asset    |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |   offset_mean |   offset_std |
|:---------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|--------------:|-------------:|
| halfmile |                       0 |  20021449 |   704570 | 5.24358e+06 |               1539 |      263.097 |      4803.65 | False             | False                   |       2613.32 |      1024.39 |
| halfmile |                       1 |  20021451 |   704546 | 5.24355e+06 |               1532 |      230.209 |      4785.16 | False             | False                   |       2590.76 |      1025.03 |
| halfmile |                       2 |  20021453 |   704503 | 5.24351e+06 |               1528 |      180.25  |      4752.22 | False             | False                   |       2577.41 |      1025.01 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `offset_gather_stats_lalor.csv`
- Path: `outputs/preprocessing/offset_gather_stats_lalor.csv`
- Size: `108,314` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `905`
- Columns: `12`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training, offset_mean, offset_std
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
| offset_mean           | float64          |
| offset_std            | float64          |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
| offset_mean           |            0 |          0 |
| offset_std            |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   |   gather_sequence_index |   shot_id |   shot_x |   shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |   offset_mean |   offset_std |
|:--------|------------------------:|----------:|---------:|---------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|--------------:|-------------:|
| lalor   |                       0 |        24 |   2237.6 |  13738.8 |               1253 |      20.4287 |      2498.8  | False             | False                   |       1522.56 |      632.478 |
| lalor   |                       1 |        25 |   2274.9 |  13704   |               1213 |      71.0634 |      2499.33 | False             | False                   |       1469.88 |      624.88  |
| lalor   |                       2 |        26 |   2302.1 |  13663.1 |               1201 |     118.893  |      2499.01 | False             | False                   |       1435.3  |      621.078 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `offset_gather_stats_sudbury.csv`
- Path: `outputs/preprocessing/offset_gather_stats_sudbury.csv`
- Size: `90,004` bytes
- Produced by stage/script: `scripts/03_feature_engineering.py`
- Consumed by: Training script `scripts/06_train.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `715`
- Columns: `12`
- Exact column list:
```text
asset, gather_sequence_index, shot_id, shot_x, shot_y, number_of_traces, offset_min, offset_max, is_small_gather, exclude_from_training, offset_mean, offset_std
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| gather_sequence_index | int64            |
| shot_id               | int64            |
| shot_x                | float64          |
| shot_y                | float64          |
| number_of_traces      | int64            |
| offset_min            | float64          |
| offset_max            | float64          |
| is_small_gather       | bool             |
| exclude_from_training | bool             |
| offset_mean           | float64          |
| offset_std            | float64          |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| gather_sequence_index |            0 |          0 |
| shot_id               |            0 |          0 |
| shot_x                |            0 |          0 |
| shot_y                |            0 |          0 |
| number_of_traces      |            0 |          0 |
| offset_min            |            0 |          0 |
| offset_max            |            0 |          0 |
| is_small_gather       |            0 |          0 |
| exclude_from_training |            0 |          0 |
| offset_mean           |            0 |          0 |
| offset_std            |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   |   gather_sequence_index |   shot_id |   shot_x |      shot_y |   number_of_traces |   offset_min |   offset_max | is_small_gather   | exclude_from_training   |   offset_mean |   offset_std |
|:--------|------------------------:|----------:|---------:|------------:|-------------------:|-------------:|-------------:|:------------------|:------------------------|--------------:|-------------:|
| sudbury |                      38 |        42 |   460809 | 5.14817e+06 |                299 |     433.619  |      1665.31 | False             | False                   |      1100.73  |      332.686 |
| sudbury |                      48 |        52 |   460354 | 5.14827e+06 |                280 |      33.4845 |      1448.99 | False             | False                   |       863.904 |      379.246 |
| sudbury |                      49 |        53 |   460315 | 5.14831e+06 |                299 |      22.0499 |      1421.43 | False             | False                   |       864.157 |      382.184 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_asset_overview_all_assets.csv`
- Path: `outputs/preprocessing/preprocessing_asset_overview_all_assets.csv`
- Size: `900` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `4`
- Columns: `14`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, removed_any_reason, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_varies_flag, ht_scale_varies_flag, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| removed_any_reason           | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_varies_flag      | bool             |
| ht_scale_varies_flag         | bool             |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| removed_any_reason           |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `2` additional columns are omitted from preview.
| asset     |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   removed_any_reason |   valid_gather_count |   small_gather_count |   small_gather_trace_count | coord_scale_varies_flag   | ht_scale_varies_flag   | working_label_column   | primary_offset_column    |
|:----------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------:|---------------------------:|:--------------------------|:-----------------------|:-----------------------|:-------------------------|
| brunswick |        4496540 |              3733221 |                     763319 |               763319 |                 1541 |                    0 |                          0 | False                     | False                  | SPARE1                 | derived_from_coordinates |
| halfmile  |        1099559 |               993180 |                     106370 |               106379 |                  690 |                    0 |                          0 | False                     | False                  | SPARE1                 | derived_from_coordinates |
| lalor     |        2424923 |              1211857 |                    1213066 |              1213066 |                  905 |                    0 |                          0 | False                     | False                  | SPARE1                 | derived_from_coordinates |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_report_all_assets.txt`
- Path: `outputs/preprocessing/preprocessing_report_all_assets.txt`
- Size: `3,485` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `118`
- Content preview:
```text
===== BRUNSWICK =====
Asset: brunswick
File: Brunswick_orig_1500ms_V2.hdf5
Total traces: 4496540
Valid labeled kept: 3733221
Inference unlabeled kept: 763319
Removed (any reason): 763319
Small gather threshold: 5
```

### `preprocessing_report_brunswick.txt`
- Path: `outputs/preprocessing/preprocessing_report_brunswick.txt`
- Size: `844` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `27`
- Content preview:
```text
Asset: brunswick
File: Brunswick_orig_1500ms_V2.hdf5
Total traces: 4496540
Valid labeled kept: 3733221
Inference unlabeled kept: 763319
Removed (any reason): 763319
Small gather threshold: 5
Small gather count: 0
```

### `preprocessing_report_halfmile.txt`
- Path: `outputs/preprocessing/preprocessing_report_halfmile.txt`
- Size: `849` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `27`
- Content preview:
```text
Asset: halfmile
File: Halfmile3D_add_geom_sorted.hdf5
Total traces: 1099559
Valid labeled kept: 993180
Inference unlabeled kept: 106370
Removed (any reason): 106379
Small gather threshold: 5
Small gather count: 0
```

### `preprocessing_report_lalor.txt`
- Path: `outputs/preprocessing/preprocessing_report_lalor.txt`
- Size: `854` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `27`
- Content preview:
```text
Asset: lalor
File: Lalor_raw_z_1500ms_norp_geom_v3.hdf5
Total traces: 2424923
Valid labeled kept: 1211857
Inference unlabeled kept: 1213066
Removed (any reason): 1213066
Small gather threshold: 10
Small gather count: 0
```

### `preprocessing_report_sudbury.txt`
- Path: `outputs/preprocessing/preprocessing_report_sudbury.txt`
- Size: `841` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: narrative report or runtime log artifact.
- Line count: `27`
- Content preview:
```text
Asset: sudbury
File: preprocessed_Sudbury3D.hdf
Total traces: 1810220
Valid labeled kept: 200338
Inference unlabeled kept: 1609882
Removed (any reason): 1609882
Small gather threshold: 5
Small gather count: 0
```

### `preprocessing_summary_all_assets.csv`
- Path: `outputs/preprocessing/preprocessing_summary_all_assets.csv`
- Size: `1,040` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `4`
- Columns: `18`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_unique_count, coord_scale_values, coord_scale_varies_flag, ht_scale_unique_count, ht_scale_values, ht_scale_varies_flag, min_gather_traces, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_unique_count     | int64            |
| coord_scale_values           | str              |
| coord_scale_varies_flag      | bool             |
| ht_scale_unique_count        | int64            |
| ht_scale_values              | str              |
| ht_scale_varies_flag         | bool             |
| min_gather_traces            | int64            |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_unique_count     |            0 |          0 |
| coord_scale_values           |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_unique_count        |            0 |          0 |
| ht_scale_values              |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| min_gather_traces            |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `6` additional columns are omitted from preview.
| asset     |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   valid_gather_count |   small_gather_count |   small_gather_trace_count |   coord_scale_unique_count | coord_scale_values   | coord_scale_varies_flag   |   ht_scale_unique_count | ht_scale_values   |
|:----------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------------:|---------------------------:|:---------------------|:--------------------------|------------------------:|:------------------|
| brunswick |        4496540 |              3733221 |                     763319 |                 1541 |                    0 |                          0 |                          1 | [-10.0]              | False                     |                       1 | [-10.0]           |
| halfmile  |        1099559 |               993180 |                     106370 |                  690 |                    0 |                          0 |                          1 | [1.0]                | False                     |                       1 | [-10000.0]        |
| lalor     |        2424923 |              1211857 |                    1213066 |                  905 |                    0 |                          0 |                          1 | [-10.0]              | False                     |                       1 | [-10.0]           |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_summary_brunswick.csv`
- Path: `outputs/preprocessing/preprocessing_summary_brunswick.csv`
- Size: `536` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1`
- Columns: `18`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_unique_count, coord_scale_values, coord_scale_varies_flag, ht_scale_unique_count, ht_scale_values, ht_scale_varies_flag, min_gather_traces, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_unique_count     | int64            |
| coord_scale_values           | str              |
| coord_scale_varies_flag      | bool             |
| ht_scale_unique_count        | int64            |
| ht_scale_values              | str              |
| ht_scale_varies_flag         | bool             |
| min_gather_traces            | int64            |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_unique_count     |            0 |          0 |
| coord_scale_values           |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_unique_count        |            0 |          0 |
| ht_scale_values              |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| min_gather_traces            |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `6` additional columns are omitted from preview.
| asset     |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   valid_gather_count |   small_gather_count |   small_gather_trace_count |   coord_scale_unique_count | coord_scale_values   | coord_scale_varies_flag   |   ht_scale_unique_count | ht_scale_values   |
|:----------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------------:|---------------------------:|:---------------------|:--------------------------|------------------------:|:------------------|
| brunswick |        4496540 |              3733221 |                     763319 |                 1541 |                    0 |                          0 |                          1 | [-10.0]              | False                     |                       1 | [-10.0]           |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_summary_halfmile.csv`
- Path: `outputs/preprocessing/preprocessing_summary_halfmile.csv`
- Size: `534` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1`
- Columns: `18`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_unique_count, coord_scale_values, coord_scale_varies_flag, ht_scale_unique_count, ht_scale_values, ht_scale_varies_flag, min_gather_traces, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_unique_count     | int64            |
| coord_scale_values           | str              |
| coord_scale_varies_flag      | bool             |
| ht_scale_unique_count        | int64            |
| ht_scale_values              | str              |
| ht_scale_varies_flag         | bool             |
| min_gather_traces            | int64            |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_unique_count     |            0 |          0 |
| coord_scale_values           |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_unique_count        |            0 |          0 |
| ht_scale_values              |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| min_gather_traces            |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `6` additional columns are omitted from preview.
| asset    |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   valid_gather_count |   small_gather_count |   small_gather_trace_count |   coord_scale_unique_count | coord_scale_values   | coord_scale_varies_flag   |   ht_scale_unique_count | ht_scale_values   |
|:---------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------------:|---------------------------:|:---------------------|:--------------------------|------------------------:|:------------------|
| halfmile |        1099559 |               993180 |                     106370 |                  690 |                    0 |                          0 |                          1 | [1.0]                | False                     |                       1 | [-10000.0]        |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_summary_lalor.csv`
- Path: `outputs/preprocessing/preprocessing_summary_lalor.csv`
- Size: `533` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1`
- Columns: `18`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_unique_count, coord_scale_values, coord_scale_varies_flag, ht_scale_unique_count, ht_scale_values, ht_scale_varies_flag, min_gather_traces, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_unique_count     | int64            |
| coord_scale_values           | str              |
| coord_scale_varies_flag      | bool             |
| ht_scale_unique_count        | int64            |
| ht_scale_values              | str              |
| ht_scale_varies_flag         | bool             |
| min_gather_traces            | int64            |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_unique_count     |            0 |          0 |
| coord_scale_values           |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_unique_count        |            0 |          0 |
| ht_scale_values              |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| min_gather_traces            |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `6` additional columns are omitted from preview.
| asset   |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   valid_gather_count |   small_gather_count |   small_gather_trace_count |   coord_scale_unique_count | coord_scale_values   | coord_scale_varies_flag   |   ht_scale_unique_count | ht_scale_values   |
|:--------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------------:|---------------------------:|:---------------------|:--------------------------|------------------------:|:------------------|
| lalor   |        2424923 |              1211857 |                    1213066 |                  905 |                    0 |                          0 |                          1 | [-10.0]              | False                     |                       1 | [-10.0]           |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `preprocessing_summary_sudbury.csv`
- Path: `outputs/preprocessing/preprocessing_summary_sudbury.csv`
- Size: `532` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1`
- Columns: `18`
- Exact column list:
```text
asset, total_traces, valid_labeled_kept, inference_unlabeled_kept, valid_gather_count, small_gather_count, small_gather_trace_count, coord_scale_unique_count, coord_scale_values, coord_scale_varies_flag, ht_scale_unique_count, ht_scale_values, ht_scale_varies_flag, min_gather_traces, working_label_column, primary_offset_column, normalization_method, trace_harmonization_strategy
```
- Inferred dtypes:
| column                       | inferred_dtype   |
|:-----------------------------|:-----------------|
| asset                        | str              |
| total_traces                 | int64            |
| valid_labeled_kept           | int64            |
| inference_unlabeled_kept     | int64            |
| valid_gather_count           | int64            |
| small_gather_count           | int64            |
| small_gather_trace_count     | int64            |
| coord_scale_unique_count     | int64            |
| coord_scale_values           | str              |
| coord_scale_varies_flag      | bool             |
| ht_scale_unique_count        | int64            |
| ht_scale_values              | str              |
| ht_scale_varies_flag         | bool             |
| min_gather_traces            | int64            |
| working_label_column         | str              |
| primary_offset_column        | str              |
| normalization_method         | str              |
| trace_harmonization_strategy | str              |
- Null profile:
| column                       |   null_count |   null_pct |
|:-----------------------------|-------------:|-----------:|
| asset                        |            0 |          0 |
| total_traces                 |            0 |          0 |
| valid_labeled_kept           |            0 |          0 |
| inference_unlabeled_kept     |            0 |          0 |
| valid_gather_count           |            0 |          0 |
| small_gather_count           |            0 |          0 |
| small_gather_trace_count     |            0 |          0 |
| coord_scale_unique_count     |            0 |          0 |
| coord_scale_values           |            0 |          0 |
| coord_scale_varies_flag      |            0 |          0 |
| ht_scale_unique_count        |            0 |          0 |
| ht_scale_values              |            0 |          0 |
| ht_scale_varies_flag         |            0 |          0 |
| min_gather_traces            |            0 |          0 |
| working_label_column         |            0 |          0 |
| primary_offset_column        |            0 |          0 |
| normalization_method         |            0 |          0 |
| trace_harmonization_strategy |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `6` additional columns are omitted from preview.
| asset   |   total_traces |   valid_labeled_kept |   inference_unlabeled_kept |   valid_gather_count |   small_gather_count |   small_gather_trace_count |   coord_scale_unique_count | coord_scale_values   | coord_scale_varies_flag   |   ht_scale_unique_count | ht_scale_values   |
|:--------|---------------:|---------------------:|---------------------------:|---------------------:|---------------------:|---------------------------:|---------------------------:|:---------------------|:--------------------------|------------------------:|:------------------|
| sudbury |        1810220 |               200338 |                    1609882 |                  715 |                    0 |                          0 |                          1 | [100.0]              | False                     |                       1 | [10.0]            |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `removed_trace_counts_all_assets.csv`
- Path: `outputs/preprocessing/removed_trace_counts_all_assets.csv`
- Size: `1,098` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `32`
- Columns: `3`
- Exact column list:
```text
asset, reason, count
```
- Inferred dtypes:
| column   | inferred_dtype   |
|:---------|:-----------------|
| asset    | str              |
| reason   | str              |
| count    | int64            |
- Null profile:
| column   |   null_count |   null_pct |
|:---------|-------------:|-----------:|
| asset    |            0 |          0 |
| reason   |            0 |          0 |
| count    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     | reason                   |   count |
|:----------|:-------------------------|--------:|
| brunswick | spare1_zero              |       0 |
| brunswick | spare1_minus_one         |  763319 |
| brunswick | spare1_gt_recording_time |       0 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `removed_trace_counts_brunswick.csv`
- Path: `outputs/preprocessing/removed_trace_counts_brunswick.csv`
- Size: `301` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `8`
- Columns: `3`
- Exact column list:
```text
asset, reason, count
```
- Inferred dtypes:
| column   | inferred_dtype   |
|:---------|:-----------------|
| asset    | str              |
| reason   | str              |
| count    | int64            |
- Null profile:
| column   |   null_count |   null_pct |
|:---------|-------------:|-----------:|
| asset    |            0 |          0 |
| reason   |            0 |          0 |
| count    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     | reason                   |   count |
|:----------|:-------------------------|--------:|
| brunswick | spare1_zero              |       0 |
| brunswick | spare1_minus_one         |  763319 |
| brunswick | spare1_gt_recording_time |       0 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `removed_trace_counts_halfmile.csv`
- Path: `outputs/preprocessing/removed_trace_counts_halfmile.csv`
- Size: `297` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `8`
- Columns: `3`
- Exact column list:
```text
asset, reason, count
```
- Inferred dtypes:
| column   | inferred_dtype   |
|:---------|:-----------------|
| asset    | str              |
| reason   | str              |
| count    | int64            |
- Null profile:
| column   |   null_count |   null_pct |
|:---------|-------------:|-----------:|
| asset    |            0 |          0 |
| reason   |            0 |          0 |
| count    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset    | reason                   |   count |
|:---------|:-------------------------|--------:|
| halfmile | spare1_zero              |       0 |
| halfmile | spare1_minus_one         |  106370 |
| halfmile | spare1_gt_recording_time |       0 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `removed_trace_counts_lalor.csv`
- Path: `outputs/preprocessing/removed_trace_counts_lalor.csv`
- Size: `273` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `8`
- Columns: `3`
- Exact column list:
```text
asset, reason, count
```
- Inferred dtypes:
| column   | inferred_dtype   |
|:---------|:-----------------|
| asset    | str              |
| reason   | str              |
| count    | int64            |
- Null profile:
| column   |   null_count |   null_pct |
|:---------|-------------:|-----------:|
| asset    |            0 |          0 |
| reason   |            0 |          0 |
| count    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   | reason                   |   count |
|:--------|:-------------------------|--------:|
| lalor   | spare1_zero              |       0 |
| lalor   | spare1_minus_one         | 1213066 |
| lalor   | spare1_gt_recording_time |       0 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `removed_trace_counts_sudbury.csv`
- Path: `outputs/preprocessing/removed_trace_counts_sudbury.csv`
- Size: `287` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `8`
- Columns: `3`
- Exact column list:
```text
asset, reason, count
```
- Inferred dtypes:
| column   | inferred_dtype   |
|:---------|:-----------------|
| asset    | str              |
| reason   | str              |
| count    | int64            |
- Null profile:
| column   |   null_count |   null_pct |
|:---------|-------------:|-----------:|
| asset    |            0 |          0 |
| reason   |            0 |          0 |
| count    |            0 |          0 |
- Sample preview (first rows, summarized):
| asset   | reason                   |   count |
|:--------|:-------------------------|--------:|
| sudbury | spare1_zero              | 1609882 |
| sudbury | spare1_minus_one         |       0 |
| sudbury | spare1_gt_recording_time |       0 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `split_random_seed.txt`
- Path: `outputs/preprocessing/split_random_seed.txt`
- Size: `4` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `1`
- Content preview:
```text
42
```

### `stalta_feature_report_all_assets.csv`
- Path: `outputs/preprocessing/stalta_feature_report_all_assets.csv`
- Size: `341` bytes
- Produced by stage/script: `scripts/03b_stalta_features.py`
- Consumed by: Training script `scripts/06_train.py` (indirectly, via updated feature CSVs/config).
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `4`
- Columns: `9`
- Exact column list:
```text
asset, rows, sta_samples, lta_samples, threshold, min_search_sample, failed_count, failed_pct, signal_window_samples
```
- Inferred dtypes:
| column                | inferred_dtype   |
|:----------------------|:-----------------|
| asset                 | str              |
| rows                  | int64            |
| sta_samples           | int64            |
| lta_samples           | int64            |
| threshold             | float64          |
| min_search_sample     | int64            |
| failed_count          | int64            |
| failed_pct            | float64          |
| signal_window_samples | int64            |
- Null profile:
| column                |   null_count |   null_pct |
|:----------------------|-------------:|-----------:|
| asset                 |            0 |          0 |
| rows                  |            0 |          0 |
| sta_samples           |            0 |          0 |
| lta_samples           |            0 |          0 |
| threshold             |            0 |          0 |
| min_search_sample     |            0 |          0 |
| failed_count          |            0 |          0 |
| failed_pct            |            0 |          0 |
| signal_window_samples |            0 |          0 |
- Sample preview (first rows, summarized):
| asset     |    rows |   sta_samples |   lta_samples |   threshold |   min_search_sample |   failed_count |   failed_pct |   signal_window_samples |
|:----------|--------:|--------------:|--------------:|------------:|--------------------:|---------------:|-------------:|------------------------:|
| brunswick | 3733221 |            10 |           100 |         3   |                   5 |         148559 |     3.97938  |                      50 |
| halfmile  |  993180 |            10 |           100 |         3   |                   5 |          34593 |     3.48305  |                      50 |
| lalor     | 1211857 |            20 |           200 |         2.5 |                  10 |            141 |     0.011635 |                      50 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `stalta_feature_report_all_assets.txt`
- Path: `outputs/preprocessing/stalta_feature_report_all_assets.txt`
- Size: `653` bytes
- Produced by stage/script: `scripts/03b_stalta_features.py`
- Consumed by: Training script `scripts/06_train.py` (indirectly, via updated feature CSVs/config).
- Purpose: narrative report or runtime log artifact.
- Line count: `7`
- Content preview:
```text
STA/LTA feature stage summary

    asset    rows  sta_samples  lta_samples  threshold  min_search_sample  failed_count  failed_pct  signal_window_samples
brunswick 3733221           10          100        3.0                  5        148559    3.979379                     50
 halfmile  993180           10          100        3.0                  5         34593    3.483054                     50
    lalor 1211857           20          200        2.5                 10           141    0.011635                     50
  sudbury  200338           10          100        3.5                  5          7013    3.500584                     50
```

### `train_shot_ids_brunswick.txt`
- Path: `outputs/preprocessing/train_shot_ids_brunswick.txt`
- Size: `7,067` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `1,310`
- Content preview:
```text
1
2
3
4
5
7
8
9
```

### `train_shot_ids_halfmile.txt`
- Path: `outputs/preprocessing/train_shot_ids_halfmile.txt`
- Size: `5,860` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `586`
- Content preview:
```text
20021449
20021453
20021455
20021457
20021461
20021462
20021463
20021464
```

### `train_shot_ids_lalor_expB.txt`
- Path: `outputs/preprocessing/train_shot_ids_lalor_expB.txt`
- Size: `3,560` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `724`
- Content preview:
```text
24
26
27
28
30
31
32
33
```

### `val_shot_ids_brunswick.txt`
- Path: `outputs/preprocessing/val_shot_ids_brunswick.txt`
- Size: `1,243` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `231`
- Content preview:
```text
6
14
35
38
44
48
50
51
```

### `val_shot_ids_halfmile.txt`
- Path: `outputs/preprocessing/val_shot_ids_halfmile.txt`
- Size: `1,040` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `104`
- Content preview:
```text
20021451
20021459
20021470
20021487
20021550
20021570
20021573
20041605
```

### `val_shot_ids_lalor_expB.txt`
- Path: `outputs/preprocessing/val_shot_ids_lalor_expB.txt`
- Size: `890` bytes
- Produced by stage/script: `scripts/04_dataset_builder.py`
- Consumed by: Training `scripts/06_train.py`, evaluation partitioning, and Experiment A/B orchestration.
- Purpose: narrative report or runtime log artifact.
- Line count: `181`
- Content preview:
```text
25
29
34
39
56
58
63
65
```

### `valid_trace_metadata_brunswick.csv`
- Path: `outputs/preprocessing/valid_trace_metadata_brunswick.csv`
- Size: `612,794,768` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `3,733,221`
- Columns: `22`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, first_break_sample, exclude_from_training
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| first_break_sample        | int64            |
| exclude_from_training     | bool             |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| first_break_sample        |            0 |          0 |
| exclude_from_training     |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `10` additional columns are omitted from preview.
| asset     |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:----------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|------------:|------------:|--------:|------------:|
| brunswick |          2515 |                       0 |                           0 |         1 |      11108 |    581001 |     287670 | 5.25307e+06 |         125 |  287658 | 5.25303e+06 |
| brunswick |          2516 |                       0 |                           1 |         1 |      11108 |    581002 |     287670 | 5.25307e+06 |         125 |  287632 | 5.25304e+06 |
| brunswick |          2517 |                       0 |                           2 |         1 |      11108 |    581003 |     287670 | 5.25307e+06 |         125 |  287605 | 5.25305e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `valid_trace_metadata_halfmile.csv`
- Path: `outputs/preprocessing/valid_trace_metadata_halfmile.csv`
- Size: `181,229,667` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `993,180`
- Columns: `22`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, first_break_sample, exclude_from_training
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| first_break_sample        | int64            |
| exclude_from_training     | bool             |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| first_break_sample        |            0 |          0 |
| exclude_from_training     |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `10` additional columns are omitted from preview.
| asset    |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |    shot_peg |     rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:---------|--------------:|------------------------:|----------------------------:|----------:|------------:|------------:|-----------:|------------:|------------:|--------:|------------:|
| halfmile |           174 |                       0 |                           0 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704346 | 5.24344e+06 |
| halfmile |           175 |                       0 |                           1 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704332 | 5.24345e+06 |
| halfmile |           176 |                       0 |                           2 |  20021449 | 2.00214e+07 | 1.00332e+07 |     704570 | 5.24358e+06 |       454.1 |  704318 | 5.24347e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `valid_trace_metadata_lalor.csv`
- Path: `outputs/preprocessing/valid_trace_metadata_lalor.csv`
- Size: `197,396,744` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `1,211,857`
- Columns: `22`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, first_break_sample, exclude_from_training
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| first_break_sample        | int64            |
| exclude_from_training     | bool             |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| first_break_sample        |            0 |          0 |
| exclude_from_training     |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `10` additional columns are omitted from preview.
| asset   |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |   source_y |   source_ht |   rec_x |   rec_y |
|:--------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|-----------:|------------:|--------:|--------:|
| lalor   |            44 |                       0 |                           0 |        24 |     214101 |    101145 |     2237.6 |    13738.8 |       298.9 |  2219.9 | 13749   |
| lalor   |            43 |                       0 |                           1 |        24 |     214101 |    101144 |     2237.6 |    13738.8 |       298.9 |  2237.5 | 13766.6 |
| lalor   |            45 |                       0 |                           2 |        24 |     214101 |    101146 |     2237.6 |    13738.8 |       298.9 |  2200.1 | 13732.1 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `valid_trace_metadata_sudbury.csv`
- Path: `outputs/preprocessing/valid_trace_metadata_sudbury.csv`
- Size: `33,422,358` bytes
- Produced by stage/script: `scripts/02_preprocessing.py`
- Consumed by: Feature engineering + training + visualization metadata joins.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `200,338`
- Columns: `22`
- Exact column list:
```text
asset, trace_index, gather_sequence_index, trace_index_within_gather, shot_id, shot_peg, rec_peg, source_x, source_y, source_ht, rec_x, rec_y, rec_ht, elevation_diff, offset, samp_rate_us, samp_num, recording_time_ms, label_column, label_ms, first_break_sample, exclude_from_training
```
- Inferred dtypes:
| column                    | inferred_dtype   |
|:--------------------------|:-----------------|
| asset                     | str              |
| trace_index               | int64            |
| gather_sequence_index     | int64            |
| trace_index_within_gather | int64            |
| shot_id                   | int64            |
| shot_peg                  | float64          |
| rec_peg                   | float64          |
| source_x                  | float64          |
| source_y                  | float64          |
| source_ht                 | float64          |
| rec_x                     | float64          |
| rec_y                     | float64          |
| rec_ht                    | float64          |
| elevation_diff            | float64          |
| offset                    | float64          |
| samp_rate_us              | float64          |
| samp_num                  | int64            |
| recording_time_ms         | float64          |
| label_column              | str              |
| label_ms                  | float64          |
| first_break_sample        | int64            |
| exclude_from_training     | bool             |
- Null profile:
| column                    |   null_count |   null_pct |
|:--------------------------|-------------:|-----------:|
| asset                     |            0 |          0 |
| trace_index               |            0 |          0 |
| gather_sequence_index     |            0 |          0 |
| trace_index_within_gather |            0 |          0 |
| shot_id                   |            0 |          0 |
| shot_peg                  |            0 |          0 |
| rec_peg                   |            0 |          0 |
| source_x                  |            0 |          0 |
| source_y                  |            0 |          0 |
| source_ht                 |            0 |          0 |
| rec_x                     |            0 |          0 |
| rec_y                     |            0 |          0 |
| rec_ht                    |            0 |          0 |
| elevation_diff            |            0 |          0 |
| offset                    |            0 |          0 |
| samp_rate_us              |            0 |          0 |
| samp_num                  |            0 |          0 |
| recording_time_ms         |            0 |          0 |
| label_column              |            0 |          0 |
| label_ms                  |            0 |          0 |
| first_break_sample        |            0 |          0 |
| exclude_from_training     |            0 |          0 |
- Sample preview (first rows, summarized):
  - Note: preview shows first `12` columns only; `10` additional columns are omitted from preview.
| asset   |   trace_index |   gather_sequence_index |   trace_index_within_gather |   shot_id |   shot_peg |   rec_peg |   source_x |    source_y |   source_ht |   rec_x |       rec_y |
|:--------|--------------:|------------------------:|----------------------------:|----------:|-----------:|----------:|-----------:|------------:|------------:|--------:|------------:|
| sudbury |         43273 |                      38 |                           0 |        42 |          0 |     15127 |     460809 | 5.14817e+06 |       312.4 |  460496 | 5.14847e+06 |
| sudbury |         43272 |                      38 |                           1 |        42 |          0 |     15126 |     460809 | 5.14817e+06 |       312.4 |  460475 | 5.14845e+06 |
| sudbury |         43274 |                      38 |                           2 |        42 |          0 |     15128 |     460809 | 5.14817e+06 |       312.4 |  460516 | 5.14849e+06 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.
