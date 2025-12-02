# readWDbin

## Summary

This repository contains Fortran 77 programs that read the binary pulse data saved with CAEN WaveDump,
plus two Python workflows for quick post-processing. All transient artifacts live outside the tracked
source tree (`JUNK/`, `readwdbin/PYTHON_OUTPUTS/`, `ESSENTIAL/ESSENTIAL_OUTPUTS/`) so the repo stays clean.

- `readWDbin.f` targets DT5742b data (up to 16 channels at 2.5 GS/s).
- `readWDbin_dt5740.f` adds first-class support for the DT5740D (up to 32 channels at 62.5 MS/s with the DT5740 time-tag format).
- `readWDbin_dt5740.py` is a Python 3 implementation of the DT5740 pipeline (uses the same configuration files, writes the same outputs, and can ingest either 16-bit or 32-bit WaveDump samples).
- `ESSENTIAL/` contains a minimal Python-only toolchain that extracts integrals + timestamps for a small list of “interesting” channels and saves ready-to-plot histograms/PNGs.

## Inputs

- `wave_X<suffix>.dat` : Binary pulse data files created by WaveDump. One file per enabled channel (0–15 for DT5742b, 0–31 for DT5740D). These files **must** include the WaveDump header.
- `input.txt` / `input_dt5740.txt` : Acquisition and analysis parameters (suffix, sampling, integration gates, channel polarity, etc.).
- `calib.txt` / `calib_dt5740.txt` : Energy calibration coefficients (`E = a·C^2 + m·C + n`) and histogram binning.
- `input-coinc.txt` / `input-coinc_dt5740.txt` : Coincidence AND/OR logic thresholds.

## Outputs

- `list.txt` : Event list file.
- `listcal.txt` : Energy-calibrated Event list file. Optional output.
- `histo_X.txt` : Integral histogram for channel `X`.
- `histocal_X.txt` : Energy histogram for channel `X`. Optional output.
- `rates.txt` : Count rates within the configured energy window for every active channel.
- `pulse_X.txt` : First 200 pulses in channel `X`. Optional output.

## Compilation

`$ ./compile.sh` (builds the DT5742b version)

DT5740D build:

```bash
$ ifort -fast readWDbin_dt5740.f -o readWDbin_dt5740.x
# or
$ ifx   -fast readWDbin_dt5740.f -o readWDbin_dt5740.x
```

## Usage

Place the executable in the same folder as the `wave_*.dat` files and the relevant configuration files.

```bash
$ ./readWDbin.x             # DT5742b data
$ ./readWDbin_dt5740.x      # DT5740D data
```

### Python DT5740 reader (full outputs)

The Python workflow mirrors the DT5740 Fortran logic but is easier to tweak/extend:

```bash
$ cd readwdbin
$ python3 readWDbin_dt5740.py \
    --sample-format int16   # overrides for custom configs/paths if needed
```

Key notes:

- Requires Python ≥3.8 with `numpy` available.
- Uses the same configuration files as the Fortran DT5740 build (suffix, channel settings, calibration, coincidence masks).
- By default, the script reads binaries from `<repo>/DATA` and writes outputs to `<repo>/readwdbin/PYTHON_OUTPUTS`, so it can be launched from any directory; override with `--data-dir` / `--output-dir` as needed.
- Supports up to 32 channels, DT5740 Trigger Time Tags (16 ns LSB, rollover handled), coincidence filtering, dynamic rate/list formats, and optional pulse dumps.
- Set `--sample-format float32` if your WaveDump run stored 32-bit floating samples (DT5742-style); otherwise keep the default 16-bit path for DT5740D captures.
- Optional plotting helper (`readWDbin_plotter.py`) additionally requires `matplotlib`.

#### Quick plotting helper (full pipeline)

After running the Python reader you can generate sanity plots directly from the ASCII outputs:

```bash
$ python3 readWDbin_plotter.py --plot hist --channel 0 --logy       # raw integral histogram
$ python3 readWDbin_plotter.py --plot histocal --channel 5 --logy   # calibrated spectrum
$ python3 readWDbin_plotter.py --plot pulse --channel 3             # waveform
$ python3 readWDbin_plotter.py --plot rates                         # count rates
$ python3 readWDbin_plotter.py --plot histocal --channel 1 9 17 22 --logy --out-prefix spectra/ch
```

By default it reads from `<repo>/readwdbin/PYTHON_OUTPUTS`; point `--data-dir` elsewhere if you saved results in a different folder. Use `--logy`/`--xlim`/`--ylim` to refine axes, and add `--out-prefix plots/spectrum` to save PNGs (one per channel) instead of showing an interactive window.

### Essential minimal Python bundle

If you only need integrals/time stamps for a few channels, use the self-contained bundle in `/ESSENTIAL`.
It consists of:

- `essential_config.json` – points to one or more `DATA` directories, lists the channels of interest, and selects the output folder (default `ESSENTIAL/ESSENTIAL_OUTPUTS`).
- `input_dt5740.txt` – copied from the main tree so baseline, integration windows, and trigger logic stay consistent.
- `essential_reader.py` – scans every configured `wave_*.dat`, keeps only the requested channels, and writes `integrals.csv` with columns `ipulse,start_time_s,channel,fine_time_ns,integral`.
- `essential_plotter.py` – reads that CSV, builds per-channel integral histograms, and saves PNGs under `ESSENTIAL_OUTPUTS/plots/`.

Run everything from the repo root (paths resolve automatically):

```bash
$ python3 ESSENTIAL/essential_reader.py
$ python3 ESSENTIAL/essential_plotter.py --logy --threshold 5
```

Adjust `ESSENTIAL/essential_config.json` to point at your data directories or change the channel list;
the same configuration drives both the reader and the plotter.

### DT5740D notes (Fortran & full Python pipeline)

- `input_dt5740.txt` is pre-populated for 32 channels with a 62.5 MS/s (`0.0625 GS/s`) sampling rate.
- `readWDbin_dt5740.f` automatically scales the Trigger Time Tag using the DT5740 16 ns LSB and handles timestamp rollovers.
- Up to 32 channels can be enabled; configuration blocks must be provided in groups of eight channels.
- Coincidence masks now accept 32-bit OR groups, and histogram/list outputs adopt dynamic column widths.
- The Python reader (`readWDbin_dt5740.py`) honours the same configuration layout and generates identical ASCII outputs.

Copy the DT5740 templates (`*_dt5740.txt`) next to your data or adapt your existing files to the new 32-channel layout.

## Python binary reader plan

A Python implementation would simplify rapid prototyping and plotting. Recommended approach:

1. **Structure decoding** – Use `struct` or `numpy.frombuffer` to parse the WaveDump header (event size, board ID, group mask, event counter, trigger time tag) followed by the waveform samples (`int16` for DT5740D).
2. **Timestamp handling** – Reproduce the rollover logic implemented in `readWDbin_dt5740.f` (32-bit Trigger Time Tag with 16 ns resolution) and expose timestamps both in ADC counts and seconds.
3. **Channel/gate bookkeeping** – Leverage NumPy arrays to align multi-channel traces, subtract baselines, integrate user-defined windows, and filter on coincidences (`orA`/`orB` masks).
4. **Configuration + CLI** – Load the existing `input*.txt`/`calib*.txt` files (e.g., via `configparser`/`numpy.loadtxt`) so that pulse alignment, integration gates, and calibration constants stay in sync between the Fortran and Python utilities.
5. **Outputs/visualization** – Emit the same CSV-style products (`list*.txt`, `rates.txt`, histograms) and optionally provide Matplotlib plots or HDF5 exports for downstream notebooks.

This plan keeps functional parity with the Fortran tools while opening the door to interactive notebooks and quick diagnostics. (The first version of this Python reader now lives in `readWDbin_dt5740.py`; extend it as needed.)

## License

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
