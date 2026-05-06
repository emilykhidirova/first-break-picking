# Training Output Documentation

## Scope
Model binaries, training metadata, feature importances, and execution logs defining fitted model state.

## Producer Scripts
- `scripts/06_train.py`

## Consumer Scripts
- `scripts/05_hyperbolic_smoothing.py`
- `scripts/07_evaluate.py`
- `scripts/08_visualize_predictions.py`

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
- Total files documented: `6`
- Source directory: `outputs/models`

### `lightgbm_feature_importance.csv`
- Path: `outputs/models/lightgbm_feature_importance.csv`
- Size: `489` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `10`
- Columns: `3`
- Exact column list:
```text
feature, importance_gain, importance_split
```
- Inferred dtypes:
| column           | inferred_dtype   |
|:-----------------|:-----------------|
| feature          | str              |
| importance_gain  | float64          |
| importance_split | int64            |
- Null profile:
| column           |   null_count |   null_pct |
|:-----------------|-------------:|-----------:|
| feature          |            0 |          0 |
| importance_gain  |            0 |          0 |
| importance_split |            0 |          0 |
- Sample preview (first rows, summarized):
| feature        |   importance_gain |   importance_split |
|:---------------|------------------:|-------------------:|
| slant_distance |       1.78267e+07 |              66642 |
| stalta_pick_ms |       5.30978e+06 |              61369 |
| offset_rank    |       3.70373e+06 |              53973 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `lightgbm_feature_importance_experimentb.csv`
- Path: `outputs/models/lightgbm_feature_importance_experimentb.csv`
- Size: `489` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: structured tabular artifact for downstream QA/metrics/reporting
- Rows: `10`
- Columns: `3`
- Exact column list:
```text
feature, importance_gain, importance_split
```
- Inferred dtypes:
| column           | inferred_dtype   |
|:-----------------|:-----------------|
| feature          | str              |
| importance_gain  | float64          |
| importance_split | int64            |
- Null profile:
| column           |   null_count |   null_pct |
|:-----------------|-------------:|-----------:|
| feature          |            0 |          0 |
| importance_gain  |            0 |          0 |
| importance_split |            0 |          0 |
- Sample preview (first rows, summarized):
| feature             |   importance_gain |   importance_split |
|:--------------------|------------------:|-------------------:|
| slant_distance      |       1.60786e+07 |              59978 |
| stalta_pick_ms      |       7.53125e+06 |              56269 |
| hyperbolic_residual |       2.34464e+06 |              47351 |
- Caveats: dtype inference is from parsed chunks; mixed-type columns are shown with combined dtype signatures.

### `lightgbm_first_break.txt`
- Path: `outputs/models/lightgbm_first_break.txt`
- Size: `51,058,245` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `322,637`
- Content preview:
```text
tree
version=v4
num_class=1
num_tree_per_iteration=1
label_index=0
max_feature_idx=9
objective=regression_l1
feature_names=offset_rank elevation_diff slant_distance pre_break_noise_energy zero_crossing_rate max_abs_amplitude stalta_pick_ms gather_median_pick_ms pick_deviation_from_gather_median hyperbolic_residual
```

### `lightgbm_first_break_experimentb.txt`
- Path: `outputs/models/lightgbm_first_break_experimentb.txt`
- Size: `44,086,560` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `278,063`
- Content preview:
```text
tree
version=v4
num_class=1
num_tree_per_iteration=1
label_index=0
max_feature_idx=9
objective=regression_l1
feature_names=offset_rank elevation_diff slant_distance pre_break_noise_energy zero_crossing_rate max_abs_amplitude stalta_pick_ms gather_median_pick_ms pick_deviation_from_gather_median hyperbolic_residual
```

### `lightgbm_training_metadata.json`
- Path: `outputs/models/lightgbm_training_metadata.json`
- Size: `969,039` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: structured configuration/summary payload.
- Top-level type: `dict`
- Top-level keys (8): `model_name, model_path, feature_columns, best_iteration, params, train_rows, val_rows, eval_history`
- Key type preview:
```json
{
  "model_name": "str",
  "model_path": "str",
  "feature_columns": "list",
  "best_iteration": "int",
  "params": "dict",
  "train_rows": "int",
  "val_rows": "dict",
  "eval_history": "dict"
}
```
- Content preview (truncated):
```json
{
  "model_name": "lightgbm_first_break",
  "model_path": "C:\\Users\\EmiliyaXidirova\\Desktop\\project-NEW\\outputs\\models\\lightgbm_first_break.txt",
  "feature_columns": [
    "offset_rank",
    "elevation_diff",
    "slant_distance",
    "pre_break_noise_energy",
    "zero_crossing_rate",
    "max_abs_amplitude",
    "stalta_pick_ms",
    "gather_median_pick_ms",
    "pick_deviation_from_gather_median",
    "hyperbolic_residual"
  ],
  "best_iteration": 16973,
  "params": {
    "objective": "regression_l1",
    "metric": "l1",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 7,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "min_data_in_leaf": 300,
    "verbosity": -1,
    "seed": 42,
    "num_threads": 0
  },
  "train_rows": 800000,
  "val_rows": {
    "train": 800000,
    "val_indistribution": 400000
  },
  "eval_history": {
    "train": {
      "l1": [
        162.86219656260246,
        156.12064588124912,
        149.57167863101537,
        143.3063779031831,
        137.316871147389,
        131.824883499541,
        126.40503804106282,
        121.16297966247092,
        116.15135835727884,
        111.36015017959859,
        106.9315118141698,
        102.71989082501317,
        98.53622666344194,
        94.71883762978314,
        90.8213878847513,
        87.07338869637542,
        83.45534910260037,
        79.99883589280576,
        76.7257747187307,
        73.5655966182149,
        70.54083296838445,
        67.66246064955732,
        64.90411106308999,
        62.269708031540134,
        60.061603390836055,
        57.63937444156164,
        55.580520087825775,
        53.38219207241673,
        51.272814958153916,
        49.27334164054078,
        47.586412018977654,
        45.97041053886964,
        44.443472508529794,
        42.75910314936677,
        41.12672499566509,
        39.76082208810653,
        38.30566169619887,
        36.881249032172406,
        35.54236199157184,
        34.262081873641286,
        33.036140874884545,
        31.877486055161498,
        30.74266170884744,
        29.666296822918582,
        28.765371536515882,
        27.769517415910478,
        26.82566707244561,
        25.90566612974492,
        25.184592759472192,
        24.328325326746114,
        23.65655693843643,
        22.85869917813113,
        22.247757539600922,
        21.53248046535047,
        20.84025336971486,
        20.179527963818725,
        19.680876227490593,
        19.0
```

### `lightgbm_training_metadata_experimentb.json`
- Path: `outputs/models/lightgbm_training_metadata_experimentb.json`
- Size: `1,252,383` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: structured configuration/summary payload.
- Top-level type: `dict`
- Top-level keys (8): `model_name, model_path, feature_columns, best_iteration, params, train_rows, val_rows, eval_history`
- Key type preview:
```json
{
  "model_name": "str",
  "model_path": "str",
  "feature_columns": "list",
  "best_iteration": "int",
  "params": "dict",
  "train_rows": "int",
  "val_rows": "dict",
  "eval_history": "dict"
}
```
- Content preview (truncated):
```json
{
  "model_name": "lightgbm_first_break",
  "model_path": "C:\\Users\\EmiliyaXidirova\\Desktop\\project-NEW\\outputs\\models\\lightgbm_first_break_experimentb.txt",
  "feature_columns": [
    "offset_rank",
    "elevation_diff",
    "slant_distance",
    "pre_break_noise_energy",
    "zero_crossing_rate",
    "max_abs_amplitude",
    "stalta_pick_ms",
    "gather_median_pick_ms",
    "pick_deviation_from_gather_median",
    "hyperbolic_residual"
  ],
  "best_iteration": 14627,
  "params": {
    "objective": "regression_l1",
    "metric": "l1",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 7,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "min_data_in_leaf": 300,
    "verbosity": -1,
    "seed": 42,
    "num_threads": 0
  },
  "train_rows": 800000,
  "val_rows": {
    "train": 800000,
    "val_indistribution": 400000,
    "val_lalor": 233366
  },
  "eval_history": {
    "train": {
      "l1": [
        154.19657624995475,
        147.98140882509242,
        141.70932294116423,
        135.89784075471624,
        130.14088024457453,
        125.05921719591457,
        119.87616089199852,
        114.87390611376573,
        110.06489137743775,
        105.45756420939804,
        101.55496238127708,
        97.78948150439825,
        93.82008688166825,
        90.15242194081117,
        86.38793791704592,
        82.82683995958733,
        79.46082319566023,
        76.20307460497632,
        73.05244951704796,
        70.07313267391847,
        67.18341769606991,
        64.40377056312444,
        61.75197222171247,
        59.22389953869015,
        57.491217348004824,
        55.164337608269356,
        53.29181332639459,
        51.141917920602026,
        49.11651682058265,
        47.16791056197288,
        45.569896082326885,
        44.00755233467722,
        42.568641438068894,
        40.91833604114994,
        39.365093836556106,
        38.094398851817935,
        36.67504535404916,
        35.28457627139016,
        33.95537628893726,
        32.75839992461869,
        31.547588958392012,
        30.38645543440032,
        29.27413753624231,
        28.215231162530078,
        27.452846925041605,
        26.457791880254582,
        25.520549812915178,
        24.618286676169475,
        24.012646670323466,
        23.193262052010716,
        22.630873900596917,
        21.873824546103716,
        21.351623414442525,
        20.711029805597242,
        20.069716666013303,
        19.43066528
```

## Training Log Artifacts
- Source directory: `outputs/training_logs`

### `test_live.log`
- Path: `outputs/training_logs/test_live.log`
- Size: `1,868` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `24`
- Content preview:
```text
[07_evaluate] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\test_live.log
[07_evaluate] Using artifact suffix: _experimentb
[07_evaluate] Loading split=train from predictions_train_experimentb_smoothed.csv
[07_evaluate] Split=train rows: 800,000 -> 800,000 after finite label filtering
[07_evaluate] Loading split=val from predictions_val_experimentb_smoothed.csv
[07_evaluate] Split=val rows: 400,000 -> 400,000 after finite label filtering
[07_evaluate] Loading split=test from predictions_test_experimentb_smoothed.csv
[07_evaluate] Split=test rows: 2,261,144 -> 2,261,144 after finite label filtering
```
- Caveats: logs are append-time dependent and reflect most recent execution context.

### `training_live.log`
- Path: `outputs/training_logs/training_live.log`
- Size: `3,258` bytes
- Produced by stage/script: `scripts/06_train.py`
- Consumed by: Smoothing `scripts/05_hyperbolic_smoothing.py`, evaluation `scripts/07_evaluate.py`, visualization `scripts/08_visualize_predictions.py`.
- Purpose: narrative report or runtime log artifact.
- Line count: `59`
- Content preview:
```text
[06_train] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\training_live.log
[06_train] Loaded 10 model feature columns
[06_train] Running experiment=b
[06_train] Preparing split=train
[06_train] Loaded shot split file train_shot_ids_brunswick.txt: 1,310 shot IDs
[06_train] Reading asset=brunswick
[06_train] Asset=brunswick merged rows=3,174,731
[06_train] Loaded shot split file train_shot_ids_halfmile.txt: 586 shot IDs
```
- Caveats: logs are append-time dependent and reflect most recent execution context.
