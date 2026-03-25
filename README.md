# Bachelor Project - Quantum Key Distribution (QKD) Processing Toolkit

This repository contains a Python-based toolkit for simulating and analyzing a Quantum Key Distribution (QKD) post-processing pipeline.

The project includes:
- Core QKD processing modules (sifting, parameter estimation, error reconciliation, privacy amplification)
- gRPC-based classical channel communication components
- Data processing scripts for large raw datasets
- A GUI plotter for visual inspection of QKD metrics
- Performance profiling scripts

## Project Structure

```text
.
├── alice_server.py
├── bob_client.py
├── process_large_file.py
├── profile_qkd_processing.py
├── qkd_grpc_cascade.proto
├── qkd_profile.prof
├── QKDPlotterGUI.py
├── small_portion_test.py
├── qkd/
│   ├── __init__.py
│   ├── cascade_wrapper.py
│   ├── grpc_classical_channel.py
│   ├── parameter_estimation.py
│   ├── privacy_amplification.py
│   ├── qkd_grpc_cascade_pb2.py
│   ├── qkd_grpc_cascade_pb2_grpc.py
│   ├── sifting.py
│   ├── cascade_open_source/
│   └── privacy_amplification_open_source/
└── raw_data/
```

## Main Components

### 1. Core QKD Modules (`qkd/`)
- `sifting.py`: Basis reconciliation and sifted key extraction logic.
- `parameter_estimation.py`: QBER/error-rate estimation and parameter checks.
- `cascade_wrapper.py`: Wrapper around Cascade error-correction routines.
- `privacy_amplification.py`: Final key compression using privacy amplification methods.
- `grpc_classical_channel.py`: Communication helpers for classical authenticated channel interactions.

### 2. Open-Source Algorithm Integrations
- `qkd/cascade_open_source/`: Cascade reconciliation implementation details.
- `qkd/privacy_amplification_open_source/`: Universal hashing / privacy amplification primitives.

### 3. Communication Layer
- `qkd_grpc_cascade.proto`: Protocol buffer definitions for gRPC communication.
- `alice_server.py`: Example/server side classical channel endpoint.
- `bob_client.py`: Example/client side interaction with server.

### 4. Data & Analysis Utilities
- `process_large_file.py`: Processing workflow for large input datasets.
- `small_portion_test.py`: Lightweight test/debug run on smaller subsets.
- `profile_qkd_processing.py`: Profiling entry point for performance analysis.
- `qkd_profile.prof`: Example/generated profiler output.

### 5. Visualization
- `QKDPlotterGUI.py`: GUI for plotting and inspecting QKD processing results.

## Requirements

- Python 3.9+ (recommended)
- `pip`
- gRPC/protobuf Python packages (depending on your setup)
- Any plotting GUI dependencies used by `QKDPlotterGUI.py`

Because this repository currently has no pinned dependency file, install missing packages based on import errors.

## Quick Start

### 1. Clone repository

```bash
git clone <your-repo-url>
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If you have no `requirements.txt` yet, install packages as needed, e.g.:

```bash
pip install grpcio grpcio-tools protobuf matplotlib pandas numpy
```

Adjust this list according to actual imports in your local version.

## Typical Workflows

### Run a small pipeline test

```bash
python small_portion_test.py
```

### Process a larger dataset

```bash
python process_large_file.py
```

### Launch gRPC server/client example

Open two terminals:

```bash
python alice_server.py
```

```bash
python bob_client.py
```

### Start the plotting GUI

```bash
python QKDPlotterGUI.py
```

### Run profiler

```bash
python profile_qkd_processing.py
```

Then inspect output (for example with `pstats` or visualization tools):

```bash
python -m pstats qkd_profile.prof
```

## Data

The `raw_data/` folder includes multiple dataset slices (from small subsets to larger files), useful for:
- Fast debugging (`1k`, `10k` style subsets)
- Intermediate testing (`100k`, `1M`)
- Stress/performance runs (`10M` or full dataset)

Use smaller files first to validate correctness before running larger jobs.

## Regenerating gRPC Python Stubs

If `qkd_grpc_cascade.proto` changes, regenerate Python files:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. qkd_grpc_cascade.proto
```

Depending on your project layout, generated files may then be moved or imported from the `qkd/` package.

## Notes for Bachelor Thesis Usage

If this repository is used as part of a bachelor thesis:
- Keep experiment configurations versioned.
- Record QBER and final key-rate metrics for each run.
- Archive profiling outputs for reproducibility.
- Document dataset origin and preprocessing assumptions.

## Suggested Improvements

- Add `requirements.txt` or `pyproject.toml`
- Add automated tests (unit + integration)
- Add CI workflow for linting/tests
- Add configurable runtime parameters via CLI args
- Add result export format standardization (CSV/JSON)

## License

Add a license file (`LICENSE`) to define usage rights.

## Author

Bachelor project repository for QKD post-processing research and implementation.
