#!/usr/bin/env python3
"""
Plot the minimum or maximum progress coordinate value at each iteration
for a WESTPA weighted ensemble simulation.

Usage:
    plot_extrema_pcoord.py <west.h5> [--mode min|max] [--dims D] [--output FILE]
    plot_extrema_pcoord.py <west.h5> --mode max --dims 1 --output extrema.png
"""

import argparse
import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt


def get_iteration_range(h5file):
    """Return sorted list of all iteration numbers."""
    iterations = h5file['iterations']
    return sorted([int(k.replace('iter_', '')) for k in iterations.keys()])


def get_latest_complete_iteration(h5file):
    """Find the latest iteration where all segments are complete."""
    iterations = h5file['iterations']
    iter_nums = sorted([int(k.replace('iter_', '')) for k in iterations.keys()])

    for iter_num in reversed(iter_nums):
        iter_grp = iterations[f'iter_{iter_num:08d}']
        if 'seg_index' not in iter_grp:
            continue
        seg_index = iter_grp['seg_index'][:]
        status = seg_index['status']
        # Status 2 = SEG_STATUS_COMPLETE
        if np.all(status == 2):
            return iter_num
    return None


def plot_extrema_pcoord(h5_path, mode='min', dim=0, first_iter=None, last_iter=None, output=None):
    """
    Plot the min or max progress coordinate value at each iteration.

    Parameters
    ----------
    h5_path : str
        Path to the west.h5 file
    mode : str
        'min' or 'max' (default: 'min')
    dim : int
        Pcoord dimension index to track (default: 0)
    first_iter : int, optional
        First iteration to include (default: 1)
    last_iter : int, optional
        Last iteration to include (default: latest complete)
    output : str, optional
        Output file path. If None, auto-generates based on input file.
    """
    agg_func = np.min if mode == 'min' else np.max

    with h5py.File(h5_path, 'r') as f:
        iter_nums = get_iteration_range(f)

        if not iter_nums:
            print("Error: No iterations found!", file=sys.stderr)
            sys.exit(1)

        # Determine iteration bounds
        if first_iter is None:
            first_iter = iter_nums[0]
        if last_iter is None:
            last_iter = get_latest_complete_iteration(f)
            if last_iter is None:
                print("Error: No complete iterations found!", file=sys.stderr)
                sys.exit(1)
            print(f"Using latest complete iteration as end: {last_iter}")

        # Filter to requested range
        iter_nums = [n for n in iter_nums if first_iter <= n <= last_iter]

        if not iter_nums:
            print(f"Error: No iterations found in range [{first_iter}, {last_iter}]",
                  file=sys.stderr)
            sys.exit(1)

        print(f"Iterations: {iter_nums[0]} to {iter_nums[-1]} ({len(iter_nums)} total)")
        print(f"Mode: {mode}")
        print(f"Pcoord dimension: {dim}")

        iterations = []
        extrema = []
        n_incomplete = 0

        for iter_num in iter_nums:
            iter_key = f'iter_{iter_num:08d}'
            iter_grp = f['iterations'][iter_key]

            if 'pcoord' not in iter_grp or 'seg_index' not in iter_grp:
                continue

            pcoord = iter_grp['pcoord'][:]  # (n_segs, n_timepoints, n_dims)

            # Validate dimension
            if dim >= pcoord.shape[2]:
                print(f"Error: Dimension {dim} requested but pcoord only has "
                      f"{pcoord.shape[2]} dimensions", file=sys.stderr)
                sys.exit(1)

            # Check completion
            seg_index = iter_grp['seg_index'][:]
            status = seg_index['status']
            if not np.all(status == 2):
                n_incomplete += 1

            # Use last timepoint of each segment
            pcoord_vals = pcoord[:, -1, dim]
            extrema.append(agg_func(pcoord_vals))
            iterations.append(iter_num)

        if n_incomplete > 0:
            print(f"Warning: {n_incomplete} incomplete iteration(s) included", file=sys.stderr)

        iterations = np.array(iterations)
        extrema = np.array(extrema)

        print(f"Pcoord {mode} range: {extrema.min():.4f} to {extrema.max():.4f}")

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(iterations, extrema, '-o', color='steelblue', markersize=3, linewidth=1,
            alpha=0.8)

    mode_label = 'Minimum' if mode == 'min' else 'Maximum'
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel(f'{mode_label} Progress Coordinate (dim {dim})', fontsize=12)
    ax.set_title(f'{mode_label} Progress Coordinate vs Iteration\n'
                 f'Iterations {iterations[0]}\u2013{iterations[-1]}', fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Determine output path
    if output is None:
        base = h5_path.rsplit('.h5', 1)[0]
        dim_str = f"_dim{dim}" if dim != 0 else ""
        output = f"{base}_{mode}_pcoord{dim_str}_iter{iterations[0]}-{iterations[-1]}.png"

    plt.savefig(output, dpi=150)
    print(f"\nPlot saved to: {output}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Plot min/max progress coordinate vs iteration for WESTPA simulations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Plot minimum pcoord (dim 0) across all iterations
    %(prog)s west.h5

    # Plot maximum pcoord
    %(prog)s west.h5 --mode max

    # Track a different dimension
    %(prog)s west.h5 --dims 1

    # Restrict to an iteration range
    %(prog)s west.h5 --first-iter 10 --last-iter 200

    # Custom output
    %(prog)s west.h5 --mode max --output max_pcoord.png
"""
    )

    parser.add_argument('h5_file', help='Path to west.h5 file')
    parser.add_argument('--mode', '-m', choices=['min', 'max'], default='min',
                        help='Track minimum or maximum pcoord value (default: min)')
    parser.add_argument('--dims', '-d', type=int, default=0,
                        help='Pcoord dimension to track (default: 0)')
    parser.add_argument('--first-iter', type=int, default=None,
                        help='First iteration to include (default: first available)')
    parser.add_argument('--last-iter', type=int, default=None,
                        help='Last iteration to include (default: latest complete)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: auto-generated)')

    args = parser.parse_args()

    plot_extrema_pcoord(
        h5_path=args.h5_file,
        mode=args.mode,
        dim=args.dims,
        first_iter=args.first_iter,
        last_iter=args.last_iter,
        output=args.output
    )


if __name__ == '__main__':
    main()
