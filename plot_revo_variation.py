#!/usr/bin/env python3
"""
Plot REVO per-iteration variation statistics parsed from a west.log file.

Usage
-----
    python plotting_scripts/plot_variation.py west.log [options]

Options
-------
    --output FILE     Save plot to FILE (default: variation_per_iteration.png
                      alongside the log file)
    --no-show         Write PNG but do not attempt to open a viewer
"""

import argparse
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ── parse ──────────────────────────────────────────────────────────────────────

def parse_log(log_path: str) -> list[dict]:
    """Return one dict per REVO iteration extracted from a west.log file."""
    records = []
    with open(log_path) as fh:
        lines = fh.readlines()

    cur_iter = None
    in_block = False
    rec: dict = {}

    for line in lines:
        m = re.match(r'^Iteration (\d+) \(', line)
        if m:
            cur_iter = int(m.group(1))
            in_block = False
            rec = {}
            continue

        if 'REVO ITERATION STATS' in line:
            in_block = True
            rec = {'iter': cur_iter}
            continue

        if not in_block:
            continue

        for key, pattern in (
            ('mean_dist',   r'\s*Mean distance:\s+([\d.e+\-]+)'),
            ('merge_dist',  r'\s*Merge distance:\s+([\d.e+\-]+)'),
            ('var_initial', r'\s*Initial variation:\s+([\d.e+\-]+)'),
            ('ops',         r'\s*Clone/merge ops:\s+(\d+)'),
            ('var_final',   r'\s*Final variation:\s+([\d.e+\-]+)'),
        ):
            m = re.match(pattern, line)
            if m:
                rec[key] = float(m.group(1)) if key != 'ops' else int(m.group(1))
                if key == 'var_final':
                    records.append(rec)
                    in_block = False
                break

    return records


# ── regime detection ───────────────────────────────────────────────────────────

def classify_fraction(ratio: float) -> str:
    """Map merge_dist/mean_dist ratio to a human-readable fraction."""
    if ratio < 0.55:
        return '0.5'
    elif ratio < 0.85:
        return '0.7'
    else:
        return '1.0'


REGIME_COLOURS = {'0.5': '#aad4f0', '1.0': '#f0bfbf', '0.7': '#c8f0c8'}


def shade_regimes(ax, revo_iter, regimes, transitions):
    starts = [1]       + [t + 1 for t in transitions]
    ends   = [t + 1 for t in transitions] + [len(revo_iter) + 1]
    labels = [regimes[s - 1] for s in starts]
    for s, e, lbl in zip(starts, ends, labels):
        colour = REGIME_COLOURS.get(lbl, '#dddddd')
        ax.axvspan(s - 0.5, e - 0.5, color=colour, alpha=0.25, zorder=0)


# ── plot ───────────────────────────────────────────────────────────────────────

def make_plot(records: list[dict], out_path: str, log_name: str) -> None:
    iters      = np.array([r['iter']       for r in records])
    var_init   = np.array([r['var_initial'] for r in records])
    var_final  = np.array([r['var_final']   for r in records])
    ops        = np.array([r['ops']         for r in records])
    mean_dist  = np.array([r['mean_dist']   for r in records])
    merge_dist = np.array([r['merge_dist']  for r in records])

    revo_iter = np.arange(1, len(records) + 1)

    ratios  = merge_dist / mean_dist
    regimes = [classify_fraction(r) for r in ratios]
    transitions = [i for i in range(1, len(regimes)) if regimes[i] != regimes[i - 1]]

    if transitions:
        print("Merge-distance regime transitions (REVO iter → abs iter):")
        for t in transitions:
            print(f"  REVO iter {t+1} (abs {iters[t]}): {regimes[t-1]} → {regimes[t]}")

    fig, axes = plt.subplots(3, 1, figsize=(11, 12), sharex=True)
    fig.suptitle(f'REVO per-iteration statistics\n{log_name}', fontsize=13)

    # ── panel 1: variation ─────────────────────────────────────────────────────
    ax = axes[0]
    shade_regimes(ax, revo_iter, regimes, transitions)
    ax.semilogy(revo_iter, var_init,  'o-', color='steelblue', ms=4,
                label='Initial variation')
    ax.semilogy(revo_iter, var_final, 's-', color='firebrick', ms=4,
                label='Final variation (post-optimisation)')
    ax.fill_between(revo_iter, var_init, var_final,
                    where=(var_final >= var_init),
                    alpha=0.2, color='firebrick', label='Gain from optimisation')
    ax.set_ylabel('Variation (log scale)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, which='both')

    # annotate first REVO iteration
    ax.annotate(
        f'Abs iter {iters[0]} (first REVO)\n'
        f'{var_init[0]:.2e} → {var_final[0]:.2e}',
        xy=(revo_iter[0], var_final[0]),
        xytext=(revo_iter[0] + max(1, len(records) * 0.05),
                var_final[0] * (1.15 if var_final[0] > var_init[0] else 0.9)),
        fontsize=8,
        arrowprops=dict(arrowstyle='->', color='gray'),
        color='firebrick',
    )

    # secondary x-axis: absolute iteration numbers
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    step = max(1, len(revo_iter) // 8)
    tick_revo = revo_iter[::step]
    tick_abs  = iters[::step]
    ax2.set_xticks(tick_revo)
    ax2.set_xticklabels([str(a) for a in tick_abs], fontsize=7)
    ax2.set_xlabel('Absolute iteration number', fontsize=8)

    # ── panel 2: clone/merge ops ───────────────────────────────────────────────
    ax = axes[1]
    shade_regimes(ax, revo_iter, regimes, transitions)
    ax.bar(revo_iter, ops, color='darkorange', alpha=0.8, width=0.7, zorder=2)
    ax.set_ylabel('Clone/merge ops per iteration')
    ax.grid(True, alpha=0.3, axis='y', zorder=0)
    if len(ops) > 1:
        med = np.median(ops[1:])
        ax.axhline(med, ls='--', color='black', alpha=0.5,
                   label=f'Median ops (excl. first REVO iter) = {med:.0f}')
        ax.legend(fontsize=9)

    # ── panel 3: distance thresholds ──────────────────────────────────────────
    ax = axes[2]
    shade_regimes(ax, revo_iter, regimes, transitions)
    ax.plot(revo_iter, mean_dist,  'o-',  color='teal',   ms=4,
            label='Mean pairwise distance')
    ax.plot(revo_iter, merge_dist, 's--', color='purple', ms=4,
            label='Merge distance threshold')
    ax.set_ylabel('Distance')
    ax.set_xlabel('REVO iteration')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # regime fraction labels in axes coordinates so placement is robust
    starts = [1]       + [t + 1 for t in transitions]
    ends   = [t + 1 for t in transitions] + [len(revo_iter) + 1]
    labels = [regimes[s - 1] for s in starts]
    for s, e, lbl in zip(starts, ends, labels):
        mid = (s + e) / 2 - 0.5
        ax.text(mid, 0.04, f'f={lbl}',
                ha='center', va='bottom', fontsize=9, color='purple',
                fontweight='bold', transform=ax.get_xaxis_transform())

    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f'Saved: {out_path}')


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Plot REVO variation statistics from a west.log file.'
    )
    parser.add_argument('log_file',
                        help='Path to west.log (or west_all.log)')
    parser.add_argument('--output', default=None, metavar='FILE',
                        help='Output PNG path (default: <log_dir>/variation_per_iteration.png)')
    parser.add_argument('--no-show', action='store_true',
                        help='Do not attempt to open the PNG after saving')
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        sys.exit(f'Error: file not found: {args.log_file}')

    out_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(args.log_file)),
        'variation_per_iteration.png',
    )

    print(f'Parsing {args.log_file} …')
    records = parse_log(args.log_file)
    if not records:
        sys.exit('No REVO ITERATION STATS blocks found in the log file.')

    print(f'Found {len(records)} REVO iterations '
          f'(abs iters {records[0]["iter"]}–{records[-1]["iter"]})')

    make_plot(records, out_path, log_name=os.path.basename(args.log_file))

    if not args.no_show:
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(out_path)}')


if __name__ == '__main__':
    main()
