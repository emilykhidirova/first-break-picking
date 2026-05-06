# Evaluation Summary

Experiment tag: experimentb

Binary target for ROC/classification is derived by thresholding arrival time (`label_ms <= threshold_ms`), with score = `-predicted_ms`.

## Training Metrics (Global Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_all | 800000 | 4.726 | 4.726 | 10.5435 | 1.65654 | 78.5909 | 88.888 | 94.4791 | 99.0321 | 340 | 0.99266 | 0.99497 | 0.990329 | 0.992644 | 2003 | 3869 | 396187 | 397941 | 0.999652 |
| train_brunswick | 508385 | 4.92987 | 4.92987 | 11.2182 | 1.67083 | 78.3377 | 88.5964 | 94.1045 | 98.7944 | 340 | 0.994136 | 0.996251 | 0.989724 | 0.992977 | 793 | 2188 | 210737 | 294667 | 0.999767 |
| train_halfmile | 135361 | 5.80396 | 5.80396 | 11.4314 | 2.37785 | 70.1775 | 84.9528 | 93.5373 | 98.8623 | 340 | 0.989391 | 0.990833 | 0.987765 | 0.989297 | 614 | 822 | 66363 | 67562 | 0.999477 |
| train_lalor | 156254 | 3.12889 | 3.12889 | 6.81871 | 1.24497 | 86.7031 | 93.2456 | 96.514 | 99.9526 | 340 | 0.990688 | 0.99502 | 0.992838 | 0.993928 | 596 | 859 | 119087 | 35712 | 0.999058 |

## Test Metrics (Global Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_all | 400000 | 6.37562 | 6.37562 | 14.0051 | 2.78085 | 65.1188 | 81.88 | 92.3755 | 99.521 | 340 | 0.988857 | 0.99656 | 0.990614 | 0.993578 | 1190 | 3267 | 344787 | 50756 | 0.997985 |
| test_lalor | 215257 | 3.78168 | 3.78168 | 13.9294 | 1.45924 | 85.3705 | 92.5582 | 96.0136 | 99.8407 | 340 | 0.989153 | 0.995277 | 0.990805 | 0.993036 | 790 | 1545 | 166481 | 46441 | 0.998002 |
| test_sudbury | 184743 | 9.398 | 9.398 | 14.0927 | 6.20899 | 41.522 | 69.4381 | 88.1365 | 99.1485 | 340 | 0.988514 | 0.997762 | 0.990435 | 0.994085 | 400 | 1722 | 178306 | 4315 | 0.997468 |

## Test Metrics (Per-Asset Threshold)

| split | rows | loss_l1_mae_ms | mae_ms | rmse_ms | median_ae_ms | within_5ms_pct | within_10ms_pct | within_20ms_pct | within_50ms_pct | classification_threshold_ms | accuracy | precision | recall | f1_score | false_positive | false_negative | true_positive | true_negative | auc_roc | threshold_kind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_lalor | 215257 | 3.78168 | 3.78168 | 13.9294 | 1.45924 | 85.3705 | 92.5582 | 96.0136 | 99.8407 | 244 | 0.990458 | 0.992841 | 0.988045 | 0.990437 | 767 | 1287 | 106370 | 106833 | 0.997984 | per_asset |
| test_sudbury | 184743 | 9.398 | 9.398 | 14.0927 | 6.20899 | 41.522 | 69.4381 | 88.1365 | 99.1485 | 162 | 0.947684 | 0.971154 | 0.923654 | 0.946809 | 2555 | 7110 | 86019 | 89059 | 0.988365 | per_asset |

## Per-Asset Holdout Report

| asset | rows | mae_ms | rmse_ms | median_ae_ms | within_50ms_pct | accuracy | precision | recall | f1_score | auc_roc | true_positive | false_positive | true_negative | false_negative | mae_gap_vs_train_all_ms | mae_ratio_vs_train_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lalor | 215257 | 3.78168 | 13.9294 | 1.45924 | 99.8407 | 0.989153 | 0.995277 | 0.990805 | 0.993036 | 0.998002 | 166481 | 790 | 46441 | 1545 | -0.94432 | 0.800186 |
| sudbury | 184743 | 9.398 | 14.0927 | 6.20899 | 99.1485 | 0.988514 | 0.997762 | 0.990435 | 0.994085 | 0.997468 | 178306 | 400 | 4315 | 1722 | 4.67199 | 1.98857 |

## Training Log (latest)

```text
[06_train] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\training_live.log
[06_train] Loaded 10 model feature columns
[06_train] Running experiment=b
[06_train] Preparing split=train
[06_train] Loaded shot split file train_shot_ids_brunswick.txt: 1,310 shot IDs
[06_train] Reading asset=brunswick
[06_train] Asset=brunswick merged rows=3,174,731
[06_train] Loaded shot split file train_shot_ids_halfmile.txt: 586 shot IDs
[06_train] Reading asset=halfmile
[06_train] Asset=halfmile merged rows=844,507
[06_train] Loaded shot split file train_shot_ids_lalor_expB.txt: 724 shot IDs
[06_train] Reading asset=lalor
[06_train] Asset=lalor merged rows=978,491
[06_train] Split=train rows before sampling: 4,997,729
[06_train] Sampling from 4,997,729 to 800,000 rows (seed=42)
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
[06_train] Loaded shot split file val_shot_ids_lalor_expB.txt: 181 shot IDs
[06_train] Reading asset=lalor
[06_train] Asset=lalor merged rows=233,366
[06_train] Reading asset=sudbury
[06_train] Asset=sudbury merged rows=200,338
[06_train] Split=test rows before sampling: 433,704
[06_train] Sampling from 433,704 to 400,000 rows (seed=43)
[06_train] Split=test rows final: 400,000
[06_train] Split=train numeric cleanup: 800,000 -> 800,000
[06_train] Split=val_indistribution numeric cleanup: 400,000 -> 400,000
[06_train] Split=test numeric cleanup: 400,000 -> 400,000
[06_train] Preparing split=val_lalor
[06_train] Loaded shot split file val_shot_ids_lalor_expB.txt: 181 shot IDs
[06_train] Reading asset=lalor
[06_train] Asset=lalor merged rows=233,366
[06_train] Split=val_lalor rows before sampling: 233,366
[06_train] Split=val_lalor rows final: 233,366
[06_train] Split=val_lalor numeric cleanup: 233,366 -> 233,366
[06_train] Train matrix shape=(800000, 10), Val matrix shape=(400000, 10)
[06_train] LightGBM rounds: max=100000, early_stopping=50
[06_train] Best iteration: 14627
[06_train] Saved model + training metadata + feature importance
[06_train] Predicting split=train rows=800,000
[06_train] Saved predictions_train_experimentb.csv
[06_train] Predicting split=val rows=400,000
[06_train] Saved predictions_val_experimentb.csv
[06_train] Predicting split=test rows=400,000
[06_train] Loaded shot split file val_shot_ids_lalor_expB.txt: 181 shot IDs
[06_train] Saved predictions_test_experimentb.csv
[06_train] Training completed
[06_train] Model: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\models\lightgbm_first_break_experimentb.txt
[06_train] Train rows: 800,000, Val rows: train=800,000, val_indistribution=400,000, val_lalor=233,366, Test rows: 400,000
```

## Test Log (latest)

```text
[07_evaluate] Log file: C:\Users\EmiliyaXidirova\Desktop\project-NEW\outputs\training_logs\test_live.log
[07_evaluate] Using artifact suffix: _experimentb
[07_evaluate] Loading split=train from predictions_train_experimentb_smoothed.csv
[07_evaluate] Split=train rows: 800,000 -> 800,000 after finite label filtering
[07_evaluate] Loading split=val from predictions_val_experimentb_smoothed.csv
[07_evaluate] Split=val rows: 400,000 -> 400,000 after finite label filtering
[07_evaluate] Loading split=test from predictions_test_experimentb_smoothed.csv
[07_evaluate] Split=test rows: 2,261,144 -> 2,261,144 after finite label filtering
[07_evaluate] Split=train labeled metric rows: 800,000 -> 800,000
[07_evaluate] Split=test labeled metric rows: 400,000 -> 400,000
[07_evaluate] Global classification threshold (median train label): 340.000 ms
[07_evaluate] Evaluating test asset=lalor rows=215,257 (global threshold)
[07_evaluate] Evaluating test asset=sudbury rows=184,743 (global threshold)
[07_evaluate] Evaluating test asset=lalor rows=215,257 (asset threshold=244.000 ms)
[07_evaluate] Evaluating test asset=sudbury rows=184,743 (asset threshold=162.000 ms)
[07_evaluate] Saved metrics CSV: metrics_train_global_threshold_experimentb.csv
[07_evaluate] Saved metrics CSV: metrics_test_global_threshold_experimentb.csv
[07_evaluate] Saved metrics CSV: metrics_test_asset_threshold_experimentb.csv
[07_evaluate] Saved holdout report: holdout_report_by_asset_experimentb.csv
[07_evaluate] Saved ROC plot: roc_curve_train_experimentb.png
[07_evaluate] Saved ROC plot: roc_curve_test_experimentb.png
```

## Output Artifacts

- metrics_train_global_threshold_experimentb.csv
- metrics_test_global_threshold_experimentb.csv
- metrics_test_asset_threshold_experimentb.csv
- holdout_report_by_asset_experimentb.csv
- roc_curve_train_experimentb.png
- roc_curve_test_experimentb.png
- experiment_comparison_a_vs_b.csv (if both experiments available)
