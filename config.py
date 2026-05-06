from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"

EDA_DIR = OUTPUTS_DIR / "eda"
PREPROCESSING_DIR = OUTPUTS_DIR / "preprocessing"
MODELS_DIR = OUTPUTS_DIR / "models"
TRAINING_LOGS_DIR = OUTPUTS_DIR / "training_logs"
EVALUATION_DIR = OUTPUTS_DIR / "evaluation"


@dataclass(frozen=True)
class DatasetAsset:
    file_name: str
    role: str
    total_traces: int
    labeled_pct: float


@dataclass(frozen=True)
class AssetSamplingSpec:
    samp_rate_us: int
    samp_num: int
    recording_time_ms: int


DATASET_ASSETS: Dict[str, DatasetAsset] = {
    "brunswick": DatasetAsset(
        file_name="Brunswick_orig_1500ms_V2.hdf5",
        role="train",
        total_traces=4_496_540,
        labeled_pct=83.02,
    ),
    "halfmile": DatasetAsset(
        file_name="Halfmile3D_add_geom_sorted.hdf5",
        role="train",
        total_traces=1_099_559,
        labeled_pct=90.33,
    ),
    "lalor": DatasetAsset(
        file_name="Lalor_raw_z_1500ms_norp_geom_v3.hdf5",
        role="validate",
        total_traces=2_424_923,
        labeled_pct=49.98,
    ),
    "sudbury": DatasetAsset(
        file_name="preprocessed_Sudbury3D.hdf",
        role="stress_test",
        total_traces=1_810_220,
        labeled_pct=11.07,
    ),
}


# Reproducibility and data controls
RANDOM_SEED = 42
MAX_GATHERS_PER_ASSET = None
SAMPLES_PER_TRACE = 1500
TIME_SAMPLE_INTERVAL_MS = 1.0
PREPROCESSING_CHUNK_SIZE = 5_000
MIN_GATHER_TRACES = 5
NORMALIZATION_METHOD = "per_trace"
STORED_OFFSET_COLUMN = "derived_from_coordinates"
CANDIDATE_LABEL_COLUMNS = ("SPARE1", "FIRST_BREAK_TIME")
UNLABELED_SENTINELS_BY_ASSET = {
    "brunswick": (-1,),
    "halfmile": (-1,),
    "lalor": (-1,),
    "sudbury": (0,),
}
WORKING_LABEL_COLUMN = "SPARE1"
PRIMARY_OFFSET_COLUMN_BY_ASSET = {
    "brunswick": "derived_from_coordinates",
    "halfmile": "derived_from_coordinates",
    "lalor": "derived_from_coordinates",
    "sudbury": "derived_from_coordinates",
}
MIN_GATHER_TRACES_BY_ASSET = {
    "brunswick": 5,
    "halfmile": 5,
    "lalor": 10,
    "sudbury": 5,
}
ZERO_OFFSET_FILTER_BY_ASSET = {}
TRACE_HARMONIZATION_STRATEGY = "downsample_lalor_to_2ms_then_pad_or_crop_at_runtime"
TRACE_HARMONIZATION_TARGET_SAMP_RATE_US = 2000
TRACE_HARMONIZATION_TARGET_SAMP_NUM = 751
FEATURE_ENGINEERING_METADATA_CHUNK_SIZE = 5_000
PRE_BREAK_NOISE_WINDOW_SAMPLES = 5
ZERO_CROSSING_WINDOW_FRACTION = 0.5
INCLUDE_SOURCE_Y_NORMALIZED = True
LALOR_ADAPT_TRAIN_FRACTION = 0.8
ASSET_SAMPLING_SPECS: Dict[str, AssetSamplingSpec] = {
    "brunswick": AssetSamplingSpec(samp_rate_us=2000, samp_num=751, recording_time_ms=1502),
    "halfmile": AssetSamplingSpec(samp_rate_us=2000, samp_num=751, recording_time_ms=1502),
    "lalor": AssetSamplingSpec(samp_rate_us=1000, samp_num=1501, recording_time_ms=1501),
    "sudbury": AssetSamplingSpec(samp_rate_us=2000, samp_num=1001, recording_time_ms=2002),
}


# Baseline/model defaults (CPU-friendly)
MODEL_NAME = "lightgbm_first_break"

# STA/LTA feature computation parameters
STALTA_STA_WINDOW_MS: float = 20.0      # Short-term average window in milliseconds
STALTA_LTA_WINDOW_MS: float = 200.0     # Long-term average window in milliseconds
STALTA_SIGNAL_WINDOW_SAMPLES: int = 50  # Samples after pick for signal energy (diagnostic only)

STALTA_THRESHOLD_BY_ASSET: Dict[str, float] = {
    "brunswick": 3.0,
    "halfmile": 3.0,
    "lalor": 2.5,
    "sudbury": 3.5,
}

STALTA_MIN_SEARCH_SAMPLE_BY_ASSET: Dict[str, int] = {
    "brunswick": 5,  # Skip first 5 samples (10ms at 2ms rate)
    "halfmile": 5,
    "lalor": 10,     # Skip first 10 samples (10ms at 1ms rate)
    "sudbury": 5,
}

# Experiment B: Lalor domain adaptation split
EXPERIMENT_B_LALOR_TRAIN_FRACTION: float = 0.80

# LightGBM defaults
LIGHTGBM_OBJECTIVE = "regression_l1"
LIGHTGBM_LEARNING_RATE = 0.05
LIGHTGBM_NUM_LEAVES = 31
LIGHTGBM_MAX_DEPTH = 7
LIGHTGBM_FEATURE_FRACTION = 0.8
LIGHTGBM_BAGGING_FRACTION = 0.8
LIGHTGBM_BAGGING_FREQ = 1
LIGHTGBM_MIN_DATA_IN_LEAF = 300
LIGHTGBM_NUM_BOOST_ROUND = 100000
LIGHTGBM_EARLY_STOPPING_ROUNDS = 50
LIGHTGBM_MAX_TRAIN_ROWS = 800_000
LIGHTGBM_MAX_VAL_ROWS = 400_000

# Evaluation defaults
EVAL_HIT_TOLERANCE_MS = 10.0


def ensure_output_dirs() -> None:
    for path in [
        DATA_DIR,
        OUTPUTS_DIR,
        EDA_DIR,
        PREPROCESSING_DIR,
        MODELS_DIR,
        TRAINING_LOGS_DIR,
        EVALUATION_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def get_asset_path(asset_key: str) -> Path:
    if asset_key not in DATASET_ASSETS:
        raise KeyError(f"Unknown asset key: {asset_key}")
    return DATA_DIR / DATASET_ASSETS[asset_key].file_name


if __name__ == "__main__":
    ensure_output_dirs()
    print(f"Root: {ROOT_DIR}")
    for key, asset in DATASET_ASSETS.items():
        print(f"{key:10s} | role={asset.role:11s} | file={asset.file_name}")
