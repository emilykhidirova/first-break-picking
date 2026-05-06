# Evaluation Summary

Experiment tag: latest

Binary target for ROC/classification is derived by thresholding arrival time (`label_ms <= threshold_ms`), with score = `-predicted_ms`.

## Training Metrics (Global Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_all | 800000 | 4.99564 | 4.99564 | 11.1084 | 1.75929 | 77.5451 | 88.3649 | 94.1661 | 98.8023 | 372 | 0.993633 | 0.996064 | 0.991184 | 0.993618 | 1567 | 3527 | 396535 | 398371 | 0.999773 |
| train_brunswick | 632054 | 4.82701 | 4.82701 | 11.0582 | 1.65112 | 79.2057 | 89.043 | 94.2268 | 98.7982 | 372 | 0.994673 | 0.996922 | 0.991963 | 0.994436 | 929 | 2438 | 300902 | 327785 | 0.999828 |
| train_halfmile | 167946 | 5.63026 | 5.63026 | 11.2955 | 2.30784 | 71.2955 | 85.8127 | 93.9379 | 98.8175 | 372 | 0.989717 | 0.993373 | 0.988741 | 0.991051 | 638 | 1089 | 95633 | 70586 | 0.999502 |

## Test Metrics (Global Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_all | 400000 | 33.3239 | 33.3239 | 36.6431 | 31.7054 | 1.10775 | 3.568 | 18.372 | 85.9213 | 372 | 0.906502 | 0.999987 | 0.893043 | 0.943495 | 4 | 37395 | 312233 | 50368 | 0.995438 |
| test_lalor | 343322 | 35.1062 | 35.1062 | 38.2333 | 33.9552 | 0.649245 | 2.45804 | 14.789 | 83.7846 | 372 | 0.892961 | 0.999988 | 0.874817 | 0.933224 | 3 | 36746 | 256792 | 49781 | 0.994708 |
| test_sudbury | 56678 | 22.5276 | 22.5276 | 24.929 | 22.1719 | 3.88511 | 10.2915 | 40.0755 | 98.8638 | 372 | 0.988532 | 0.999982 | 0.988429 | 0.994172 | 1 | 649 | 55441 | 587 | 0.999316 |

## Test Metrics (Per-Asset Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc | threshold_kind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_lalor | 343322 | 35.1062 | 35.1062 | 38.2333 | 33.9552 | 0.649245 | 2.45804 | 14.789 | 83.7846 | 248 | 0.894064 | 0.999853 | 0.788772 | 0.881857 | 20 | 36350 | 135739 | 171213 | 0.997024 | per_asset |
| test_sudbury | 56678 | 22.5276 | 22.5276 | 24.929 | 22.1719 | 3.88511 | 10.2915 | 40.0755 | 98.8638 | 162 | 0.84052 | 0.997552 | 0.685123 | 0.812333 | 48 | 8991 | 19563 | 28076 | 0.99153 | per_asset |

## Per-Asset Holdout Report

| asset | rows | mae_ms | rmse_ms | median_ae_ms | within_50ms_pct | accuracy | precision | recall | f1_score | auc_roc | true_positive | false_positive | true_negative | false_negative | mae_gap_vs_train_all_ms | mae_ratio_vs_train_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lalor | 343322 | 35.1062 | 38.2333 | 33.9552 | 83.7846 | 0.892961 | 0.999988 | 0.874817 | 0.933224 | 0.994708 | 256792 | 3 | 49781 | 36746 | 30.1106 | 7.02737 |
| sudbury | 56678 | 22.5276 | 24.929 | 22.1719 | 98.8638 | 0.988532 | 0.999982 | 0.988429 | 0.994172 | 0.999316 | 55441 | 1 | 587 | 649 | 17.5319 | 4.50945 |

## Training Log (latest)

```text
[06_train] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\training_live.log
[06_train] Loaded 10 model feature columns
[06_train] Running experiment=a
[06_train] Preparing split=train
[06_train] Loaded shot split file train_shot_ids_brunswick.txt: 1,310 shot IDs
[06_train] Reading asset=brunswick
[06_train] Asset=brunswick merged rows=3,174,731
[06_train] Loaded shot split file train_shot_ids_halfmile.txt: 586 shot IDs
[06_train] Reading asset=halfmile
[06_train] Asset=halfmile merged rows=844,507
[06_train] Split=train rows before sampling: 4,019,238
[06_train] Sampling from 4,019,238 to 800,000 rows (seed=42)
[06_train] Split=train rows final: 800,000
[06_train] Preparing split=val_indistribution
[06_train] Loaded shot split file val_shot_ids_brunswick.txt: 231 shot IDs
[06_train] Reading asset=brunswick
[06_train] Asset=brunswick merged rows=558,490
[06_train] Loaded shot split file val_shot_ids_halfmile.txt: 104 shot IDs
[06_train] Reading asset=halfmile
[06_train] Asset=halfmile merged rows=148,673
[06_train] Split=val_indistribution rows before sampling: 707,163
[06_train] Sampling from 707,163 to 400,000 rows (seed=42)
[06_train] Split=val_indistribution rows final: 400,000
[06_train] Preparing split=test
[06_train] Reading asset=lalor
[06_train] Asset=lalor merged rows=1,211,857
[06_train] Reading asset=sudbury
[06_train] Asset=sudbury merged rows=200,338
[06_train] Split=test rows before sampling: 1,412,195
[06_train] Sampling from 1,412,195 to 400,000 rows (seed=43)
[06_train] Split=test rows final: 400,000
[06_train] Split=train numeric cleanup: 800,000 -> 800,000
[06_train] Split=val_indistribution numeric cleanup: 400,000 -> 400,000
[06_train] Split=test numeric cleanup: 400,000 -> 400,000
[06_train] Train matrix shape=(800000, 10), Val matrix shape=(400000, 10)
[06_train] LightGBM rounds: max=100000, early_stopping=50
[06_train] Best iteration: 16973
[06_train] Saved model + training metadata + feature importance
[06_train] Predicting split=train rows=800,000
[06_train] Saved predictions_train.csv
[06_train] Predicting split=val rows=400,000
[06_train] Saved predictions_val.csv
[06_train] Predicting split=test rows=400,000
[06_train] Saved predictions_test.csv
[06_train] Training completed
[06_train] Model: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\models\lightgbm_first_break.txt
[06_train] Train rows: 800,000, Val rows: train=800,000, val_indistribution=400,000, Test rows: 400,000
```

## Test Log (latest)

```text
[07_evaluate] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\test_live.log
[07_evaluate] Loading split=train from predictions_train_smoothed.csv
[07_evaluate] Split=train rows: 800,000 -> 800,000 after finite label filtering
[07_evaluate] Loading split=val from predictions_val_smoothed.csv
[07_evaluate] Split=val rows: 400,000 -> 400,000 after finite label filtering
[07_evaluate] Loading split=test from predictions_test_smoothed.csv
[07_evaluate] Split=test rows: 3,222,948 -> 3,222,948 after finite label filtering
[07_evaluate] Split=train labeled metric rows: 800,000 -> 800,000
[07_evaluate] Split=test labeled metric rows: 400,000 -> 400,000
[07_evaluate] Global classification threshold (median train label): 372.000 ms
[07_evaluate] Evaluating test asset=lalor rows=343,322 (global threshold)
[07_evaluate] Evaluating test asset=sudbury rows=56,678 (global threshold)
[07_evaluate] Evaluating test asset=lalor rows=343,322 (asset threshold=248.000 ms)
[07_evaluate] Evaluating test asset=sudbury rows=56,678 (asset threshold=162.000 ms)
[07_evaluate] Saved metrics CSV: metrics_train_global_threshold_latest.csv
[07_evaluate] Saved metrics CSV: metrics_test_global_threshold_latest.csv
[07_evaluate] Saved metrics CSV: metrics_test_asset_threshold_latest.csv
[07_evaluate] Saved holdout report: holdout_report_by_asset_latest.csv
[07_evaluate] Saved ROC plot: roc_curve_train_latest.png
[07_evaluate] Saved ROC plot: roc_curve_test_latest.png
[07_evaluate] Saved ROC plot: roc_curve_train.png
[07_evaluate] Saved ROC plot: roc_curve_test.png
```

## Output Artifacts

- metrics_train_global_threshold_latest.csv
- metrics_test_global_threshold_latest.csv
- metrics_test_asset_threshold_latest.csv
- holdout_report_by_asset_latest.csv
- roc_curve_train_latest.png
- roc_curve_test_latest.png
- experiment_comparison_a_vs_b.csv (if both experiments available)
