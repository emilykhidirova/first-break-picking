# First-Break Picking with LightGBM

A machine-learning pipeline for **automated seismic first-break picking** across multi-asset 3D survey datasets. The model uses hand-crafted geophysical features combined with a gradient-boosted tree (LightGBM) to achieve near-human accuracy on in-distribution data and strong generalisation to unseen surveys.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Results at a Glance](#results-at-a-glance)
- [Repository Structure](#repository-structure)
- [Datasets](#datasets)
- [Installation](#installation)
- [Running the Pipeline](#running-the-pipeline)
- [Experiments](#experiments)
- [Documentation](#documentation)

---

## Project Overview

First-break picking is the task of identifying the arrival time of the direct seismic wave on each trace. It is a critical preprocessing step in seismic imaging workflows. Manual picking at scale is prohibitively expensive; this project automates it with a supervised learning approach.

**Key design choices:**

- **Feature-based approach:** Rather than raw-waveform deep learning, the model uses compact, interpretable geophysical features (STA/LTA ratio, slant distance, offset rank, hyperbolic residual, etc.) making it fast, explainable, and trainable on CPU.
- **Cross-asset generalisation:** Trained on Brunswick + Halfmile (separate surveys), evaluated as a strict holdout on Lalor and Sudbury.
- **Experiment A vs B:** Experiment A uses Lalor and Sudbury as pure holdout. Experiment B adds 80% of Lalor traces to training (domain adaptation), evaluating on the remaining 20%.

---

## Results at a Glance

### Experiment A — Zero-Shot Generalisation

| Split | MAE (ms) | Median AE (ms) | Within 10 ms | Within 50 ms | AUC-ROC |
|---|---|---|---|---|---|
| Train (Brunswick + Halfmile) | 4.99 | 1.76 | 88.4% | 98.8% | 0.9998 |
| **Test — Lalor** (holdout) | **35.1** | **33.96** | 2.5% | 83.8% | 0.9947 |
| **Test — Sudbury** (stress test) | **22.5** | **22.17** | 10.3% | 98.9% | 0.9993 |

### Experiment B — Domain Adaptation (Lalor 80/20 split)

| Split | MAE (ms) | Median AE (ms) | Within 10 ms | AUC-ROC |
|---|---|---|---|---|
| Test — Lalor holdout | varies | varies | see `outputs/evaluation/` | 0.997 |

### STA/LTA Baseline vs LightGBM

LightGBM consistently outperforms the classical STA/LTA baseline across all assets. See `outputs/evaluation/stalta_baseline_summary.json` for full comparison.

### Key Feature Importances

| Feature | Importance (Gain) |
|---|---|
| slant_distance | 1.78 × 10⁷ |
| stalta_pick_ms | 5.31 × 10⁶ |
| offset_rank | 3.70 × 10⁶ |

---

## Repository Structure

```
first-break-picking/
│
├── config.py                        # All project-level constants and asset definitions
│
├── scripts/
│   ├── 01_eda.py                    # Exploratory data analysis
│   ├── 01b_label_comparison.py      # Label quality / cross-label diagnostics
│   ├── 02_preprocessing.py          # Trace filtering and normalisation
│   ├── 03_feature_engineering.py    # Geophysical feature extraction
│   ├── 03b_stalta_features.py       # STA/LTA feature computation + baseline
│   ├── 04_dataset_builder.py        # Train/val/test split construction
│   ├── 05_hyperbolic_smoothing.py   # Post-prediction hyperbolic gather smoothing
│   ├── 06_train.py                  # LightGBM model training
│   ├── 07_evaluate.py               # Metrics computation and reporting
│   └── 08_visualize_predictions.py  # Gather overlay visualisations
│
├── data/
│   └── README.md                    # Dataset download instructions
│
├── outputs/
│   ├── eda/                         # EDA plots, tables, reports
│   ├── preprocessing/               # Preprocessing reports, split manifests, configs
│   ├── models/                      # Feature importance CSVs (model binaries excluded)
│   ├── training_logs/               # Live training and test logs
│   └── evaluation/                  # Metrics CSVs, ROC curves, gather overlays
│
└── docs/
    └── output-docs/
        ├── README_EDA.md
        ├── README_PREPROCESSING.md
        ├── README_TRAINING.md
        └── README_EVALUATION.md
```

> **Note:** Large model binary (`lightgbm_first_break.txt`, ~51 MB) and raw prediction CSVs (~215–500 MB) are excluded from the repository via `.gitignore`. They are reproducible by running the pipeline end-to-end.

---

## Datasets

The pipeline uses four 3D seismic survey datasets stored as HDF5 files. **The data files are not bundled in this repository.** Download them from the links below and place them in the `data/` directory.

| Asset | Role | Traces | Labeled % | Download |
|---|---|---|---|---|
| **Brunswick** | Training | 4,496,540 | 83.0% | [Download](https://d3sakqnghgsk6x.cloudfront.net/Brunswick_3D/Brunswick_orig_1500ms_V2.hdf5.xz) |
| **Halfmile** | Training | 1,099,559 | 90.3% | [Download](https://d3sakqnghgsk6x.cloudfront.net/Halfmile_3D/Halfmile3D_add_geom_sorted.hdf5.xz) |
| **Lalor** | Validation / Domain Adapt. | 2,424,923 | 50.0% | [Download](https://d3sakqnghgsk6x.cloudfront.net/Lalor_3D/Lalor_raw_z_1500ms_norp_geom_v3.hdf5.xz) |
| **Sudbury** | Stress Test | 1,810,220 | 11.1% | [Download](https://d3sakqnghgsk6x.cloudfront.net/Sudbury_3D/preprocessed_Sudbury3D.hdf.xz) |

> Files are `.xz`-compressed. After downloading, decompress with `xz -d <filename>` and place the resulting `.hdf5` / `.hdf` files in `data/`. Exact filenames are defined in `config.py`.

See [`data/README.md`](data/README.md) for full download and setup instructions.

---

## Installation

### Prerequisites

- Python 3.10+
- ~10 GB free disk space for the datasets
- A modern CPU (GPU not required — LightGBM is CPU-native)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/first-break-picking.git
cd first-break-picking

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download datasets (see data/README.md)
```

---

## Running the Pipeline

Scripts are designed to be run **in order**. Each script reads from `data/` and writes outputs to the corresponding `outputs/` subdirectory.

```bash
# Step 1 — Exploratory Data Analysis
python scripts/01_eda.py
python scripts/01b_label_comparison.py

# Step 2 — Preprocessing (trace filtering, normalisation)
python scripts/02_preprocessing.py

# Step 3 — Feature Engineering
python scripts/03_feature_engineering.py
python scripts/03b_stalta_features.py

# Step 4 — Dataset Building (train/val/test splits)
python scripts/04_dataset_builder.py

# Step 5 — Training
python scripts/06_train.py

# Step 6 — Post-processing (hyperbolic smoothing)
python scripts/05_hyperbolic_smoothing.py

# Step 7 — Evaluation
python scripts/07_evaluate.py

# Step 8 — Visualisation
python scripts/08_visualize_predictions.py
```

All paths and hyperparameters are controlled via `config.py` — no hardcoded paths in scripts.

---

## Experiments

### Experiment A (Default)
- **Train:** Brunswick + Halfmile
- **Validate:** 15% shot holdout from Brunswick and Halfmile
- **Test:** Lalor (full holdout) + Sudbury (stress test, 11% labeled)

### Experiment B (Domain Adaptation)
- Same as Experiment A, plus 80% of Lalor shots added to training
- Evaluates how much the model improves with even partial target-domain data
- Run with `--experiment b` flag on `scripts/06_train.py` (see script `--help`)

### STA/LTA Baseline
- Classical signal-energy-ratio baseline computed in `scripts/03b_stalta_features.py`
- Results in `outputs/evaluation/stalta_baseline_summary.json`

---

## Documentation

Detailed auto-generated documentation for each pipeline stage lives in `docs/output-docs/`:

| Document | Contents |
|---|---|
| [`README_EDA.md`](docs/output-docs/README_EDA.md) | EDA artifact inventory, column profiles, data quality findings |
| [`README_PREPROCESSING.md`](docs/output-docs/README_PREPROCESSING.md) | Preprocessing decisions, removed trace counts, normalisation strategy |
| [`README_TRAINING.md`](docs/output-docs/README_TRAINING.md) | Model binaries, feature importances, training metadata |
| [`README_EVALUATION.md`](docs/output-docs/README_EVALUATION.md) | Full metrics breakdown, ROC curves, gather overlay descriptions |

---

## License

This project is released for research and educational use. Dataset licensing is governed by the original data providers — please refer to each dataset's download page for terms of use.
