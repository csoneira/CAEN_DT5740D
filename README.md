# Minimal DT5740 Processing Toolkit

## Overview

The `ESSENTIAL/` directory contains a lightweight Python workflow to extract
integrals and timestamps from CAEN DT5740 WaveDump files. It is designed to be
self-contained: copy the folder next to your raw data, adjust the config, run
the reader, and you are done. Generated artifacts live under
`ESSENTIAL/ESSENTIAL_OUTPUTS/` so the repository stays clean.

If you only need integrals/time stamps for a few channels, use the self-contained bundle in `/ESSENTIAL`.
It consists of:

- `essential_config.json` – points to one or more `DATA` directories, lists the channels of interest, and selects the output folder (default `ESSENTIAL/ESSENTIAL_OUTPUTS`).
- `input_dt5740.txt` – copied from the main tree so baseline, integration windows, and trigger logic stay consistent.
- `essential_reader.py` – scans every configured `wave_*.dat`, keeps only the requested channels, and writes `integrals.csv` with columns `ipulse,start_time_s,channel,fine_time_ns,integral`.
- `essential_plotter.py` – reads that CSV, builds per-channel integral histograms, and saves PNGs under `ESSENTIAL_OUTPUTS/plots/`.

Run everything from the repo root (paths resolve automatically):

```bash
$ python3 -m venv .venv && source .venv/bin/activate
$ pip install -r CONFIG/requirements.txt
$ python3 ESSENTIAL/essential_reader.py
$ python3 ESSENTIAL/essential_plotter.py --logy --threshold 5
```

### Configuring `essential_config.json`

All knobs live in `ESSENTIAL/essential_config.json`. Example:

```json
{
  "data_paths": ["../../DATA", "/mnt/usb2/DATA_BACKUP"],
  "output_dir": "ESSENTIAL_OUTPUTS",
  "channels": [1, 9, 17, 22],
  "suffix": "",
  "sample_format": "int16",
  "max_events": 0
}
```

- `data_paths`: ordered list of directories where `wave_*.dat` live. Relative paths resolve from the config’s location.
- `output_dir`: relative or absolute folder where `integrals.csv` and the `plots/` subfolder will be created.
- `channels`: list of integer channel IDs to keep. Both the reader and the plotter use this list.
- `suffix`: optional string (e.g., `-runA`) appended between the channel number and `.dat` when looking for `wave_<ch><suffix>.dat`.
- `sample_format`: either `int16` (DT5740 default) or `float32` if WaveDump stored 32-bit samples.
- `max_events`: limit the number of events processed (0 means “read everything available”).

Edit these fields to match your acquisition layout; no other code changes are required.

## License

Distributed under the MIT License. See `LICENSE` for details.
