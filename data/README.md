# Dataset Download Instructions

The pipeline uses four 3D seismic survey datasets. They are **not included** in this repository due to their large size. Follow the steps below to set them up.

---

## Download Links

| Asset | Expected Filename (after decompression) | Download |
|---|---|---|
| **Brunswick** | `Brunswick_orig_1500ms_V2.hdf5` | [Download .xz](https://d3sakqnghgsk6x.cloudfront.net/Brunswick_3D/Brunswick_orig_1500ms_V2.hdf5.xz) |
| **Halfmile** | `Halfmile3D_add_geom_sorted.hdf5` | [Download .xz](https://d3sakqnghgsk6x.cloudfront.net/Halfmile_3D/Halfmile3D_add_geom_sorted.hdf5.xz) |
| **Lalor** | `Lalor_raw_z_1500ms_norp_geom_v3.hdf5` | [Download .xz](https://d3sakqnghgsk6x.cloudfront.net/Lalor_3D/Lalor_raw_z_1500ms_norp_geom_v3.hdf5.xz) |
| **Sudbury** | `preprocessed_Sudbury3D.hdf` | [Download .xz](https://d3sakqnghgsk6x.cloudfront.net/Sudbury_3D/preprocessed_Sudbury3D.hdf.xz) |

> All files are `.xz`-compressed. You only need the datasets relevant to your run (e.g. just Brunswick + Halfmile for training-only experiments).

---

## Setup Steps

### 1. Download the files

Click the links above or use `wget` / `curl`:

```bash
# Example using wget (run from the repo root)
wget -P data/ https://d3sakqnghgsk6x.cloudfront.net/Brunswick_3D/Brunswick_orig_1500ms_V2.hdf5.xz
wget -P data/ https://d3sakqnghgsk6x.cloudfront.net/Halfmile_3D/Halfmile3D_add_geom_sorted.hdf5.xz
wget -P data/ https://d3sakqnghgsk6x.cloudfront.net/Lalor_3D/Lalor_raw_z_1500ms_norp_geom_v3.hdf5.xz
wget -P data/ https://d3sakqnghgsk6x.cloudfront.net/Sudbury_3D/preprocessed_Sudbury3D.hdf.xz
```

### 2. Decompress the files

```bash
# Linux / macOS
cd data/
xz -d Brunswick_orig_1500ms_V2.hdf5.xz
xz -d Halfmile3D_add_geom_sorted.hdf5.xz
xz -d Lalor_raw_z_1500ms_norp_geom_v3.hdf5.xz
xz -d preprocessed_Sudbury3D.hdf.xz
```

On Windows, you can use [7-Zip](https://www.7-zip.org/) to decompress `.xz` files.

### 3. Verify the directory

After decompression, your `data/` folder should look like:

```
data/
├── Brunswick_orig_1500ms_V2.hdf5
├── Halfmile3D_add_geom_sorted.hdf5
├── Lalor_raw_z_1500ms_norp_geom_v3.hdf5
└── preprocessed_Sudbury3D.hdf
```

The filenames must match exactly — they are defined in `config.py` under `DATASET_ASSETS`.

---

## Dataset Summary

| Asset | Role | Total Traces | Labeled Traces (%) | Sampling Rate |
|---|---|---|---|---|
| Brunswick | Training | 4,496,540 | 83.0% | 2 ms |
| Halfmile | Training | 1,099,559 | 90.3% | 2 ms |
| Lalor | Validation / Domain Adapt. | 2,424,923 | 50.0% | 1 ms (resampled to 2 ms) |
| Sudbury | Stress Test | 1,810,220 | 11.1% | 2 ms |

---

## Notes

- **Disk space:** ~10–30 GB total depending on which assets you download.
- **Lalor resampling:** Lalor is recorded at 1 ms and is downsampled to 2 ms at runtime (controlled by `TRACE_HARMONIZATION_STRATEGY` in `config.py`).
- **Sudbury labels:** Sudbury uses `0` (not `-1`) as the unlabeled sentinel — this is handled automatically by `config.py`.
