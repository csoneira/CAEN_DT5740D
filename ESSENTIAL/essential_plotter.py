#!/usr/bin/env python3
"""
Plot integral histograms from the simplified DT5740 outputs.
Reads channel list and output directory from essential_config.json.
"""

import argparse
import json
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np


def load_config(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def resolve_path(base: Path, entry: str) -> Path:
    path = Path(entry)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Plot integrals from ESSENTIAL pipeline outputs.")
    parser.add_argument("--config", default=str(script_dir / "essential_config.json"))
    parser.add_argument("--bins", type=int, default=200, help="Number of histogram bins.")
    parser.add_argument("--logy", action="store_true", help="Use logarithmic Y axis.")
    parser.add_argument("--threshold", type=float, default=0.0, help="Drop bins with counts <= threshold.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)
    base = config_path.parent

    output_dir = resolve_path(base, cfg.get("output_dir", "ESSENTIAL_OUTPUTS"))
    results_path = output_dir / "integrals.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"{results_path} not found. Run essential_reader.py first.")

    data = np.genfromtxt(results_path, delimiter=",", names=True)
    if data.size == 0:
        raise RuntimeError("No data in integrals.csv.")

    plots_dir = output_dir / "plots"
    ensure_dir(plots_dir)
    channels: List[int] = cfg.get("channels", [])

    for ch in channels:
        mask = data["channel"] == ch
        if not mask.any():
            print(f"[WARN] Channel {ch} has no entries in results.")
            continue
        integrals = data["integral"][mask]
        counts, edges = np.histogram(integrals, bins=args.bins)
        counts = counts.astype(float)
        counts[counts <= args.threshold] = 0.0
        centers = edges[:-1]

        # If bin has 0 counts, do not plot it not even in x
        cond = counts != 0
        counts = counts[cond]
        centers = centers[cond]

        fig = plt.figure(figsize=(8, 4.5))
        plt.step(centers, counts, where="post", lw=1.5, color="tab:blue")
        plt.fill_between(centers, counts, step="post", alpha=0.2, color="tab:blue")
        plt.xlabel("Integral (arb. units)")
        plt.ylabel("Counts")
        plt.title(f"Integral histogram - channel {ch}")
        plt.grid(True, alpha=0.3)
        if args.logy:
            plt.yscale("log")

        plt.tight_layout()
        out_path = plots_dir / f"hist_ch{ch}.png"
        plt.savefig(out_path, dpi=180)
        plt.close(fig)
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
